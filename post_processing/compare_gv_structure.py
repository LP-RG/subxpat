from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, Set, Tuple


NODE_RE = re.compile(r"^(?P<name>[A-Za-z_][\w.]*)\s*\[")
EDGE_RE = re.compile(r"^(?P<src>[A-Za-z_][\w.]*)\s*->\s*(?P<dst>[A-Za-z_][\w.]*)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare the structure of two GraphViz .gv files")
    parser.add_argument("first", type=Path, help="First .gv file")
    parser.add_argument("second", type=Path, help="Second .gv file")
    return parser.parse_args()


def iter_clean_lines(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("//"):
                continue
            if line in {"{", "}", "digraph {", "strict digraph {"}:
                continue
            yield line


def extract_structure(path: Path) -> Tuple[Set[str], Set[Tuple[str, str]]]:
    nodes: Set[str] = set()
    edges: Set[Tuple[str, str]] = set()

    for line in iter_clean_lines(path):
        edge_match = EDGE_RE.match(line)
        if edge_match:
            edges.add((edge_match.group("src"), edge_match.group("dst")))
            continue

        node_match = NODE_RE.match(line)
        if node_match:
            nodes.add(node_match.group("name"))

    return nodes, edges


def main() -> int:
    args = parse_args()

    if not args.first.exists():
        print(f"Missing file: {args.first}", file=sys.stderr)
        return 2
    if not args.second.exists():
        print(f"Missing file: {args.second}", file=sys.stderr)
        return 2

    first_nodes, first_edges = extract_structure(args.first)
    second_nodes, second_edges = extract_structure(args.second)

    only_first_nodes = sorted(first_nodes - second_nodes)
    only_second_nodes = sorted(second_nodes - first_nodes)
    only_first_edges = sorted(first_edges - second_edges)
    only_second_edges = sorted(second_edges - first_edges)

    if not only_first_nodes and not only_second_nodes and not only_first_edges and not only_second_edges:
        print("STRUCTURE MATCH")
        print(f"nodes: {len(first_nodes)}")
        print(f"edges: {len(first_edges)}")
        return 0

    print("STRUCTURE DIFFER")
    print(f"first nodes: {len(first_nodes)}")
    print(f"second nodes: {len(second_nodes)}")
    print(f"first edges: {len(first_edges)}")
    print(f"second edges: {len(second_edges)}")

    if only_first_nodes:
        print("nodes only in first:")
        for node in only_first_nodes:
            print(f"  {node}")
    if only_second_nodes:
        print("nodes only in second:")
        for node in only_second_nodes:
            print(f"  {node}")
    if only_first_edges:
        print("edges only in first:")
        for src, dst in only_first_edges:
            print(f"  {src} -> {dst}")
    if only_second_edges:
        print("edges only in second:")
        for src, dst in only_second_edges:
            print(f"  {src} -> {dst}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())