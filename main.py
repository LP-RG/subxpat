import shutil
import csv
import Z3Log
from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.z3solver import Z3solver
from Z3Log.config import path as z3logpath

from sxpat.templateCreator import Template_SOP1
from sxpat.templateSpecs import TemplateSpecs
from sxpat.config.paths import *

from sxpat.synthesis import Synthesis
from sxpat.arguments import Arguments
from sxpat.xplore import explore_cell, explore_grid


def clean_all():
    directories = [z3logpath.OUTPUT_PATH['ver'][0], z3logpath.OUTPUT_PATH['aig'][0], z3logpath.OUTPUT_PATH['gv'][0],
                   z3logpath.OUTPUT_PATH['z3'][0],
                   z3logpath.OUTPUT_PATH['report'][0], z3logpath.OUTPUT_PATH['figure'][0], z3logpath.TEST_PATH['tb'][0],
                   OUTPUT_PATH['area'][0], OUTPUT_PATH['power'][0], OUTPUT_PATH['delay'][0],
                   z3logpath.LOG_PATH['yosys'][0],
                   OUTPUT_PATH['json'][0]]

    for directory in directories:
        shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)


def main():
    args = Arguments.parse()

    if args.clean:
        clean_all()

    setup_folder_structure()
    for key in OUTPUT_PATH.keys():
        directory = OUTPUT_PATH[key][0]
        if ~os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    specs_obj = TemplateSpecs(name='Sop1', exact=args.benchmark_name, literals_per_product=args.lpp, products_per_output=args.ppo,
                              benchmark_name=args.benchmark_name, num_of_models=1, subxpat=args.subxpat, et=args.et,
                              partitioning_percentage=args.partitioning_percentage, iterations=args.iterations)

    explore_cell(specs_obj)


if __name__ == "__main__":
    main()
