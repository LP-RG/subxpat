from __future__ import annotations
from typing import Dict, Iterable, Iterator, List, Tuple

from tabulate import tabulate
import functools as ft
import csv
import math
import networkx as nx
import itertools as it

from sxpat.annotatedGraph import AnnotatedGraph
from sxpat.graph import IOGraph, SGraph
from sxpat.graph.node import BoolVariable, Identity

from sxpat.specifications import Specifications, TemplateType, ErrorPartitioningType, DistanceType

from Z3Log.config import path as z3logpath
from sxpat.config import paths as sxpatpaths
from sxpat.config.config import *

from sxpat.utils.collections import iterable_replace
from sxpat.utils.filesystem import FS
from sxpat.utils.name import NameData
from sxpat.utils.timer import Timer
from sxpat.utils.print import pprint

from sxpat.metrics import MetricsEstimator
from sxpat.stats import Stats, sxpatconfig, Model

from sxpat.definitions.templates import get_specialized as get_templater
from sxpat.definitions.templates import v2Phase1
from sxpat.definitions.distances import *

from sxpat.definitions.questions import exists_parameters
from sxpat.definitions.questions.max_distance_evaluation import MaxDistanceEvaluation
from sxpat.labeling import labeling_explicit
from sxpat.temp_labelling import labeling

from sxpat.solvers import get_specialized as get_solver
from sxpat.solvers import Z3DirectBitVecSolver

from sxpat.converting import set_bool_constants, prevent_assignment
from sxpat.converting import VerilogExporter
from sxpat.converting.legacy import iograph_from_legacy, sgraph_from_legacy


def explore_grid(specs_obj: Specifications):
    previous_subgraphs = []

    labeling_time: float = -1
    subgraph_extraction_time: float = -1

    # Select toolname
    toolname = get_toolname(specs_obj)

    # initial setup
    exact_file_path = f'{sxpatpaths.INPUT_PATH["ver"][0]}/{specs_obj.exact_benchmark}.v'

    # create stat and template object
    stats_obj = Stats(specs_obj)

    obtained_wce_exact = 0
    specs_obj.iteration = 0
    persistence = 0
    persistence_limit = 2
    prev_actual_error = 0 if specs_obj.subxpat else 1
    prev_given_error = 0
    v2 = specs_obj.template == TemplateType.V2

    distance_function = {
        (DistanceType.ABSOLUTE_DIFFERENCE_OF_INTEGERS): AbsoluteDifferenceOfInteger,
        (DistanceType.ABSOLUTE_DIFFERENCE_OF_WEIGHTED_SUM): AbsoluteDifferenceOfWeightedSum,
        (DistanceType.HAMMING_DISTANCE): HammingDistance,
        (DistanceType.WEIGHTED_HAMMING_DISTANCE): WeightedHammingDistance,
    }[(specs_obj.subgraph_distance)]

    # setup caches
    AnnotatedGraph.set_loading_cache_size(specs_obj.wanted_models + 2)

    if specs_obj.error_partitioning is ErrorPartitioningType.ASCENDING:
        orig_et = specs_obj.max_error
        if orig_et <= 8:
            et_array = iter(list(range(1, orig_et + 1, 1)))
        else:
            step = orig_et // 8 if orig_et // 8 > 0 else 1
            et_array = iter(list(range(step, orig_et + step, step)))

    while (obtained_wce_exact < specs_obj.max_error):
        specs_obj.iteration += 1
        if not specs_obj.subxpat:
            if prev_actual_error == 0:
                break
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
            raise NotImplementedError('invalid status')

        if specs_obj.et > specs_obj.max_error or specs_obj.et <= 0:
            break

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
                continue

        pprint.info1(f'iteration {specs_obj.iteration} with et {specs_obj.et}, available error {specs_obj.max_error}'
                     if (specs_obj.subxpat) else
                     f'Only one iteration with et {specs_obj.et}')

        if specs_obj.current_benchmark.endswith('.v'):
            specs_obj.current_benchmark = specs_obj.current_benchmark[:-2]
        pprint.info1(f'benchmark {specs_obj.current_benchmark}')

        # > grid step settings

        # import the graph
        ag_loading_time = Timer.now()
        current_graph = AnnotatedGraph.cached_load(specs_obj.current_benchmark)
        exact_graph = AnnotatedGraph.cached_load(specs_obj.exact_benchmark)
        print(f'annotated_graph_loading_time = {(ag_loading_time := (Timer.now() - ag_loading_time))}')

        # label graph
        if specs_obj.requires_labeling:
            label_timer, _label_graph = Timer.from_function(label_graph)
            _label_graph(current_graph, specs_obj)
            print(f'labeling_time = {(labeling_time := label_timer.total)}')

        # extract subgraph
        subex_timer, extract_subgraph = Timer.from_function(current_graph.extract_subgraph)
        subgraph_is_available = extract_subgraph(specs_obj)
        previous_subgraphs.append(current_graph.subgraph)
        print(f'subgraph_extraction_time = {(subgraph_extraction_time := subex_timer.total)}')

        # todo:wip: export subgraph
        FS.mkdir(folder := 'output/gv/subgraphs')
        graph_path = f'{folder}/{specs_obj.current_benchmark}_et{specs_obj.et}_mode{specs_obj.extraction_mode}_omax{specs_obj.omax}.gv'
        current_graph.export_annotated_graph(graph_path)
        print(f'subgraph exported at {graph_path}')

        # guard: skip if no subgraph was found
        if not subgraph_is_available:
            pprint.warning(f'No subgraph available.')
            prev_actual_error = 0
            continue

        # guard: skip if the subraph is equal to the previous one
        # note:  does not apply for extraction mode 6
        if (
            specs_obj.extraction_mode != 6
            and len(previous_subgraphs) >= 2
            and nx.is_isomorphic(previous_subgraphs[-2], previous_subgraphs[-1], node_match=node_matcher)
        ):
            pprint.warning('The subgraph is equal to the previous one. Skipping iteration ...')
            prev_actual_error = 0
            continue

        # convert from legacy graphs to refactored circuits
        exact_circ = iograph_from_legacy(exact_graph)
        current_circ = sgraph_from_legacy(current_graph)

        #
        if v2:
            from sxpat.definitions.questions import min_subdistance_with_error
            # DEFINE
            v2p1_define_timer = Timer()

            # TODO
            # question
            define_question = v2p1_define_timer.wrap(min_subdistance_with_error.variant_1)
            base_question = define_question(current_circ, specs_obj, AbsoluteDifferenceOfInteger, distance_function)

            # SOLVE
            v2p1_solve_timer = Timer()

            question = [exact_circ, param_circ, param_circ_constr]
            solve = v2p1_solve_timer.wrap(get_solver(specs_obj).solve)
            status, model = solve(question, specs_obj)

            # extract v2 threshold
            v2_threshold = {
                'sat': lambda: model['sum_s_out'] - 1,
                'unsat': lambda: sum(n.weight for n in current_circ.subgraph_outputs),
            }[status]()

            # store error treshold and replace with v2 threshold
            specs_obj.et, v2_threshold = v2_threshold, specs_obj.et

        # explore the grid
        pprint.info2(f'Grid ({specs_obj.grid_param_1} X {specs_obj.grid_param_2}) and et={specs_obj.et} exploration started...')
        dominant_cells = []
        for lpp, ppo in CellIterator.factory(specs_obj):
            print(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration}: ', end='')

            if is_dominated((lpp, ppo), dominant_cells):
                pprint.info3('DOMINATED')
                continue

            # > cell step settings

            # update the context
            update_context(specs_obj, lpp, ppo)

            if v2:
                rem = current_circ.subgraph_inputs
                current_circ = SGraph(
                    it.chain(
                        (n for n in current_circ.nodes if n.in_subgraph),
                        (BoolVariable(n.name) for n in current_circ.subgraph_inputs),
                        (Identity(f's_out{i}', operands=(n.name,)) for i, n in enumerate(current_circ.subgraph_outputs)),
                    ),
                    inputs_names=(n.name for n in current_circ.subgraph_inputs),
                    outputs_names=(f's_out{i}' for i in range(len(current_circ.subgraph_outputs))),
                )
                exact_circ = IOGraph(
                    (n for n in current_circ.nodes),
                    inputs_names=(n.name for n in rem),
                    outputs_names=(f's_out{i}' for i in range(len(current_circ.subgraph_outputs))),
                )

            # DEFINE
            define_timer = Timer()

            # template (and relative constraints)
            define_template = define_timer.wrap(get_templater(specs_obj).define)
            param_circ, *param_circ_constr = define_template(current_circ, specs_obj)

            # question
            define_question = define_timer.wrap(exists_parameters.not_above_threshold_forall_inputs)
            base_question = define_question(current_circ, param_circ, distance_function, specs_obj.et)

            # SOLVE
            solve_timer, solve = Timer.from_function(get_solver(specs_obj).solve)
            question = [exact_circ, param_circ, *param_circ_constr, *base_question]

            models = []
            for i in range(specs_obj.wanted_models):
                # prevent parameters combination if any
                if len(models) > 0: question.append(prevent_assignment(models[-1], i - 1))

                # solve question
                status, model = solve(question, specs_obj)

                # terminate if status is not sat, otherwise store the model
                if status != 'sat': break
                models.append(model)

            if len(models) > 0: status = 'sat'

            # legacy adaptation
            execution_time = define_timer.total + solve_timer.total

            # restore error treshold
            if v2: specs_obj.et = v2_threshold

            if len(models) == 0:
                pprint.warning(f'{status.upper()}')

                # store model
                this_model_info = Model(id=0, status=status.upper(), cell=(lpp, ppo), et=specs_obj.et, iteration=specs_obj.iteration,
                                        labeling_time=labeling_time,
                                        subgraph_extraction_time=subgraph_extraction_time,
                                        subgraph_number_inputs=current_graph.subgraph_num_inputs,
                                        subgraph_number_outputs=current_graph.subgraph_num_outputs,
                                        subxpat_v1_time=execution_time)
                stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_info)

                # store cell as dominant (to skip dominated subgrid)
                if status == UNKNOWN: dominant_cells.append((lpp, ppo))

            else:
                pprint.success(f'{status.upper()} ({len(models)} models found)')

                # TODO:#15: use serious name generator
                base_path = f'input/ver/{specs_obj.exact_benchmark}_{specs_obj.time_id}_i{specs_obj.iteration}_{{model_number}}.v'
                cur_model_results: Dict[str: List[float, float, float, (int, int), int, int]] = {}

                for model_number, model in enumerate(models):

                    a_graph = set_bool_constants(param_circ, model, skip_missing=True)

                    if v2:
                        s_graph_complete = sgraph_from_legacy(current_graph)
                        updated_nodes = dict()
                        for i, out_node in enumerate(s_graph_complete.subgraph_outputs):
                            for succ in filter(lambda n: not n.in_subgraph, s_graph_complete.successors(out_node)):
                                new_operands = iterable_replace(succ.operands, out_node.name, f'a_s_out{i}')
                                updated_nodes[succ.name] = succ.copy(operands=new_operands)
                        a_graph = SGraph(
                            it.chain(
                                (n for n in s_graph_complete.nodes if not n.in_subgraph and not n.name in updated_nodes),
                                (n for n in a_graph.nodes if not n.name in s_graph_complete or not s_graph_complete[n.name] in s_graph_complete.subgraph_inputs),
                                updated_nodes.values(),
                            ),
                            inputs_names=(n.name for n in s_graph_complete.inputs),
                            outputs_names=(n.name for n in s_graph_complete.outputs),
                        )

                    # export approximate graph as verilog
                    # TODO:#15: use serious name generator
                    verilog_path = base_path.format(model_number=model_number)
                    VerilogExporter.to_file(
                        a_graph, verilog_path,
                        VerilogExporter.Info(model_number=model_number),
                    )

                    # compute metrics
                    metrics = MetricsEstimator.estimate_metrics(specs_obj.path.synthesis, verilog_path)
                    verilog_filename = verilog_path[10:]  # TODO: this should be kept as the path, we should update the usages to use the path instead of the name
                    cur_model_results[verilog_filename] = [
                        metrics.area,
                        metrics.power,
                        metrics.delay,
                        (lpp, ppo),
                        None,  # abs diff to exact
                        None  # abs diff to previous
                    ]

                # todo: should we refactor with pandas?
                with open(f'{z3logpath.OUTPUT_PATH["report"][0]}/area_model_nummodels{specs_obj.wanted_models}_{specs_obj.current_benchmark}_{specs_obj.et}_{toolname}.csv', 'w') as f:
                    csvwriter = csv.writer(f)
                    header = list(range(len(cur_model_results)))
                    all = list(cur_model_results.values())
                    content = [f for (f, *_) in all]

                    csvwriter.writerow(header)
                    csvwriter.writerow(content)

                # verify all models and store errors
                pprint.info1('verifying all approximate circuits ...')
                for candidate_name, candidate_data in cur_model_results.items():

                    candidate_data[4] = error_evaluation(exact_circ, candidate_name[:-2], specs_obj)
                    candidate_data[5] = error_evaluation(current_circ, candidate_name[:-2], specs_obj)

                    if candidate_data[4] > specs_obj.et:
                        pprint.error(f'ErrorEval Verification FAILED! with wce {candidate_data[4]}')
                        stats_obj.store_grid()
                        return stats_obj

                pprint.success('ErrorEval Verification PASSED')

                # sort circuits
                sorted_circuits = sorted(cur_model_results.items(), key=ft.cmp_to_key(model_compare))

                # select best circuit
                best_name, best_data = sorted_circuits[0]
                obtained_wce_exact = best_data[4]
                prev_actual_error = best_data[5]

                specs_obj.current_benchmark = best_name
                best_model_info = Model(id=0,
                                        status=status.upper(),
                                        cell=(lpp, ppo),
                                        et=best_data[4],
                                        iteration=specs_obj.iteration,
                                        area=best_data[0],
                                        total_power=best_data[1],
                                        delay=best_data[2],
                                        labeling_time=labeling_time,
                                        subgraph_extraction_time=subgraph_extraction_time,
                                        subgraph_number_inputs=current_graph.subgraph_num_inputs,
                                        subgraph_number_outputs=current_graph.subgraph_num_outputs,
                                        subxpat_v1_time=execution_time)

                stats_obj.grid.cells[lpp][ppo].store_model_info(best_model_info)
                pprint.success(f'ErrorEval PASS! with total wce = {best_data[4]}')

                exact_stats = MetricsEstimator.estimate_metrics(specs_obj.path.synthesis, exact_file_path, True)
                print_current_model(sorted_circuits, normalize=False, exact_stats=exact_stats)
                store_current_model(cur_model_results, exact_stats=exact_stats, benchmark_name=specs_obj.current_benchmark, et=specs_obj.et,
                                    encoding=specs_obj.encoding, subgraph_extraction_time=subgraph_extraction_time, labeling_time=labeling_time)

                break  # SAT found, stop grid exploration

            prev_actual_error = 0

        if status == SAT and best_data[0] == 0:
            pprint.info3('Area zero found!\nTerminated.')
            break

    stats_obj.store_grid()
    return stats_obj


def error_evaluation(e_graph: IOGraph, graph_name: str, specs_obj: Specifications):
    ag_loading_time = Timer.now()
    current = AnnotatedGraph.cached_load(graph_name)
    print(f'erreval_annotated_graph_loading_time = {(ag_loading_time := (Timer.now() - ag_loading_time))}')

    cur_graph = iograph_from_legacy(current)

    p_graph, c_graph = MaxDistanceEvaluation.define(cur_graph)
    status, model = Z3DirectBitVecSolver.solve((e_graph, p_graph, c_graph), specs_obj)

    assert status == 'sat'
    assert len(model) == 1

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


def print_current_model(sorted_models: List[Tuple[str, List]], normalize: bool = True, exact_stats: List = None) -> None:
    data = []

    if exact_stats:
        # add exact circuit data
        e_area, e_power, e_delay, *_ = exact_stats
        data.append(['Exact', e_area, e_power, e_delay, 0])

        if normalize:
            for _, stats in sorted_models:
                stats[0] = (stats[0] / e_area) * 100
                stats[1] = (stats[1] / e_power) * 100
                stats[2] = (stats[2] / e_delay) * 100

    # keep wanted models
    if len(sorted_models) > 10:
        sorted_models = sorted_models[0:10]

    # add candidates data
    for c_name, c_stats in sorted_models:
        c_id = NameData.from_filename(c_name).total_id
        c_area, c_power, c_delay, _, c_error, _ = c_stats
        data.append([c_id, c_area, c_power, c_delay, c_error])

    pprint.success(tabulate(data, headers=['Design ID', 'Area', 'Power', 'Delay', 'Error']))


def store_current_model(cur_model_result: Dict, benchmark_name: str, et: int, encoding: int, subgraph_extraction_time: float, labeling_time: float, exact_stats: List = None) -> None:
    with open(f"{z3logpath.OUTPUT_PATH['report'][0]}/area_power_delay.csv", 'a') as f:
        csvwriter = csv.writer(f)

        # to avoid duplicate data
        if encoding == 2:
            if exact_stats:
                e_area, e_power, e_delay, *_ = exact_stats
                exact_data = (
                    benchmark_name,
                    'Exact',
                    e_area, e_power, e_delay,
                    et, encoding,
                    labeling_time, subgraph_extraction_time,
                )
            else:
                exact_data = ()
            csvwriter.writerow(exact_data)

        # get best candidate data
        sorted_candidates = sorted(cur_model_result.items(), key=lambda x: x[1])
        c_name, c_stats = sorted_candidates[0]
        c_id = NameData.from_filename(c_name).total_id
        c_area, c_power, c_delay, *_ = c_stats

        approx_data = (
            benchmark_name,
            c_id,
            c_area, c_power, c_delay,
            et, encoding,
            labeling_time, subgraph_extraction_time,
        )
        csvwriter.writerow(approx_data)


def label_graph(graph: AnnotatedGraph, specs_obj: Specifications) -> None:
    """This function adds the labels inplace to the given graph"""

    # compute weights
    ET_COEFFICIENT = 1
    if specs_obj.iteration == 1:
        weights = labeling(graph.name, graph.name, specs_obj.et * ET_COEFFICIENT)
    else:
        weights, check_pair = labeling_explicit(
            graph.name, graph.name,
            min_labeling=specs_obj.min_labeling,
            partial_labeling=specs_obj.partial_labeling, partial_cutoff=specs_obj.et * ET_COEFFICIENT,
            parallel=specs_obj.parallel
        )
    

        for key in check_pair.keys():
            if check_pair[key] == False:
                print(f'model from labeling didn\'t match handle.upper():\n{graph.name}\n{key}')

    # apply weights to graph
    inner_graph: nx.DiGraph = graph.graph
    for (node_name, node_data) in inner_graph.nodes.items():
        node_data[WEIGHT] = weights.get(node_name, -1)
        # TODO: get output's weights in the correct way
        if node_name[:3] == 'out':
            node_data[WEIGHT] = 2**int(node_name[3:])


def get_toolname(specs_obj: Specifications) -> str:
    message, toolname = {
        (False, TemplateType.NON_SHARED): ('XPAT', sxpatconfig.XPAT),
        (False, TemplateType.SHARED): ('Shared XPAT', sxpatconfig.SHARED_XPAT),
        (True, TemplateType.NON_SHARED): ('SubXPAT', sxpatconfig.SUBXPAT),
        (True, TemplateType.SHARED): ('Shared SubXPAT', sxpatconfig.SHARED_SUBXPAT),
        (True, TemplateType.V2): ('v2', sxpatconfig.V2)
    }[(specs_obj.subxpat, specs_obj.template)]

    pprint.info2(f'{message} started...')
    return toolname


def node_matcher(n1: dict, n2: dict) -> bool:
    """Return if two node data dicts represent the same semantic node"""
    return (
        n1.get('label') == n2.get('label')
        and n1.get('subgraph', 0) == n2.get('subgraph', 0)
    )


def model_compare(a, b) -> bool:
    if a[1][0] < b[1][0]: return -1
    elif a[1][0] > b[1][0]: return +1
    elif a[1][4] < b[1][4]: return -1
    elif a[1][4] > b[1][4]: return +1
    else: return 0
