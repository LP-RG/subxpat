from typing import Iterable, Iterator, List

from tabulate import tabulate
import csv
import time
import math
import networkx as nx

from Z3Log.config import path as z3logpath

from sxpat.labeling import labeling_explicit
from sxpat.templateSpecs import TemplateSpecs
from sxpat.config.paths import *
from sxpat.config.config import *
from sxpat.synthesis import Synthesis
from sxpat.template_manager.template_manager import TemplateManager
from sxpat.utils.filesystem import FS
from sxpat.utils.name import NameData
from sxpat.verification import erroreval_verification_wce
from sxpat.stats import Stats, sxpatconfig, Model
from sxpat.annotatedGraph import AnnotatedGraph

from z_marco.utils import pprint


def explore_grid(specs_obj: TemplateSpecs):
    previous_subgraphs = []
    print(f'{specs_obj = }')

    labeling_time: float = -1
    subgraph_extraction_time: float = -1

    # Select toolname
    toolname = get_toolname(specs_obj)

    # initial setup
    total_iterations = specs_obj.iterations
    exact_file_path = f"{INPUT_PATH['ver'][0]}/{specs_obj.exact_benchmark}.v"
    exact_file_name = specs_obj.exact_benchmark
    sum_wce_actual = 0

    # create stat and template object
    stats_obj = Stats(specs_obj)

    # This line would cause a problem,
    # current_population: Dict = {specs_obj.benchmark_name: -1}
    # So I changed it into the following:
    current_population: Dict = {specs_obj.benchmark_name: ('Area', 'Delay', 'Power', ('LPP', 'PPO'))}
    next_generation: Dict = {}
    total: Dict[Dict] = {}
    available_error = specs_obj.et
    obtained_wce_exact = 0
    i = 0
    prev_actual_error = 0
    prev_given_error = 0

    while (obtained_wce_exact < available_error):
        i += 1

        if not specs_obj.subxpat:
            et = specs_obj.et

        elif specs_obj.et_partitioning == 'asc':
            log2 = int(math.log2(specs_obj.et))
            et = 2**(i-1)
        elif specs_obj.et_partitioning == 'desc':
            log2 = int(math.log2(specs_obj.et))
            et = 2**(log2 - i - 2)
        elif specs_obj.et_partitioning == 'smart_asc':
            et = 1 if i == 1 else prev_given_error * (2 if prev_actual_error == 0 else 1)
            prev_given_error = et
        elif specs_obj.et_partitioning == 'smart_desc':
            et = available_error if i == 1 else prev_given_error / (2 if prev_actual_error == 0 else 1)
            prev_given_error = et
        else:
            raise NotImplementedError('invalid status')

        pprint.info1(f'iteration {i} with et {et}, available error {available_error}'
                     if (specs_obj.subxpat or specs_obj.subxpat_v2) else
                     f'Only one iteration with et {et}')

        # for all candidates
        for candidate in current_population:

            pprint.info1(f'candidate {candidate}')
            if candidate.endswith('.v'):
                specs_obj.benchmark_name = candidate[:-2]

            # > grid step settings

            # initialize context
            specs_obj.et = et

            # import the graph
            current_graph = AnnotatedGraph(specs_obj.benchmark_name, is_clean=False, partitioning_percentage=1)
            exact_graph = AnnotatedGraph(specs_obj.exact_benchmark, is_clean=False, partitioning_percentage=0)

            # label graph
            if specs_obj.max_sensitivity > 0 or specs_obj.mode >= 3:
                et_coefficient = 1

                t_start = time.time()
                label_graph(current_graph,
                            min_labeling=specs_obj.min_labeling, partial=specs_obj.partial_labeling,
                            et=et*et_coefficient, parallel=specs_obj.parallel)
                labeling_time = time.time() - t_start
                print(f'labeling_time = {labeling_time}')

            # extract subgraph
            t_start = time.time()
            subgraph_is_available = current_graph.extract_subgraph(specs_obj)
            subgraph_extraction_time = time.time() - t_start
            print(f'subgraph_extraction_time = {subgraph_extraction_time}')
            previous_subgraphs.append(current_graph.subgraph)

            # todo:wip: export subgraph
            folder = 'output/gv/subgraphs'
            graph_path = f'{folder}/{specs_obj.benchmark_name}_et{specs_obj.et}_mode{specs_obj.mode}_omax{specs_obj.omax}_serr{specs_obj.sub_error_function}.gv'
            FS.mkdir(folder)
            current_graph.export_annotated_graph(graph_path)
            print(f'subgraph exported at {graph_path}')

            # guard: skip if no subgraph was found
            if not subgraph_is_available:
                pprint.warning(f'No subgraph available.')
                prev_actual_error = 0
                if et == available_error:
                    available_error = 0
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
                    pprint.info1(f'Cell({lpp},{ppo}) at iteration {i} -> DOMINATED')
                    continue

                # > cell step settings

                # update the context
                specs_obj = set_current_context(specs_obj, lpp, ppo, i)

                # run script
                manager = TemplateManager.factory(specs_obj, exact_graph, current_graph)
                start_time = time.time()
                results = manager.run()
                execution_time = time.time() - start_time

                cur_status = results[0].status
                if cur_status in (UNSAT, UNKNOWN):
                    pprint.warning(f'Cell({lpp},{ppo}) at iteration {i} -> {cur_status.upper()}')

                    # store model
                    this_model_info = Model(id=0, status=cur_status.upper(), cell=(lpp, ppo), et=et, iteration=i,
                                            labeling_time=labeling_time,
                                            subgraph_extraction_time=subgraph_extraction_time,
                                            subgraph_number_inputs=current_graph.subgraph_num_inputs,
                                            subgraph_number_outputs=current_graph.subgraph_num_outputs,
                                            subxpat_v1_time=execution_time)
                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_info)

                    if cur_status == UNKNOWN:
                        # store cell as dominant (to skip dominated subgrid)
                        dominant_cells.append((lpp, ppo))

                elif cur_status == SAT:
                    synth_obj = Synthesis(specs_obj, current_graph, [res.model for res in results])
                    cur_model_results: Dict[str: List[float, float, float, (int, int)]] = {}
                    for idx in range(synth_obj.num_of_models):
                        synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'], id=idx)
                        synth_obj.export_verilog(idx=idx)
                        synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0], idx=idx)
                        cur_model_results[synth_obj.ver_out_name] = (
                            synth_obj.estimate_area(),
                            synth_obj.estimate_power(),
                            synth_obj.estimate_delay(),
                            (lpp, ppo)
                        )

                    # todo: should we refactor with pandas?
                    with open(f"{z3logpath.OUTPUT_PATH['report'][0]}/area_model_nummodels{specs_obj.num_of_models}_{specs_obj.benchmark_name}_{specs_obj.et}_{toolname}.csv", 'w') as f:
                        csvwriter = csv.writer(f)

                        header = list(range(len(cur_model_results)))
                        all = list(cur_model_results.values())
                        content = [f for (f, _, _, _) in all]

                        csvwriter.writerow(header)
                        csvwriter.writerow(content)

                    pprint.success('verifying all approximate circuits -> ', end='')
                    for candidate in cur_model_results:
                        approximate_benchmark = candidate[:-2]

                        obtained_wce_exact = erroreval_verification_wce(specs_obj.exact_benchmark, approximate_benchmark, et)
                        obtained_wce_prev = erroreval_verification_wce(specs_obj.benchmark_name, approximate_benchmark, et)
                        prev_actual_error = obtained_wce_prev

                        if obtained_wce_exact > et:
                            pprint.error('ErrorEval Verification FAILED!')
                            stats_obj.store_grid()
                            return stats_obj

                    this_model_info = Model(id=0, status=cur_status.upper(), cell=(lpp, ppo), et=obtained_wce_exact, iteration=i,
                                            area=cur_model_results[synth_obj.ver_out_name][0],
                                            total_power=cur_model_results[synth_obj.ver_out_name][1],
                                            delay=cur_model_results[synth_obj.ver_out_name][2],
                                            labeling_time=labeling_time,
                                            subgraph_extraction_time=subgraph_extraction_time,
                                            subgraph_number_inputs=current_graph.subgraph_num_inputs,
                                            subgraph_number_outputs=current_graph.subgraph_num_outputs,
                                            subxpat_v1_time=execution_time)

                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_info)
                    pprint.success(f'ErrorEval PASS! with total wce = {obtained_wce_exact}')

                    specs_obj.benchmark_name = approximate_benchmark

                    synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'], list(cur_model_results.keys())[0])

                    pprint.success(f'Cell = ({lpp}, {ppo}) iteration = {i} -> {cur_status} ({synth_obj.num_of_models} models found)')
                    exact_stats = [synth_obj.estimate_area(exact_file_path),
                                   synth_obj.estimate_power(exact_file_path),
                                   synth_obj.estimate_delay(exact_file_path)]
                    print_current_model(cur_model_results, normalize=False, exact_stats=exact_stats)

                    store_current_model(cur_model_results, exact_stats=exact_stats, benchmark_name=specs_obj.benchmark_name, et=specs_obj.et,
                                        encoding=specs_obj.encoding, subgraph_extraction_time=subgraph_extraction_time, labeling_time=labeling_time)

                    for key in cur_model_results.keys():
                        next_generation[key] = cur_model_results[key]

                    current_population = select_candidates_for_next_iteration(specs_obj, next_generation)
                    total[i] = current_population

                    next_generation = {}

                    # SAT found, stop grid exploration
                    break
                prev_actual_error = 0

        if exists_an_area_zero(current_population):
            break

    stats_obj.store_grid()
    return stats_obj


class CellIterator:
    @classmethod
    def factory(cls, specs: TemplateSpecs) -> Iterator[Tuple[int, int]]:
        return {
            True: cls.shared,
            False: cls.non_shared,
        }[specs.shared](specs)

    @staticmethod
    def shared(specs: TemplateSpecs) -> Iterator[Tuple[int, int]]:
        max_pit = specs.max_pit

        # special cell
        yield (0, 1)

        # grid cells
        for pit in range(1, max_pit + 1):
            for its in range(pit, pit + 3 + 1):
                yield (its, pit)

    @staticmethod
    def non_shared(specs: TemplateSpecs) -> Iterator[Tuple[int, int]]:
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


def set_current_context(specs_obj: TemplateSpecs, lpp: int, ppo: int, iteration: int) -> TemplateSpecs:
    specs_obj.lpp = lpp
    specs_obj.ppo = specs_obj.pit = ppo
    specs_obj.iterations = iteration
    return specs_obj


def print_current_model(cur_model_result: Dict, normalize: bool = True, exact_stats: List = None) -> None:
    data = []

    if exact_stats:
        # add exact circuit data
        e_area, e_power, e_delay, *_ = exact_stats
        data.append(['Exact', e_area, e_power, e_delay])

        if normalize:
            for stats in cur_model_result.values():
                stats[0] = (stats[0] / e_area) * 100
                stats[1] = (stats[1] / e_power) * 100
                stats[2] = (stats[2] / e_delay) * 100

    # keep wanted models
    sorted_candidates = sorted(cur_model_result.items(), key=lambda x: x[1])
    if len(cur_model_result) < 10:
        wanted_candidates = sorted_candidates
    else:
        wanted_candidates = [sorted_candidates[0]]

    # add candidates data
    for c_name, c_stats in wanted_candidates:
        c_id = NameData.from_filename(c_name).total_id
        c_area, c_power, c_delay, *_ = c_stats
        data.append([c_id, c_area, c_power, c_delay])

    pprint.success(tabulate(data, headers=['Design ID', 'Area', 'Power', 'Delay']))


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


def exists_an_area_zero(candidates: Dict[str, float]) -> bool:
    print(f'{candidates = }')
    for key in candidates.keys():
        if candidates[key][0] == 0:
            pprint.info3('Area zero found!\nTerminated.')
            return True
    return False


def select_candidates_for_next_iteration(spec_obj: TemplateSpecs, candidates: Dict[str, float]) -> Dict[str, float]:
    # Check which alogirhtm we use for selection of the next generation
    if spec_obj.population > 1:
        return pick_best_model(candidates)
    else:
        selected_candidates = {}
        for key in candidates.keys():
            selected_candidates[key] = candidates[key]
            break
        return selected_candidates


def pick_k_best_k_worst(candidates: Dict[str, float], k: int):
    num_of_candidates: int = len(candidates)
    if 2 * k >= num_of_candidates:
        return candidates
    else:
        # sort the dict based on the value and remove everything but the k first and k last elements
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1])
        i = 0
        selected_candidates: Dict = {}
        for key in sorted_candidates:
            if i < k or (i >= len(candidates) - k):
                selected_candidates[key[0]] = candidates[key[0]]
            i += 1
        return selected_candidates

def pick_best_model(candidates: Dict[str, float]):
    sorted_candidates = sorted(candidates.items(), key=lambda x: x[1])
    return dict([next(iter(sorted_candidates))])

def label_graph(current_graph: AnnotatedGraph,
                min_labeling: bool = False,  partial: bool = False,
                et: int = -1, parallel: bool = False):
    labels, _ = labeling_explicit(current_graph.name, current_graph.name,
                                  constant_value=0, min_labeling=min_labeling,
                                  partial=partial, et=et, parallel=parallel)

    for n in current_graph.graph.nodes:
        current_graph.graph.nodes[n][WEIGHT] = int(labels[n]) if n in labels else -1


def get_toolname(specs_obj: TemplateSpecs) -> str:
    if specs_obj.subxpat_v2:
        pprint.info2('SubXPAT-V2 started...')
        toolname = sxpatconfig.SUBXPAT_V2
    elif specs_obj.subxpat and specs_obj.shared:
        pprint.info2('Shared SubXPAT started...')
        toolname = sxpatconfig.SHARED_SUBXPAT
    elif specs_obj.subxpat and not specs_obj.shared:
        pprint.info2('SubXPAT started...')
        toolname = sxpatconfig.SUBXPAT
    elif not specs_obj.subxpat and specs_obj.shared:
        pprint.info2('Shared XPAT started...')
        toolname = sxpatconfig.SHARED_XPAT
    elif not specs_obj.subxpat and not specs_obj.shared:
        pprint.info2('XPAT started...')
        toolname = sxpatconfig.XPAT

    return toolname


def node_matcher(n1: dict, n2: dict) -> bool:
    """Return if two node data dicts represent the same semantic node"""
    return (
        n1.get('label') == n2.get('label')
        and n1.get('subgraph', 0) == n2.get('subgraph', 0)
    )
