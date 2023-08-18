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
from sxpat.xplore import explore_grid_shared, explore_grid_xpat
from sxpat.stats import Stats


def main():
    args = Arguments.parse()

    if args.plot:
        specs_obj = TemplateSpecs(name='SOP1ShareLogic', literals_per_product=args.lpp, products_per_output=args.ppo,
                                  benchmark_name=args.benchmark_name, exact_benchmark=args.benchmark_name,
                                  num_of_models=1, subxpat=args.subxpat, et=args.et,
                                  products_in_total=args.pit, shared=args.shared, timeout=args.timeout,
                                  partitioning_percentage=0, iterations=1, all=args.all)

        stats_obj = Stats(specs_obj)
        stats_obj.plot_area()
        stats_obj.plot_runtime()
        exit()

    else:
        if args.clean:
            clean_all()
        setup_folder_structure()
        for key in OUTPUT_PATH.keys():
            directory = OUTPUT_PATH[key][0]
            if ~os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

        if args.multiple:
            n_o = int(re.search(f'.*o(\d+).*', args.benchmark_name).group(1))
            max_error = 2 ** (n_o - 1)
            if max_error <= 8:
                et_array = list(range(1, max_error + 1))
            else:
                step = max_error // 8
                et_array = list(range(step, max_error + 1, step))

            for et in et_array:
                specs_obj = TemplateSpecs(name='SOP1ShareLogic', literals_per_product=args.lpp, products_per_output=args.ppo,
                                      benchmark_name=args.benchmark_name, exact_benchmark=args.benchmark_name,
                                      num_of_models=1, subxpat=args.subxpat, et=et,
                                      products_in_total=args.pit, shared=args.shared, timeout=args.timeout,
                                      partitioning_percentage=0, iterations=1, all=args.all)

                if args.shared:
                    stats_obj = explore_grid_shared(specs_obj)
                else:
                    stats_obj = explore_grid_xpat(specs_obj)
                stats_obj.store_grid()
        else:
            specs_obj = TemplateSpecs(name='SOP1ShareLogic', literals_per_product=args.lpp, products_per_output=args.ppo,
                                      benchmark_name=args.benchmark_name, exact_benchmark=args.benchmark_name,
                                      num_of_models=1, subxpat=args.subxpat, et=args.et,
                                      products_in_total=args.pit, shared=args.shared, timeout=args.timeout,
                                      partitioning_percentage=0, iterations=1, all=args.all)

            if args.shared:
                stats_obj = explore_grid_shared(specs_obj)
            else:
                stats_obj = explore_grid_xpat(specs_obj)
            stats_obj.store_grid()



if __name__ == "__main__":
    main()
