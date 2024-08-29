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

    # todo:later: update how we create the templatespecs (more than 2 names, ecc.)
    specs_obj = TemplateSpecs(name='Sop1' if not args.shared else 'SharedLogic', exact=args.exact_benchmark,
                              literals_per_product=args.lpp, products_per_output=args.ppo,
                              benchmark_name=args.current_benchmark, num_of_models=args.num_models,
                              subxpat=args.subxpat,
                              et=args.et, et_partitioning=args.error_partitioning,
                              imax=args.imax, omax=args.omax,
                              timeout=args.timeout, subgraph_size=args.min_subgraph_size, mode=args.extraction_mode,
                              min_labeling=args.min_labeling,
                              shared=args.shared, products_in_total=args.pit, parallel=args.parallel, encoding=args.encoding,
                              partial_labeling=args.partial_labeling, num_subgraphs=args.num_subgraphs)

    if args.plot:
        pprint.info2('Plotting...')
        stats_obj = Stats(specs_obj)
        stats_obj.gather_results()

    else:
        if args.clean:
            pprint.info2('cleaning...')
            clean_all()

        # prepare folders
        setup_folder_structure()
        for (directory, _) in sxpatpaths.OUTPUT_PATH.values():
            FS.mkdir(directory)

        # run system
        stats_obj = explore_grid(specs_obj)


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
