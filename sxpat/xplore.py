from __future__ import annotations
from typing import Iterable, Iterator, List, Literal, Tuple, Union
import dataclasses as dc

import functools as ft
import math
import networkx as nx
import os
from os.path import join as path_join

from sxpat.annotatedGraph import AnnotatedGraph
from sxpat.graph import IOGraph

from sxpat.specifications import Specifications, TemplateType, ErrorPartitioningType, DistanceType

from sxpat.config.config import UNKNOWN, SAT, WEIGHT

from sxpat.utils.filesystem import FS
from sxpat.utils.name import NameData
from sxpat.utils.timer import Timer
from sxpat.utils.print import pprint

from sxpat.metrics import MetricsEstimator

from sxpat.definitions.templates import get_specialized as get_templater
from sxpat.definitions.distances import *

from sxpat.definitions.questions import exists_parameters
from sxpat.definitions.questions.max_distance_evaluation import MaxDistanceEvaluation

from sxpat.solvers import get_specialized as get_solver
from sxpat.solvers import Z3DirectBitVecSolver

from sxpat.converting import set_bool_constants, prevent_assignment
from sxpat.converting import VerilogExporter
from sxpat.converting.legacy import iograph_from_legacy, sgraph_from_legacy


def explore_grid(specs_obj: Specifications):

    # initial setup
    # store circuits
    FS.copy(specs_obj.exact_benchmark, tmp := path_join(specs_obj.path.run.verilog, 'origin.v'))
    specs_obj.exact_benchmark = tmp
    FS.copy(specs_obj.current_benchmark, tmp := path_join(specs_obj.path.run.verilog, 'current.v'))
    specs_obj.current_benchmark = tmp
    # setup caches
    AnnotatedGraph.set_loading_cache_size(specs_obj.wanted_models + 2)
    # constant metrics
    exact_circuit_metrics = MetricsEstimator.estimate_metrics(specs_obj.path.synthesis, specs_obj.exact_benchmark, specs_obj.path.run.temporary)

    #
    all_generated_circuits_data = list()
    previous_subgraphs = []
    obtained_wce_exact = 0
    specs_obj.iteration = 0
    persistence = 0
    persistence_limit = 2
    prev_actual_error = 0 if specs_obj.subxpat else 1
    prev_given_error = 0

    #
    if specs_obj.error_partitioning is ErrorPartitioningType.ASCENDING:
        orig_et = specs_obj.max_error
        if orig_et <= 8:
            et_array = iter(list(range(1, orig_et + 1, 1)))
        else:
            step = orig_et // 8 if orig_et // 8 > 0 else 1
            et_array = iter(list(range(step, orig_et + step, step)))

    #
    while (obtained_wce_exact < specs_obj.max_error):
        specs_obj.iteration += 1
        specs_obj.stats_storage.stage(iteration=specs_obj.iteration)

        # compute error threshold for the iteration
        if not specs_obj.subxpat:
            if prev_actual_error == 0: break
            specs_obj.et = specs_obj.max_error

        elif specs_obj.error_partitioning is ErrorPartitioningType.ASCENDING:
            if (persistence == persistence_limit or prev_actual_error == 0):
                persistence = 0
                try:
                    specs_obj.et = next(et_array)
                except StopIteration:
                    pprint.warning('The error space is exhausted!')
                    break
            else:
                persistence += 1

        elif specs_obj.error_partitioning is ErrorPartitioningType.DESCENDING:
            log2 = int(math.log2(specs_obj.max_error))
            specs_obj.et = 2 ** (log2 - specs_obj.iteration - 2)

        elif specs_obj.error_partitioning is ErrorPartitioningType.SMART_ASCENDING:
            if specs_obj.iteration == 1:
                specs_obj.et = 1
            else:
                if prev_actual_error == 0 or persistence == persistence_limit:
                    specs_obj.et = prev_given_error * 2
                else:
                    specs_obj.et = prev_given_error
                    persistence += 1
            prev_given_error = specs_obj.et

        elif specs_obj.error_partitioning is ErrorPartitioningType.SMART_DESCENDING:
            specs_obj.et = specs_obj.max_error if specs_obj.iteration == 1 else math.ceil(prev_given_error / (2 if prev_actual_error == 0 else 1))
            prev_given_error = specs_obj.et

        else:
            # logging
            specs_obj.stats_storage.stage(ERROR='illegal_state__error_partitioning')
            specs_obj.stats_storage.commit()
            #
            raise NotImplementedError('invalid status')

        #
        if specs_obj.et > specs_obj.max_error or specs_obj.et <= 0: break

        # slash to kill
        if specs_obj.slash_to_kill:
            # first iteration: apply slash
            if specs_obj.iteration == 1:
                # store relevant specifications values
                saved_min_labeling = specs_obj.min_labeling
                saved_exctraction_mode = specs_obj.extraction_mode

                # update specifications
                specs_obj.min_labeling = False
                specs_obj.extraction_mode = 100
                specs_obj.et = specs_obj.error_for_slash

            # second iteration: restore state
            elif specs_obj.iteration == 2:
                # restore specifications values
                specs_obj.min_labeling = saved_min_labeling
                specs_obj.extraction_mode = saved_exctraction_mode

            # skip all iterations implicitly achieved through the slash to kill step
            if specs_obj.iteration > 1 and specs_obj.et < specs_obj.error_for_slash:
                specs_obj.stats_storage.ignore()
                continue

        # logging
        specs_obj.stats_storage.stage(
            error_threshold=specs_obj.et,
            circuit_to_approximate=os.path.relpath(specs_obj.current_benchmark, specs_obj.path.run.base_folder),
        )
        pprint.info1(f'benchmark {specs_obj.current_benchmark}')
        pprint.info1(f'iteration {specs_obj.iteration} with et {specs_obj.et}, available error {specs_obj.max_error}'
                     if specs_obj.subxpat else
                     f'Only one iteration with et {specs_obj.et}')

        # > grid step settings

        # import the graph
        _time = Timer.now()
        current_graph = AnnotatedGraph.cached_load(specs_obj.current_benchmark, specs_obj.path.run)
        exact_graph = AnnotatedGraph.cached_load(specs_obj.exact_benchmark, specs_obj.path.run)
        _time = Timer.now() - _time
        # logging
        specs_obj.stats_storage.stage(annotated_graphs_initialization_time=_time)
        print(f'annotated_graph_loading_time = {_time}')

        # label graph
        if specs_obj.requires_labeling:
            print('started labelling')
            _time = Timer.now()
            label_graph(specs_obj.current_benchmark, current_graph, specs_obj)
            _time = Timer.now() - _time
            # logging
            specs_obj.stats_storage.stage(labelling_time=_time)
            print(f'labelling_time = {_time}')

        # extract subgraph
        _time = Timer.now()
        subgraph_is_available = current_graph.extract_subgraph(specs_obj)
        _time = Timer.now() - _time
        previous_subgraphs.append(current_graph.subgraph)
        # logging
        specs_obj.stats_storage.stage(
            subgraph_extraction_time=_time,
            subgraph_nodes_count=current_graph.subgraph_num_gates,
            subgraph_inputs_count=current_graph.subgraph_num_inputs,
            subgraph_outputs_count=current_graph.subgraph_num_outputs,
        )
        print(f'subgraph_extraction_time = {_time}')
        # logging
        if specs_obj.debug: 
            current_graph.export_annotated_graph()
            print(f'subgraph exported at {current_graph.subgraph_out_path}')

        # guard: skip if no subgraph was found
        if not subgraph_is_available:
            prev_actual_error = 0
            # logging
            pprint.warning(f'No subgraph available.')
            specs_obj.stats_storage.commit()
            continue

        # guard: skip if the subraph is equal to the previous one
        # note:  does not apply for extraction mode 6
        if (
            specs_obj.extraction_mode != 6
            and len(previous_subgraphs) >= 2
            and nx.is_isomorphic(previous_subgraphs[-2], previous_subgraphs[-1], node_match=node_matcher)
        ):
            prev_actual_error = 0
            # logging
            pprint.warning('The subgraph is equal to the previous one. Skipping iteration ...')
            specs_obj.stats_storage.commit()
            continue

        # convert from legacy graphs to refactored circuits
        exact_circ = iograph_from_legacy(exact_graph)
        current_circ = sgraph_from_legacy(current_graph)

        # explore the grid
        pprint.info2(f'Grid ({specs_obj.grid_param_1} X {specs_obj.grid_param_2}) and et={specs_obj.et} exploration started...')
        dominant_cells = []
        for lpp, ppo in CellIterator.factory(specs_obj):
            _cell_time = Timer.now()
            print(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration}: ', end='')
            
            if lpp > len(current_circ.subgraph_inputs): 
                pprint.info3('SKIPPED (lpp > #subgraph_inputs)')
                continue

            # skip if dominated
            if is_dominated((lpp, ppo), dominant_cells):
                pprint.info3('DOMINATED')
                continue

            # > cell step settings

            # update the context
            update_context(specs_obj, lpp, ppo)
            # logging
            specs_obj.stats_storage.stage(
                cell_coord_0=lpp,
                cell_coord_1=ppo,
            )

            # define template (and relative constraints)
            _time = Timer.now()
            param_circ, *param_circ_constr = get_templater(specs_obj).define(current_circ, specs_obj)
            _time_define = Timer.now() - _time
            # define question
            _time = Timer.now()
            base_question = exists_parameters.not_above_threshold_forall_inputs(
                current_circ, param_circ,
                AbsoluteDifferenceOfInteger, specs_obj.et,
            )
            _time_define += Timer.now() - _time
            # logging
            specs_obj.stats_storage.stage(grid_phase_definition_time=_time_define)

            # prepare solver/question
            solve_timer, solve = Timer.from_function(get_solver(specs_obj).solve)
            question = [exact_circ, param_circ, *param_circ_constr, *base_question]
            #
            models = []
            for i in range(specs_obj.wanted_models):
                specs_obj.sub_iteration = f'ca{lpp}_cb{ppo}_m{i}'

                # prevent parameters combination if any
                if len(models) > 0: question.append(prevent_assignment(models[-1], i - 1))

                # solve question
                status, model = solve(question, specs_obj)

                # terminate if status is not sat, otherwise store the model
                if status != 'sat': break
                models.append(model)
            #
            if len(models) > 0: status = 'sat'
            # logging
            _cell_time = Timer.now() - _cell_time
            specs_obj.stats_storage.stage(
                grid_phase_solution_time=solve_timer.total,
                status=status.upper(),
                cell_time=_cell_time,
            )

            # skip if no model found
            if len(models) == 0:
                # if UNKNOWN, store cell as dominant (to skip dominated subgrid)
                if status == UNKNOWN: dominant_cells.append((lpp, ppo))

                # logging
                pprint.warning(status.upper(), f'{_cell_time:.2f}s')
                specs_obj.stats_storage.commit()

            # otherwise verify all models and select best for next iteration
            else:
                pprint.success(f'{status.upper()} ({len(models)} models found)', f'{_cell_time:.2f}s')

                #
                base_path = path_join(specs_obj.path.run.verilog, f'gen_iter{specs_obj.iteration}_model{{model_number}}.v')
                cur_model_results: List[ExpandedCircuitData] = list()
                #
                for model_number, model in enumerate(models):
                    # apply model to circuit
                    a_graph = set_bool_constants(param_circ, model, skip_missing=True)

                    # export approximate graph as verilog
                    verilog_path = base_path.format(model_number=model_number)
                    VerilogExporter.to_file(
                        a_graph, verilog_path,
                        VerilogExporter.Info(model_number=model_number),
                    )

                    # compute circuit metrics
                    _metrics = MetricsEstimator.estimate_metrics(specs_obj.path.synthesis, verilog_path, specs_obj.path.run.temporary)
                    cur_model_results.append(ExpandedCircuitData(
                        verilog_path,
                        _metrics.area,
                        _metrics.power,
                        _metrics.delay,
                    ))

                # verify all models and store errors
                pprint.info1('verifying all approximate circuits ...')
                verification_timer, _error_evaluation = Timer.from_function(error_evaluation)
                # for candidate_path, candidate_data in cur_model_results.items():
                for candidate_data in cur_model_results:
                    #
                    _time = Timer.now()
                    current = AnnotatedGraph.cached_load(candidate_data.path, specs_obj.path.run)
                    cur_graph = iograph_from_legacy(current)
                    _time = Timer.now() - _time
                    # logging
                    specs_obj.stats_storage.stage(erroreval_annotated_graphs_initialization_time=_time)
                    print(f'erreval_annotated_graph_loading_time = {_time}')

                    # compute errors relative to origin and previous
                    candidate_data.error_to_origin = _error_evaluation(exact_circ, cur_graph, specs_obj)
                    candidate_data.error_to_previous = _error_evaluation(current_circ, cur_graph, specs_obj)

                    #
                    if candidate_data.error_to_origin > specs_obj.et:
                        # logging
                        specs_obj.stats_storage.stage(verification_time=verification_timer.total)
                        specs_obj.stats_storage.stage(ERROR='error_verification_failed')
                        specs_obj.stats_storage.commit()
                        #
                        raise Exception(f'ErrorEval Verification FAILED! with wce = {candidate_data.error_to_origin}')

                # logging
                specs_obj.stats_storage.stage(verification_time=verification_timer.total)

                # sort circuits and select best
                sorted_circuits = sorted(cur_model_results, key=ft.cmp_to_key(model_compare))
                best_model_data = sorted_circuits[0]
                pprint.success(f'ErrorEval verification PASSED. ( wce = {best_model_data.error_to_origin} )')

                # store all circuits
                all_generated_circuits_data.extend(sorted_circuits)

                # prepare for next iteration
                specs_obj.current_benchmark = best_model_data.path
                obtained_wce_exact = best_model_data.error_to_origin
                prev_actual_error = best_model_data.error_to_previous

                # logging
                # commit all circuit data
                for (i, circuit_data) in enumerate(sorted_circuits):
                    specs_obj.stats_storage.stage(
                        circuit_path=os.path.relpath(circuit_data.path, specs_obj.path.run.base_folder),
                        circuit_error=circuit_data.error_to_origin,
                        circuit_area=circuit_data.area,
                        circuit_power=circuit_data.power,
                        circuit_delay=circuit_data.delay,
                        circuit_is_best=(i == 0),
                    )
                    specs_obj.stats_storage.commit()
                # print table
                print_current_model(sorted_circuits, origin_circuit_data=exact_circuit_metrics)

                # a valid circuit was found, stop grid exploration
                break

            prev_actual_error = 0

            # debug
            if specs_obj.debug: specs_obj.stats_storage.save()

        if status == SAT and best_model_data.area == 0:
            pprint.info3('Area zero found!\nTerminated.')
            break

    # find best circuit between all the generated ones for each order of metric
    return ResultCircuitsSelection(
        area_power_delay=min(all_generated_circuits_data, key=lambda d: (d.area, d.power, d.delay, d.error_to_origin)),
        area_delay_power=min(all_generated_circuits_data, key=lambda d: (d.area, d.delay, d.power, d.error_to_origin)),
        power_area_delay=min(all_generated_circuits_data, key=lambda d: (d.power, d.area, d.delay, d.error_to_origin)),
        power_delay_area=min(all_generated_circuits_data, key=lambda d: (d.power, d.delay, d.area, d.error_to_origin)),
        delay_area_power=min(all_generated_circuits_data, key=lambda d: (d.delay, d.area, d.power, d.error_to_origin)),
        delay_power_area=min(all_generated_circuits_data, key=lambda d: (d.delay, d.power, d.area, d.error_to_origin)),
    )


def error_evaluation(reference_circuit: IOGraph, current_circuit: IOGraph, specs_obj: Specifications) -> int:
    # define error evaluation question
    p_graph, c_graph = MaxDistanceEvaluation.define(current_circuit)
    # solve error evaluation question
    status, model = Z3DirectBitVecSolver.solve((reference_circuit, p_graph, c_graph), specs_obj)

    #
    assert status == 'sat'
    assert len(model) == 1

    # return the only value (the absolute distance between the two circuits)
    return next(iter(model.values()))


class CellIterator:
    @classmethod
    def factory(cls, specs: Specifications) -> Iterator[Tuple[int, int]]:
        return {
            TemplateType.NON_SHARED: cls.non_shared,
            TemplateType.SHARED: cls.shared,
        }[specs.template](specs)

    @staticmethod
    def shared(specs: Specifications) -> Iterator[Tuple[int, int]]:
        max_pit = specs.max_pit

        # special cell
        yield (0, 1)

        # grid cells
        for pit in range(1, max_pit + 1):
            for its in range(max(pit, specs.outputs), max(pit + 3 + 1, specs.outputs + 1)):
                yield (its, pit)

    @staticmethod
    def non_shared(specs: Specifications) -> Iterator[Tuple[int, int]]:
        max_lpp = specs.max_lpp
        max_ppo = specs.max_ppo

        # special cell
        yield (0, 1)

        # grid cells
        for ppo in range(1, max_ppo + 1):
            for lpp in range(1, max_lpp + 1):
                yield (lpp, ppo)


def is_dominated(coords: Tuple[int, int], dominant_cells: Iterable[Tuple[int, int]]) -> bool:
    (lpp, ppo) = coords
    return any(
        lpp >= dom_lpp and ppo >= dom_ppo
        for (dom_lpp, dom_ppo) in dominant_cells
    )


def update_context(specs_obj: Specifications, lpp: int, ppo: int):
    specs_obj.lpp = lpp
    specs_obj.ppo = specs_obj.pit = ppo


def print_current_model(
        sorted_models_data: List[ExpandedCircuitData],
        origin_circuit_data: MetricsEstimator.Metrics = None,
        normalize: bool = False
) -> None:
    # imports
    from tabulate import tabulate

    #
    data = list()

    # if the exact is given, print that too
    if origin_circuit_data is not None:
        # add exact circuit data
        origin_area, origin_power, origin_delay = (origin_circuit_data.area, origin_circuit_data.power, origin_circuit_data.delay)
        data.append(['Exact', origin_area, origin_power, origin_delay, 0])

        # if the models data should be normalized to the exact, normalize into a copy
        if normalize:
            sorted_models_data = [
                ExpandedCircuitData(
                    model_data.path,
                    model_data.area / origin_area,
                    model_data.power / origin_power,
                    model_data.delay / origin_delay,
                    model_data.error_to_origin
                )
                for model_data in sorted_models_data
            ]

    # aggregate table data
    data.extend(
        (
            NameData.from_filename(model_data.path).total_id,
            model_data.area, model_data.power, model_data.delay,
            model_data.error_to_origin
        )
        for model_data in sorted_models_data
    )
    # print table
    pprint.success(tabulate(data, headers=['Design ID', 'Area', 'Power', 'Delay', 'Error']))


def label_graph(circuit_verilog_path: str, graph: AnnotatedGraph, specs_obj: Specifications) -> None:
    """This function adds the labels inplace to the given graph"""

    # imports
    from sxpat.labeling import labeling_explicit

    # compute weights
    ET_COEFFICIENT = 1
    weights, _ = labeling_explicit(
        circuit_verilog_path, circuit_verilog_path, specs_obj.path.run,
        min_labeling=specs_obj.min_labeling,
        partial_labeling=specs_obj.partial_labeling, partial_cutoff=specs_obj.et * ET_COEFFICIENT,
        parallel=specs_obj.parallel
    )

    # apply weights to graph
    inner_graph: nx.DiGraph = graph.graph
    for (node_name, node_data) in inner_graph.nodes.items():
        node_data[WEIGHT] = weights.get(node_name, -1)
        # TODO: get output's weights in the correct way
        if node_name[:3] == 'out':
            node_data[WEIGHT] = 2**int(node_name[3:])


def node_matcher(n1: dict, n2: dict) -> bool:
    """Return if two node data dicts represent the same semantic node"""
    return (
        n1.get('label') == n2.get('label')
        and n1.get('subgraph', 0) == n2.get('subgraph', 0)
    )


@dc.dataclass
class ExpandedCircuitData:
    path: str
    area: float
    power: float
    delay: float
    error_to_origin: int = None
    error_to_previous: int = None


@dc.dataclass(frozen=True)
class ResultCircuitsSelection:
    area_power_delay: ExpandedCircuitData
    area_delay_power: ExpandedCircuitData
    power_area_delay: ExpandedCircuitData
    power_delay_area: ExpandedCircuitData
    delay_area_power: ExpandedCircuitData
    delay_power_area: ExpandedCircuitData

    @property
    def apd(self): return self.area_power_delay
    @property
    def adp(self): return self.area_delay_power
    @property
    def pad(self): return self.power_area_delay
    @property
    def pda(self): return self.power_delay_area
    @property
    def dap(self): return self.delay_area_power
    @property
    def dpa(self): return self.delay_power_area


def print_results(sel: ResultCircuitsSelection):
    from tabulate import tabulate
    print(tabulate(
        headers=['metrics', 'file', 'area', 'power', 'delay', 'error'],
        tabular_data=[
            ['area->power->delay', sel.apd.path, sel.apd.area, sel.apd.power, sel.apd.delay, sel.apd.error_to_origin],
            ['area->delay->power', sel.adp.path, sel.adp.area, sel.adp.power, sel.adp.delay, sel.adp.error_to_origin],
            ['power->area->delay', sel.pad.path, sel.pad.area, sel.pad.power, sel.pad.delay, sel.pad.error_to_origin],
            ['power->delay->area', sel.pda.path, sel.pda.area, sel.pda.power, sel.pda.delay, sel.pda.error_to_origin],
            ['delay->area->power', sel.dap.path, sel.dap.area, sel.dap.power, sel.dap.delay, sel.dap.error_to_origin],
            ['delay->power->area', sel.dpa.path, sel.dpa.area, sel.dpa.power, sel.dpa.delay, sel.dpa.error_to_origin],
        ],
        tablefmt='simple_outline',
    ))


def model_compare(a: ExpandedCircuitData, b: ExpandedCircuitData) -> Union[Literal[-1] | Literal[0] | Literal[+1]]:
    if a.area < b.area: return -1
    elif a.area > b.area: return +1
    elif a.error_to_origin < b.error_to_origin: return -1
    elif a.error_to_origin > b.error_to_origin: return +1
    else: return 0
