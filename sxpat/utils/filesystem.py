import os
import tempfile


class FS:
    """NOT YET USED"""
    @classmethod
    def makedir(cls, path: str) -> None:
        """Recursively create the directory. Does nothing if the directory already exists."""
        os.makedirs(path, exist_ok=True)

    @classmethod
    def listdir(cls, path: str):
        """Returns a list of paths representing all files in the given folder."""
        path = os.path.normpath(path)
        return [f"{path}/{file}" for file in os.listdir(path)]

    @classmethod
    def open(cls, path: str, mode: str):
        folder, _ = os.path.split(path)
        cls.create_directory(folder)
        return open(path, mode)


def create_directory(path: str) -> None:
    """Recursively create the directory. Does nothing if the directory already exists."""
    os.makedirs(path, exist_ok=True)


def open_file(path: str, mode: str):
    """Open the wanted file, creating all necessary folders in the path"""
    directory = os.path.dirname(path)
    create_directory(directory)
    return open(path, mode)


def listdir(path: str):
    """Returns a list of paths representing all files in the given folder."""
    path = os.path.normpath(path)
    return [
        os.path.relpath(f"{path}/{file}")
        for file in os.listdir(path)
    ]


def get_temporary_file(directory: str = None, delete: bool = False, binary: bool = False):
    """ Create a temporary file on the filesystem. \n
        If `directory` is given, the file will be created in that directory (created if missing). \n
        If `delete` is `True` the file will be deleted once it is closed. \n
        If `binary` is `True` the file will be opened in binary mode.
    """

    if directory is not None:
        create_directory(directory)

    # create temporary file
    return tempfile.NamedTemporaryFile(
        mode='w+b' if binary else 'w+',
        dir=directory,
        delete=delete
    )
