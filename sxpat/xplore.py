from typing import Iterable, Iterator, List

from tabulate import tabulate
import functools as ft
import csv
import time
import math
import networkx as nx

from Z3Log.config import path as z3logpath

from sxpat.labeling import labeling_explicit
from sxpat.specifications import Specifications, TemplateType, ErrorPartitioningType
from sxpat.config.paths import *
from sxpat.config.config import *
from sxpat.synthesis import Synthesis
from sxpat.template_manager.template_manager import TemplateManager, Subxpat_v2
from sxpat.utils.filesystem import FS
from sxpat.utils.name import NameData
from sxpat.verification import erroreval_verification_wce
from sxpat.stats import Stats, sxpatconfig, Model
from sxpat.annotatedGraph import AnnotatedGraph

from z_marco.utils import pprint
from z_marco.ma_graph import insert_subgraph, xpat_model_to_magraph, remove_subgraph
from sxpat.template_manager.encoding import Encoding


def explore_grid(specs_obj: Specifications):
    exp_start = time.perf_counter()
    previous_subgraphs = []
    previous_current_benchmark = ''
    previous_checked_error = 1
    previous_available_subgraph = 0

    labeling_time: float = -1
    subgraph_extraction_time: float = -1

    # Select toolname
    toolname = get_toolname(specs_obj)

    # initial setup
    exact_file_path = f"{INPUT_PATH['ver'][0]}/{specs_obj.exact_benchmark}.v"

    # create stat and template object
    stats_obj = Stats(specs_obj)

    obtained_wce_exact = 0
    specs_obj.iteration = 0
    persistance = 0
    persistance_limit = 2
    prev_actual_error = 0 if specs_obj.subxpat else 1
    prev_given_error = 0

    #v2
    sum_wce_actual = 0

    # Morteza added for local experiments ==================
    if specs_obj.error_partitioning is ErrorPartitioningType.ASCENDING:
        orig_et = specs_obj.max_error
        if orig_et <= 8:
            et_array = iter(list(range(1, orig_et +1, 1)))
        else:
            step = orig_et // 8 if orig_et // 8 > 0 else 1
            et_array = iter(list(range(step, orig_et + step, step)))
    # Ends here ============================================

    while (obtained_wce_exact < specs_obj.max_error):
        specs_obj.iteration += 1
        if not specs_obj.subxpat:
            if prev_actual_error == 0:
                break
            specs_obj.et = specs_obj.max_error
        elif specs_obj.error_partitioning is ErrorPartitioningType.ASCENDING:
            # Morteza added for local experiments ==================
            if (persistance == persistance_limit or prev_actual_error == 0):
                persistance = 0
                try:
                    specs_obj.et = next(et_array)
                except StopIteration:
                    pprint.warning('The error space is exhausted! continuing for now')
                    specs_obj.et = specs_obj.max_error
                    # break
            else:
                persistance += 1
            print("persistance is: ",persistance)
            # Ends here ============================================
        elif specs_obj.error_partitioning is ErrorPartitioningType.DESCENDING:
            log2 = int(math.log2(specs_obj.max_error))
            specs_obj.et = 2 ** (log2 - specs_obj.iteration - 2)
        elif specs_obj.error_partitioning is ErrorPartitioningType.SMART_ASCENDING:
            specs_obj.et = 1 if specs_obj.iteration == 1 else prev_given_error * (2 if prev_actual_error == 0 else 1)
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
        if specs_obj.current_benchmark != previous_current_benchmark:
            current_graph = AnnotatedGraph(specs_obj.current_benchmark, is_clean=False)
        exact_graph = AnnotatedGraph(specs_obj.exact_benchmark, is_clean=False)

        # label graph
        if specs_obj.requires_labeling and not previous_available_subgraph or specs_obj.current_benchmark != previous_current_benchmark:
            et_coefficient = 1

            t_start = time.perf_counter()
            label_graph(exact_graph, current_graph, obtained_wce_exact, specs_obj.exact_labeling,
                        min_labeling=specs_obj.min_labeling, partial=specs_obj.partial_labeling,
                        et=specs_obj.et * et_coefficient, parallel=specs_obj.parallel,
                        incremental_labeling=specs_obj.current_benchmark == previous_current_benchmark)
            labeling_time = time.perf_counter() - t_start
            print(f'labeling_time = {labeling_time}')
        else:
            print('skipped labeling\n')
        

        mini = 1e100
        for n in current_graph.graph.nodes:
            x = current_graph.graph.nodes[n][WEIGHT]
            lab = current_graph.graph.nodes[n]['label']
            if x != -1 and lab != 'TRUE' and lab != 'FALSE':
                mini = min(x,mini)
        if mini + obtained_wce_exact > specs_obj.max_error:
            print("impossible to conclude any iteration, stopping")
            break

        # extract subgraph
        t_start = time.perf_counter()
        subgraph_is_available = current_graph.extract_subgraph(specs_obj)
        subgraph_extraction_time = time.perf_counter() - t_start
        print(f'subgraph_extraction_time = {subgraph_extraction_time}')
        previous_subgraphs.append(current_graph.subgraph)

        # todo:wip: export subgraph
        folder = 'output/gv/subgraphs'
        graph_path = f'{folder}/{specs_obj.current_benchmark}_et{specs_obj.et}_mode{specs_obj.extraction_mode}_omax{specs_obj.omax}.gv'
        FS.mkdir(folder)
        current_graph.export_annotated_graph(graph_path)
        print(f'subgraph exported at {graph_path}')

        # guard: skip if no subgraph was found
        if not subgraph_is_available:
            pprint.warning(f'No subgraph available.')
            prev_actual_error = 0
            continue

        # guard: don't skip if the subraph is equal to the previous one
        # if (
        #     len(previous_subgraphs) >= 2
        #     and nx.is_isomorphic(previous_subgraphs[-2], previous_subgraphs[-1], node_match=node_matcher)
        # ):
        #     pprint.warning('The subgraph is equal to the previous one. Skipping iteration ...')
        #     prev_actual_error = 0
        #     continue

        if specs_obj.template_name == 'V2':
            # todo:wip:marco
            encoding_temp = Encoding.factory(
                specs_obj.encoding,
                exact_graph.num_inputs,
                exact_graph.num_outputs
            )
            manager = Subxpat_v2(exact_graph, current_graph,specs_obj, encoding_temp)
            manager.set_new_context(specs_obj, specs_obj.et - obtained_wce_exact)
            full_magraph, sub_magraph = manager.set_graph_and_update_functions(current_graph)

            p1_start = time.perf_counter()
            success, message = manager.run_phase1([specs_obj.et - obtained_wce_exact, specs_obj.wanted_models, 1*60*60])
            subxpat_phase1_time = time.perf_counter() - p1_start
            print(f"p1_time = {subxpat_phase1_time:.6f}")

            if not success:
                # TODO: Look into this in v2
                pprint.warning(f'phase 1 failed with message: {message}')
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

            # run script
            if specs_obj.template_name != 'V2':
                manager = TemplateManager.factory(specs_obj, exact_graph, current_graph)
                start_time = time.perf_counter()
                results = manager.run()
                execution_time = time.perf_counter() - start_time

                cur_status = results[0].status
            else:
                manager.set_new_context(specs_obj, specs_obj.et - obtained_wce_exact)
                p2_start = time.perf_counter()
                cur_status, model = manager.run_phase2()
                subxpat_phase2_time = time.perf_counter() - p2_start
                print(f"p2_time = {subxpat_phase2_time:.6f}")
                phase2_tot += subxpat_phase2_time
                execution_time = subxpat_phase2_time
                manager.import_json_model()

            if cur_status in (UNSAT, UNKNOWN):
                pprint.warning(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration} -> {cur_status.upper()}')

                # store model
                this_model_info = Model(id=0, status=cur_status.upper(), cell=(lpp, ppo), et=specs_obj.et, iteration=specs_obj.iteration,
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
                if specs_obj.template_name == 'V2':
                    # remove sub-graph from the full-graph
                    hole_magraph = remove_subgraph(full_magraph, sub_magraph)
                    # convert the model to a circuit
                    model_magraph = xpat_model_to_magraph(model, iter_id=specs_obj.iteration)
                    # insert the subgraph into the hole-graph
                    merged_magraph = insert_subgraph(hole_magraph, model_magraph)

                    synth_obj = Synthesis(
                        specs_obj,
                        current_graph,  # not used if magraph is given
                        manager.json_model,  # not used if magraph is given
                        merged_magraph
                    )

                    # todo:marco: this seems to be working, lets make sure
                    cur_model_results: Dict[str: List[float, float, float, (int, int)]] = {}
                    synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'])
                    synth_obj.export_verilog()
                    synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])
                    cur_model_results[synth_obj.ver_out_name] = [
                        synth_obj.estimate_area(),
                        synth_obj.estimate_power(),
                        synth_obj.estimate_delay(),
                        (lpp, ppo),
                        None,
                        None
                    ]

                    # Morteza: Here we create a Model object and then save it
                    this_model = Model(id=0, status=cur_status.upper(), cell=(lpp, ppo), et=specs_obj.et, iteration=specs_obj.iteration,
                                        area=cur_model_results[synth_obj.ver_out_name][0],
                                        total_power=cur_model_results[synth_obj.ver_out_name][1],
                                        delay=cur_model_results[synth_obj.ver_out_name][2],
                                        labeling_time=labeling_time,
                                        subgraph_extraction_time=subgraph_extraction_time,
                                        subgraph_number_inputs=current_graph.subgraph_num_inputs,
                                        subgraph_number_outputs=current_graph.subgraph_num_outputs,
                                        subxpat_phase1_time=subxpat_phase1_time,
                                        subxpat_phase2_time=subxpat_phase2_time)
                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model)

                else:
                # synthesize all models and compute circuit specifications
                    synth_obj = Synthesis(specs_obj, current_graph, [res.model for res in results])
                    cur_model_results: Dict[str: List[float, float, float, (int, int), int, int]] = {}
                    for idx in range(synth_obj.num_of_models):
                        synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'], id=idx)
                        synth_obj.export_verilog(idx=idx)
                        synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0], idx=idx)
                        cur_model_results[synth_obj.ver_out_name] = [
                            synth_obj.estimate_area(),
                            synth_obj.estimate_power(),
                            synth_obj.estimate_delay(),
                            (lpp, ppo),
                            None,  # abs diff to exact
                            None  # abs diff to previous
                        ]

                # todo: should we refactor with pandas?
                with open(f"{z3logpath.OUTPUT_PATH['report'][0]}/area_model_nummodels{specs_obj.wanted_models}_{specs_obj.current_benchmark}_{specs_obj.et}_{toolname}.csv", 'w') as f:
                    csvwriter = csv.writer(f)

                    header = list(range(len(cur_model_results)))
                    all = list(cur_model_results.values())
                    content = [f for (f, *_) in all]

                    csvwriter.writerow(header)
                    csvwriter.writerow(content)

                # verify all models and store errors
                pprint.success('verifying all approximate circuits -> ', end='')
                start_error_eval = time.perf_counter()
                for candidate_name, candidate_data in cur_model_results.items():
                    candidate_data[4] = erroreval_verification_wce(specs_obj.exact_benchmark, candidate_name[:-2])
                    candidate_data[5] = erroreval_verification_wce(specs_obj.current_benchmark, candidate_name[:-2])

                    #v2
                    if specs_obj.template_name == 'V2':
                        # obtained_wce_prev = erroreval_verification_wce(specs_obj.current_benchmark, candidate_name[:-2])
                        prev_actual_error = candidate_data[5]
                        obtained_wce_prev = candidate_data[5]
                    
                    if candidate_data[4] > specs_obj.et:
                        pprint.error(f'ErrorEval Verification FAILED! with wce {candidate_data[4]}')
                        stats_obj.store_grid()
                        return stats_obj
                pprint.success(f'Cell = ({lpp}, {ppo}) iteration = {specs_obj.iteration} -> {cur_status} ({synth_obj.num_of_models} models found)')
                error_eval_time = time.perf_counter() - start_error_eval
                print(f"p1_time = {error_eval_time:.6f}") 

                # sort circuits
                sorted_circuits = sorted(cur_model_results.items(), key=ft.cmp_to_key(model_compare))

                # select best circuit
                best_name, best_data = sorted_circuits[0]
                obtained_wce_exact = best_data[4]
                prev_actual_error = best_data[5]

                specs_obj.current_benchmark = best_name
                best_model_info = Model(id=0,
                                        status=cur_status.upper(),
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
                if specs_obj.template_name == 'V2':
                    sum_wce_actual += obtained_wce_prev
                    pprint.success(f' and prev_wce = {obtained_wce_prev} with sum of prevs wce = {sum_wce_actual}')

                exact_stats = [synth_obj.estimate_area(exact_file_path),
                               synth_obj.estimate_power(exact_file_path),
                               synth_obj.estimate_delay(exact_file_path)]
                print_current_model(sorted_circuits, normalize=False, exact_stats=exact_stats)
                store_current_model(cur_model_results, exact_stats=exact_stats, benchmark_name=specs_obj.current_benchmark, et=specs_obj.et,
                                    encoding=specs_obj.encoding, subgraph_extraction_time=subgraph_extraction_time, labeling_time=labeling_time)

                break  # SAT found, stop grid exploration

            prev_actual_error = 0

        if cur_status == SAT and best_data[0] == 0:
            pprint.info3('Area zero found!\nTerminated.')
            break

    stats_obj.store_grid()
    total_time = time.perf_counter() - exp_start
    print(f'total_time = {total_time}')
    return stats_obj


class CellIterator:
    @classmethod
    def factory(cls, specs: Specifications) -> Iterator[Tuple[int, int]]:
        return {
            TemplateType.NON_SHARED: cls.non_shared,
            TemplateType.V2: cls.non_shared,
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


def label_graph(exact_graph: AnnotatedGraph, current_graph: AnnotatedGraph, substract: int, exact_labeling: bool,
                min_labeling: bool = False,  partial: bool = False,
                et: int = -1, parallel: bool = False, incremental_labeling = False):
    labels, _ = labeling_explicit(current_graph.name, current_graph.name,
                                  constant_value=0, min_labeling=min_labeling,
                                  partial=partial, et=et, parallel=parallel)


    # already_labeled = {}
    # if incremental_labeling:
    #     for n in current_graph.graph.nodes:
    #         x = current_graph.graph.nodes[n][WEIGHT]
    #         if x != -1:
    #             already_labeled[n] = x
    # if exact_labeling:
    #     labels = lollo.temp_labelling.labeling(exact_graph.name, current_graph.name, et, already_labeled)

    #     for n in current_graph.graph.nodes:
    #         current_graph.graph.nodes[n][WEIGHT] = max(1,int(labels[n]) - substract) if n in labels else -1

    # else:
    #     labels = lollo.temp_labelling.labeling(current_graph.name, current_graph.name, et, already_labeled)

    for n in current_graph.graph.nodes:
        current_graph.graph.nodes[n][WEIGHT] = int(labels[n]) if n in labels else -1


def get_toolname(specs_obj: Specifications) -> str:
    message, toolname = {
        (False, TemplateType.NON_SHARED): ('XPAT', sxpatconfig.XPAT),
        (False, TemplateType.SHARED): ('Shared XPAT', sxpatconfig.SHARED_XPAT),
        (True, TemplateType.NON_SHARED): ('SubXPAT', sxpatconfig.SUBXPAT),
        (True, TemplateType.SHARED): ('Shared SubXPAT', sxpatconfig.SHARED_SUBXPAT),
        (True, TemplateType.V2): ('SubXPAT V2', sxpatconfig.SUBXPAT_V2),
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
    if a[1][0] < b[1][0]:
        return -1
    elif a[1][0] > b[1][0]:
        return +1
    elif a[1][4] < b[1][4]:
        return -1
    elif a[1][4] > b[1][4]:
        return +1
    else:
        return 0
