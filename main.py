import shutil
import csv
import Z3Log
from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.z3solver import Z3solver
from Z3Log.config import path as z3logpath
# from Z3Log.argument import Arguments
from sxpat.templateCreator import TemplateCreator
from sxpat.templateCreator import Template_SOP1ShareLogic, Template_SOP1
from sxpat.templateSpecs import TemplateSpecs
from sxpat.config.paths import *
from sxpat.synthesis import Synthesis
from sxpat.annotatedGraph import AnnotatedGraph
from sxpat.synthesis import Synthesis
from sxpat.arguments import Arguments
from sxpat.verification import erroreval_verification
from sxpat.xplore import explore_grid
from sxpat.stats import Stats


def main():
    args = Arguments.parse()

    if args.clean:
        clean_all()
    setup_folder_structure()
    for key in OUTPUT_PATH.keys():
        directory = OUTPUT_PATH[key][0]
        if ~os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    specs_obj = TemplateSpecs(name='SOP1ShareLogic', literals_per_product=args.lpp, products_per_output=args.ppo,
                              benchmark_name=args.benchmark_name, exact_benchmark=args.benchmark_name,
                              num_of_models=1, subxpat=args.subxpat, et=args.et,
                              products_in_total=args.pit, shared=args.shared, timeout=args.timeout,
                              partitioning_percentage=0, iterations=1)

    stats_obj = explore_grid(specs_obj)
    stats_obj.store_grid()

    stats_obj.plot_area()
    stats_obj.plot_runtime()


if __name__ == "__main__":
    main()
