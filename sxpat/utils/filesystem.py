from typing import Iterable, Optional

import os
import shutil
import tempfile

from sxpat.utils.decorators import make_utility_class


__all__ = ['FS']


@make_utility_class
class FS:
    """
        Utility class for filesystem operations.

        @authors: Marco Biasion
    """

    @classmethod
    def exists(cls, path: str) -> bool:
        """Returns if there is something at the given path."""
        path = os.path.normpath(path)
        return os.path.exists(path)

    @classmethod
    def mkdir(cls, path: str) -> None:
        """Recursively create the directory. Does nothing if the directory already exists."""
        path = os.path.normpath(path)
        os.makedirs(path, exist_ok=True)

    @classmethod
    def rmdir(cls, path: str, recursive: bool = False) -> None:
        """Remove the directory (recursively if wanted). Does nothing if the directory does not exist."""
        path = os.path.normpath(path)
        if os.path.exists(path): (shutil.rmtree if recursive else os.rmdir)(path)

    @classmethod
    def emptydir(cls, path: str) -> None:
        """Empties an existing directory."""
        path = os.path.normpath(path)

        if not os.path.exists(path): raise FileNotFoundError(f'{path} does not exists')
        if not os.path.isdir(path): raise NotADirectoryError(f'{path} is not a directory')

        for _path in FS.listdir(path):
            if os.path.isfile(_path) or os.path.islink(_path): os.remove(_path)
            elif os.path.isdir(_path): shutil.rmtree(_path)

    @classmethod
    def listdir(cls, path: str) -> Iterable[str]:
        """Returns an iterable of paths corresponding to the contents of the given folder."""
        path = os.path.normpath(path)
        return (os.path.join(path, file) for file in os.listdir(path))

    # @classmethod
    # def open(cls, path: str, mode: str):
    #     """TODO: should this also create the directory or not?"""
    #     raise NotImplementedError()

    #     path = os.path.normpath(path)
    #     directory = os.path.dirname(path)

    #     cls.mkdir(directory)
    #     return open(path, mode)

    @staticmethod
    def open_tmp(directory: Optional[str] = None, delete: bool = False, binary: bool = False):
        """
            Create a temporary file on the filesystem.  
            If `directory` is given, the file will be created in that directory (created if missing).  
            If `delete` is `True` the file will be deleted once it is closed.  
            If `binary` is `True` the file will be opened in binary mode.
        """

        if directory is not None:
            directory = os.path.normpath(directory)
            FS.mkdir(directory)

        # create temporary file
        return tempfile.NamedTemporaryFile(
            mode='w+b' if binary else 'w+',
            dir=directory,
            delete=delete
        )

    @staticmethod
    def copy(src_path: str, dst_path: str, exists_ok: bool = False) -> None:
        """
            Copies a file or an entire directory from source to destination.  
            Raises an exception if `exists_ok` is false and `dst_path` already exists.
        """

        src_path = os.path.normpath(src_path)
        dst_path = os.path.normpath(dst_path)

        if not exists_ok and os.path.exists(dst_path): raise FileExistsError(f'{dst_path} already exists')

        if os.path.isdir(src_path): shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else: shutil.copyfile(src_path, dst_path, follow_symlinks=True)
