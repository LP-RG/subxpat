import shutil
import csv
from colorama import Fore, Style

from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.z3solver import Z3solver
from Z3Log.config import path as z3logpath

from sxpat.templateCreator import Template_SOP1
from sxpat.templateSpecs import TemplateSpecs
from sxpat.config import paths as sxpatpaths
from sxpat.config import config as sxpatconfig

from sxpat.synthesis import Synthesis
from sxpat.arguments import Arguments


from sxpat.xplore import explore_grid#, explore_grid_shared
from sxpat.stats import Stats, Result


def clean_all():
    directories = [z3logpath.OUTPUT_PATH['ver'][0], z3logpath.OUTPUT_PATH['aig'][0], z3logpath.OUTPUT_PATH['gv'][0],
                   z3logpath.OUTPUT_PATH['z3'][0],
                   z3logpath.OUTPUT_PATH['report'][0], z3logpath.OUTPUT_PATH['figure'][0], z3logpath.TEST_PATH['tb'][0],
                   sxpatpaths.OUTPUT_PATH['area'][0], sxpatpaths.OUTPUT_PATH['power'][0], sxpatpaths.OUTPUT_PATH['delay'][0],
                   z3logpath.LOG_PATH['yosys'][0],
                   sxpatpaths.OUTPUT_PATH['json'][0]]

    for directory in directories:

        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)


def main():
    args = Arguments.parse()
    print(f'{args = }')
    # exit()




    if args.plot:

        print(Fore.BLUE + f'Plotting...' + Style.RESET_ALL)
        specs_obj = TemplateSpecs(name='Sop1' if not args.shared else 'SharedLogic', exact=args.benchmark_name, literals_per_product=args.lpp,
                                  products_per_output=args.ppo,
                                  benchmark_name=args.approximate_benchmark, num_of_models=args.num_models, subxpat=args.subxpat,
                                  et=args.et,
                                  partitioning_percentage=args.partitioning_percentage, iterations=args.iterations,
                                  grid=args.grid, imax=args.imax, omax=args.omax, sensitivity=args.sensitivity,
                                  timeout=args.timeout, subgraph_size=args.subgraph_size, mode=args.mode, population=args.population,
                                  min_labeling=args.min_labeling,
                                  shared= args.shared, products_in_total=args.pit)
        stats_obj = Stats(specs_obj)
        stats_obj.gather_results()




    else:
        if args.clean:
            print(Fore.BLUE + f'cleaning...' + Style.RESET_ALL)
            clean_all()

        setup_folder_structure()
        for key in sxpatpaths.OUTPUT_PATH.keys():
            directory = sxpatpaths.OUTPUT_PATH[key][0]
            if ~os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

        specs_obj = TemplateSpecs(name='Sop1' if not args.shared else 'SharedLogic', exact=args.benchmark_name, literals_per_product=args.lpp,
                                  products_per_output=args.ppo,
                                  benchmark_name=args.approximate_benchmark, num_of_models=args.num_models, subxpat=args.subxpat,
                                  et=args.et,
                                  partitioning_percentage=args.partitioning_percentage, iterations=args.iterations,
                                  grid=args.grid, imax=args.imax, omax=args.omax, sensitivity=args.sensitivity,
                                  timeout=args.timeout, subgraph_size=args.subgraph_size, mode=args.mode, population=args.population,
                                  min_labeling=args.min_labeling,
                                  shared= args.shared, products_in_total=args.pit)

        if specs_obj.grid:
            stats_obj = explore_grid(specs_obj)
            # if specs_obj.shared:
            #     stats_obj = explore_grid_shared(specs_obj)
            # else:
            #     stats_obj = explore_grid(specs_obj)



if __name__ == "__main__":
    main()
