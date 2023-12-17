import os
import tempfile


def create_directory(path: str) -> None:
    """Recursively create the directory. Does nothing if the directory already exists."""
    os.makedirs(path, exist_ok=True)


def open_file(path: str, mode: str):
    folder, filename = os.path.split(path)
    create_directory(folder)
    return open(path, mode)


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
