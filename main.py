
def main():
    # instrumentations
    from instrumentations.import_timer import ImportTimer
    import_timer = ImportTimer.instrument()

    # > parse arguments and prepare specifications
    from sxpat.specifications import Specifications
    specs_obj = Specifications.parse_args()
    print('id:', specs_obj.run_id)
    print('directory:', specs_obj.path.run.base_folder)

    # > create wanted directories
    from sxpat.utils.filesystem import FS
    for dir in specs_obj.path.run.folders: FS.mkdir(dir)

    # > prepare storage
    from sxpat.utils.storage import LiveStorage, AppendStorage
    specs_obj.stats_storage = LiveStorage(specs_obj.path.run.run_stats)
    specs_obj.details_storage = AppendStorage(specs_obj.path.run.run_details)

    # > run system
    from sxpat.xplore import explore_grid, print_results
    from sxpat.utils.timer import Timer
    #
    try:
        _t0 = Timer.now()
        specs_obj.details_storage.add(specs_obj.constant_fields)

        #
        results = explore_grid(specs_obj)
        # print results for each relevance of metrics
        print_results(results)

        # if no exception
        specs_obj.details_storage.add(exception='')

    except BaseException as ex:
        # if exception
        specs_obj.details_storage.add(exception=ex)
        raise ex

    finally:
        # timings
        _td = Timer.now() - _t0
        print(f'total_time = {_td}')
        specs_obj.details_storage.add(total_time=_td)
        specs_obj.details_storage.add(import_time=import_timer.time)

        # gracefully close storages
        specs_obj.stats_storage.save()
        specs_obj.details_storage.close()

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


if __name__ == '__main__': main()
