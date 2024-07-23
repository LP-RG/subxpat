from Z3Log.utils import setup_folder_structure
from Z3Log.config import path as z3logpath

from sxpat.templateSpecs import TemplateSpecs
from sxpat.config import paths as sxpatpaths

from sxpat.arguments import Arguments

from sxpat.xplore import explore_grid
from sxpat.stats import Stats

from z_marco.utils import pprint
from sxpat.utils.filesystem import FS
from sxpat.templateCreator import Template_SOP1
import time

def main():
    args = Arguments.parse()
    print(f'{args = }')

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
                              partial_labeling=args.partial_labeling, num_subgraphs=args.num_subgraphs)

    pprint.info1(f'Creating the template...')
    template_obj = Template_SOP1(specs_obj)
    template_obj.current_graph = template_obj.import_graph()

    labeling_start = time.time()
    et_coefficient = 2
    pprint.info1(f'Labeling...')
    template_obj.label_graph(min_labeling=specs_obj.min_labeling, partial=specs_obj.partial_labeling, et=specs_obj.et * et_coefficient, parallel=specs_obj.parallel)
    labeling_time = time.time() - labeling_start
    print(f'labeling_time = {labeling_time}')
    t_start = time.time()
    subgraph_is_available = template_obj.current_graph.extract_subgraph(specs_obj)
    subgraph_extraction_time = time.time() - t_start
    print(f'{subgraph_extraction_time = }')

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