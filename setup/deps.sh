#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPS_DIR="$REPO_DIR/.deps"
BIN_DIR="$DEPS_DIR/bin"
ENV_NAME="${ENV_NAME:-.venv}"
VENV="$REPO_DIR/$ENV_NAME"
PY="${PY:-python3.15}"

OPENSTA_REPO="${OPENSTA_REPO:-https://github.com/The-OpenROAD-Project/OpenSTA.git}"
OPENSTA_REF="${OPENSTA_REF:-c018cb21}"
CQESTO_REPO="${CQESTO_REPO:-https://github.com/MikolasJanota/cqesto.git}"
CQESTO_REF="${CQESTO_REF:-4fe4937000731fa8922b2bb25ced0352de01861f}"
QFUN_REPO="${QFUN_REPO:-https://github.com/MikolasJanota/qfun.git}"
QFUN_REF="${QFUN_REF:-adbc96047bd9d68fa21035a8c680ebc64d85a456}"
CADICAL_REPO="${CADICAL_REPO:-https://github.com/arminbiere/cadical.git}"
CADICAL_REF="${CADICAL_REF:-c60730422e758ef1cebe7aeddf2dda31c996bf04}"  # rel-3.0.1

# the QBF solvers that can be installed individually with `--solver <name>`
SOLVERS="cqesto cqesto-cadical qfun qfun-cadical"

MODE="${1:-}"
JOBS="$( (sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4) )"

log() { printf '\n[[ %s ]]\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }
is_macos() { [ "$(uname -s)" = "Darwin" ]; }
build_tools_hint() {
  if is_macos; then echo "install the Xcode command line tools"; else echo "install build-essential"; fi
}
package_hint() {
  if is_macos; then echo "install it with brew install $1"; else echo "install $1"; fi
}

case "$MODE" in
  --python-init|--python-dep|--macos|--all|--solver) ;;
  *) die "usage: $0 {--python-init|--python-dep|--macos|--all|--solver <solver>...}" ;;
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
  is_macos || die "$PY not found, install Python 3.15 first"
  command -v brew >/dev/null 2>&1 || die "$PY not found and Homebrew is not installed (https://brew.sh)"
  brew_install python@3.15
  PY="$(brew --prefix python@3.15)/bin/python3.15"
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
  brew_install_missing python@3.15 cmake yosys swig tcl-tk@8
  build_opensta
}

build_opensta() {
  local tcl_prefix tcl_lib target stamp sha
  ensure_python
  need_tool git
  need_tool cmake "$(package_hint cmake)"
  need_tool make "$(build_tools_hint)"
  need_tool cc "$(build_tools_hint)"

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
  git rev-parse --verify --quiet "${OPENSTA_REF}^{commit}" >/dev/null \
    || die "OpenSTA ref '$OPENSTA_REF' not found in $OPENSTA_REPO"
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

fetch_source() {  # $1 = directory under src/, $2 = repository, $3 = revision; prints the sha
  local dir="$DEPS_DIR/src/$1" repo="$2" ref="$3" sha
  mkdir -p "$DEPS_DIR/src"
  # keep git from discovering the repository this project is checked out in
  export GIT_CEILING_DIRECTORIES="$DEPS_DIR/src"
  if [ ! -f "$dir/.git/HEAD" ] || ! git -C "$dir" rev-parse --verify --quiet HEAD >/dev/null 2>&1; then
    rm -rf "$dir"
    git clone --quiet "$repo" "$dir"
  fi
  git -C "$dir" checkout --quiet -- .
  if ! git -C "$dir" cat-file -e "${ref}^{commit}" 2>/dev/null; then
    git -C "$dir" fetch --quiet --tags origin
  fi
  git -C "$dir" rev-parse --verify --quiet "${ref}^{commit}" >/dev/null \
    || die "revision '$ref' not found in $repo"
  git -C "$dir" checkout --quiet "$ref"
  sha="$(git -C "$dir" rev-parse HEAD)"
  echo "$sha"
}

build_cadical() {
  local sha stamp="$DEPS_DIR/src/cadical/.build-stamp"
  need_tool git
  need_tool make "$(build_tools_hint)"
  need_tool c++ "$(build_tools_hint)"

  sha="$(fetch_source cadical/cadical "$CADICAL_REPO" "$CADICAL_REF")"
  [ -n "$sha" ] || die "cannot check out cadical at '$CADICAL_REF'"
  if [ -f "$stamp" ] && [ "$(cat "$stamp")" = "$sha" ] \
    && [ -e "$DEPS_DIR/src/cadical/libcadical.a" ] && [ -e "$DEPS_DIR/src/cadical/ipasir.h" ]; then
    return 0
  fi

  log "building cadical ${sha:0:7}"
  ( cd "$DEPS_DIR/src/cadical/cadical" && ./configure && make -j"$JOBS" ) \
    > "$DEPS_DIR/src/cadical-build.log" 2>&1 \
    || die "cadical build failed, see $DEPS_DIR/src/cadical-build.log"
  # the layout the vendored setup scripts of cqesto and qfun would have produced
  ln -sfn cadical/build/libcadical.a "$DEPS_DIR/src/cadical/libcadical.a"
  ln -sfn cadical/src/ipasir.h "$DEPS_DIR/src/cadical/ipasir.h"
  echo "$sha" > "$stamp"
}

prepare_minisat() {  # $1 = the checkout of a solver vendoring minisat
  local dir="$1" minisat="$1/contrib/minisat"
  if [ -e "$minisat/lib/libminisat.a" ] || [ -e "$minisat/lib/libminisat.so" ] \
    || [ -e "$minisat/lib/libminisat.dylib" ]; then
    return 0
  fi
  # a partial setup cannot be reused, and the configure script rebuilds it when it is absent
  rm -rf "$minisat"
  [ -f "$dir/contrib/setup-minisat.sh" ] || return 0
  # minisat asks for a cmake version that cmake 4 refuses
  sed -i.bak 's|cmake -DCMAKE_INSTALL_PREFIX=${MDIR} ..|cmake -DCMAKE_INSTALL_PREFIX=${MDIR} -DCMAKE_POLICY_VERSION_MINIMUM=3.5 ..|' \
    "$dir/contrib/setup-minisat.sh"
  rm -f "$dir/contrib/setup-minisat.sh.bak"
}

install_solver() {  # $1 = one of $SOLVERS
  local name="$1" repo ref sat dir product target stamp identity sha sha_sat mode flags
  case "$name" in
    cqesto)         repo="$CQESTO_REPO"; ref="$CQESTO_REF"; sat='minisat' ;;
    cqesto-cadical) repo="$CQESTO_REPO"; ref="$CQESTO_REF"; sat='cadical' ;;
    qfun)           repo="$QFUN_REPO";   ref="$QFUN_REF";   sat='minisat' ;;
    qfun-cadical)   repo="$QFUN_REPO";   ref="$QFUN_REF";   sat='cadical' ;;
    *) die "unknown solver '$name' (available: $(echo "$SOLVERS" | tr ' ' ','))" ;;
  esac

  need_tool git
  need_tool cmake "$(package_hint cmake)"
  need_tool make "$(build_tools_hint)"
  need_tool c++ "$(build_tools_hint)"

  dir="$DEPS_DIR/src/$name"
  sha="$(fetch_source "$name" "$repo" "$ref")"
  [ -n "$sha" ] || die "cannot check out $name at '$ref'"
  [ -f "$dir/configure" ] || die "$name: checkout is incomplete, remove $dir and retry"

  # what the executable is built from: the solver revision, the SAT solver it is linked
  # against and how it is linked, so that any of the three changes forces a rebuild
  if [ "$sat" = 'cadical' ]; then
    build_cadical
    sha_sat="$(cat "$DEPS_DIR/src/cadical/.build-stamp")"
  else
    sha_sat='minisat'
  fi
  # on Linux the vendored SAT solver is a shared library, so the executables are linked
  # statically: they leave their build tree and have to stay self-contained. On macOS
  # the libraries are found through their absolute install name
  mode='dynamic'
  flags=''
  if ! is_macos; then mode='static'; flags='-s'; fi
  if [ "$sat" = 'cadical' ]; then flags="$flags -c"; fi
  identity="$sha $sha_sat $mode"

  mkdir -p "$DEPS_DIR/opt" "$BIN_DIR"
  target="$DEPS_DIR/opt/$name"
  stamp="$target.stamp"
  if [ -s "$target" ] && [ -f "$stamp" ] && [ "$(cat "$stamp")" = "$identity" ] \
    && probe_tool "$name" "$target"; then
    ln -sfn "$target" "$BIN_DIR/$name"
    return 0
  fi

  if [ "$sat" = 'cadical' ]; then
    # the vendored setup script would clone and build cadical again; it leaves a directory
    # in its place, which has to go for the link to be created
    rm -rf "$dir/contrib/cadical"
    ln -sfn "$DEPS_DIR/src/cadical" "$dir/contrib/cadical"
  fi
  prepare_minisat "$dir"

  log "building $name ($sat, $mode)"
  rm -rf "$dir/build"
  ( cd "$dir" && CC="${CC:-cc}" CXX="${CXX:-c++}" ./configure $flags ) > "$DEPS_DIR/src/$name-configure.log" 2>&1 \
    || die "$name: configure failed, see $DEPS_DIR/src/$name-configure.log"
  make -C "$dir/build" -j"$JOBS" > "$DEPS_DIR/src/$name-build.log" 2>&1 \
    || die "$name: build failed, see $DEPS_DIR/src/$name-build.log"

  product="${name%%-*}"  # the executable keeps the upstream name
  [ -x "$dir/build/$product" ] || die "$name: build produced no '$product' executable"
  cp "$dir/build/$product" "$target"
  echo "$identity" > "$stamp"
  ln -sfn "$target" "$BIN_DIR/$name"
}

probe_tool() {
  local output
  output="$(case "$1" in
    yosys) "$2" -V ;;
    sta) "$2" -version ;;
    cqesto|cqesto-cadical|qfun|qfun-cadical) "$2" --help ;;
    *) return 1 ;;
  esac 2>/dev/null)"
  # an empty file is executable, and bash runs it as an empty script that exits 0
  [ -n "$output" ]
}

check_toolchain() {
  local missing=0 tool path
  log "checking the toolchain"
  for tool in yosys sta $SOLVERS; do
    if [ -x "$BIN_DIR/$tool" ]; then
      path="$BIN_DIR/$tool"
    else
      path="$(command -v "$tool" 2>/dev/null || echo "$BIN_DIR/$tool")"
    fi
    if [ ! -x "$path" ]; then
      case "$tool" in
        yosys|sta) printf '  %-14s missing\n' "$tool"; missing=1 ;;
        *) printf '  %-14s missing (optional)\n' "$tool" ;;
      esac
    elif ! probe_tool "$tool" "$path"; then
      case "$tool" in
        yosys|sta) printf '  %-14s %s does not run\n' "$tool" "$path"; missing=1 ;;
        *) printf '  %-14s %s does not run (optional)\n' "$tool" "$path" ;;
      esac
    else
      printf '  %-14s %s\n' "$tool" "$path"
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
    for solver in $SOLVERS; do install_solver "$solver"; done
    check_toolchain
    ;;
  --solver)
    shift
    [ "$#" -gt 0 ] || die "usage: $0 --solver {$(echo "$SOLVERS" | tr ' ' '|')}"
    for solver in "$@"; do
      install_solver "$solver"
      printf '  %-14s %s\n' "$solver" "$BIN_DIR/$solver"
    done
    ;;
esac
