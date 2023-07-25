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
    i = 1
    total_iterations = specs_obj.iterations
    while i <= total_iterations:
        specs_obj.iterations = i
        print(Fore.GREEN + f'{specs_obj}' + Style.RESET_ALL)
        template_obj = Template_SOP1(specs_obj)

        print(Fore.GREEN + f'{template_obj}' + Style.RESET_ALL)
        template_obj.z3_generate_z3pyscript()

        template_obj.run_z3pyscript(specs_obj.et)
        template_obj.import_json_model()

        synth_obj = Synthesis(specs_obj, template_obj.current_graph, template_obj.json_model)


        if i > 1:
            synth_obj.benchmark_name = specs_obj.exact_benchmark
            synth_obj.set_path(z3logpath.OUTPUT_PATH['ver'])

        synth_obj.export_verilog()
        synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])
        print(f'area = {synth_obj.estimate_area()}')

        approximate_benchmark = synth_obj.ver_out_name[:-2]  # remove the extension
        erroreval_verification(specs_obj.exact_benchmark, approximate_benchmark, template_obj.et)

        i += 1

        specs_obj.benchmark_name = approximate_benchmark


def explore_grid():
    pass
