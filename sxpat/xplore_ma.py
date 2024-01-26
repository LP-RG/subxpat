import csv
import time
from typing import Iterable, Iterator, Union
from colorama import Fore, Style

from tabulate import tabulate

import Z3Log

from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.z3solver import Z3solver
from Z3Log.config import path as z3logpath
from sxpat.templateCreator import Template_SOP1, Template_SOP1ShareLogic
from sxpat.templateSpecs import TemplateSpecs
from sxpat.config.paths import *
from sxpat.config.config import *
from sxpat.synthesis import Synthesis
from sxpat.utils.filesystem import create_directory
from sxpat.verification import erroreval_verification, erroreval_verification_explicit, erroreval_verification_buggy
from sxpat.stats import Stats
from sxpat.stats import *

# executor
from sxpat.executor.subxpat2_executor import SubXPatV2Executor
# graph
from z_marco.ma_graph import MaGraph, draw_gv, insert_subgraph, extract_subgraph, xpat_model_to_magraph
# distance function
from sxpat.distance_function import WeightedAbsoluteDifference, HammingDistance

from z_marco.utils import pprint, color


def explore_cell(specs_obj: TemplateSpecs):
    pprint.info2(f'cell ({specs_obj.lpp}, {specs_obj.ppo}) et={specs_obj.et} exploration started')

    exact_file_path = f"{INPUT_PATH['ver'][0]}/{specs_obj.benchmark_name}.v"
    total_iterations = specs_obj.iterations

    for iteration in range(1, total_iterations + 1):
        specs_obj.iterations = iteration

        # create template object
        template_obj = Template_SOP1(specs_obj)

        # load graph
        graph = template_obj.import_graph()
        template_obj.current_graph = graph

        # label graph
        t_start = time.time()
        template_obj.label_graph(specs_obj.min_labeling, parallel=True)
        print(f'labeling_time = {time.time() - t_start}')

        # extract subgraph
        t_start = time.time()
        graph.extract_subgraph(specs_obj)
        print(f'subgraph_extraction_time = {time.time() - t_start}')

        graph.export_graph("./aaaaa.gv")
        print("./aaaaa.gv")
        print(*graph.input_dict.items(), sep="\n")
        exit()

        folder = 'output/gv/subgraphs'
        graph_path = f'{folder}/{specs_obj.benchmark_name}_lpp{specs_obj.lpp}_ppo{specs_obj.ppo}_et{specs_obj.et}_mode{specs_obj.mode}_omax{specs_obj.omax}_serr{specs_obj.sub_error_function}.gv'
        create_directory(folder)
        graph.export_annotated_graph(graph_path)
        print(f'exported at {graph_path}')

        # convert AnnotatedGraph to MaGraph(s)
        full_graph = MaGraph.from_digraph(graph.subgraph)
        sub_graph = extract_subgraph(graph)

        # print(full_graph.inputs)
        # print(full_graph.constants)
        # exit()

        # print(sub_graph)
        # draw_gv(sub_graph, "subby.gv")
        # exit(0)

        # define distance/error function of graph
        if specs_obj.full_error_function == 1:
            circuit_distance_function = WeightedAbsoluteDifference(
                full_graph.inputs,
                [2 ** int(out_name.strip("out")) for out_name in full_graph.outputs]
            )
        else:
            raise RuntimeError("Should not ever raise this")

        # define distance/error function of subgraph
        if specs_obj.sub_error_function == 1:
            subcircuit_distance_function = WeightedAbsoluteDifference(
                sub_graph.inputs,
                [graph.subgraph.nodes[n][WEIGHT] for n in sub_graph.unaliased_outputs]
            )
        elif specs_obj.sub_error_function == 2:
            subcircuit_distance_function = HammingDistance(
                sub_graph.inputs
            )
        else:
            raise RuntimeError("Should not ever raise this")

        # log subgraph output info
        print("out_weights =", [(n, graph.subgraph.nodes[n][WEIGHT]) for n in sub_graph.unaliased_outputs])

        # create the executor object
        executor = SubXPatV2Executor(
            full_graph, sub_graph, specs_obj.exact_benchmark,
            specs_obj.literals_per_product, specs_obj.products_per_output,
            circuit_distance_function,
            subcircuit_distance_function,
            specs_obj.et
        )

        # run the executor, retrieving the status (sat, unsat, ...) and the model (only if sat)
        status, model = executor.run()
        if status != 'sat':
            # no model was found
            pprint.warning(f'Change the parameters!')
            exit()

        template_obj.json_model = model
        # print(status, sorted(model.items()))

        # convert the model to a graph
        model_graph = xpat_model_to_magraph(model, iter_id=iteration)
        # insert the model_graph in the full_graph, replacing the original sub_graph
        merged_graph = insert_subgraph(full_graph, model_graph)
        print(merged_graph.inputs, merged_graph.outputs)
        # draw_gv(merged_graph, "banana.gv")

        # create synthesis object
        synth_obj = Synthesis(
            specs_obj,
            template_obj.current_graph,  # not needed but given for now
            template_obj.json_model,  # not needed but given for now
            merged_graph
        )
        # print(synth_obj.verilog_string)

        if iteration > 1:
            synth_obj.benchmark_name = specs_obj.exact_benchmark
            synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'])

        synth_obj.export_verilog()
        synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])
        print(
            f'area = {synth_obj.estimate_area()} (exact = {synth_obj.estimate_area(exact_file_path)})'
        )

        # remove the extension
        approximate_benchmark = synth_obj.ver_out_name[:-2]

        # error evaluation verification failed
        if not erroreval_verification(specs_obj.exact_benchmark, approximate_benchmark, template_obj.et):
            print("VERIFICATION BUG")
            raise Exception(color.error(f'ErrorEval Verification: FAILED!'))

        exit()

        # prepare for next interation
        specs_obj.benchmark_name = approximate_benchmark


def explore_grid(specs_obj: TemplateSpecs):
    print(f'{specs_obj = }')

    if specs_obj.subxpat and specs_obj.shared:
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

    i = 1
    total_iterations = specs_obj.iterations
    exact_file_path = f"{INPUT_PATH['ver'][0]}/{specs_obj.exact_benchmark}.v"
    max_lpp = specs_obj.lpp
    max_ppo = specs_obj.ppo
    max_pit = specs_obj.pit

    if specs_obj.shared:
        max_ppo = specs_obj.pit
    else:
        max_ppo = specs_obj.ppo
    cur_lpp = -1
    cur_ppo = -1

    pre_iter_same = False
    total_number_of_cells_per_iter = max_lpp * max_ppo + 1
    stats_obj = Stats(specs_obj)
    if specs_obj.shared:
        template_obj = Template_SOP1ShareLogic(specs_obj)
    else:
        template_obj = Template_SOP1(specs_obj)

    current_population: Dict = {specs_obj.benchmark_name: -1}
    next_generation: Dict = {}
    total: Dict[Dict] = {}
    pre_iter_unsats: Dict = {specs_obj.benchmark_name: 0}

    for i in range(1, total_iterations + 1):
        if not specs_obj.subxpat:
            print(Fore.LIGHTBLUE_EX + f'Only one iteration' + Style.RESET_ALL)
        else:
            print(Fore.LIGHTBLUE_EX + f'iteration {i}' + Style.RESET_ALL)
        for candidate in current_population:
            # print(f'{pre_iter_unsats[candidate] = } {total_number_of_cells_per_iter = }')
            if pre_iter_unsats[candidate] == total_number_of_cells_per_iter:
                continue
            print(Fore.LIGHTBLUE_EX + f'candidate {candidate}' + Style.RESET_ALL)
            if candidate.endswith('.v'):
                specs_obj.benchmark_name = candidate[:-2]
            template_obj.set_new_context(specs_obj)
            template_obj.current_graph = template_obj.import_graph()
            if specs_obj.max_sensitivity > 0 or specs_obj.mode == 3 or specs_obj.mode == 4:
                template_obj.label_graph(min_labeling=specs_obj.min_labeling)
            subgraph_is_available = template_obj.current_graph.extract_subgraph(specs_obj)

            if subgraph_is_available:
                print(Fore.BLUE + f'Grid ({max_lpp} X {max_ppo}) and et={specs_obj.et} exploration started...' + Style.RESET_ALL)
                ppo = 1
                lpp = 0
                found = False
                while ppo <= max_ppo and not found:
                    while lpp <= max_lpp and not found:

                        if lpp == 0 and ppo > 1:
                            lpp, ppo = next_cell(lpp, ppo, max_lpp, max_ppo)
                            continue

                        specs_obj = set_current_context(specs_obj, lpp, ppo, i)
                        template_obj.set_new_context(specs_obj)
                        template_obj.z3_generate_z3pyscript()
                        template_obj.run_z3pyscript(ET=specs_obj.et, num_models=specs_obj.num_of_models, timeout=10800)
                        cur_status = get_status(template_obj)
                        if cur_status == UNSAT or cur_status == UNKNOWN:
                            print(Fore.YELLOW + f'Cell({lpp},{ppo}) at iteration {i} -> {cur_status.upper()} ' + Style.RESET_ALL)
                            stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                            this_iteration=i,
                                                                            this_area=-1,
                                                                            this_runtime=template_obj.get_json_runtime(),
                                                                            this_status=UNSAT.upper() if cur_status == UNSAT else UNKNOWN.upper(),
                                                                            this_cell=(lpp, ppo))
                            lpp, ppo = next_cell(lpp, ppo, max_lpp, max_ppo)
                            pre_iter_unsats[candidate] += 1

                            # print(f'{lpp}, {ppo}')
                        elif cur_status == SAT:
                            synth_obj = Synthesis(specs_obj, template_obj.current_graph, template_obj.json_model)
                            cur_model_results: Dict[str: List[float, float, float, (int, int)]] = {}
                            for idx in range(synth_obj.num_of_models):
                                synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'], id=idx)
                                synth_obj.export_verilog(idx=idx)
                                synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0], idx=idx)
                                cur_model_results[synth_obj.ver_out_name] = synth_obj.estimate_area(), \
                                    synth_obj.estimate_power(), \
                                    synth_obj.estimate_delay(), \
                                    (lpp, ppo)

                            with open(f"{OUTPUT_PATH['report'][0]}/area_model_nummodels{specs_obj.num_of_models}_{toolname}.csv", 'w') as f:
                                csvwriter = csv.writer(f)

                                header = list(range(len(cur_model_results)))
                                all = list(cur_model_results.values())
                                content = [f for f, _, _, _ in all]
                                print(f'{content = }')

                                csvwriter.writerow(header)
                                csvwriter.writerow(content)

                            print(Fore.GREEN + f'verifying all approximate circuits -> ', end='' + Style.RESET_ALL)
                            for candidate in cur_model_results:
                                approximate_benchmark = candidate[:-2]

                                if not erroreval_verification_explicit(specs_obj.exact_benchmark, approximate_benchmark,
                                                                       template_obj.et):
                                    raise Exception(Fore.RED + f'ErrorEval Verification: FAILED!' + Style.RESET_ALL)
                            print(Fore.GREEN + f'ErrorEval PASS! ' + Style.RESET_ALL)

                            specs_obj.benchmark_name = approximate_benchmark
                            template_obj.set_new_context(specs_obj)

                            cur_lpp = lpp
                            cur_ppo = ppo
                            runtime = template_obj.get_json_runtime()
                            synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'], list(cur_model_results.keys())[0])

                            print(
                                Fore.GREEN + f'Cell = ({cur_lpp}, {cur_ppo}) iteration = {i} -> {cur_status} ({synth_obj.num_of_models} models found)',)
                            exact_stats = [synth_obj.estimate_area(exact_file_path),
                                           synth_obj.estimate_power(exact_file_path),
                                           synth_obj.estimate_delay(exact_file_path)]
                            print_current_model(cur_model_results, normalize=False, exact_stats=exact_stats)

                            found = True

                            for key in cur_model_results.keys():
                                next_generation[key] = cur_model_results[key]
                            pre_iter_unsats[candidate] = 0
            else:
                break

        current_population = select_candidates_for_next_iteration(specs_obj, next_generation)
        total[i] = current_population

        next_generation = {}
        pre_iter_unsats = {}
        for key in current_population.keys():
            pre_iter_unsats[key] = 0

        if exists_an_area_zero(current_population):
            break

    for iteration in total.keys():
        if total[iteration]:
            sorted_candidates = sorted(total[iteration].items(), key=lambda x: x[1])
            # print(Fore.LIGHTGREEN_EX + f'iteration{iteration} = {sorted_candidates}' + Style.RESET_ALL)
            this_iteration = iteration
            this_area = sorted_candidates[0][1][0]
            this_power = sorted_candidates[0][1][1]
            this_delay = sorted_candidates[0][1][2]
            lpp, ppo = sorted_candidates[0][1][3]

            stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                            this_iteration=this_iteration,
                                                            this_area=this_area,
                                                            this_total_power=this_power,
                                                            this_delay=this_delay,
                                                            this_runtime=-1,
                                                            this_status='SAT',
                                                            this_cell=(lpp, ppo))

    display_the_tree(total)

    stats_obj.store_grid()
    return stats_obj


def is_last_cell(cur_lpp, cur_ppo, max_lpp, max_ppo) -> bool:
    return cur_lpp == max_lpp and cur_ppo == max_ppo


def next_cell(cur_lpp, cur_ppo, max_lpp, max_ppo) -> Tuple[int, int]:
    if is_last_cell(cur_lpp, cur_ppo, max_lpp, max_ppo):
        return cur_lpp + 1, cur_lpp + 1
    else:
        if cur_lpp < max_lpp:
            return cur_lpp + 1, cur_ppo
        else:
            return 0, cur_ppo + 1


def cell_iterator(max_lpp: int, max_ppo: int) -> Iterator[Tuple[int, int]]:
    # NOTE: By Marco

    # special cell
    yield (0, 1)

    # grid cells
    for ppo in range(1, max_ppo + 1):
        for lpp in range(1, max_lpp + 1):
            yield (lpp, ppo)


def is_dominated(coords: Tuple[int, int], sats: Iterable[Tuple[int, int]]) -> bool:
    # NOTE: By Marco

    lpp, ppo = coords
    for d_lpp, d_ppo in sats:
        if lpp >= d_lpp and ppo >= d_ppo:
            return True
    return False


def set_current_context(specs_obj: TemplateSpecs, lpp: int, ppo: int, iteration: int) -> TemplateSpecs:
    specs_obj.lpp = lpp
    specs_obj.ppo = ppo
    specs_obj.iterations = iteration

    return specs_obj


def is_unknown(template_obj: Template_SOP1) -> bool:
    """
        checks whether the current model was unknown or not
        :param: the current template object
        :rtype: boolean True if the current result is unknown
    """
    if template_obj.import_json_model():
        return False
    elif template_obj.json_model == UNKNOWN:
        print(f'my unknown!')
        return True
    else:
        return False


def is_unsat(template_obj: Template_SOP1) -> bool:
    """
    checks whether the current model was unsat or not
    :param: the current template object
    :rtype: boolean True if the current result is unsat
    """
    if template_obj.import_json_model():
        return False
    elif template_obj.json_model == UNSAT:
        print(f'my unsat!')
        return True
    else:
        return False


def get_status(template_obj: Union[Template_SOP1, Template_SOP1ShareLogic]) -> str:
    """
    checks whether the current model was sat, unsat or unknown
    :param: the current template object
    :rtype: an str containing either of SAT, UNSAT, or UNKNOWN
    """

    # NOTE: updated by marco
    template_obj.import_json_model()
    assert template_obj.json_status in [SAT, UNSAT, UNKNOWN], "Invalid status"
    return template_obj.json_status

    # original
    if template_obj.json_status == SAT:
        return SAT
    elif template_obj.json_status == UNSAT:
        return UNSAT
    elif template_obj.json_status == UNKNOWN:
        return UNKNOWN


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
        sorted_candidates = sorted(cur_model_result.items(), key=lambda x: x[1])
        for idx, key in enumerate(sorted_candidates):
            # print(f'{sorted_candidates[idx] = }')
            this_id = re.search('(id.*)', sorted_candidates[idx][0]).group(1).split('.')[0]
            this_area = sorted_candidates[idx][1][0]
            this_power = sorted_candidates[idx][1][1]
            this_delay = sorted_candidates[idx][1][2]
            data.append([this_id, this_area, this_power, this_delay])
        print(Fore.LIGHTGREEN_EX + tabulate(data, headers=["Design ID", "Area", "Power", "Delay"]) + Style.RESET_ALL)
    else:
        sorted_candidates = sorted(cur_model_result.items(), key=lambda x: x[1])
        # print(sorted_candidates)
        best_id = re.search('(id.*)', sorted_candidates[0][0]).group(1).split('.')[0]
        best_area = sorted_candidates[0][1][0]
        best_power = sorted_candidates[0][1][1]
        best_delay = sorted_candidates[0][1][2]
        data.append([best_id, best_area, best_power, best_delay])
        print(Fore.LIGHTGREEN_EX + tabulate(data, headers=["Design ID", "Area", "Power", "Delay"]) + Style.RESET_ALL)
        # print the best model for now


def exists_an_area_zero(candidates: Dict[str, float]) -> bool:
    for key in candidates.keys():

        if candidates[key][0] == 0:
            print(Fore.LIGHTMAGENTA_EX + f'Area zero found!\nTerminated.' + Style.RESET_ALL)
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