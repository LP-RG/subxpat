#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPS_DIR="${DEPS_DIR:-$REPO_DIR/.deps}"
case "$DEPS_DIR" in
  /*) ;;
  *) DEPS_DIR="$REPO_DIR/$DEPS_DIR" ;;
esac
BIN_DIR="$DEPS_DIR/bin"
ENV_NAME="${ENV_NAME:-.venv}"
VENV="$REPO_DIR/$ENV_NAME"
PY="${PY:-python3.14}"

OPENSTA_REPO="${OPENSTA_REPO:-https://github.com/The-OpenROAD-Project/OpenSTA.git}"
OPENSTA_REF="${OPENSTA_REF:-c018cb21}"
CQESTO_REPO="${CQESTO_REPO:-https://github.com/MikolasJanota/cqesto.git}"

MODE="${1:-}"
JOBS="$( (sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4) )"

log() { printf '\n[[ %s ]]\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }
is_macos() { [ "$(uname -s)" = "Darwin" ]; }

case "$MODE" in
  --python-init|--python-dep|--macos|--all) ;;
  *) die "usage: $0 {--python-init|--python-dep|--macos|--all}" ;;
esac

need_tool() {
  command -v "$1" >/dev/null 2>&1 && return 0
  die "`$1` not found${2:+ ($2)}"
}

brew_install() {
  if brew list --versions "$1" >/dev/null 2>&1; then return 0; fi
  log "installing $1 with brew"
  brew install "$1"
}

ensure_python() {
  if command -v "$PY" >/dev/null 2>&1; then return 0; fi
  is_macos || die "$PY not found, install Python 3.14 first"
  command -v brew >/dev/null 2>&1 || die "$PY not found and Homebrew is not installed (https://brew.sh)"
  brew_install python@3.14
  PY="$(brew --prefix python@3.14)/bin/python3.14"
  command -v "$PY" >/dev/null 2>&1 || die "$PY not found after brew install"
}

venv_is_current() {
  [ -x "$VENV/bin/python" ] || return 1
  "$VENV/bin/python" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 14) else 1)' 2>/dev/null
}

create_venv() {
  if venv_is_current; then return 0; fi
  ensure_python
  log "creating the python environment ($ENV_NAME) with $("$PY" -V 2>&1)"
  rm -rf "$VENV"
  "$PY" -m venv "$VENV"
}

install_python_deps() {
  create_venv
  log "installing python dependencies"
  "$VENV/bin/python" -m pip install --quiet --upgrade pip
  "$VENV/bin/python" -m pip install --quiet --upgrade -r "$REPO_DIR/requirements.txt"
}

install_macos_deps() {
  is_macos || die "--macos is only available on macOS"
  command -v brew >/dev/null 2>&1 || die "Homebrew is required on macOS (https://brew.sh)"
  log "installing brew packages"
  brew_install python@3.14
  brew_install cmake
  brew_install yosys
  brew_install swig
  brew_install tcl-tk@8
  build_opensta
}

build_opensta() {
  local tcl_prefix tcl_lib target stamp sha
  need_tool git
  need_tool cmake "install it with brew install cmake"
  need_tool make "install the Xcode command line tools"
  need_tool cc "install the Xcode command line tools"

  tcl_prefix="$(brew --prefix tcl-tk@8)"
  tcl_lib="$tcl_prefix/lib/libtcl8.6.dylib"
  [ -f "$tcl_prefix/include/tcl-tk/tcl.h" ] || die "tcl.h not found under $tcl_prefix (brew install tcl-tk@8)"
  [ -f "$tcl_lib" ] || die "libtcl8.6.dylib not found under $tcl_prefix/lib"

  mkdir -p "$DEPS_DIR/src" "$BIN_DIR"
  cd "$DEPS_DIR/src"
  [ -d OpenSTA ] || git clone --quiet "$OPENSTA_REPO" OpenSTA
  cd OpenSTA
  if ! git cat-file -e "${OPENSTA_REF}^{commit}" 2>/dev/null; then
    git fetch --quiet --tags origin
  fi
  git checkout --quiet -- .
  git checkout --quiet "$OPENSTA_REF"
  sha="$(git rev-parse HEAD)"

  target="$DEPS_DIR/opt/opensta"
  stamp="$target/.build-stamp"
  if [ -x "$target/bin/sta" ] && [ -f "$stamp" ] && [ "$(cat "$stamp")" = "$sha" ]; then
    ln -sf "$target/bin/sta" "$BIN_DIR/sta"
    return 0
  fi

  if [ -f tcl/StaException.i ]; then
    "$PY" - <<'PY'
import pathlib
p = pathlib.Path('tcl/StaException.i')
s = p.read_text()
if '$function' in s:
    p.write_text(s.replace('try { $function }', 'try { $action }'))
PY
  fi

  log "building OpenSTA $OPENSTA_REF (${sha:0:7})"
  rm -rf build
  cmake -B build -DCMAKE_BUILD_TYPE=Release \
    -DTCL_LIB="$tcl_lib" -DTCL_HEADER="$tcl_prefix/include/tcl-tk/tcl.h" \
    -DCMAKE_INSTALL_PREFIX="$target" > "$DEPS_DIR/src/opensta-configure.log" 2>&1 \
    || die "OpenSTA configure failed, see $DEPS_DIR/src/opensta-configure.log"
  cmake --build build -j"$JOBS"
  cmake --install build > /dev/null
  echo "$sha" > "$stamp"
  ln -sf "$target/bin/sta" "$BIN_DIR/sta"
}

build_cqesto() {
  local minisat_lib
  need_tool git
  need_tool cmake "install cmake to build cqesto"
  need_tool make
  need_tool c++

  mkdir -p "$DEPS_DIR/src" "$BIN_DIR"
  cd "$DEPS_DIR/src"
  [ -d cqesto ] || git clone --quiet "$CQESTO_REPO" cqesto
  cd cqesto
  if [ -x "$BIN_DIR/cqesto" ]; then return 0; fi

  log "building cqesto"
  minisat_lib="contrib/minisat/lib/libminisat.so"
  [ -e "$minisat_lib" ] || minisat_lib="contrib/minisat/lib/libminisat.dylib"
  [ -e "$minisat_lib" ] || minisat_lib="contrib/minisat/lib/libminisat.a"
  if [ ! -e "$minisat_lib" ]; then rm -rf contrib/minisat; fi
  if [ ! -d contrib/minisat ] && [ -f contrib/setup-minisat.sh ]; then
    sed -i.bak 's|cmake -DCMAKE_INSTALL_PREFIX=${MDIR} ..|cmake -DCMAKE_INSTALL_PREFIX=${MDIR} -DCMAKE_POLICY_VERSION_MINIMUM=3.5 ..|' contrib/setup-minisat.sh
  fi
  [ -f configure ] || die "cqesto checkout is incomplete, remove $DEPS_DIR/src/cqesto and retry"
  CC="${CC:-cc}" CXX="${CXX:-c++}" ./configure > "$DEPS_DIR/src/cqesto-configure.log" 2>&1 \
    || die "cqesto configure failed, see $DEPS_DIR/src/cqesto-configure.log"
  make -C build -j"$JOBS" || die "cqesto build failed"
  ln -sf "$DEPS_DIR/src/cqesto/build/cqesto" "$BIN_DIR/cqesto"
}

probe_tool() {
  case "$1" in
    yosys) "$2" -V ;;
    sta) "$2" -version ;;
    cqesto) "$2" --help ;;
  esac > /dev/null 2>&1
}

check_toolchain() {
  local missing=0 tool path
  log "checking the toolchain"
  for tool in yosys sta cqesto; do
    if [ -x "$BIN_DIR/$tool" ]; then
      path="$BIN_DIR/$tool"
    else
      path="$(command -v "$tool" 2>/dev/null || echo "$BIN_DIR/$tool")"
    fi
    if [ ! -x "$path" ]; then
      case "$tool" in
        yosys|sta) printf '  %-8s missing\n' "$tool"; missing=1 ;;
        *) printf '  %-8s missing (optional)\n' "$tool" ;;
      esac
    elif ! probe_tool "$tool" "$path"; then
      case "$tool" in
        yosys|sta) printf '  %-8s %s does not run\n' "$tool" "$path"; missing=1 ;;
        *) printf '  %-8s %s does not run (optional)\n' "$tool" "$path" ;;
      esac
    else
      printf '  %-8s %s\n' "$tool" "$path"
    fi
  done
  [ "$missing" = 0 ] || die "toolchain incomplete"
}

case "$MODE" in
  --python-init) create_venv ;;
  --python-dep) install_python_deps ;;
  --macos)
    install_macos_deps
    check_toolchain
    ;;
  --all)
    if is_macos; then install_macos_deps; fi
    build_cqesto
    check_toolchain
    ;;
esac
