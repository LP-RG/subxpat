from typing import Iterable, Iterator, Literal, final

import os as _os
import sys as _sys
import shutil as _shutil
import errno as _errno

from itertools import product as _product
from sxpat.utils.decorators import make_utility_class


__all__ = ['FS']


@final
@make_utility_class
class FS:
    """
        Utility class for filesystem operations.

        :authors: Marco Biasion
    """

    from tempfile import gettempdir as get_tempdir

    @classmethod
    def exists(
        cls, path: str,
    ) -> bool:
        """
        Returns if something exists at the given path.

        :param path: the path to check.
        """

        path = _os.path.normpath(path)

        return _os.path.exists(path)

    @classmethod
    def mkfile(
        cls, filename: str,
        directory: str = '',
    ) -> None:
        """
        Create a file.

        :param filename: the name of the file to create.
        :param directory: the directory in which to create the file (defaults to the working directory).

        :raises FileExistsError: if something already exists in the directory with name `filename`.
        :raises FileNotFoundError: if the directory does not exists.
        :raises NotADirectoryError: if `directory` does not represent a directory.
        """

        path = _os.path.normpath(_os.path.join(directory, filename))

        _os.close(_os.open(path, _os.O_CREAT, 0o666))

    @classmethod
    def mkfile_unique(
        cls, fileprefix: str, filesuffix: str = '',
        directory: str = '',
        *,
        id_size: int = 5,
    ) -> str:
        """
        Create the file, with a unique id inserted in the name.
        The unique id is in the format `###`, where `###` is a number (000, 001, ..., 999).

        :param fileprefix: the base name of the file to create.
        :param filesuffix: the name suffix of the file to create.
        :param directory: the directory in which to create the file (defaults to the working directory).
        :param id_size: the size of the unique id.

        :raises PermissionError:
        :raises FileExistsError: if an entity already exists for all ids.
        :raises FileNotFoundError: if the directory does not exists.
        :raises NotADirectoryError: if `directory` does not represent a directory.
        """

        # normalize and prepare filepath
        filepath = _os.path.join(
            _os.path.normpath(directory),
            _os.path.normpath(fileprefix),
        )

        # iterate over all possible ids
        for id in cls._get_codes_iter(id_size):
            # compose full path
            path = filepath + id + filesuffix

            try:
                # notify auditors
                _sys.audit("custom tempfile.mkstemp", path)
                # try to create file
                fd = _os.open(path, _os.O_CREAT | _os.O_WRONLY, 0o666)

            except FileExistsError:
                continue  # try again
            except PermissionError as _e:
                # custom managing of Windows edge-cases (see tempfile.mkdtemp)
                if _os.name == 'nt': continue
                else: raise _e

            # close file
            _os.close(fd)
            # return the first valid path
            return _os.path.basename(path)

        raise FileExistsError(_errno.EEXIST, 'No usable unique file name found')

    @classmethod
    def mkdir(
        cls, dirname: str,
        directory: str = '',
    ) -> None:
        """
        Create the directory (recursively).
        Does nothing if the directory already exists.

        :param dirname: the name of the directory to create.
        :param directory: the parent directory in which to create the new directory (defaults to the working directory).
        """

        dirpath = _os.path.join(_os.path.normpath(directory), dirname)

        _os.makedirs(dirpath, exist_ok=True)

    @classmethod
    def mkdir_unique(
        cls, dirname: str,
        directory: str = '',
        *,
        id_size: int = 5,
    ) -> str:
        """
        Create the directory (recursively), postfixed with a unique id.
        The unique id is in the format `###`, where `###` is a number (000, 001, ..., 999).

        :param dirname: the base name of the directory to create.
        :param directory: the parent directory in which to create the new directory (defaults to the working directory).
        :param id_size: the size of the unique id.

        :raises PermissionError:
        :raises FileExistsError: if an entity already exists for all ids.
        :raises FileNotFoundError: if the parent directory does not exists.
        :raises NotADirectoryError: if `directory` does not represent a directory.
        """

        # normalize and prepare dirpath
        dirpath = _os.path.join(
            _os.path.normpath(directory),
            _os.path.normpath(dirname),
        )

        # iterate over all possible ids
        for id in cls._get_codes_iter(id_size):
            # compose full path
            path = dirpath + id

            try:
                # notify auditors
                _sys.audit("custom tempfile.mkdtemp", path)
                # create all parent directories (if needed) and try to create leaf directory
                _os.makedirs(path)
            except FileExistsError:
                continue  # try again
            except PermissionError as _e:
                # custom managing of Windows edge-cases (see tempfile.mkdtemp)
                if _os.name == 'nt': continue
                else: raise _e

            # return the first valid path
            return _os.path.basename(path)

        raise FileExistsError(_errno.EEXIST, 'No usable unique directory name found')

    @classmethod
    def rmdir(
        cls, dirpath: str,
        recursive: bool = False,
    ) -> None:
        """
        Remove the directory (recursively if wanted).
        Does nothing if the directory does not exist.

        :param dirpath: the path to the directory.

        :raises NotADirectoryError: if the path does not represent a directory.
        """

        dirpath = _os.path.normpath(dirpath)

        if _os.path.exists(dirpath):
            if recursive:
                _shutil.rmtree(dirpath)
            else:
                _os.rmdir(dirpath)

    @classmethod
    def emptydir(
        cls, dirpath: str,
    ) -> None:
        """
        Empties an existing directory.

        :param dirpath: the path to the directory.

        :raises FileNotFoundError: if the directory does not exists.
        :raises NotADirectoryError: if the path does not represent a directory.
        """

        dirpath = _os.path.normpath(dirpath)

        for _path in cls.listdir(dirpath):
            if _os.path.isfile(_path) or _os.path.islink(_path):
                _os.remove(_path)
            elif _os.path.isdir(_path):
                _shutil.rmtree(_path)

    @classmethod
    def listdir(
        cls, dirpath: str,
    ) -> Iterable[str]:
        """
        Returns an iterable of paths corresponding to the contents of the given directory.

        :param dirpath: the path to the directory.

        :raises FileNotFoundError: if the directory does not exists.
        :raises NotADirectoryError: if the path does not represent a directory.
        """

        dirpath = _os.path.normpath(dirpath)

        return (
            _os.path.join(dirpath, file)
            for file in _os.listdir(dirpath)
        )

    @classmethod
    def walkdir(
        cls, dirpath: str,
    ) -> Iterator[str]:
        """
        Tree walk generator.

        :param dirpath: the path to the directory to walk through.
        """

        path = _os.path.normpath(dirpath)

        yield from (
            _os.path.join(dirpath, filename)
            for dirpath, _, filenames in _os.walk(path)
            for filename in filenames
        )

    @classmethod
    def walk(
        cls, path: str,
    ) -> Iterator[str]:
        """
        Tree walk generator.

        If `path` is a directory, it will be recursively traversed.  
        If `path` is a file, it will be the only one yielded.

        :param path: the path to the entity to walk through.
        """

        path = _os.path.normpath(path)

        if _os.path.isdir(path):
            yield from cls.walkdir(path)
        else:
            yield path

    @classmethod
    def get_unique_name(
        cls,
        name: str,
        *,
        id_size: int = 5,
        directory: str = get_tempdir(),
        entity: Literal['file', 'directory'] = 'directory',
    ) -> str:
        """
        Generate a unique name using the file system.

        The returned name is in the format `{name}###` where `###` is a number (000, 001, ..., 999).

        The created entity is **not** automatically removed; the caller is responsible for cleaning it up.

        :param name: the base name.
        :param id_size: the size of the unique id (`###`).
        :param directory: the directory into which the new uniquely named entity will be created.
        :param entity: if the generated entity should be a file or a directory.
        """

        match entity:
            case 'directory':
                return cls.mkdir_unique(
                    name,
                    directory,
                    id_size=id_size,
                )
            case 'file':
                return cls.mkfile_unique(
                    name,
                    directory=directory,
                    id_size=id_size,
                )
            case _: raise

    @classmethod
    def copy(
        cls, src_path: str, dst_path: str,
        overwrite: bool = False,
    ) -> None:
        """
        Copies a file or an entire directory from source to destination.  

        :param src_path: the path to copy from.
        :param dst_path: the path to copy to.
        :param overwrite: if the destination or destinations (in case of a directory) 
            should be overwritten if they already exists.

        :raises FileExistsError: if `dst_path` already exists and `overwrite` is false.
        """

        src_path = _os.path.normpath(src_path)
        dst_path = _os.path.normpath(dst_path)

        if not overwrite and _os.path.exists(dst_path):
            raise FileExistsError(_errno.EEXIST, f'{dst_path} already exists')

        if _os.path.isdir(src_path):
            _shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else:
            _shutil.copyfile(src_path, dst_path, follow_symlinks=True)

    @classmethod
    def _get_codes_iter(
        cls, size: int,
        characters: str = '0123456789'
    ) -> Iterator[str]:
        """
        Returns an iterator over all codes (in the format '000', '001', ..., '999').

        :param size: how many characters to use for each code.
        :param characters: what characters to use (defaults to decimal digits).
        """

        yield from (
            ''.join(chars)
            for chars in _product(characters, repeat=size)
        )
