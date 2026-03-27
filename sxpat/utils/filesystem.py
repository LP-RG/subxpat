from typing import Iterable, Iterator, final

import os
import shutil
import tempfile

from sxpat.utils.decorators import make_utility_class


__all__ = ['FS']


@final
@make_utility_class
class FS:
    """
        Utility class for filesystem operations.

        :authors: Marco Biasion
    """

    @classmethod
    def exists(cls, path: str) -> bool:
        """
            Returns if there is something at the given path.
        """

        path = os.path.normpath(path)

        return os.path.exists(path)

    @classmethod
    def mkdir(cls, path: str) -> None:
        """
            Create the directory (recursively).
            Does nothing if the directory already exists.
        """

        path = os.path.normpath(path)

        os.makedirs(path, exist_ok=True)

    @classmethod
    def rmdir(cls, path: str, recursive: bool = False) -> None:
        """
            Remove the directory (recursively if wanted).
            Does nothing if the directory does not exist.

            :raises NotADirectoryError: if the path does not represent a directory.
        """

        path = os.path.normpath(path)

        if os.path.exists(path):
            (shutil.rmtree if recursive else os.rmdir)(path)

    @classmethod
    def emptydir(cls, path: str) -> None:
        """
            Empties an existing directory.

            :raises FileNotFoundError: if the directory does not exists.
            :raises NotADirectoryError: if the path does not represent a directory.
        """

        path = os.path.normpath(path)

        for _path in cls.listdir(path):
            if os.path.isfile(_path) or os.path.islink(_path): os.remove(_path)
            elif os.path.isdir(_path): shutil.rmtree(_path)

    @classmethod
    def listdir(cls, path: str) -> Iterable[str]:
        """
            Returns an iterable of paths corresponding to the contents of the given folder.

            :raises FileNotFoundError: if the directory does not exists.
            :raises NotADirectoryError: if the path does not represent a directory.
        """

        path = os.path.normpath(path)

        return (os.path.join(path, file) for file in os.listdir(path))

    # @classmethod
    # def open(cls, path: str, mode: str):
    #     ### following `man mkdir`: --parents
    #     """TODO: should this also create the directory or not?"""
    #     raise NotImplementedError()

    #     path = os.path.normpath(path)
    #     directory = os.path.dirname(path)

    #     cls.mkdir(directory)
    #     return open(path, mode)

    @classmethod
    def open_tmp(
        cls, directory: str = None,
        delete: bool = False, binary: bool = False,
        prefix: str = '', suffix: str = '',
    ):
        """
            Create a temporary file on the filesystem.  
            If `directory` is given, the file will be created in that directory (created if missing).  
            If `delete` is `True` the file will be deleted once it is closed.   
            If `binary` is `True` the file will be opened in binary mode, else it is opened in text mode.
        """

        if directory is not None:
            directory = os.path.normpath(directory)
            cls.mkdir(directory)

        # create temporary file
        try:
            old_name_sequence = tempfile._name_sequence
            tempfile._name_sequence = cls._AlphaNumRandomSequence()

            file = tempfile.NamedTemporaryFile(
                mode='w+b' if binary else 'w+',
                prefix=prefix,
                suffix=suffix,
                dir=directory,
                delete=delete,
            )
        finally:
            tempfile._name_sequence = old_name_sequence

        return file

    @classmethod
    def get_unique_filename(
        cls, directory: str = None,
        prefix: str = '', suffix: str = '',
    ) -> str:
        """
            Creates a temporary file in the filesystem, closes it and returns its name.

            :note: the created file is not deleted, allowing for the name to be reserved.
        """

        tmp_file = cls.open_tmp(directory, delete=False, prefix=prefix, suffix=suffix)
        tmp_file.close()
        return os.path.split(tmp_file.name)[1]

    @classmethod
    def get_unique_dirname(
        cls, directory: str = None,
        prefix: str = '', suffix: str = '',
    ) -> str:
        """
            Creates a temporary folder in the filesystem and returns its name.

            :note: The caller is responsible for deleting the directory when done with it.
        """
        try:
            old_name_sequence = tempfile._name_sequence
            tempfile._name_sequence = cls._AlphaNumRandomSequence()
            dirpath = tempfile.mkdtemp(suffix, prefix, directory)
            return os.path.split(dirpath)[1]
        finally:
            tempfile._name_sequence = old_name_sequence

    @staticmethod
    def copy(src_path: str, dst_path: str, exists_ok: bool = False) -> None:
        """
            Copies a file or an entire directory from source to destination.  

            :raises FileExistsError: if `dst_path` already exists and `exists_ok` is false.
        """

        src_path = os.path.normpath(src_path)
        dst_path = os.path.normpath(dst_path)

        if not exists_ok and os.path.exists(dst_path): raise FileExistsError(f'{dst_path} already exists')

        if os.path.isdir(src_path): shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else: shutil.copyfile(src_path, dst_path, follow_symlinks=True)

    @staticmethod
    def walk(path: str) -> Iterator[str]:
        """
            Tree walk generator.

            If `path` is a directory, it will be recursively traversed.
            If `path` is a file, it will be the only one returned.
        """

        if os.path.isdir(path):
            yield from (
                os.path.join(dirpath, filename)
                for dirpath, _, filenames in os.walk(path)
                for filename in filenames
            )
        else:
            yield path

    class _AlphaNumRandomSequence(tempfile._RandomNameSequence):
        characters = tempfile._RandomNameSequence.characters.replace('_', '')
