import os.path
import zipfile
from sxpat.utils.filesystem import FS


__all__ = ['archive_files', 'NO_COMPRESSION', 'BEST_COMPRESSION']


# define compression flags
NO_COMPRESSION = zipfile.ZIP_STORED
BEST_COMPRESSION = zipfile.ZIP_STORED
# select best compression algorithm
try:
    import zlib
    BEST_COMPRESSION = zipfile.ZIP_DEFLATED
except ImportError: pass
try:
    import bz2
    BEST_COMPRESSION = zipfile.ZIP_BZIP2
except ImportError: pass
try:
    import lzma
    BEST_COMPRESSION = zipfile.ZIP_LZMA
except ImportError: pass


def archive_files(archive_file_path: str, *paths_to_store: str, compression: int = BEST_COMPRESSION, ignore_root_folder: bool = True):
    """
        Create `archive_file_path` and insert all `paths_to_store` recursively.

        `compression` defines if the archive should be simply stored or if it should be compressed as best as possible.

        If `ignore_root_folder` is `True` files will be added without the folder path (as given from `paths_to_store`).

        Raises `FileExistsError` if `archive_file_path` already exists.
    """

    with zipfile.ZipFile(archive_file_path, 'x', compression=compression, compresslevel=9) as f:
        for path in paths_to_store:
            #
            if ignore_root_folder:
                prefix_length = len(os.path.split(path.rstrip('/'))[0])
            else:
                prefix_length = 0

            #
            for file in FS.walk(path):
                if prefix_length == 0:
                    f.write(file)
                else:
                    f.write(file, file[prefix_length:])
