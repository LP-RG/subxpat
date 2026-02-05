from __future__ import annotations
from collections import Counter, defaultdict
from typing import Dict, List

from sxpat.annotatedGraph import AnnotatedGraph
from sxpat.graph import Graph

import sys
import os
import time


from patterns import *


patterns = {
    # 1 to 1 (simple not)
    'pattern1 (1 = not(0))': SimplePattern(2, [(0, 1)], {0}, {1}),
    # 2 to 1 (simple and)
    'pattern2 (2 = and(0, 1))': SimplePattern(3, {(0, 2), (1, 2)}, {0, 1}, {2}, [[0], [1]]),
    #
    'pattern3': SimplePattern(4, {(0, 1), (0, 2), (3, 2)}, {0, 3}, {1, 2}),
    #
    'pattern4': SimplePattern(5, {(0, 1), (0, 2), (3, 2), (3, 4)}, {0, 3}, {1, 2, 4}, [[0, 1], [3, 4]]),
    # cones
    'cones': ConesAggregatePattern(),
}


def load_graph(filename: str) -> Graph:
    # imports
    from sxpat.converting.legacy import iograph_from_legacy
    from pickle import load

    # deserialize
    with open(filename, 'rb') as f: annotated_graph: AnnotatedGraph = load(f)
    # for (i, n) in annotated_graph.output_dict.items():
    #     annotated_graph.graph.nodes[n]['weight'] = 2**i
        # print(i, n)

    # convert
    return iograph_from_legacy(annotated_graph)


def elaborate_and_rules(filename: str):
    g = load_graph(filename)

    for (pname, pattern) in patterns.items():
        t = time.perf_counter()
        matches = pattern.match(g._inner)
        t = time.perf_counter() - t

        print(f'{filename} X {pname:<9}: found {len(matches):>4} matches in {t:.4f}s ({len(g._inner):>5} nodes)')

        c = Counter()
        t = time.perf_counter()
        for m in matches:
            m.analyze_rules(lambda n: g[n].weight, lambda n: g[n].weight > 0, c)
            if c['0!=1'] > 0:
                print(m)
                break
        t = time.perf_counter() - t

        print(*c.items(), t, sep='\n')
        exit()


def analyze_patterns():

    print('generating matches (step 1/3)', file=sys.stderr)
    matches: List[Match] = []
    for (ip, (pname, pattern)) in enumerate(patterns.items()):
        print('-' * 50, pname)

        folder = 'labelled_graphs'
        files = os.listdir(folder)

        for (i, filename) in enumerate(files):
            print(f'{((ip / len(patterns)) + (i / len(files) / len(patterns))) * 100:>3.0f}% ({i+1:>3} / {len(files)} + {ip+1:>2} / {len(patterns)}) {filename}', file=sys.stderr)

            filename = f'{folder}/{filename}'
            g = load_graph(filename)

            should_analyze = lambda n: g[n].weight > 0
            matches.extend([
                (m, g)
                for m in pattern.match(g._inner)
                if m.is_match_ok(should_analyze)
            ])

    print('grouping matches by concrete pattern (step 2/3)', file=sys.stderr)
    groups: Dict[Pattern, List[Match]] = defaultdict(list)
    for (m, g) in matches:
        groups[m.pattern].append((m, g))

    print('analyzing rules (step 3/3)', file=sys.stderr)
    for (ip, (pattern, _matches)) in enumerate(groups.items()):
        print('-' * 50, str(pattern))

        counter = Counter()
        matches_count = 0

        for (i, (m, g)) in enumerate(_matches):
            m: Match
            print(f'{((ip / len(groups)) + (i / len(_matches) / len(groups))) * 100:>3.0f}% ({i+1:>3} / {len(_matches)} + {ip+1:>2} / {len(groups)})', file=sys.stderr)

            should_analyze = lambda n: g[n].weight > 0
            matches_count += m.ok_count(should_analyze)

            get_value = lambda n: g[n].weight
            m.analyze_rules(get_value, should_analyze, counter)

        print(*(f'{op:<20} is correct {count:>8} times out of {matches_count:>8}' for (op, count) in counter.items()), sep='\n')


def elaborate(filename: str) -> dict:
    g = load_graph(filename)
    # GraphVizPorter.to_file(g, 'banana.gv')

    results = dict()
    for (pname, pattern) in patterns.items():
        t = time.perf_counter()
        matches = pattern.match(g._inner)
        # print(*matches, sep='\n')
        t = time.perf_counter() - t
        results[pname] = (matches, t)

        print(f'{filename} X {pname:<9}: found {len(matches):>4} matches in {t:.4f}s ({len(g._inner):>5} nodes)')

    return results


def main():
    folder = 'labelled_graphs'
    results = dict()

    files = os.listdir(folder)
    for (i, filename) in enumerate(files):
        print(f'{i+1 / len(files) * 100:>3.0f}% ({i+1} / {len(files)})')

        filename = f'{folder}/{filename}'
        results[filename] = elaborate(filename)

    return results


def benchmark():
    # setings
    filename = 'labelled_graphs/adder_i256_o129.pkl'
    patterns_name = ['pattern1', 'pattern2']
    N = 20

    # setup
    g = load_graph(filename)._inner
    ps = tuple(patterns[pname] for pname in patterns_name)

    t = time.perf_counter()
    for i in range(N):
        for p in ps:
            p.match(g)
    t = time.perf_counter() - t

    print(t)


if __name__ == '__main__':
    # benchmark()
    # at = time.perf_counter()
    # main()
    # at = time.perf_counter() - at
    # print(f'total took {at:.4f}s')
    # elaborate('labelled_graphs/adder_i176_o89_DEL3K3O5ZZCY_i2_0.pkl')
    # elaborate('labelled_graphs/adder_i256_o129.pkl')
    # elaborate_and_rules('labelled_graphs/adder_i256_o129.pkl')
    analyze_patterns()
