import csv
from typing import Iterator
from colorama import Fore, Style
import Z3Log

from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.z3solver import Z3solver
from Z3Log.config import path as z3logpath
from sxpat.templateCreator import Template_SOP1
from sxpat.templateSpecs import TemplateSpecs
from sxpat.config.paths import *
from sxpat.config.config import *
from sxpat.synthesis import Synthesis
from sxpat.verification import erroreval_verification
from sxpat.stats import Stats
from sxpat.stats import *

# executor
from sxpat.executor.subxpat2_executor import SubXPatV2Executor
# graph
from z_marco.ma_graph import MaGraph, draw_gv, insert_subgraph, exctract_subgraph, xpat_model_to_magraph
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

        # generate subgraph
        template_obj.label_graph(False, True)
        graph.extract_subgraph(specs_obj)
        # graph.export_annotated_graph()

        # convert AnnotatedGraph to MaGraph(s)
        full_graph = MaGraph.from_digraph(graph.subgraph)
        # full_graph = outputs_reordered(full_graph, ['out0', 'out1', 'out2'])
        sub_graph = exctract_subgraph(graph)

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

        # TODO
        # far partire esperimenti con ham e wad
        # - ham vs wad
        # -

        # integra subgraph extraction

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
        exit()
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
        # draw_gv(merged_graph, "banana.gv")
        # exit()

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
            raise Exception(color.error(f'ErrorEval Verification: FAILED!'))

        exit()

        # prepare for next interation
        specs_obj.benchmark_name = approximate_benchmark


def explore_grid(specs_obj: TemplateSpecs):
    print(f'{specs_obj = }')
    print(Fore.BLUE + f'Subxpat started...' + Style.RESET_ALL)
    i = 1
    total_iterations = specs_obj.iterations
    exact_file_path = f"{INPUT_PATH['ver'][0]}/{specs_obj.exact_benchmark}.v"
    max_lpp = specs_obj.lpp
    max_ppo = specs_obj.ppo
    cur_lpp = -1
    cur_ppo = -1

    pre_iter_unsats = 0
    total_number_of_cells_per_iter = max_lpp * max_ppo + 1
    stats_obj = Stats(specs_obj)
    template_obj = Template_SOP1(specs_obj)

    for i in range(1, total_iterations + 1):

        if pre_iter_unsats == total_number_of_cells_per_iter:
            break
        print(Fore.LIGHTBLUE_EX + f'iteration {i}' + Style.RESET_ALL)
        template_obj.current_graph = template_obj.import_graph()

        # if specs_obj.exact_benchmark != specs_obj.benchmark_name:
        #     folder, extension = INPUT_PATH['ver']
        #     print(f'{folder}/{specs_obj.benchmark_name}.{extension}')
        #     if os.path.exists(f'{folder}/{specs_obj.benchmark_name}.{extension}'):
        #         print(f'Exists!')
        #         os.remove(f'{folder}/{specs_obj.benchmark_name}.{extension}')

        if specs_obj.max_sensitivity > 0:
            template_obj.label_graph(2)
        subgraph_is_available = template_obj.current_graph.extract_subgraph(
            specs_obj)

        if subgraph_is_available:
            print(
                Fore.BLUE + f'Grid ({max_lpp} X {max_ppo}) and et={specs_obj.et} exploration started...' + Style.RESET_ALL)
            ppo = 1
            lpp = 0
            found = False
            while ppo <= max_ppo:
                if found:
                    break
                while lpp <= max_lpp:
                    if found:
                        break
                    if lpp == 0 and ppo > 1:
                        lpp, ppo = next_cell(lpp, ppo, max_lpp, max_ppo)
                        continue

                    specs_obj = set_current_context(specs_obj, lpp, ppo, i)
                    template_obj.set_new_context(specs_obj)
                    template_obj.z3_generate_z3pyscript()

                    template_obj.run_z3pyscript(
                        specs_obj.et, specs_obj.num_of_models, 10800)
                    cur_status = get_status(template_obj)

                    if cur_status == EMPTY:  # if empty
                        stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                        this_iteration=i,
                                                                        this_area='',
                                                                        this_runtime='',
                                                                        this_status='Empty',
                                                                        this_cell=(lpp, ppo))
                        print(
                            Fore.YELLOW + f'Cell({lpp},{ppo}) at iteration {i} -> Empty ' + Style.RESET_ALL)

                        lpp, ppo = next_cell(lpp, ppo, max_lpp, max_ppo)
                    elif cur_status == UNSAT:  # if unsat
                        print(
                            Fore.YELLOW + f'Cell({lpp},{ppo}) at iteration {i} -> UNSAT ' + Style.RESET_ALL)
                        runtime = template_obj.get_json_runtime()
                        stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                        this_iteration=i,
                                                                        this_area=-1,
                                                                        this_runtime=runtime,
                                                                        this_status='UNSAT',
                                                                        this_cell=(lpp, ppo))

                        lpp, ppo = next_cell(lpp, ppo, max_lpp, max_ppo)
                        pre_iter_unsats += 1
                    elif cur_status == UNKNOWN:  # if unknown
                        print(
                            Fore.MAGENTA + f'Cell({lpp},{ppo}) at iteration {i} -> TIMEOUT ' + Style.RESET_ALL)
                        runtime = template_obj.get_json_runtime()
                        stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                        this_iteration=i,
                                                                        this_area=-1,
                                                                        this_runtime=runtime,
                                                                        this_status=sxpatconfig.UNKNOWN,
                                                                        this_cell=(lpp, ppo))

                        lpp, ppo = next_cell(lpp, ppo, max_lpp, max_ppo)
                        pre_iter_unsats += 1
                    elif cur_status == SAT:  # if sat
                        # if sat => move up to the next iteration, reset the parameters
                        synth_obj = Synthesis(
                            specs_obj, template_obj.current_graph, template_obj.json_model)
                        if i > 1:
                            synth_obj.benchmark_name = specs_obj.exact_benchmark
                            synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'])
                        synth_obj.export_verilog()
                        synth_obj.export_verilog(
                            z3logpath.INPUT_PATH['ver'][0])

                        # remove the extension
                        approximate_benchmark = synth_obj.ver_out_name[:-2]
                        if not erroreval_verification(specs_obj.exact_benchmark, approximate_benchmark,
                                                      template_obj.et):
                            raise Exception(
                                Fore.RED + f'ErrorEval Verification: FAILED!' + Style.RESET_ALL)
                        specs_obj.benchmark_name = approximate_benchmark
                        template_obj.set_new_context(specs_obj)
                        cur_lpp = lpp
                        cur_ppo = ppo
                        runtime = template_obj.get_json_runtime()
                        area = synth_obj.estimate_area()
                        delay = synth_obj.estimate_delay()
                        if area == 0.0 and delay == -1:
                            delay = 0.0
                        total_power = synth_obj.estimate_power()

                        print(
                            Fore.GREEN + f'Cell = ({cur_lpp}, {cur_ppo}) iteration = {i} -> SAT', end='')
                        print(
                            f' -> [area={area}, power={total_power}, delay={delay}'
                            f' (exact area={synth_obj.estimate_area(exact_file_path)},'
                            f' exact power={synth_obj.estimate_power(exact_file_path)},'
                            f' exact delay={synth_obj.estimate_delay(exact_file_path)})]' + Style.RESET_ALL)

                        found = True

                        stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                        this_iteration=i,
                                                                        this_area=area,
                                                                        this_total_power=total_power,
                                                                        this_delay=delay,
                                                                        this_runtime=runtime,
                                                                        this_status='SAT',
                                                                        this_cell=(lpp, ppo))
        else:
            break
    stats_obj.store_grid()
    return stats_obj


def is_last_cell(cur_lpp, cur_ppo, max_lpp, max_ppo) -> bool:
    # NOTE: Update by Marco
    return cur_lpp == max_lpp and cur_ppo == max_ppo

    # Original
    if cur_lpp == max_lpp and cur_ppo == max_ppo:
        return True
    else:
        return False


def next_cell(cur_lpp, cur_ppo, max_lpp, max_ppo) -> (int, int):
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
    for ppo in range(1, max_ppo):
        for lpp in range(1, max_lpp):
            yield (lpp, ppo)


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


def get_status(template_obj: Template_SOP1) -> str:
    """
    checks whether the current model was sat, unsat or unknown
    :param: the current template object
    :rtype: an str containing either of SAT, UNSAT, or UNKNOWN
    """
    template_obj.import_json_model()
    if template_obj.json_status == SAT:
        return SAT
    elif template_obj.json_status == UNSAT:
        return UNSAT
    elif template_obj.json_status == UNKNOWN:
        return UNKNOWN
