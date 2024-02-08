import os
import shutil
import tempfile


class FS:
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

        if FS.exists(path):
            (shutil.rmtree if recursive else os.rmdir)(path)

    @classmethod
    def cleandir(cls, path: str) -> None:
        """Creates or empty the directory."""
        path = os.path.normpath(path)

        FS.rmdir(path, True)
        FS.mkdir(path)

    @classmethod
    def listdir(cls, path: str):
        """Returns a list of paths representing all files in the given folder."""
        path = os.path.normpath(path)
        return [
            os.path.relpath(f"{path}/{file}")
            for file in os.listdir(path)
        ]

    @classmethod
    def open(cls, path: str, mode: str):
        path = os.path.normpath(path)
        directory = os.path.dirname(path)

        cls.mkdir(directory)
        return open(path, mode)

    @classmethod
    def open_tmp(directory: str = None, delete: bool = False, binary: bool = False):
        """ Create a temporary file on the filesystem. \n
            If `directory` is given, the file will be created in that directory (created if missing). \n
            If `delete` is `True` the file will be deleted once it is closed. \n
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
