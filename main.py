from sxpat.specifications import Specifications
from sxpat.utils.print import pprint


def main():
    specs_obj = Specifications.parse_args()
    print(f'{specs_obj = }')

    if specs_obj.plot: plot(specs_obj)
    else: run(specs_obj)


def plot(specs_obj: Specifications) -> None:
    from sxpat.stats import Stats

    pprint.info2('generating plots from matching data')
    stats_obj = Stats(specs_obj)
    stats_obj.gather_results()


def run(specs_obj: Specifications) -> None:
    # select wanted directories
    from sxpat.config import paths as sxpatpaths
    from Z3Log.config import path as z3logpath
    WANTED_DIRECTORIES = [
        sxpatpaths.OUTPUT_PATH['ver'][0],
        sxpatpaths.OUTPUT_PATH['gv'][0],
        sxpatpaths.OUTPUT_PATH['z3'][0],
        sxpatpaths.OUTPUT_PATH['report'][0],
        z3logpath.TEST_PATH['tb'][0],
    ]
    # create/empty the wanted directories
    from sxpat.utils.filesystem import FS
    for dir in WANTED_DIRECTORIES: FS.mkdir(dir)
    if specs_obj.clean:  # clean if wanted
        pprint.info2('removing final and intermediary data')
        for dir in WANTED_DIRECTORIES: FS.emptydir(dir)

    # run system
    from sxpat.xplore import explore_grid
    explore_grid(specs_obj)


if __name__ == '__main__': main()
