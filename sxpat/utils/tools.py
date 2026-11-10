import os
import os.path as path
import shutil
import sys

from typing import Optional


PROJECT_ROOT = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
LOCAL_TOOLS_DIR = path.join(PROJECT_ROOT, '.deps', 'bin')


def find_tool(name: str) -> Optional[str]:
    local = path.join(LOCAL_TOOLS_DIR, name)
    if path.isfile(local) and os.access(local, os.X_OK): return local
    return shutil.which(name)


def require_tool(name: str, hint: str = '') -> str:
    if (found := find_tool(name)) is not None: return found
    if path.basename(name) != name:
        raise RuntimeError(f'The `{name}` executable was not found or is not executable')
    hint = hint or ('run `make setup macos`' if sys.platform == 'darwin' else '')
    raise RuntimeError(f'The `{name}` executable was not found in {LOCAL_TOOLS_DIR} or on the PATH'
                       + (f' ({hint})' if hint else ''))
