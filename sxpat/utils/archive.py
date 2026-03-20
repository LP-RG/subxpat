
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


def archive_files(archive_file_path: str, *paths_to_store: str, compression: int = BEST_COMPRESSION):
    """
        Create `archive_file_path` and insert all `paths_to_store` recursively.

        `compression` defines if the archive should be simply stored or if it should be compressed as best as possible.

        Raises `FileExistsError` if `archive_file_path` already exists.
    """

    with zipfile.ZipFile(archive_file_path, 'x', compression=compression, compresslevel=9) as f:
        for path in paths_to_store:
            for file in FS.walk(path):
                f.write(file)
