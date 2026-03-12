
def main():
    # > parse arguments
    from sxpat.specifications import Specifications
    specs_obj = Specifications.parse_args()

    # > create wanted directories
    from sxpat.utils.filesystem import FS
    #
    for dir in specs_obj.path.run.folders: FS.mkdir(dir)

    # > prepare storage
    from sxpat.utils.storage import LiveStorage
    import csv
    # initialize run stats storage
    specs_obj.stats_storage = LiveStorage(specs_obj.path.run.run_stats)
    print('run stats storage created at:', specs_obj.path.run.run_stats)
    # store arguments
    with open(specs_obj.path.run.arguments, 'w') as args_file:
        csv_writer = csv.writer(args_file)
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

    # > remove temporary files
    if not specs_obj.debug: FS.rmdir(specs_obj.path.run.temporary, True)


if __name__ == '__main__':
    from sxpat.utils.timer import Timer

    main()
    print(f'total_time = {Timer.now()}')
