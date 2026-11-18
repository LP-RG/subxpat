import os
import os.path as path
import shutil
import sys

from typing import Optional


PROJECT_ROOT = path.abspath(path.join(__file__, *[path.pardir] * 3))
LOCAL_TOOLS_DIR = path.join(PROJECT_ROOT, '.deps', 'bin')

_warned: set[str] = set()
_found_tools: dict[str, str] = dict()


def find_tool(name: str) -> Optional[str]:
    if path.basename(name) == name:
        local = path.join(LOCAL_TOOLS_DIR, name)
        if path.isfile(local) and os.access(local, os.X_OK): return local
        if path.lexists(local) and name not in _warned:
            _warned.add(name)
            print(f'warning: {local} is not executable, falling back to the PATH', file=sys.stderr)
    return shutil.which(name)


def require_tool(name: str, hint: str = '') -> str:
    if (found := _found_tools.get(name, None)) is not None: return found
    if (found := find_tool(name)) is not None: _found_tools[name] = found; return found
    if path.basename(name) != name:
        raise RuntimeError(f'The `{name}` executable ' + ('is not executable' if path.exists(name) else 'does not exist'))
    hint = hint or ('run `make setup macos`' if sys.platform == 'darwin' else 'see the Dependencies section of the README')
    raise RuntimeError(f'The `{name}` executable was not found in {LOCAL_TOOLS_DIR} or on the PATH ({hint})')
