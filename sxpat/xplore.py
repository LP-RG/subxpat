import csv
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


def explore_cell(specs_obj: TemplateSpecs):
    print(
        Fore.BLUE + f'cell ({specs_obj.lpp}, {specs_obj.ppo}) and et={specs_obj.et} exploration started...' + Style.RESET_ALL)
    i = 1
    total_iterations = specs_obj.iterations
    exact_file_path = f"{INPUT_PATH['ver'][0]}/{specs_obj.exact_benchmark}.v"
    for i in range(1, total_iterations):
        specs_obj.iterations = i
        template_obj = Template_SOP1(specs_obj)
        template_obj.z3_generate_z3pyscript()
        template_obj.run_z3pyscript(specs_obj.et)

        if template_obj.import_json_model():
            synth_obj = Synthesis(specs_obj, template_obj.current_graph, template_obj.json_model)
            if i > 1:
                synth_obj.benchmark_name = specs_obj.exact_benchmark
                synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'])
            synth_obj.export_verilog()
            synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])
            print(f'area = {synth_obj.estimate_area()} (exact = {synth_obj.estimate_area(exact_file_path)})')
            approximate_benchmark = synth_obj.ver_out_name[:-2]  # remove the extension
            if not erroreval_verification(specs_obj.exact_benchmark, approximate_benchmark, template_obj.et):
                raise Exception(Fore.RED + f'ErrorEval Verification: FAILED!' + Style.RESET_ALL)
            specs_obj.benchmark_name = approximate_benchmark
        else:
            print(Fore.YELLOW + f'Change the parameters!' + Style.RESET_ALL)
            exit()


def explore_grid(specs_obj: TemplateSpecs):
    print(
        Fore.BLUE + f'Subxpat started...' + Style.RESET_ALL)
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

        # run for a cell
        # print(f'importing the graph')
        template_obj.current_graph = template_obj.import_graph()
        # template_obj.label_graph(0)
        # print(f'graph is imported')
        subgraph_is_available = template_obj.current_graph.extract_subgraph(specs_obj)

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
                    if i == 1:
                        grid_row = lpp
                        grid_column = ppo
                    elif i == 2:
                        grid_row = cur_lpp
                        grid_column = cur_ppo
                    specs_obj = set_current_context(specs_obj, lpp, ppo, i)
                    template_obj.set_new_context(specs_obj)
                    template_obj.z3_generate_z3pyscript()
                    template_obj.run_z3pyscript(specs_obj.et, specs_obj.num_of_models, 10800)
                    cur_status = get_status(template_obj)

                    if cur_status == EMPTY:  # if empty
                        stats_obj.grid.cells[grid_row][grid_column].store_model_info(this_model_id=0,
                                                                        this_iteration=i,
                                                                        this_area='',
                                                                        this_runtime='',
                                                                        this_status='Empty',
                                                                        this_cell=(lpp, ppo))
                        print(Fore.YELLOW + f'Cell({lpp},{ppo}) at iteration {i} -> Empty ' + Style.RESET_ALL)

                        lpp, ppo = next_cell(lpp, ppo, max_lpp, max_ppo)
                    elif cur_status == UNSAT: # if unsat
                        print(Fore.YELLOW + f'Cell({lpp},{ppo}) at iteration {i} -> UNSAT ' + Style.RESET_ALL)
                        runtime = template_obj.get_json_runtime()
                        stats_obj.grid.cells[grid_row][grid_column].store_model_info(this_model_id=0,
                                                                        this_iteration=i,
                                                                        this_area=-1,
                                                                        this_runtime=runtime,
                                                                        this_status='UNSAT',
                                                                        this_cell=(lpp, ppo))

                        lpp, ppo = next_cell(lpp, ppo, max_lpp, max_ppo)
                        pre_iter_unsats += 1
                    elif cur_status == UNKNOWN: # if unknown
                        print(Fore.MAGENTA + f'Cell({lpp},{ppo}) at iteration {i} -> TIMEOUT ' + Style.RESET_ALL)
                        runtime = template_obj.get_json_runtime()
                        stats_obj.grid.cells[grid_row][grid_column].store_model_info(this_model_id=0,
                                                                        this_iteration=i,
                                                                        this_area=-1,
                                                                        this_runtime=runtime,
                                                                        this_status=sxpatconfig.UNKNOWN,
                                                                        this_cell=(lpp, ppo))

                        lpp, ppo = next_cell(lpp, ppo, max_lpp, max_ppo)
                        pre_iter_unsats += 1
                    elif cur_status == SAT:  # if sat
                        # if sat => move up to the next iteration, reset the parameters
                        synth_obj = Synthesis(specs_obj, template_obj.current_graph, template_obj.json_model)
                        if i > 1:
                            synth_obj.benchmark_name = specs_obj.exact_benchmark
                            synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'])
                        synth_obj.export_verilog()
                        synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])

                        approximate_benchmark = synth_obj.ver_out_name[:-2]  # remove the extension
                        if not erroreval_verification(specs_obj.exact_benchmark, approximate_benchmark,
                                                      template_obj.et):
                            raise Exception(Fore.RED + f'ErrorEval Verification: FAILED!' + Style.RESET_ALL)
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

                        print(Fore.GREEN + f'Cell = ({cur_lpp}, {cur_ppo}) iteration = {i} -> SAT', end='')
                        print(
                            f' -> [area={area}, power={total_power}, delay={delay}'
                            f' (exact area={synth_obj.estimate_area(exact_file_path)},'
                            f' exact power={synth_obj.estimate_power(exact_file_path)},'
                            f' exact delay={synth_obj.estimate_delay(exact_file_path)})]' + Style.RESET_ALL)

                        found = True

                        stats_obj.grid.cells[grid_row][grid_column].store_model_info(this_model_id=0,
                                                                            this_iteration=i,
                                                                            this_area=area,
                                                                            this_total_power = total_power,
                                                                            this_delay = delay,
                                                                            this_runtime=runtime,
                                                                            this_status='SAT',
                                                                            this_cell=(lpp, ppo))
        else:
            break
    stats_obj.store_grid()
    return stats_obj


def is_last_cell(cur_lpp, cur_ppo, max_lpp, max_ppo) -> bool:
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



def explore_grid_old(specs_obj: TemplateSpecs):
    print(
        Fore.BLUE + f'Grid ({specs_obj.lpp} X {specs_obj.ppo}) and et={specs_obj.et} exploration started...' + Style.RESET_ALL)
    i = 1
    total_iterations = specs_obj.iterations
    exact_file_path = f"{INPUT_PATH['ver'][0]}/{specs_obj.exact_benchmark}.v"
    max_lpp = specs_obj.lpp
    max_ppo = specs_obj.ppo
    cur_lpp = -1
    cur_ppo = -1
    found = False

    stats_obj = Stats(specs_obj)

    for ppo in range(1, max_ppo + 1):
        for lpp in range(max_lpp + 1):
            for i in range(1, total_iterations + 1):
                if lpp == 0 and ppo > 1:
                    break
                specs_obj.lpp = lpp
                specs_obj.ppo = ppo
                specs_obj.iterations = i
                try:
                    template_obj = Template_SOP1(specs_obj)
                except:

                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                    this_iteration=i,
                                                                    this_area='',
                                                                    this_runtime='',
                                                                    this_status='Empty')
                    break
                template_obj.z3_generate_z3pyscript()
                template_obj.run_z3pyscript(specs_obj.et)

                if template_obj.import_json_model():

                    synth_obj = Synthesis(specs_obj, template_obj.current_graph, template_obj.json_model)
                    if i > 1:
                        synth_obj.benchmark_name = specs_obj.exact_benchmark
                        synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'])
                    synth_obj.export_verilog()
                    synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])

                    approximate_benchmark = synth_obj.ver_out_name[:-2]  # remove the extension
                    if not erroreval_verification(specs_obj.exact_benchmark, approximate_benchmark, template_obj.et):
                        raise Exception(Fore.RED + f'ErrorEval Verification: FAILED!' + Style.RESET_ALL)
                    specs_obj.benchmark_name = approximate_benchmark

                    cur_lpp = lpp
                    cur_ppo = ppo
                    runtime = template_obj.get_json_runtime()
                    area = synth_obj.estimate_area()

                    print(Fore.GREEN + f'Dominant SAT Cell = ({cur_lpp}, {cur_ppo}) iteration = {i}', end='')
                    print(
                        f' -> [area = {synth_obj.estimate_area()} (exact = {synth_obj.estimate_area(exact_file_path)})]' + Style.RESET_ALL)
                    found = True

                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                    this_iteration=i,
                                                                    this_area=area,
                                                                    this_runtime=runtime,
                                                                    this_status='SAT')


                else:
                    print(Fore.YELLOW + f'Cell({lpp},{ppo}) at iteration {i} -> UNSAT ' + Style.RESET_ALL)
                    runtime = template_obj.get_json_runtime()

                    area = -1

                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                    this_iteration=i,
                                                                    this_area=area,
                                                                    this_runtime=runtime,
                                                                    this_status='UNSAT')

                    break

            if found:
                break
        if found:
            break

    if cur_lpp != -1 and cur_ppo != -1:
        print(Fore.BLUE + f'Exploration of non-dominated cells started...' + Style.RESET_ALL)

        for ppo in range(cur_ppo + 1, max_ppo + 1):
            for lpp in range(1, cur_lpp):
                for i in range(1, total_iterations + 1):
                    specs_obj.lpp = lpp
                    specs_obj.ppo = ppo
                    specs_obj.iterations = i
                    template_obj = Template_SOP1(specs_obj)
                    template_obj.z3_generate_z3pyscript()
                    template_obj.run_z3pyscript(specs_obj.et)

                    if template_obj.import_json_model():
                        synth_obj = Synthesis(specs_obj, template_obj.current_graph, template_obj.json_model)
                        if i > 1:
                            synth_obj.benchmark_name = specs_obj.exact_benchmark
                            synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'])
                        synth_obj.export_verilog()
                        synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])

                        approximate_benchmark = synth_obj.ver_out_name[:-2]  # remove the extension
                        if not erroreval_verification(specs_obj.exact_benchmark, approximate_benchmark,
                                                      template_obj.et):
                            raise Exception(Fore.RED + f'ErrorEval Verification: FAILED!' + Style.RESET_ALL)
                        specs_obj.benchmark_name = approximate_benchmark

                        runtime = template_obj.get_json_runtime()
                        area = synth_obj.estimate_area()

                        print(Fore.GREEN + f'Another (non-dominated) SAT Cell = ({lpp}, {ppo}) iteration = {i}', end='')
                        print(
                            f' -> [area = {synth_obj.estimate_area()} (exact = {synth_obj.estimate_area(exact_file_path)})]' + Style.RESET_ALL)
                        found = True
                        stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                        this_iteration=i,
                                                                        this_area=area,
                                                                        this_runtime=runtime,
                                                                        this_status='SAT')
                    else:
                        runtime = template_obj.get_json_runtime()
                        area = -1
                        stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                        this_iteration=i,
                                                                        this_area=area,
                                                                        this_runtime=runtime,
                                                                        this_status='UNSAT')

                        print(Fore.YELLOW + f'Cell({lpp},{ppo}) at iteration {i} -> UNSAT ' + Style.RESET_ALL)
                        break

    stats_obj.store_grid()
