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
    All methods are more expensive compared to their os/shutil counterpart; this is because we do cleaning/normalization and more checks.

    :authors: Marco Biasion
    """

    # > FILES

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
        Create the file, with the name made unique using an inserted code.  
        The code is in the format `###`, where `###` is a number (000, 001, ..., 999).

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
    def rmfile(
        cls, filepath: str,
    ) -> None:
        """
        Remove the file (or symlink).
        Does nothing if the file does not exist.

        :param filepath: the path to the file.

        :raises IsADirectoryError: if the path is a directory.
        """

        filepath = _os.path.normpath(filepath)

        if _os.path.exists(filepath):
            _os.remove(filepath)

    # > DIRECTORIES

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
        Create the directory (recursively), with the name made unique by suffixing it with a code.
        The code is in the format `###`, where `###` is a number (000, 001, ..., 999).

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
        Remove the directory.
        Does nothing if the directory does not exist.

        :param dirpath: the path to the directory.
        :param recursive: if the directory should be removed even if it has content.

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
        Empty an existing directory.

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
        Get all contents of a directory.

        :param dirpath: the path to the directory.
        :return: iterable of paths of the contents (prefixed with the input path).

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

    # > MISC

    @classmethod
    def exists(
        cls, path: str,
    ) -> bool:
        """
        Check if something exists.

        :param path: the path to check.
        """

        path = _os.path.normpath(path)

        return _os.path.exists(path)

    @classmethod
    def join(
        cls, path: str, *paths: str,
    ) -> str:
        """
        Join two or more path components.

        :param path: the first path component.
        :param paths: the other paths components.

        :raises ValueError: if any component in `paths` is an absolute path.
        :raises ValueError: if no component is given in `paths`.
        """

        if len(paths) == 0:
            raise ValueError('no components given')
        if any(p.startswith('/') for p in paths):
            raise ValueError('invalid absolute path as component')

        path = _os.path.normpath(path)
        paths = tuple(_os.path.normpath(p) for p in paths)

        return _os.path.normpath(_os.path.join(path, *paths))

    @classmethod
    def copy(
        cls, src_path: str, dst_path: str,
        overwrite: bool = False,
    ) -> None:
        """
        Recursively copy a file or a directory from `src_path` to `dst_path`.

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
            _shutil.copy

    @classmethod
    def move(
        cls, src_path: str, dst_path: str,
        overwrite: bool = False,
    ) -> None:
        """
        Recursively move a file or a directory from `src_path` to `dst_path`.  
        `dst_path` will be the new path of the entity (different from the standard `mv` behaviour, which may place the entity inside an already existing folder).

        :param src_path: the path to move from.
        :param dst_path: the path to move to.
        :param overwrite: if the destination should be overwritten if it already exists.

        :raises FileExistsError: if `dst_path` already exists and `overwrite` is false.
        """

        src_path = _os.path.normpath(src_path)
        dst_path = _os.path.normpath(dst_path)

        if not overwrite and _os.path.exists(dst_path):
            raise FileExistsError(_errno.EEXIST, f'{dst_path} already exists')

        _shutil.rmtree(dst_path, ignore_errors=True)
        _shutil.move(src_path, dst_path)

    from tempfile import gettempdir as get_tempdir

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

    # > helpers

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
