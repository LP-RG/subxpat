#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SRC_DIR="$REPO_DIR/src"

DEPS_DIR="$REPO_DIR/.deps"
OBJS_DIR="$DEPS_DIR/objs"

YOSYS_SRC_DIR="$SRC_DIR/yosys_objs"
YOSYS_DST_DIR="$OBJS_DIR/yosys"


compile_yosys_objects() {
  mkdir $YOSYS_DST_DIR -p
  cd $YOSYS_DST_DIR
  for file in $YOSYS_SRC_DIR/*; do
    [ -f "$file" ] || continue
    filename="$(basename ${file%.*})"
    yosys-config --build "$filename.so" "$file"
  done
  cd -
}

compile_yosys_objects