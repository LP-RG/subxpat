"""
Aiger files conversion, loading, and parsing into IOGraph.

:authors: Ilia Zeller, Marco Biasion
"""

from typing import ClassVar, Iterable, Mapping, MutableMapping, Sequence
from collections import defaultdict

from sxpat.graph import IOGraph
from sxpat.graph.node import BoolVariable, BoolConstant, And, Not, Identity

import bisect
import itertools
import re
import aigverse.io as aig_io
from aigverse.networks import NamedAig
import networkx as nx
import subprocess
from textwrap import dedent

from sxpat.utils.tools import require_tool


__all__ = [
    'verilog_to_aiger',
    'load_aiger',
]


type AigValidNode = BoolVariable | And | Not | Identity | BoolConstant


def verilog_to_aiger(
    input_verilog_path: str,
    output_aiger_path: str,
) -> None:
    """
    Convert the given verilog into an optimised aiger file and the relative symbols map.

    :authors: Ilia Zeller, Marco Biasion
    """

    # synthesize to gate level
    yosys_command = dedent(f"""
        read_verilog {input_verilog_path};

        # flattening
        synth -flatten;
        opt -purge;

        # prepare aig nodes
        abc -g AND,NAND,ANDNOT,ORNOT; # aig-targeted gates
        opt -purge;
        aigmap;

        #
        write_aiger -symbols {output_aiger_path};
    """)

    yosys_exe = require_tool('yosys')
    process = subprocess.run(
        [yosys_exe, '-p', yosys_command],
        capture_output=True,
    )
    if process.returncode != 0:  # TODO: improve error
        raise RuntimeError(f"ERROR!!! yosys cannot do its pass on file {input_verilog_path}\n{process.stderr.decode()}")


class load_aiger:
    class UnparsableIdentifierError(Exception):
        def __init__(self, identifier: str, *args: object) -> None:
            super().__init__(identifier, *args)
            self.identifier = identifier

    class MissingAigerSymbolError(Exception): ...

    def __new__(cls, input_aiger_path: str, ports_order: list[str]) -> IOGraph:
        """
        Given the path to an .aig file containing also the symbols table, load the circuit as an IOGraph.

        :authors: Ilia Zeller, Marco Biasion
        """

        # load aig as NamedAig
        aig_obj = aig_io.read_aiger_into_aig(input_aiger_path)

        # group and order inputs/outputs
        g_inputs, g_outputs = cls.extract_inout(aig_obj, ports_order)
        inputs_ids = list(itertools.chain.from_iterable(indexes for _, indexes in sorted(g_inputs.items())))
        outputs_ids = list(itertools.chain.from_iterable(indexes for _, indexes in sorted(g_outputs.items())))

        # construct all nodes
        # NOTE: if the aig gates are not in topological order (they should), this will raise an exception, which is ok
        nodes = dict[tuple[int, bool], AigValidNode]()

        # inputs
        nodes.update(((i_id, False), BoolVariable(f'in{i}')) for i, i_id in enumerate(inputs_ids))

        # gates
        for gate in aig_obj.gates():
            # get inputs to the current gate
            fanin = list[str]()
            for _source_sig in aig_obj.fanins(gate):
                _source_node = aig_obj.get_node(_source_sig)
                if aig_obj.is_constant(_source_node): _in = cls._get_constant(nodes, aig_obj.is_complemented(_source_sig))
                elif aig_obj.is_complemented(_source_sig): _in = cls._get_negated(nodes, _source_node)
                else: _in = nodes[(_source_node, False)]
                fanin.append(_in.name)
            nodes[(gate, False)] = And(f'g_and{gate}', tuple(fanin))

        # outputs
        for i, out_id in enumerate(outputs_ids):
            _source_sig = aig_obj.pos()[out_id]
            _source_node = aig_obj.get_node(_source_sig)
            if aig_obj.is_constant(_source_node): _in = cls._get_constant(nodes, aig_obj.is_complemented(_source_sig))
            elif aig_obj.is_complemented(_source_sig): _in = cls._get_negated(nodes, _source_node)
            else: _in = nodes[(_source_node, False)]
            nodes[(-1 - out_id, False)] = Identity(f'out{i}', (_in.name,))

        # construct graph
        return IOGraph(
            nodes.values(),
            inputs_names=[nodes[(i, False)].name for i in inputs_ids],
            outputs_names=[nodes[(-1 - i, False)].name for i in outputs_ids],
        )

    @staticmethod
    def _get_negated(nodes: MutableMapping[tuple[int, bool], AigValidNode], n: int) -> AigValidNode:
        if (nn := nodes.get((n, True), None)) is None:  # negated node does not exists
            nn = nodes[(n, True)] = Not(f'g_not{n}', (nodes[(n, False)].name,))
        return nn

    @staticmethod
    def _get_constant(nodes: MutableMapping[tuple[int, bool], AigValidNode], value: bool) -> AigValidNode:
        if (cn := nodes.get((0, value), None)) is None:  # negated node does not exists
            cn = nodes[(0, value)] = BoolConstant(f'const{int(value)}', value)
        return cn

    @classmethod
    def extract_inout(cls, aig_obj: NamedAig, ports_order: list[str]
                      ) -> tuple[dict[str, list[int]], dict[str, list[int]]]:
        """
        Given a NamedAig containing a symbols table and the order of the ports, return the ordered groups of inputs/outputs bits.

        :raises MissingAigerSymbolError: if `aig_obj` was not generated from an .aig containing a symbols table.

        :authors: Marco Biasion, Ilia Zeller
        """
        try:

            # group ordered inputs
            _inputs = defaultdict[str, list[tuple[int, int]]](list)  # {name: [(index, aig_index)]}
            for pi in aig_obj.pis():
                signal = aig_obj.make_signal(pi)
                name = aig_obj.get_name(signal)
                cls._insort_match(_inputs, name, pi)

            # group ordered outputs
            _outputs = defaultdict[str, list[tuple[int, int]]](list)  # {name: [(index, aig_index)]}
            for aig_p_index in range(aig_obj.num_pos):
                name = aig_obj.get_output_name(aig_p_index)
                cls._insort_match(_outputs, name, aig_p_index)

        except IndexError as e:
            if 'aig_p_index' in locals():
                raise cls.MissingAigerSymbolError(f'Primary output index={aig_p_index} does not have an associated symbol.')  # type: ignore
            else:
                raise cls.MissingAigerSymbolError(f'Primary input id={pi} does not have an associated symbol.')  # type: ignore

        # collapse in/out
        return (
            cls._collapse(_inputs, ports_order),
            cls._collapse(_outputs, ports_order),
        )

    _PATTERN_PRIMARY_INOUT: ClassVar = re.compile(r'([a-zA-Z0-9_$]+)(?:\[(\d+)\])?')

    @classmethod
    def _insort_match(cls, groups: Mapping[str, list[tuple[int, int]]], name: str, aig_p_index: int):
        m = cls._PATTERN_PRIMARY_INOUT.fullmatch(name)
        if m is None: raise cls.UnparsableIdentifierError(name)

        if m.group(2) is None: idx = 0
        else: idx = int(m.group(2))

        bisect.insort(groups[m.group(1)], (idx, aig_p_index))

    @staticmethod
    def _collapse(groups: Mapping[str, list[tuple[int, int]]], ports_order: Sequence[str]):
        return {
            _name: [_aig_index for (_, _aig_index) in _bits]
            for (_name, _bits) in sorted(groups.items(), key=lambda nb: ports_order.index(nb[0]))
        }


def is_topological_order(G: nx.DiGraph, order: Iterable) -> bool:
    """
    :authors: Ilia Zeller
    """

    # Create a position map: node -> index in the given order
    pos = {node: i for i, node in enumerate(order)}
    # Check all edges
    return all(pos[u] < pos[v] for u, v in G.edges())


def topological_sort(G: nx.DiGraph) -> nx.DiGraph:
    """
    :authors: Ilia Zeller
    """

    # Sort nodes in topological order
    sorted_G = nx.DiGraph()
    sorted_G.graph.update(G.graph)
    sorted_G.add_nodes_from((n, G.nodes[n]) for n in nx.topological_sort(G))
    sorted_G.add_edges_from(G.edges.data())
    return sorted_G
