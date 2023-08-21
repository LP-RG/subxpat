import shutil
import csv

from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.z3solver import Z3solver
from Z3Log.config import path as z3logpath

from sxpat.templateCreator import Template_SOP1
from sxpat.templateSpecs import TemplateSpecs
from sxpat.config import paths as sxpatpaths

from sxpat.synthesis import Synthesis
from sxpat.arguments import Arguments
from sxpat.xplore import explore_cell, explore_grid
from sxpat.stats import Stats

def main():
    args = Arguments.parse()

    if args.clean:
        print(f'cleaning...')
        clean_all()

    setup_folder_structure()
    for key in sxpatpaths.OUTPUT_PATH.keys():
        directory = sxpatpaths.OUTPUT_PATH[key][0]
        if ~os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    specs_obj = TemplateSpecs(name='Sop1', exact=args.benchmark_name, literals_per_product=args.lpp,
                              products_per_output=args.ppo,
                              benchmark_name=args.approximate_benchmark, num_of_models=1, subxpat=args.subxpat,
                              et=args.et,
                              partitioning_percentage=args.partitioning_percentage, iterations=args.iterations,
                              grid=args.grid)

    template_obj = Template_SOP1(specs_obj)

if __name__ == "__main__":
    main()