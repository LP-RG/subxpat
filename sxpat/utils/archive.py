import os.path
import tarfile
import zipfile
from sxpat.utils.filesystem import FS


__all__ = ['archive_zip', 'archive_tgz', 'archive_txz']


__NO_COMPRESSION = (zipfile.ZIP_STORED, 0)
__BEST_COMPRESSION = None


def __get_best_compression():
    global __BEST_COMPRESSION

    # select best compression algorithm
    if __BEST_COMPRESSION is None:
        __BEST_COMPRESSION = __NO_COMPRESSION
        try:
            import zlib
            __BEST_COMPRESSION = (zipfile.ZIP_DEFLATED, 9)
        except ImportError: pass
        try:
            import bz2
            __BEST_COMPRESSION = (zipfile.ZIP_BZIP2, 9)
        except ImportError: pass
        try:
            import lzma
            __BEST_COMPRESSION = (zipfile.ZIP_LZMA, None)
        except ImportError: pass

    return __BEST_COMPRESSION


def archive_zip(
    archive_path: str,
    *paths: str,
    compress: bool = True,
    shrink_prefix: bool = True,
):
    """
    Create a .zip archive at `archive_path` containing all `paths` recursively.

    :param archive_path: the path of the zip archive to create.
    :param paths: the paths of files/folders to add to the archive.
    :param compression: if the archive should be compressed or not.
    :param shrink_prefix: if the archived paths should ignore all but the last component of the common prefix.

    :raises FileExistsError: if `archive_path` already exists.
    """

    # select compression
    if compress:
        _comp = __get_best_compression()
    else:
        _comp = __NO_COMPRESSION

    # extract prefix
    prefix = ''
    if shrink_prefix:
        prefix = os.path.dirname(os.path.commonpath(paths))

    # archive
    with zipfile.ZipFile(
        archive_path, 'x',
        compression=_comp[0], compresslevel=_comp[1],
    ) as archive:
        for path in paths:
            for file in FS.walk(path):
                archive.write(file, os.path.relpath(file, prefix))


try:
    import gzip

    def archive_tgz(
        archive_path: str,
        *paths: str,
        shrink_prefix: bool = True,
    ):
        """
        Create a .tgz archive at `archive_path` containing all `paths` recursively, .

        :param archive_path: the path of the tar.gz archive to create.
        :param paths: the paths of files/folders to add to the archive.
        :param shrink_prefix: if the archived paths should ignore all but the last component of the common prefix.

        :raises FileExistsError: if `archive_path` already exists.
        """

        # extract prefix
        prefix = ''
        if shrink_prefix:
            prefix = os.path.dirname(os.path.commonpath(paths))

        with tarfile.open(
            archive_path,
            mode="x:gz",
        ) as tar:
            for path in paths:
                tar.add(path, os.path.relpath(path, prefix))

except ImportError: pass

try:
    import lzma

    def archive_txz(
        archive_path: str,
        *paths: str,
        shrink_prefix: bool = True,
        max_compression: bool = False
    ):
        """
        Create a .txz archive at `archive_path` containing all `paths` recursively, .

        :param archive_path: the path of the tar.xz archive to create.
        :param paths: the paths of files/folders to add to the archive.
        :param shrink_prefix: if the archived paths should ignore all but the last component of the common prefix.

        :raises FileExistsError: if `archive_path` already exists.
        """

        if max_compression:
            preset = 9 | lzma.PRESET_EXTREME
        else:
            preset = 9

        # extract prefix
        prefix = ''
        if shrink_prefix:
            prefix = os.path.dirname(os.path.commonpath(paths))

        with tarfile.open(  # pyright: ignore[reportCallIssue]
            archive_path,
            mode="x:xz",
            preset=preset,  # pyright: ignore[reportArgumentType]
        ) as tar:
            for path in paths:
                tar.add(path, os.path.relpath(path, prefix))

except ImportError: pass
