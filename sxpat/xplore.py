import itertools
from typing import Dict, Iterable, Iterator, List, Literal, Optional, Tuple, Union
import dataclasses as dc

import functools as ft
import networkx as nx
import os
from os.path import join as path_join

from sxpat.graph.graph import SGraph, IOGraph
from sxpat.graph.node import Extras, Node
from sxpat.error_iter import ErrorIterator
from sxpat.newag import load_circuit_from_verilog
from sxpat.converting.legacy import iograph_to_sgraph, iograph_with_weights

from sxpat.specifications import Specifications, TemplateType, ErrorPartitioningType

from sxpat.constants.misc import UNKNOWN, SAT

from sxpat.utils.filesystem import FS
from sxpat.utils.iterators import while_predicate
from sxpat.utils.names import extract_name
from sxpat.utils.timer import Timer
from sxpat.utils.print import pprint

from sxpat.metrics import MetricsEstimator

from sxpat.definitions.templates import get_specialized as get_templater
from sxpat.definitions.distances import *

from sxpat.definitions.questions import exists_parameters
from sxpat.definitions.questions.max_distance_evaluation import MaxDistanceEvaluation

from sxpat.subgraph_extractions.legacy import *
from sxpat.subgraph_extractions.manual import extract

from sxpat.solvers import get_specialized as get_solver
from sxpat.solvers import Z3DirectBitVecSolver

from sxpat.converting import set_bool_constants, prevent_assignment
from sxpat.converting import VerilogExporter

from sxpat.labelling.labelling import Labelling


def explore_grid(specs_obj: Specifications):
    # initial setup
    # store circuits
    FS.copy(specs_obj.exact_benchmark, tmp := path_join(specs_obj.path.run.verilog, 'origin.v'))
    specs_obj.exact_benchmark = tmp
    FS.copy(specs_obj.current_benchmark, tmp := path_join(specs_obj.path.run.verilog, 'current.v'))
    specs_obj.current_benchmark = tmp
    # load exact circuit and compute its metrics
    exact_graph = load_circuit_from_verilog(specs_obj.exact_benchmark, specs_obj.path.run)
    exact_circuit_metrics = MetricsEstimator.estimate_metrics(
        specs_obj.path.synthesis, specs_obj.exact_benchmark, specs_obj.path.run.temporary)

    #
    all_generated_circuits_data = [
        ExpandedCircuitData(
            'origin.v',
            path_join(specs_obj.path.run.verilog, f'origin.v'),
            exact_circuit_metrics.area,
            exact_circuit_metrics.power,
            exact_circuit_metrics.delay,
            0,
            0
        )
    ]
    specs_obj.details_storage.add(
        origin_circuit_area=exact_circuit_metrics.area,
        origin_circuit_power=exact_circuit_metrics.power,
        origin_circuit_delay=exact_circuit_metrics.delay,
    )

    #
    previous_graphs: List[SGraph] = list()
    obtained_wce_exact = 0
    specs_obj.iteration = 0

    # initialize error iterator (error partitioning)
    erriter = error_iterator(specs_obj)
    if erriter is None:
        # logging
        specs_obj.stats_storage.stage(ERROR='illegal_state__error_partitioning')
        specs_obj.stats_storage.commit()
        #
        raise NotImplementedError('invalid error iteration')

    #
    for (
        specs_obj.iteration,
        specs_obj.et,
        *_,
    ) in zip(
        itertools.count(1),  # iteration id
        erriter,  # error threshold for the iteration
        while_predicate(lambda: obtained_wce_exact < specs_obj.max_error),  # normal continuation
    ):
        # slash to kill
        if specs_obj.slash_to_kill:
            # first iteration: apply slash
            if specs_obj.iteration == 1:
                # store relevant specifications values
                preserved_slash_state = (specs_obj.min_labeling, specs_obj.extraction_mode)

                # update specifications
                specs_obj.min_labeling = False
                specs_obj.extraction_mode = 100
                specs_obj.et = specs_obj.error_for_slash

            # second iteration: restore state
            elif specs_obj.iteration == 2:
                (specs_obj.min_labeling, specs_obj.extraction_mode) = preserved_slash_state

            # skip all iterations implicitly achieved through the slash to kill step
            if specs_obj.iteration > 1 and specs_obj.et < specs_obj.error_for_slash:
                specs_obj.stats_storage.ignore()
                continue

        # logging
        specs_obj.stats_storage.stage(
            iteration=specs_obj.iteration,
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
        current_graph = load_circuit_from_verilog(specs_obj.current_benchmark, specs_obj.path.run)
        _time = Timer.now() - _time
        # logging
        specs_obj.stats_storage.stage(annotated_graphs_initialization_time=_time)
        print(f'annotated_graph_loading_time = {_time}')

        # label graph
        if specs_obj.requires_labeling:
            print('started labelling')
            _time = Timer.now()

            weights = label_graph(current_graph, specs_obj)
            for (i, n) in enumerate(current_graph.outputs_names):
                weights[n] = 2 ** i

            current_graph = iograph_with_weights(current_graph, weights)
            _time = Timer.now() - _time

            # logging
            specs_obj.stats_storage.stage(labelling_time=_time)
            print(f'labelling_time = {_time}')

        # extract subgraph
        _time = Timer.now()
        subgraph_nodes = extract_subgraph(current_graph, specs_obj)
        subgraph_is_available = len(subgraph_nodes) > 0
        current_graph = iograph_to_sgraph(current_graph, subgraph_nodes)
        _time = Timer.now() - _time
        previous_graphs.append(current_graph)

        # logging
        specs_obj.stats_storage.stage(
            subgraph_extraction_time=_time,
            subgraph_nodes_count=len(current_graph.subgraph_nodes),
            subgraph_inputs_count=len(current_graph.subgraph_inputs),
            subgraph_outputs_count=len(current_graph.subgraph_outputs),
        )
        print(f'subgraph_extraction_time = {_time}')
        # logging
        if specs_obj.debug:
            from sxpat.newag import export_annotated_graph
            # construct path
            _path = path_join(specs_obj.path.run.graphviz, f'{extract_name(specs_obj.current_benchmark)}_subgraph.gv')
            _p_path = os.path.relpath(_path, specs_obj.path.run.base_folder)
            # export graph
            export_annotated_graph(current_graph, _path)
            specs_obj.stats_storage.stage(subgraph_dot=_p_path)
            print(f'subgraph exported at {_path}')

        # guard: skip if no subgraph was found
        if not subgraph_is_available:
            erriter.give_feedback(error_to_previous=0)
            # logging
            pprint.warning(f'No subgraph available.')
            specs_obj.stats_storage.commit()
            continue

        # guard: skip if the subraph is equal to the previous one
        # note:  does not apply for extraction mode 6 and 0
        if (
            specs_obj.extraction_mode != 6 and specs_obj.extraction_mode != 0
            and len(previous_graphs) >= 2
            and are_circuits_equal(previous_graphs[-2], previous_graphs[-1])
        ):
            erriter.give_feedback(error_to_previous=0)
            # logging
            pprint.warning('The subgraph is equal to the previous one. Skipping iteration ...')
            specs_obj.stats_storage.commit()
            continue

        # explore the grid
        pprint.info2(f'Grid ({specs_obj.grid_param_1} X {specs_obj.grid_param_2}) and et={specs_obj.et} exploration started...')
        dominant_cells = []
        for lpp, ppo in CellIterator.factory(specs_obj):
            _cell_time = Timer.now()
            print(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration}: ', end='')

            if lpp > len(current_graph.subgraph_inputs):
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
            param_circ, *param_circ_constr = get_templater(specs_obj).define(current_graph, specs_obj)
            _time_define = Timer.now() - _time
            # define question
            _time = Timer.now()
            base_question = exists_parameters.not_above_threshold_forall_inputs(
                current_graph, param_circ,
                AbsoluteDifferenceOfInteger, specs_obj.et,
            )
            _time_define += Timer.now() - _time
            # logging
            specs_obj.stats_storage.stage(grid_phase_definition_time=_time_define)

            # prepare solver/question
            solve_timer, solve = Timer.from_function(get_solver(specs_obj).solve)
            question = [exact_graph, param_circ, *param_circ_constr, *base_question]
            #
            models = []
            status = UNKNOWN
            for i in range(specs_obj.wanted_models):
                specs_obj.sub_iteration = f'ca{lpp}_cb{ppo}_m{i}'

                # prevent parameters combination if any
                if len(models) > 0: question.append(prevent_assignment(models[-1], i - 1))

                # solve question
                status, model = solve(question, specs_obj)

                # terminate if status is not sat, otherwise store the model
                if status != SAT: break
                models.append(model)
            #
            if len(models) > 0: status = SAT
            # logging
            _cell_time = Timer.now() - _cell_time
            specs_obj.stats_storage.stage(
                grid_phase_solution_time=solve_timer.total,
                status=status.upper(),
                cell_time=_cell_time,
            )

            # skip if no model found
            if status != SAT:
                # if UNKNOWN, store cell as dominant (to skip dominated subgrid)
                if status == UNKNOWN: dominant_cells.append((lpp, ppo))

                # logging
                pprint.warning(status.upper(), f'{_cell_time:.2f}s')
                specs_obj.stats_storage.commit()

            # otherwise verify all models and select best for next iteration
            else:
                pprint.success(f'{status.upper()} ({len(models)} models found)', f'{_cell_time:.2f}s')

                #
                cur_model_results: List[ExpandedCircuitData] = list()
                #
                for model_number, model in enumerate(models):
                    # apply model to circuit
                    a_graph = set_bool_constants(param_circ, model, skip_missing=True)

                    # export approximate graph as verilog
                    circuit_id = f'gen_iter{specs_obj.iteration}_model{model_number}'
                    verilog_path = path_join(specs_obj.path.run.verilog, f'{circuit_id}.v')
                    VerilogExporter.to_file(
                        a_graph, verilog_path,
                        VerilogExporter.Info(model_number=model_number),
                    )

                    # compute circuit metrics
                    _metrics = MetricsEstimator.estimate_metrics(
                        specs_obj.path.synthesis, verilog_path,
                        specs_obj.path.run.temporary,
                    )
                    cur_model_results.append(ExpandedCircuitData(
                        circuit_id,
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
                    cur_graph = load_circuit_from_verilog(verilog_path, specs_obj.path.run)
                    _time = Timer.now() - _time
                    # logging
                    specs_obj.stats_storage.stage(erroreval_annotated_graphs_initialization_time=_time)
                    print(f'erreval_annotated_graph_loading_time = {_time}')

                    # compute errors relative to origin and previous
                    candidate_data.error_to_origin = _error_evaluation(exact_graph, cur_graph, specs_obj)
                    candidate_data.error_to_previous = _error_evaluation(current_graph, cur_graph, specs_obj)

                    #
                    if candidate_data.error_to_origin > specs_obj.et:
                        # logging
                        specs_obj.stats_storage.stage(verification_time=verification_timer.total)
                        specs_obj.stats_storage.stage(ERROR='error_verification_failed')
                        specs_obj.stats_storage.commit()
                        #
                        raise Exception(
                            f'ErrorEval Verification FAILED with wce = {candidate_data.error_to_origin}'
                            f' for circuit {candidate_data.path}'
                        )

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
                obtained_wce_exact: int = best_model_data.error_to_origin  # pyright: ignore[reportAssignmentType]
                erriter.give_feedback(
                    error_to_origin=best_model_data.error_to_origin,  # pyright: ignore[reportArgumentType]
                    error_to_previous=best_model_data.error_to_previous,  # pyright: ignore[reportArgumentType]
                )

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

            erriter.give_feedback(error_to_previous=0)

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
    assert status == SAT
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
        origin_circuit_data: Optional[MetricsEstimator.Metrics] = None,
        normalize: bool = False
) -> None:
    # imports
    from tabulate import tabulate

    #
    data = list()

    # if the exact is given, print that too
    if origin_circuit_data is not None:
        # add exact circuit data
        origin_area, origin_power, origin_delay = (
            origin_circuit_data.area, origin_circuit_data.power, origin_circuit_data.delay)
        data.append(['Exact', origin_area, origin_power, origin_delay, 0])

        # if the models data should be normalized to the exact, normalize into a copy
        if normalize:
            sorted_models_data = [
                ExpandedCircuitData(
                    '',
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
            model_data.id,
            model_data.area, model_data.power, model_data.delay,
            model_data.error_to_origin
        )
        for model_data in sorted_models_data
    )
    # print table
    pprint.success(tabulate(data, headers=['Design ID', 'Area', 'Power', 'Delay', 'Error']))


def extract_subgraph(circuit: IOGraph, specs_obj: Specifications) -> List[str]:
    return {
        0: find_subgraph_output_nodes_ascendant,
        1: find_subgraph,
        2: find_subgraph_sensitivity,
        3: find_subgraph_sensitivity_no_io_constraints,
        4: find_subgraph_feasible,
        42: extract,
        5: find_subgraph_feasible_hard,
        55: find_subgraph_feasible_hard_datatype_bitvec,
        6: find_subgraph_feasible_hard_datatype_bitvec_mintreshold,
        100: slash_to_kill,
        11: find_subgraph_feasible_soft,
        12: find_subgraph_feasible_soft_outputs,
    }[specs_obj.extraction_mode](circuit, specs_obj)


def error_iterator(specs: Specifications) -> ErrorIterator | None:
    import sxpat.error_iter as _ei

    if specs.subxpat:
        erriter = {
            ErrorPartitioningType.ASCENDING: _ei.AscendingEI(specs.max_error, 2),
            ErrorPartitioningType.SMART_ASCENDING: _ei.SmartAscendingEI(specs.max_error, 2),
            ErrorPartitioningType.DESCENDING: _ei.DescendingEI(specs.max_error),
            ErrorPartitioningType.SMART_DESCENDING: _ei.SmartDescendingEI(specs.max_error),
        }.get(specs.error_partitioning, None)
    else:
        erriter = _ei.XPATEI(specs.max_error)

    return erriter


def label_graph(circuit: IOGraph, specs_obj: Specifications) -> Dict[str, int]:
    """This function adds the labels inplace to the given graph"""

    reference: IOGraph = circuit
    to_be_labelled: IOGraph = circuit

    #
    labeller = Labelling(
        reference, to_be_labelled,
        specs_obj,
        minimise=specs_obj.min_labeling,
        use_functions=True,
    )
    weights = labeller.label_graph(
        partial_cutoff=specs_obj.et if specs_obj.partial_labeling else -1,
        parallelism=int(specs_obj.parallel) * (os.cpu_count() or 1)
    )

    return weights


def are_circuits_equal(g1: SGraph, g2: SGraph) -> bool:
    class _Node(Node, Extras): ...

    def node_matcher(_n1: dict, _n2: dict) -> bool:
        n1: _Node = _n1[SGraph.K]
        n2: _Node = _n2[SGraph.K]
        return (
            type(n1) == type(n2)
            and n1.in_subgraph == n2.in_subgraph
        )

    return nx.is_isomorphic(g1._inner, g2._inner, node_match=node_matcher)


@dc.dataclass
class ExpandedCircuitData:
    id: str
    path: str
    area: float
    power: float
    delay: float
    error_to_origin: Optional[int] = None
    error_to_previous: Optional[int] = None


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


def model_compare(a: ExpandedCircuitData, b: ExpandedCircuitData) -> Union[Literal[-1], Literal[0], Literal[+1]]:
    if a.area < b.area: return -1
    elif a.area > b.area: return +1
    elif a.error_to_origin < b.error_to_origin: return -1
    elif a.error_to_origin > b.error_to_origin: return +1
    else: return 0
