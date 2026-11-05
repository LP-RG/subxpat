import os.path as path
import shutil
import sys

from typing import Optional


PROJECT_ROOT = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
LOCAL_TOOLS_DIR = path.join(PROJECT_ROOT, '.deps', 'bin')


def find_tool(name: str) -> Optional[str]:
    if (found := shutil.which(name)) is not None: return found
    if path.isfile(local := path.join(LOCAL_TOOLS_DIR, name)): return local
    return None


def require_tool(name: str, hint: str = '') -> str:
    if (found := find_tool(name)) is not None: return found
    hint = hint or ('run `make setup macos`' if sys.platform == 'darwin' else '')
    raise RuntimeError(f'The `{name}` executable was not found on PATH' + (f' ({hint})' if hint else ''))
