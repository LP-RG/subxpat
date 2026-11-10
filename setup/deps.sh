#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPS_DIR="$REPO_DIR/.deps"
BIN_DIR="$DEPS_DIR/bin"
ENV_NAME="${ENV_NAME:-.venv}"
VENV="$REPO_DIR/$ENV_NAME"
PY="${PY:-python3.14}"

OPENSTA_REPO="${OPENSTA_REPO:-https://github.com/The-OpenROAD-Project/OpenSTA.git}"
OPENSTA_REF="${OPENSTA_REF:-c018cb21}"
CQESTO_REPO="${CQESTO_REPO:-https://github.com/MikolasJanota/cqesto.git}"
CQESTO_REF="${CQESTO_REF:-4fe4937000731fa8922b2bb25ced0352de01861f}"

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
  die "'$1' not found${2:+ ($2)}"
}

brew_install() {
  if brew list --versions "$1" >/dev/null 2>&1; then return 0; fi
  log "installing $1 with brew"
  brew install "$1"
}

brew_install_missing() {
  local installed missing formula
  installed="$(brew list --versions "$@" 2>/dev/null || true)"
  missing=""
  for formula in "$@"; do
    case "$installed" in
      *"$formula "*) ;;
      *) missing="$missing $formula" ;;
    esac
  done
  if [ -n "$missing" ]; then
    log "installing$missing with brew"
    brew install $missing
  fi
}

ensure_python() {
  if command -v "$PY" >/dev/null 2>&1; then return 0; fi
  is_macos || die "$PY not found, install Python 3.14 first"
  command -v brew >/dev/null 2>&1 || die "$PY not found and Homebrew is not installed (https://brew.sh)"
  brew_install python@3.14
  PY="$(brew --prefix python@3.14)/bin/python3.14"
  command -v "$PY" >/dev/null 2>&1 || die "$PY not found after brew install"
}

python_version() {
  "$1" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null
}

venv_is_current() {
  local want
  [ -x "$VENV/bin/python" ] || return 1
  want="$(python_version "$PY")" || return 1
  [ -n "$want" ] && [ "$(python_version "$VENV/bin/python")" = "$want" ]
}

create_venv() {
  case "$ENV_NAME" in
    .|..|/*|*/*) die "invalid ENV_NAME '$ENV_NAME'" ;;
  esac
  ensure_python
  if venv_is_current; then return 0; fi
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
  case "$REPO_DIR" in
    *" "*) die "the path '$REPO_DIR' contains a space, which the OpenSTA build does not support" ;;
  esac
  command -v brew >/dev/null 2>&1 || die "Homebrew is required on macOS (https://brew.sh)"
  log "installing brew packages"
  brew_install_missing python@3.14 cmake yosys swig tcl-tk@8
  build_opensta
}

build_opensta() {
  local tcl_prefix tcl_lib target stamp sha
  ensure_python
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
  export GIT_CEILING_DIRECTORIES="$DEPS_DIR/src"
  if [ ! -f OpenSTA/.git/HEAD ] || ! git -C OpenSTA rev-parse --verify --quiet HEAD >/dev/null 2>&1; then
    rm -rf OpenSTA
    git clone --quiet "$OPENSTA_REPO" OpenSTA
  fi
  cd OpenSTA
  if ! git cat-file -e "${OPENSTA_REF}^{commit}" 2>/dev/null; then
    git fetch --quiet --tags origin
  fi
  git checkout --quiet -- .
  git checkout --quiet "$OPENSTA_REF" \
    || die "cannot check out OpenSTA ref '$OPENSTA_REF' (check that it exists in $OPENSTA_REPO)"
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
  rm -rf build "$target.next"
  cmake -B build -DCMAKE_BUILD_TYPE=Release \
    -DTCL_LIB="$tcl_lib" -DTCL_HEADER="$tcl_prefix/include/tcl-tk/tcl.h" \
    -DCMAKE_INSTALL_PREFIX="$target.next" > "$DEPS_DIR/src/opensta-configure.log" 2>&1 \
    || die "OpenSTA configure failed, see $DEPS_DIR/src/opensta-configure.log"
  cmake --build build -j"$JOBS" || die "OpenSTA build failed"
  cmake --install build > /dev/null || die "OpenSTA install failed"
  rm -rf "$target"
  mv "$target.next" "$target"
  echo "$sha" > "$stamp"
  ln -sf "$target/bin/sta" "$BIN_DIR/sta"
}

build_cqesto() {
  local minisat_lib sha stamp
  need_tool git
  need_tool cmake "install cmake to build cqesto"
  need_tool make "install the Xcode command line tools"
  need_tool c++ "install the Xcode command line tools"

  mkdir -p "$DEPS_DIR/src" "$BIN_DIR"
  cd "$DEPS_DIR/src"
  export GIT_CEILING_DIRECTORIES="$DEPS_DIR/src"
  if [ ! -f cqesto/.git/HEAD ] || ! git -C cqesto rev-parse --verify --quiet HEAD >/dev/null 2>&1; then
    rm -rf cqesto
    git clone --quiet "$CQESTO_REPO" cqesto
  fi
  cd cqesto
  if ! git cat-file -e "${CQESTO_REF}^{commit}" 2>/dev/null; then
    git fetch --quiet origin
  fi
  git checkout --quiet -- .
  git checkout --quiet "$CQESTO_REF" \
    || die "cannot check out cqesto ref '$CQESTO_REF' (check that it exists in $CQESTO_REPO)"
  sha="$(git rev-parse HEAD)"
  stamp="$DEPS_DIR/opt/cqesto.stamp"
  if [ -x "$BIN_DIR/cqesto" ] && [ -f "$stamp" ] && [ "$(cat "$stamp")" = "$sha" ]; then
    return 0
  fi
  [ -f configure ] || die "cqesto checkout is incomplete, remove $DEPS_DIR/src/cqesto and retry"

  log "building cqesto"
  minisat_lib="contrib/minisat/lib/libminisat.so"
  [ -e "$minisat_lib" ] || minisat_lib="contrib/minisat/lib/libminisat.dylib"
  [ -e "$minisat_lib" ] || minisat_lib="contrib/minisat/lib/libminisat.a"
  if [ ! -e "$minisat_lib" ]; then rm -rf contrib/minisat; fi
  if [ ! -d contrib/minisat ] && [ -f contrib/setup-minisat.sh ]; then
    sed -i.bak 's|cmake -DCMAKE_INSTALL_PREFIX=${MDIR} ..|cmake -DCMAKE_INSTALL_PREFIX=${MDIR} -DCMAKE_POLICY_VERSION_MINIMUM=3.5 ..|' contrib/setup-minisat.sh
    rm -f contrib/setup-minisat.sh.bak
  fi
  rm -rf build
  CC="${CC:-cc}" CXX="${CXX:-c++}" ./configure > "$DEPS_DIR/src/cqesto-configure.log" 2>&1 \
    || die "cqesto configure failed, see $DEPS_DIR/src/cqesto-configure.log"
  make -C build -j"$JOBS" || die "cqesto build failed"
  mkdir -p "$DEPS_DIR/opt"
  echo "$sha" > "$stamp"
  ln -sf "$DEPS_DIR/src/cqesto/build/cqesto" "$BIN_DIR/cqesto"
}

probe_tool() {
  case "$1" in
    yosys) "$2" -V ;;
    sta) "$2" -version ;;
    cqesto) "$2" --help ;;
    *) return 1 ;;
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
