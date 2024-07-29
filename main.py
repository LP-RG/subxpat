import time
from Z3Log.utils import setup_folder_structure
from Z3Log.config import path as z3logpath

from sxpat.templateSpecs import TemplateSpecs
from sxpat.config import paths as sxpatpaths

from sxpat.arguments import Arguments

from sxpat.xplore import explore_grid
from sxpat.stats import Stats

from z_marco.utils import pprint
from sxpat.utils.filesystem import FS


def main():
    args = Arguments.parse()
    print(f'{args = }')

    if args.plot:
        pprint.info2('Plotting...')

        specs_obj = TemplateSpecs(name='Sop1' if not args.shared else 'SharedLogic', exact=args.benchmark_name,
                                  literals_per_product=args.lpp, products_per_output=args.ppo,
                                  benchmark_name=args.approximate_benchmark, num_of_models=args.num_models,
                                  subxpat=args.subxpat, subxpat_v2=args.subxpat_v2,
                                  full_error_function=args.full_error_function,
                                  sub_error_function=args.sub_error_function,
                                  et=args.et, et_partitioning=args.et_partitioning,
                                  partitioning_percentage=args.partitioning_percentage, iterations=args.iterations,
                                  grid=args.grid, imax=args.imax, omax=args.omax, sensitivity=args.sensitivity,
                                  timeout=args.timeout, subgraph_size=args.subgraph_size, mode=args.mode,
                                  population=args.population,
                                  min_labeling=args.min_labeling, manual_nodes=args.manual_nodes,
                                  shared=args.shared, products_in_total=args.pit, parallel=args.parallel,
                                  encoding=args.encoding,
                                  partial_labeling=args.partial_labeling, num_subgraphs=args.num_subgraphs,
                                  multilevel=args.multilevel,number_of_levels=args.lv)
        stats_obj = Stats(specs_obj)
        stats_obj.gather_results()

    else:
        if args.clean:
            pprint.info2('cleaning...')
            clean_all()

        setup_folder_structure()
        for (directory, _) in sxpatpaths.OUTPUT_PATH.values():
            FS.mkdir(directory)

        # todo:later: update how we create the templatespecs (more than 2 names, ecc.)
        specs_obj = TemplateSpecs(name='Sop1' if not args.shared else 'SharedLogic', exact=args.benchmark_name,
                                  literals_per_product=args.lpp, products_per_output=args.ppo,
                                  benchmark_name=args.approximate_benchmark, num_of_models=args.num_models,
                                  subxpat=args.subxpat, subxpat_v2=args.subxpat_v2,
                                  full_error_function=args.full_error_function, sub_error_function=args.sub_error_function,
                                  et=args.et, et_partitioning=args.et_partitioning,
                                  partitioning_percentage=args.partitioning_percentage, iterations=args.iterations,
                                  grid=args.grid, imax=args.imax, omax=args.omax, sensitivity=args.sensitivity,
                                  timeout=args.timeout, subgraph_size=args.subgraph_size, mode=args.mode, population=args.population,
                                  min_labeling=args.min_labeling, manual_nodes=args.manual_nodes,
                                  shared=args.shared, products_in_total=args.pit, parallel=args.parallel, encoding=args.encoding,
                                  partial_labeling=args.partial_labeling, num_subgraphs=args.num_subgraphs, 
                                  multilevel=args.multilevel,number_of_levels=args.lv)
        if specs_obj.grid:
            stats_obj = explore_grid(specs_obj)
        else:
            # todo:question: What should happen here?
            raise NotImplementedError('WIP: for now --grid must be passed')


def clean_all():
    for (directory, _) in [
        z3logpath.OUTPUT_PATH['ver'],
        z3logpath.OUTPUT_PATH['gv'],
        z3logpath.OUTPUT_PATH['aig'],
        z3logpath.OUTPUT_PATH['z3'],
        z3logpath.OUTPUT_PATH['report'],
        z3logpath.OUTPUT_PATH['figure'],
        z3logpath.TEST_PATH['tb'],
        sxpatpaths.OUTPUT_PATH['area'],
        sxpatpaths.OUTPUT_PATH['power'],
        sxpatpaths.OUTPUT_PATH['delay'],
        sxpatpaths.OUTPUT_PATH['json']
    ]:
        FS.cleandir(directory)


if __name__ == "__main__":
    main()
