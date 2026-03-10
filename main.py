from sxpat.utils.print import pprint


def main():
    # > parse arguments
    from sxpat.specifications import Specifications
    specs_obj = Specifications.parse_args()

    # > create wanted directories
    from sxpat.config import paths as sxpatpaths
    from sxpat.utils.filesystem import FS
    # legacy
    wanted_directories = [
        # legacy
        sxpatpaths.OUTPUT_PATH['gv'][0],
        # TODO: merge with next block when removing legacy
        *specs_obj.path.run.folders,
    ]
    # create
    for dir in wanted_directories: FS.mkdir(dir)
    # legacy: clean if wanted
    if specs_obj.clean:
        pprint.info2('removing final and intermediary data')
        for dir in wanted_directories: FS.emptydir(dir)

    # > prepare storage
    from sxpat.utils.storage import LiveStorage
    import csv
    # initialize run stats storage
    specs_obj.stats_storage = LiveStorage(specs_obj.path.run.run_stats)
    print('run stats storage created at:', specs_obj.path.run.run_stats)
    # store arguments
    with open(specs_obj.path.run.arguments, 'w') as args_file:
        csv_writer = csv.writer(args_file)
        csv_writer.writerow(['argument', 'value'])
        csv_writer.writerows(specs_obj.constant_fields.items())

    # > run system
    from sxpat.xplore import explore_grid
    #
    with specs_obj.stats_storage:
        results = explore_grid(specs_obj)
    # print results for each relevance of metrics
    print(results.for_area_power_delay)
    print(results.for_area_delay_power)
    print(results.for_power_area_delay)
    print(results.for_power_delay_area)
    print(results.for_delay_area_power)
    print(results.for_delay_power_area)


if __name__ == '__main__':
    from sxpat.utils.timer import Timer

    main()
    print(f'total_time = {Timer.now()}')
