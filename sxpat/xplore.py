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


def explore_cell(specs_obj: TemplateSpecs):
    print(Fore.BLUE + f'cell ({specs_obj.lpp}, {specs_obj.ppo}) and et={specs_obj.et} exploration started...' + Style.RESET_ALL)
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
    print(Fore.BLUE + f'Grid ({specs_obj.lpp} X {specs_obj.ppo}) and et={specs_obj.et} exploration started...' + Style.RESET_ALL)
    i = 1
    total_iterations = specs_obj.iterations
    exact_file_path = f"{INPUT_PATH['ver'][0]}/{specs_obj.exact_benchmark}.v"
    max_lpp = specs_obj.lpp
    max_ppo = specs_obj.ppo
    cur_lpp = -1
    cur_ppo = -1
    found = False


    for ppo in range(1, max_ppo + 1):

        for lpp in range(max_lpp + 1):

            for i in range(1, total_iterations):
                if lpp == 0 and ppo > 1:
                    # print(Fore.BLUE + f'skipping over ({lpp}, {ppo}) and so on...')
                    break
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
                    if not erroreval_verification(specs_obj.exact_benchmark, approximate_benchmark, template_obj.et):
                        raise Exception(Fore.RED + f'ErrorEval Verification: FAILED!' + Style.RESET_ALL)
                    specs_obj.benchmark_name = approximate_benchmark

                    cur_lpp = lpp
                    cur_ppo = ppo

                    print(Fore.GREEN + f'Dominant SAT Cell = ({cur_lpp}, {cur_ppo}) iteration = {i}', end='')
                    print(f' -> [area = {synth_obj.estimate_area()} (exact = {synth_obj.estimate_area(exact_file_path)})]' + Style.RESET_ALL)
                    found = True
                    exit()
                else:
                    print(Fore.YELLOW + f'Cell({lpp},{ppo}) at iteration {i} -> UNSAT ' + Style.RESET_ALL)
                    break


            if found:
                break
        if found:
            break

    if cur_lpp != -1 and cur_ppo != -1:
        print(Fore.BLUE + f'Exploration of non-dominated cells started...' + Style.RESET_ALL)

        for ppo in range(cur_ppo + 1, max_ppo + 1):
            for lpp in range(1, cur_lpp - 1):
                print(Fore.BLUE + f'Cell({lpp}, {ppo})')
                for i in range(1, total_iterations):
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
                        print(f'area = {synth_obj.estimate_area()} (exact = {synth_obj.estimate_area(exact_file_path)})')
                        approximate_benchmark = synth_obj.ver_out_name[:-2]  # remove the extension
                        if not erroreval_verification(specs_obj.exact_benchmark, approximate_benchmark, template_obj.et):
                            raise Exception(Fore.RED + f'ErrorEval Verification: FAILED!' + Style.RESET_ALL)
                        specs_obj.benchmark_name = approximate_benchmark
                        print(Fore.GREEN + f'Another SAT Cell = ({cur_lpp}, {cur_ppo})' + Style.RESET_ALL)




