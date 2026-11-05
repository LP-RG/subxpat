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
  --python|--python-init|--python-dep|--macos|--all) ;;
  *) die "usage: $0 {--python|--python-init|--python-dep|--macos|--all}" ;;
esac

ensure_python() {
  if command -v "$PY" >/dev/null 2>&1; then return; fi
  is_macos || die "$PY not found, install Python 3.14 first"
  command -v brew >/dev/null 2>&1 || die "$PY not found and Homebrew is not installed (https://brew.sh)"
  log "installing python@3.14 with brew"
  brew list --versions python@3.14 >/dev/null 2>&1 || brew install python@3.14
  PY="$(brew --prefix python@3.14)/bin/python3.14"
  command -v "$PY" >/dev/null 2>&1 || die "$PY not found after brew install"
}

create_venv() {
  if [ -x "$VENV/bin/python" ]; then return; fi
  log "creating the python environment ($ENV_NAME)"
  ensure_python
  rm -rf "$VENV"
  "$PY" -m venv "$VENV"
}

install_python_deps() {
  create_venv
  log "installing python dependencies"
  "$VENV/bin/python" -m pip install --quiet --upgrade pip
  "$VENV/bin/python" -m pip install --quiet --upgrade -r "$REPO_DIR/requirements.txt"
}

brew_install() {
  brew list --versions "$1" >/dev/null 2>&1 && return
  log "installing $1 with brew"
  brew install "$1"
}

install_macos_deps() {
  is_macos || die "--macos is only available on macOS"
  command -v brew >/dev/null 2>&1 || die "Homebrew is required on macOS (https://brew.sh)"
  ensure_python
  log "installing brew packages"
  brew_install yosys
  brew_install graphviz
  brew_install swig
  brew_install tcl-tk@8
  build_opensta
}

build_opensta() {
  local tcl_prefix tcl_lib target
  tcl_prefix="$(brew --prefix tcl-tk@8)"
  tcl_lib="$tcl_prefix/lib/libtcl8.6.dylib"
  [ -f "$tcl_prefix/include/tcl-tk/tcl.h" ] || die "tcl.h not found under $tcl_prefix"
  [ -f "$tcl_lib" ] || die "libtcl8.6.dylib not found under $tcl_prefix/lib"

  mkdir -p "$DEPS_DIR/src" "$BIN_DIR"
  cd "$DEPS_DIR/src"
  [ -d OpenSTA ] || git clone --recursive "$OPENSTA_REPO" OpenSTA
  cd OpenSTA
  git fetch --all --quiet --tags
  git checkout --quiet "$OPENSTA_REF"
  git submodule update --init --recursive --quiet
  "$PY" - <<'PY'
import pathlib
p = pathlib.Path('tcl/StaException.i')
s = p.read_text()
if '$function' in s:
    p.write_text(s.replace('try { $function }', 'try { $action }'))
PY

  target="$DEPS_DIR/opt/opensta"
  if [ ! -x "$target/bin/sta" ]; then
    log "building OpenSTA $OPENSTA_REF"
    cmake -B build -DCMAKE_BUILD_TYPE=Release -DCUDD=0 \
      -DTCL_LIB="$tcl_lib" -DTCL_HEADER="$tcl_prefix/include/tcl-tk/tcl.h" \
      -DCMAKE_INSTALL_PREFIX="$target" > "$DEPS_DIR/src/opensta-configure.log" 2>&1
    cmake --build build -j"$JOBS"
    cmake --install build > /dev/null
  fi
  ln -sf "$target/bin/sta" "$BIN_DIR/sta"
}

build_cqesto() {
  mkdir -p "$DEPS_DIR/src" "$BIN_DIR"
  cd "$DEPS_DIR/src"
  [ -d cqesto ] || git clone "$CQESTO_REPO" cqesto
  cd cqesto
  if [ ! -x "$BIN_DIR/cqesto" ]; then
    log "building cqesto"
    if [ ! -e contrib/minisat/lib/libminisat.so ] && [ ! -e contrib/minisat/lib/libminisat.dylib ] && [ ! -e contrib/minisat/lib/libminisat.a ]; then
      rm -rf contrib/minisat
    fi
    if [ ! -d contrib/minisat ] && [ -f contrib/setup-minisat.sh ]; then
      sed -i.bak 's|cmake -DCMAKE_INSTALL_PREFIX=${MDIR} ..|cmake -DCMAKE_INSTALL_PREFIX=${MDIR} -DCMAKE_POLICY_VERSION_MINIMUM=3.5 ..|' contrib/setup-minisat.sh
    fi
    CC="${CC:-cc}" CXX="${CXX:-c++}" ./configure > "$DEPS_DIR/src/cqesto-configure.log" 2>&1
    make -C build -j"$JOBS"
    cp build/cqesto "$BIN_DIR/cqesto"
  fi
}

check_toolchain() {
  local missing=0
  log "checking the toolchain"
  for tool in yosys sta; do
    if command -v "$tool" >/dev/null 2>&1 || [ -x "$BIN_DIR/$tool" ]; then
      printf '  %-8s %s\n' "$tool" "$(command -v "$tool" 2>/dev/null || echo "$BIN_DIR/$tool")"
    else
      printf '  %-8s missing\n' "$tool"
      missing=1
    fi
  done
  if command -v dot >/dev/null 2>&1 || [ -x "$BIN_DIR/dot" ]; then
    printf '  %-8s %s\n' dot "$(command -v dot 2>/dev/null || echo "$BIN_DIR/dot")"
  else
    printf '  %-8s missing (only needed by --debug)\n' dot
  fi
  if [ -x "$BIN_DIR/cqesto" ]; then
    printf '  %-8s %s\n' cqesto "$BIN_DIR/cqesto"
  fi
  printf '  %-8s %s\n' python "$("$VENV/bin/python" -V 2>&1)"
  [ "$missing" = 0 ] || die "toolchain incomplete"
}

case "$MODE" in
  --python-init) create_venv ;;
  --python-dep) install_python_deps ;;
  --python) install_python_deps ;;
  --macos) install_macos_deps && install_python_deps && check_toolchain ;;
  --all)
    if is_macos; then install_macos_deps; fi
    build_cqesto
    install_python_deps
    check_toolchain
    ;;
esac
