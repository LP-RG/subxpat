import os.path
import tarfile
from typing import Iterable
from sxpat.utils.filesystem import FS


__all__ = ['archive_tgz', 'archive_txz']


def get_unique_paths(paths: Iterable[str]) -> Iterable[str]:
    """Given some paths, recirsively traverse all of them, yielding them at most once each."""
    _seen = set()
    for path in paths:
        for file in FS.walk(path):
            if file in _seen: continue
            _seen.add(file)
            yield file


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
            for path in get_unique_paths(paths):
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
            preset = 3

        # extract prefix
        prefix = ''
        if shrink_prefix:
            prefix = os.path.dirname(os.path.commonpath(paths))

        with tarfile.open(  # pyright: ignore[reportCallIssue]
            archive_path,
            mode="x:xz",
            preset=preset,  # pyright: ignore[reportArgumentType]
        ) as tar:
            for path in get_unique_paths(paths):
                tar.add(path, os.path.relpath(path, prefix))

except ImportError: pass
