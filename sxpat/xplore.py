import csv
import time
from typing import Iterable, Iterator, List, Union

from tabulate import tabulate

import math

from Z3Log.utils import *
from Z3Log.config import path as z3logpath

from sxpat.templateCreator import Template_SOP1, Template_SOP1ShareLogic
from sxpat.TempWrappers.subxpat_v2 import Template_V2

from sxpat.templateSpecs import TemplateSpecs
from sxpat.config.paths import *
from sxpat.config.config import *
from sxpat.synthesis import Synthesis
from sxpat.utils.filesystem import FS
from sxpat.verification import erroreval_verification_explicit, erroreval_verification_wce
from sxpat.stats import Stats, sxpatconfig, Model

from z_marco.ma_graph import insert_subgraph, xpat_model_to_magraph, remove_subgraph

from z_marco.utils import pprint, color


def explore_grid(specs_obj: TemplateSpecs):

    print(f'{specs_obj = }')

    labeling_time: float = -1
    subgraph_extraction_time: float = -1
    subxpat_phase1_time: float = -1
    subxpat_phase2_time: float = -1

    # Select toolname
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

    # initial setup
    total_iterations = specs_obj.iterations
    exact_file_path = f"{INPUT_PATH['ver'][0]}/{specs_obj.exact_benchmark}.v"
    exact_file_name = specs_obj.exact_benchmark
    sum_wce_actual = 0
    max_lpp = specs_obj.lpp
    max_ppo = specs_obj.pit if specs_obj.shared else specs_obj.ppo
    total_number_of_cells_per_iter = max_lpp * max_ppo + 1

    # create stat and template object
    stats_obj = Stats(specs_obj)
    if specs_obj.shared:
        template_obj = Template_SOP1ShareLogic(specs_obj)
    elif specs_obj.subxpat_v2:
        template_obj = Template_V2(specs_obj)
    else:
        template_obj = Template_SOP1(specs_obj)

    # This line would cause a problem,
    # current_population: Dict = {specs_obj.benchmark_name: -1}
    # So I changed it into the following:
    current_population: Dict = {specs_obj.benchmark_name: ('Area', 'Delay', 'Power', ('LPP', 'PPO'))}
    next_generation: Dict = {}
    total: Dict[Dict] = {}
    pre_iter_unsats: Dict = {specs_obj.benchmark_name: 0}
    original_et = specs_obj.et
    available_error = specs_obj.et
    obtained_wce_exact = 0
    i = 0
    prev_actual_error = 0
    prev_given_error = 0
    while (obtained_wce_exact <= available_error):
        # for i, et in error_iterator:
        i += 1
        if specs_obj.et_partitioning == 'asc':
            log2 = int(math.log2(specs_obj.et))
            et = 2**(i-1)
        elif specs_obj.et_partitioning == 'desc':
            log2 = int(math.log2(specs_obj.et))
            et = 2**(log2 - i - 2)
        elif specs_obj.et_partitioning == 'smart_asc':
            et = 1 if i == 1 else prev_given_error + (1 if prev_actual_error == 0 else 0)
            if available_error < et*2:
                et = available_error
            prev_given_error = et
        elif specs_obj.et_partitioning == 'smart_desc':
            et = available_error if i == 1 else prev_given_error - (1 if prev_actual_error == 0 else 0)
            if et > available_error:
                et = available_error
            prev_given_error = et
        else:
            raise NotImplementedError('invalid status')

        pprint.info1(f'iteration {i} with et {et}, available error {available_error}'
                     if (specs_obj.subxpat or specs_obj.subxpat_v2) else
                     f'Only one iteration with et {et}')

        # for all candidates
        for candidate in current_population:
            # guard
            if pre_iter_unsats[candidate] == total_number_of_cells_per_iter and not specs_obj.keep_unsat_candidate:
                pprint.info1(f'Number of UNSATs reached!')
                continue

            pprint.info1(f'candidate {candidate}')
            if candidate.endswith('.v'):
                specs_obj.benchmark_name = candidate[:-2]

            # > grid step settings

            # initialize context
            specs_obj.et = et
            template_obj.set_new_context(specs_obj)

            # import the graph
            template_obj.current_graph = template_obj.import_graph()

            # extract the subgraph
            if specs_obj.max_sensitivity > 0 or specs_obj.mode >= 3:
                # label graph
                t_start = time.time()
                print(f'{et = }')
                et_coefficient = 8
                template_obj.label_graph(min_labeling=specs_obj.min_labeling, partial=specs_obj.partial_labeling, et=et*et_coefficient, parallel=specs_obj.parallel)
                labeling_time = time.time() - t_start
                print(f'labeling_time = {labeling_time}')

            # extract subgraph
            t_start = time.time()
            subgraph_is_available = template_obj.current_graph.extract_subgraph(specs_obj)
            subgraph_extraction_time = time.time() - t_start
            subgraph_number_inputs = template_obj.current_graph.subgraph_num_inputs
            subgraph_number_outputs = template_obj.current_graph.subgraph_num_outputs
            print(f'subgraph_extraction_time = {subgraph_extraction_time}')
            print(f'subgraph_number_inputs = {subgraph_number_inputs}')
            print(f'subgraph_number_outputs = {subgraph_number_outputs}')

            # todo:wip:marco: export subgraph
            folder = 'output/gv/subgraphs'
            graph_path = f'{folder}/{specs_obj.benchmark_name}_lpp{specs_obj.lpp}_ppo{specs_obj.ppo}_et{specs_obj.et}_mode{specs_obj.mode}_omax{specs_obj.omax}_serr{specs_obj.sub_error_function}.gv'
            FS.mkdir(folder)
            template_obj.current_graph.export_annotated_graph(graph_path)
            print(f'subgraph exported at {graph_path}')

            # guard
            if not subgraph_is_available:
                pprint.warning(f'No subgraph available.')
                prev_actual_error = 0
                if et == available_error:
                    available_error = 0
                continue

            # run grid phase
            if template_obj.is_two_phase_kind:
                # todo:wip:marco
                full_magraph, sub_magraph = template_obj.set_graph_and_update_functions(template_obj.current_graph)

                p1_start = time.time()
                success, message = template_obj.run_phase1([specs_obj.et, specs_obj.num_of_models, 1*60*60])
                subxpat_phase1_time = time.time() - p1_start
                print(f"p1_time = {subxpat_phase1_time:.6f}")

                if not success:
                    # TODO: Look into this in v2
                    pprint.warning(f'phase 1 failed with message: {message}')
                    prev_actual_error = 0
                    if et == available_error:
                        available_error = 0
                    continue

            # explore the grid
            pprint.info2(f'Grid ({max_lpp} X {max_ppo}) and et={specs_obj.et} exploration started...')
            dominant_cells = []
            for lpp, ppo in cell_iterator(max_lpp, max_ppo):
                if is_dominated((lpp, ppo), dominant_cells):
                    pprint.info1(f'Cell({lpp},{ppo}) at iteration {i} -> DOMINATED')
                    continue

                # > cell step settings

                # update the context
                specs_obj = set_current_context(specs_obj, lpp, ppo, i)
                template_obj.set_new_context(specs_obj)

                # run cell phase
                if template_obj.is_two_phase_kind:
                    # run script
                    p2_start = time.time()
                    cur_status, model = template_obj.run_phase2()
                    subxpat_phase2_time = time.time() - p2_start
                    print(f"p2_time = {subxpat_phase2_time:.6f}")
                    template_obj.import_json_model()

                else:
                    # run script
                    template_obj.z3_generate_z3pyscript()
                    template_obj.run_z3pyscript(ET=specs_obj.et, num_models=specs_obj.num_of_models, timeout=specs_obj.timeout)
                    # at this point the internal verification using verification solver is already passed!


                    # gather results
                    cur_status = get_status(template_obj)

                if cur_status in (UNSAT, UNKNOWN):
                    pprint.warning(f'Cell({lpp},{ppo}) at iteration {i} -> {cur_status.upper()}')

                    # store model
                    this_model_info = Model(id=0, status=cur_status.upper(), cell=(lpp, ppo), et=et, iteration=i,
                                            labeling_time=labeling_time,
                                            subgraph_extraction_time=subgraph_extraction_time,
                                            subgraph_number_inputs=subgraph_number_inputs,
                                            subgraph_number_outputs=subgraph_number_outputs,
                                            subxpat_phase1_time=subxpat_phase1_time,
                                            subxpat_phase2_time=subxpat_phase2_time)
                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_info)
                    pre_iter_unsats[candidate] += 1

                    if cur_status == UNKNOWN:
                        # store cell as dominant (to skip dominated subgrid)
                        dominant_cells.append((lpp, ppo))

                elif cur_status == SAT:
                    if specs_obj.subxpat_v2:
                        # remove sub-graph from the full-graph
                        hole_magraph = remove_subgraph(full_magraph, sub_magraph)
                        # convert the model to a circuit
                        model_magraph = xpat_model_to_magraph(model, iter_id=i)
                        # insert the subgraph into the hole-graph
                        merged_magraph = insert_subgraph(hole_magraph, model_magraph)

                        synth_obj = Synthesis(
                            specs_obj,
                            template_obj.current_graph,  # not used if magraph is given
                            template_obj.json_model,  # not used if magraph is given
                            merged_magraph
                        )

                        # todo:marco: this seems to be working, lets make sure
                        cur_model_results: Dict[str: List[float, float, float, (int, int)]] = {}
                        synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'])
                        print(f"{synth_obj.ver_out_path = }")
                        synth_obj.export_verilog()
                        synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])
                        cur_model_results[synth_obj.ver_out_name] = (
                            synth_obj.estimate_area(),
                            synth_obj.estimate_power(),
                            synth_obj.estimate_delay(),
                            (lpp, ppo)
                        )

                        # Morteza: Here we create a Model object and then save it
                        this_model = Model(id=0, status=cur_status.upper(), cell=(lpp, ppo), et=et, iteration=i,
                                           area=cur_model_results[synth_obj.ver_out_name][0],
                                           total_power=cur_model_results[synth_obj.ver_out_name][1],
                                           delay=cur_model_results[synth_obj.ver_out_name][2],
                                           labeling_time=labeling_time,
                                           subgraph_extraction_time=subgraph_extraction_time,
                                           subgraph_number_inputs=subgraph_number_inputs,
                                           subgraph_number_outputs=subgraph_number_outputs,
                                           subxpat_phase1_time=subxpat_phase1_time,
                                           subxpat_phase2_time=subxpat_phase2_time)
                        stats_obj.grid.cells[lpp][ppo].store_model_info(this_model)
                    else:
                        synth_obj = Synthesis(specs_obj, template_obj.current_graph, template_obj.json_model)
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
                        print(f'{content = }')

                        csvwriter.writerow(header)
                        csvwriter.writerow(content)

                    pprint.success('verifying all approximate circuits -> ', end='')
                    for candidate in cur_model_results:
                        approximate_benchmark = candidate[:-2]

                        obtained_wce_exact = erroreval_verification_wce(exact_file_name, approximate_benchmark, original_et)
                        if specs_obj.subxpat_v2:
                            obtained_wce_prev = erroreval_verification_wce(specs_obj.exact_benchmark, approximate_benchmark, template_obj.et)
                            prev_actual_error = obtained_wce_prev

                        if obtained_wce_exact > original_et:
                            raise Exception(color.error('ErrorEval Verification: FAILED!'))

                    prev_string = ''
                    if specs_obj.subxpat_v2:
                        sum_wce_actual += obtained_wce_prev
                        prev_string = f' and prev_wce = {obtained_wce_prev} with sum of prevs wce = {sum_wce_actual}'
                    pprint.success(f'ErrorEval PASS! with total wce = {obtained_wce_exact}' + prev_string)

                    benchmark_name = specs_obj.benchmark_name

                    # todo:check: this seems to be working, lets make sure
                    specs_obj.exact_benchmark = approximate_benchmark
                    specs_obj.benchmark_name = approximate_benchmark
                    template_obj.set_new_context(specs_obj)

                    synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'], list(cur_model_results.keys())[0])

                    pprint.success(f'Cell = ({lpp}, {ppo}) iteration = {i} -> {cur_status} ({synth_obj.num_of_models} models found)')
                    exact_stats = [synth_obj.estimate_area(exact_file_path),
                                   synth_obj.estimate_power(exact_file_path),
                                   synth_obj.estimate_delay(exact_file_path)]
                    print_current_model(cur_model_results, normalize=False, exact_stats=exact_stats)

                    store_current_model(cur_model_results, exact_stats=exact_stats, benchmark_name=benchmark_name, et=specs_obj.et, encoding=specs_obj.encoding, subgraph_extraction_time=subgraph_extraction_time, labeling_time=labeling_time)

                    for key in cur_model_results.keys():
                        next_generation[key] = cur_model_results[key]
                    pre_iter_unsats[candidate] = 0

                    current_population = select_candidates_for_next_iteration(specs_obj, next_generation)
                    total[i] = current_population

                    next_generation = {}
                    pre_iter_unsats = {}
                    for key in current_population.keys():
                        pre_iter_unsats[key] = 0
                    next_generation = {}
                    pre_iter_unsats = {}
                    for key in current_population.keys():
                        pre_iter_unsats[key] = 0

                    # SAT found, stop grid exploration
                    break

        if exists_an_area_zero(current_population):
            break
    display_the_tree(total)

    stats_obj.store_grid()
    return stats_obj


def cell_iterator(max_lpp: int, max_ppo: int) -> Iterator[Tuple[int, int]]:
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
    specs_obj.ppo = ppo
    specs_obj.iterations = iteration
    return specs_obj


def is_unknown(template_obj: Template_SOP1) -> bool:
    # NOTE: Never used
    """
        checks whether the current model was unknown or not
        :param: the current template object
        :rtype: boolean True if the current result is unknown
    """

    if template_obj.import_json_model():
        # NOTE: Never enters here
        return False

    if template_obj.json_model == UNKNOWN:
        print(f'my unknown!')
        return True
    else:
        return False
    # return template_obj.json_model == UNKNOWN


def is_unsat(template_obj: Template_SOP1) -> bool:
    # NOTE: Never used
    """
        checks whether the current model was unsat or not
        :param: the current template object
        :rtype: boolean True if the current result is unsat
    """

    if template_obj.import_json_model():
        # NOTE: Never enters here
        return False

    if template_obj.json_model == UNSAT:
        print(f'my unsat!')
        return True
    else:
        return False
    # return template_obj.json_model == UNSAT


def get_status(template_obj: Union[Template_SOP1, Template_SOP1ShareLogic]) -> str:
    """
        checks whether the current model was sat, unsat or unknown
        :param: the current template object
        :rtype: an str containing either of SAT, UNSAT, or UNKNOWN
    """

    # note:refactor:marco
    template_obj.import_json_model()
    assert all(res in (SAT, UNSAT, UNKNOWN) for res in template_obj.json_status), f'Invalid status ({template_obj.json_status})'
    # todo:question: why do we return only the 0th element? doesn't the json model include many models?
    return template_obj.json_status[0]

    # original
    # template_obj.import_json_model()
    # if template_obj.json_status[0] == SAT:
    #     return SAT
    # elif template_obj.json_status[0] == UNSAT:
    #     return UNSAT
    # elif template_obj.json_status[0] == UNKNOWN:
    #     return UNKNOWN


def print_current_model(cur_model_result: Dict, normalize: bool = True, exact_stats: List = None) -> None:
    data = []
    if exact_stats:
        exact_area = exact_stats[0]
        exact_power = exact_stats[1]
        exact_delay = exact_stats[2]
        data.append(['Exact', exact_area, exact_power, exact_delay])
        if normalize:
            for key in cur_model_result.keys():
                cur_model_result[key][0] = (cur_model_result[key][0] / exact_area) * 100
                cur_model_result[key][1] = (cur_model_result[key][1] / exact_power) * 100
                cur_model_result[key][2] = (cur_model_result[key][2] / exact_delay) * 100

    if len(cur_model_result) < 10:
        #

        sorted_candidates = sorted(cur_model_result.items(), key=lambda x: x[1])
        for idx, key in enumerate(sorted_candidates):
            # print(f'{sorted_candidates[idx] = }')
            this_id = re.search('(id.*)', sorted_candidates[idx][0]).group(1).split('.')[0]
            this_area = sorted_candidates[idx][1][0]
            this_power = sorted_candidates[idx][1][1]
            this_delay = sorted_candidates[idx][1][2]
            data.append([this_id, this_area, this_power, this_delay])
        pprint.success(tabulate(data, headers=["Design ID", "Area", "Power", "Delay"]))

    else:
        #

        sorted_candidates = sorted(cur_model_result.items(), key=lambda x: x[1])
        # print(sorted_candidates)
        best_id = re.search('(id.*)', sorted_candidates[0][0]).group(1).split('.')[0]
        best_area = sorted_candidates[0][1][0]
        best_power = sorted_candidates[0][1][1]
        best_delay = sorted_candidates[0][1][2]
        data.append([best_id, best_area, best_power, best_delay])
        pprint.success(tabulate(data, headers=["Design ID", "Area", "Power", "Delay"]))
        # print the best model for now

def store_current_model(cur_model_result: Dict, benchmark_name: str, et: int, encoding: int, subgraph_extraction_time: float, labeling_time: float, exact_stats: List = None) -> None:
    with open(f"{z3logpath.OUTPUT_PATH['report'][0]}/area_power_delay.csv", 'a') as f:
        csvwriter = csv.writer(f)

        # to avoid duplicate data 
        if encoding == 2:
            exact_data = []
            if exact_stats:
                exact_area = exact_stats[0]
                exact_power = exact_stats[1]
                exact_delay = exact_stats[2]
                exact_data.append(f'{benchmark_name}')
                exact_data.append('Exact')
                exact_data.append(exact_area)
                exact_data.append(exact_power)
                exact_data.append(exact_delay)
                exact_data.append(et)
                exact_data.append(encoding)
                exact_data.append(labeling_time)
                exact_data.append(subgraph_extraction_time)
                exact_data = tuple(exact_data)

            csvwriter.writerow(exact_data)

        approx_data = []
        sorted_candidates = sorted(cur_model_result.items(), key=lambda x: x[1])
        best_id = re.search('(id.*)', sorted_candidates[0][0]).group(1).split('.')[0]
        best_area = sorted_candidates[0][1][0]
        best_power = sorted_candidates[0][1][1]
        best_delay = sorted_candidates[0][1][2]
        approx_data.append(f'{benchmark_name}')
        approx_data.append(best_id)
        approx_data.append(best_area)
        approx_data.append(best_power)
        approx_data.append(best_delay)
        approx_data.append(et)
        approx_data.append(encoding)
        approx_data.append(labeling_time)
        approx_data.append(subgraph_extraction_time)
        approx_data = tuple(approx_data)

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
        return pick_k_best_k_worst(candidates, spec_obj.population // 2)
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


def display_the_tree(this_dict: Dict) -> None:

    file_path = 'output/file.gv'

    # with open(file_path, 'w') as f:
    #     pass
