from Z3Log.utils import setup_folder_structure
from Z3Log.config import path as z3logpath

from sxpat.specifications import Specifications
from sxpat.config import paths as sxpatpaths

from sxpat.xplore import explore_grid
from sxpat.stats import Stats

from z_marco.utils import pprint
from sxpat.utils.filesystem import FS


def main():
    specs_obj = Specifications.parse_args()
    print(f'{specs_obj = }')

    if specs_obj.plot:
        pprint.info2('Plotting...')
        stats_obj = Stats(specs_obj)
        stats_obj.gather_results()

    else:
        if specs_obj.clean:
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
