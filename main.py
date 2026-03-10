from sxpat.utils.print import pprint


def main():
    # > parse arguments
    from sxpat.specifications import Specifications
    specs_obj = Specifications.parse_args()
    # print(f'{specs_obj = }')

    # > select wanted directories
    from sxpat.config import paths as sxpatpaths
    # from Z3Log.config import path as z3logpath
    # legacy:
    WANTED_DIRECTORIES = [
        # sxpatpaths.OUTPUT_PATH['ver'][0],
        sxpatpaths.OUTPUT_PATH['gv'][0],
        sxpatpaths.OUTPUT_PATH['z3'][0],
        # sxpatpaths.OUTPUT_PATH['report'][0],
        # z3logpath.TEST_PATH['tb'][0],
    ]

    # > create/empty the wanted directories
    from sxpat.utils.filesystem import FS
    # legacy: create if missing
    for dir in WANTED_DIRECTORIES: FS.mkdir(dir)
    # legacy: clean if wanted
    if specs_obj.clean:
        pprint.info2('removing final and intermediary data')
        for dir in WANTED_DIRECTORIES: FS.emptydir(dir)
    #
    FS.mkdir(specs_obj.path.run.base_folder)
    FS.mkdir(specs_obj.path.run.verilog)
    FS.mkdir(specs_obj.path.run.graphviz)
    FS.mkdir(specs_obj.path.run.solver_scripts)
    FS.mkdir(specs_obj.path.run.temporary)

    # > prepare storage
    from sxpat.utils.storage import LiveStorage
    import csv
    # initialize run stats storage
    specs_obj.stats_storage = LiveStorage(specs_obj.path.run.run_stats)
    print('run stats storage created at:', specs_obj.path.run.run_stats)
    #
    with open(specs_obj.path.run.arguments, 'w') as args_file:
        csv_writer = csv.writer(args_file)
        csv_writer.writerow(['argument', 'value'])
        csv_writer.writerows(specs_obj.constant_fields.items())

    # > run system
    from sxpat.xplore import explore_grid
    #
    with specs_obj.stats_storage:
        # input('ready to explore')
        explore_grid(specs_obj)


if __name__ == '__main__':
    from sxpat.utils.timer import Timer

    main()
    print(f'total_time = {Timer.now()}')
