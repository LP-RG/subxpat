from __future__ import annotations
from typing import Callable, Dict, Iterable, Iterator, List, Tuple, TypeVar
import dataclasses as dc

from tabulate import tabulate
import functools as ft
import csv
import time
import math
import networkx as nx

from Z3Log.config import path as z3logpath

from sxpat.labeling import labeling_explicit
from sxpat.metrics import MetricsEstimator
from sxpat.specifications import Specifications, TemplateType, ErrorPartitioningType
from sxpat.config import paths as sxpatpaths
from sxpat.config.config import *
from sxpat.utils.filesystem import FS
from sxpat.utils.name import NameData
from sxpat.verification import erroreval_verification_wce
from sxpat.stats import Stats, sxpatconfig, Model
from sxpat.annotatedGraph import AnnotatedGraph

from sxpat.templating import get_specialized as get_templater
from sxpat.solving import get_specialized as get_solver

from sxpat.converting import VerilogExporter
from sxpat.converting import iograph_from_legacy, sgraph_from_legacy
from sxpat.converting import set_bool_constants, prevent_combination

from sxpat.utils.print import pprint


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

        pprint.info1(f'iteration {specs_obj.iteration} with et {specs_obj.et}, available error {specs_obj.max_error}'
                     if (specs_obj.subxpat) else
                     f'Only one iteration with et {specs_obj.et}')

        if specs_obj.current_benchmark.endswith('.v'):
            specs_obj.current_benchmark = specs_obj.current_benchmark[:-2]
        pprint.info1(f'benchmark {specs_obj.current_benchmark}')

        # > grid step settings

        # import the graph
        exact_graph = AnnotatedGraph(specs_obj.exact_benchmark, is_clean=False)
        current_graph = AnnotatedGraph(specs_obj.current_benchmark, is_clean=False)

        # label graph
        if specs_obj.requires_labeling:
            et_coefficient = 1

            label_timer, _label_graph = Timer.from_function(label_graph)
            _label_graph(current_graph,
                         min_labeling=specs_obj.min_labeling, partial=specs_obj.partial_labeling,
                         et=specs_obj.et * et_coefficient, parallel=specs_obj.parallel)
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
        if (
            len(previous_subgraphs) >= 2
            and nx.is_isomorphic(previous_subgraphs[-2], previous_subgraphs[-1], node_match=node_matcher)
        ):
            pprint.warning('The subgraph is equal to the previous one. Skipping iteration ...')
            prev_actual_error = 0
            continue

        # explore the grid
        pprint.info2(f'Grid ({specs_obj.grid_param_1} X {specs_obj.grid_param_2}) and et={specs_obj.et} exploration started...')
        dominant_cells = []
        for lpp, ppo in CellIterator.factory(specs_obj):
            if is_dominated((lpp, ppo), dominant_cells):
                pprint.info1(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration} -> DOMINATED')
                continue

            # > cell step settings

            # update the context
            update_context(specs_obj, lpp, ppo)

            # convert from legacy graph to new architecture graph
            e_graph = iograph_from_legacy(exact_graph)
            s_graph = sgraph_from_legacy(current_graph)

            # define template (and constraints)
            template_timer, define_template = Timer.from_function(get_templater(specs_obj).define)
            p_graph, c_graph = define_template(s_graph, specs_obj)

            # solve
            solve_timer, solve = Timer.from_function(get_solver(specs_obj).solve)
            models = []
            for _ in range(specs_obj.wanted_models):
                # prevent parameters combination if any
                if len(models) > 0: c_graph = prevent_combination(c_graph, model)
                # run solver
                status, model = solve((e_graph, p_graph, c_graph), specs_obj)
                # terminate if status is not sat, otherwise store the models
                if status != 'sat': break
                models.append(model)

            # legacy adaptation
            execution_time = template_timer.total + solve_timer.total

            if len(models) == 0:
                pprint.warning(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration} -> {status.upper()}')

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
                pprint.success(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration} -> {status.upper()} ({len(models)} models found)')

                # TODO:#15: use serious name generator
                base_path = f'input/ver/{specs_obj.exact_benchmark}_{specs_obj.time_id}_i{specs_obj.iteration}_{{model_number}}.v'
                cur_model_results: Dict[str: List[float, float, float, (int, int), int, int]] = {}

                for model_number, model in enumerate(models):
                    # finalize approximate graph
                    a_graph = set_bool_constants(p_graph, model)

                    # export approximate graph as verilog
                    # TODO:#15: use serious name generator
                    verilog_path = base_path.format(model_number=model_number)
                    VerilogExporter.to_file(
                        a_graph, verilog_path,
                        VerilogExporter.Info(model_number=model_number),
                    )

                    # compute metrics
                    metrics = MetricsEstimator.estimate_metrics(verilog_path)
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
                    candidate_data[4] = erroreval_verification_wce(specs_obj.exact_benchmark, candidate_name[:-2])
                    candidate_data[5] = erroreval_verification_wce(specs_obj.current_benchmark, candidate_name[:-2])

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

                exact_stats = MetricsEstimator.estimate_metrics(exact_file_path)
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
            for its in range(pit, pit + 3 + 1):
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


def label_graph(current_graph: AnnotatedGraph,
                min_labeling: bool = False, partial: bool = False,
                et: int = -1, parallel: bool = False):
    labels, _ = labeling_explicit(current_graph.name, current_graph.name,
                                  constant_value=0, min_labeling=min_labeling,
                                  partial=partial, et=et, parallel=parallel)

    for n in current_graph.graph.nodes:
        current_graph.graph.nodes[n][WEIGHT] = int(labels[n]) if n in labels else -1


def get_toolname(specs_obj: Specifications) -> str:
    message, toolname = {
        (False, TemplateType.NON_SHARED): ('XPAT', sxpatconfig.XPAT),
        (False, TemplateType.SHARED): ('Shared XPAT', sxpatconfig.SHARED_XPAT),
        (True, TemplateType.NON_SHARED): ('SubXPAT', sxpatconfig.SUBXPAT),
        (True, TemplateType.SHARED): ('Shared SubXPAT', sxpatconfig.SHARED_SUBXPAT),
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


@dc.dataclass(init=False, repr=False, eq=False, frozen=True)
class Timer:
    from time import time as now
    _C = TypeVar('_C', bound=Callable)

    total: float = 0
    last: float = 0

    def wrap(self, function: _C) -> _C:
        @ft.wraps(function)
        def wrapper(*args, **kwds):
            start_time = self.now()
            result = function(*args, **kwds)
            object.__setattr__(self, 'last', self.now() - start_time)
            object.__setattr__(self, 'total', self.total + self.last)
            return result
        return wrapper

    @classmethod
    def from_function(cls, function: _C) -> Tuple[Timer, _C]:
        timer = Timer()
        wrapped = timer.wrap(function)
        return (timer, wrapped)
