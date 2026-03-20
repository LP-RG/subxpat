
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
    from sxpat.xplore import explore_grid, print_results
    #
    with specs_obj.stats_storage:
        results = explore_grid(specs_obj)
    # print results for each relevance of metrics
    print_results(results)

    # > remove temporary files
    if not specs_obj.debug: FS.rmdir(specs_obj.path.run.temporary, True)

    # > archive run (and delete raw files)
    if specs_obj.should_archive:
        from sxpat.utils.archive import archive_files
        # create and fill archive
        archive_path = f'{specs_obj.path.run.base_folder.rstrip("/")}.zip'
        archive_files(archive_path, specs_obj.path.run.base_folder)
        # delete raw files
        if not specs_obj.debug: FS.rmdir(specs_obj.path.run.base_folder, recursive=True)


class ImportTimer:
    def __init__(self):
        self.time = 0

    def _instrument(self):
        from time import perf_counter
        import builtins

        __builtin_import__ = builtins.__import__  # store a reference to the built-in import

        def __custom_import__(name, *args, **kwargs):
            _time = perf_counter()
            ret = __builtin_import__(name, *args, **kwargs)
            self.time += perf_counter() - _time

            return ret  # return back the actual import result

        builtins.__import__ = __custom_import__  # override the built-in import with our method

    @classmethod
    def instrument(cls):
        timer = cls()
        timer._instrument()
        return timer


if __name__ == '__main__':
    import_timer = ImportTimer.instrument()
    from sxpat.utils.timer import Timer

    main()

    print(f'imports_time = {import_timer.time}s')
    print(f'total_time = {Timer.now()}')
