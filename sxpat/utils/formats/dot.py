from typing import Dict

import re
import networkx as nx


__all__ = [
    'load_yosys_dot',
    'InvalidGateError',
    'InvalidNodeError',
]


class InvalidGateError(RuntimeError): pass
class InvalidNodeError(RuntimeError): pass


class load_yosys_dot:
    _UNWANTED_FIELDS = frozenset((
        # possibly present in loaded file
        'height', 'width', 'pos',
        'rects',
        'color', 'fontcolor', 'style',
        # possibly added during loading
        'contraction',
    ))
    _CONSTANT_MAPPING = {
        "1'0": 'FALSE',
        "1'1": 'TRUE',
    }
    _INDEX_PATTERN = re.compile(r'\d+')
    _GATE_PATTERN = re.compile('and|or|not')

    def __new__(cls, dot_path: str) -> nx.DiGraph:
        #
        digraph: nx.DiGraph = nx.drawing.nx_agraph.read_dot(dot_path)  # type: ignore

        # remove all artifacts (extra wires, buffers, etc.)
        cls.merge_artifacts_into_nodes(digraph)

        # removes and reconnects outgoing edges from outputs
        cls.reconnect_output_passthrough_edges(digraph)

        # normalize all nodes to standard format
        cls.normalize_nodes(digraph)

        # cleanup nodes from unnecessary attributes
        cls.clean_nodes_attributes(digraph)

        # updates all nodes addresses (names)
        cls.readdress_nodes(digraph)

        # force type to be nx.DiGraph
        return nx.DiGraph(digraph)

    @classmethod
    def merge_artifacts_into_nodes(cls, mutable_graph: nx.DiGraph) -> nx.DiGraph:
        """
        Removes all artifact from the graph (such as wires, points, etc.).

        :authors: Marco Biasion
        :performance: 20% faster compared to iterative nx.contracted_nodes
        """

        # map artifacts to unique predecessor
        artifacts: Dict[str, str] = {
            dst: src
            for (src, dst) in mutable_graph.edges()
            if (
                cls._is_buffer(mutable_graph, dst)
                or cls._is_wire(mutable_graph, dst)
                or cls._is_point(mutable_graph, dst)
            )
        }

        # update parent with artifact outedges
        for (artifact, parent) in artifacts.items():
            mutable_graph.add_edges_from(
                (parent, dst)
                for (_, dst) in mutable_graph.out_edges(artifact)
            )

        # remove artifacts
        mutable_graph.remove_nodes_from(artifacts.keys())

        return mutable_graph

    @classmethod
    def reconnect_output_passthrough_edges(cls, mutable_graph: nx.DiGraph) -> nx.DiGraph:
        """
        Remove all outgoing edges from output nodes, and reconnect them to the output's parent.

        :authors: Marco Biasion, Morteza Rezaalipour
        """

        for n in mutable_graph.nodes:
            if (
                cls._is_output(mutable_graph, n)
                and mutable_graph.out_degree(n) > 0
            ):
                parent = next(mutable_graph.predecessors(n))
                destinations = tuple(mutable_graph.successors(n))
                mutable_graph.remove_edges_from((n, dst) for dst in destinations)
                mutable_graph.add_edges_from((parent, dst) for dst in destinations)

        return mutable_graph

    @classmethod
    def normalize_nodes(cls, mutable_graph: nx.DiGraph) -> nx.DiGraph:
        """
        Update all nodes attributes to follow the standard.

        :authors: Marco Biasion, Morteza Rezaalipour
        """

        for n in mutable_graph.nodes:
            #
            if cls._is_input(mutable_graph, n):
                idx = cls._INDEX_PATTERN.search(mutable_graph.nodes[n]['label']).group()  # type: ignore
                mutable_graph.nodes[n]['label'] = f'in{idx}'
                mutable_graph.nodes[n]['shape'] = f'circle'
                mutable_graph.nodes[n]['type'] = 'input'
            #
            elif cls._is_output(mutable_graph, n):
                idx = cls._INDEX_PATTERN.search(mutable_graph.nodes[n]['label']).group()  # type: ignore
                mutable_graph.nodes[n]['label'] = f'out{idx}'
                mutable_graph.nodes[n]['shape'] = f'doublecircle'
                mutable_graph.nodes[n]['type'] = 'output'
            #
            elif cls._is_gate(mutable_graph, n):
                _m = cls._GATE_PATTERN.search(mutable_graph.nodes[n]['label'])
                if _m is None: raise InvalidGateError(
                    f'expected one of ({cls._GATE_PATTERN.pattern.replace("|", ", ")})'
                    f' but found {mutable_graph.nodes[n]["label"].upper()!r}'
                )

                mutable_graph.nodes[n]['label'] = _m.group()
                mutable_graph.nodes[n]['shape'] = 'invhouse'
                mutable_graph.nodes[n]['type'] = 'gate'
            #
            elif cls._is_constant(mutable_graph, n):
                mutable_graph.nodes[n]['label'] = cls._CONSTANT_MAPPING[mutable_graph.nodes[n]['label']]
                mutable_graph.nodes[n]['shape'] = 'square'
                mutable_graph.nodes[n]['type'] = 'constant'
            #
            else:
                nx.nx_agraph.write_dot(mutable_graph, 'error.dot')
                raise InvalidNodeError(f'node {n} = {mutable_graph.nodes[n]} cannot be parsed')

        return mutable_graph

    @classmethod
    def readdress_nodes(cls, mutable_graph: nx.DiGraph) -> nx.DiGraph:
        """
        Update all nodes names to follow the standard, and sort the graph in topologial order.

        :authors: Marco Biasion, Morteza Rezaalipour
        :performance: 25% faster than legacy
        """

        # compute names updates
        updates: Dict[str, str] = dict()
        gates_indexes = iter(range(len(mutable_graph)))
        for old_name in nx.topological_sort(mutable_graph):
            attrs = mutable_graph.nodes[old_name]

            if (
                cls._is_input(mutable_graph, old_name)
                or cls._is_output(mutable_graph, old_name)
            ):
                updates[old_name] = attrs.get('label')  # type: ignore

            elif (
                cls._is_gate(mutable_graph, old_name)
                or cls._is_constant(mutable_graph, old_name)
            ):
                updates[old_name] = f'g{next(gates_indexes)}'

            else:
                raise RuntimeError('Invalid state')

        # extract old structure
        edges = list(mutable_graph.edges())
        nodes = dict(mutable_graph.nodes(True))
        # empty the graph
        mutable_graph.clear()
        # readd nodes and edges (following the updated names)
        mutable_graph.add_nodes_from((new, nodes[old]) for (old, new) in updates.items())
        mutable_graph.add_edges_from((updates[o_src], updates[o_dst]) for (o_src, o_dst) in edges)

        return mutable_graph

    @classmethod
    def clean_nodes_attributes(cls, mutable_graph: nx.DiGraph) -> nx.DiGraph:
        """
        Removes all unwanted attributes from nodes.

        :authors: Morteza Rezaalipour, Marco Biasion
        """

        # delete node fields
        for (_, attrs) in mutable_graph.nodes(data=True):
            for field in cls._UNWANTED_FIELDS.intersection(attrs.keys()):
                attrs.pop(field)

        return mutable_graph

    @classmethod
    def _is_gate(cls, g: nx.DiGraph, n: str) -> bool:
        _attrs = g.nodes[n]
        return (
            _attrs.get('type', None) == 'gate'
            or (
                _attrs.get('shape', None) == 'record'
            )
        )

    @classmethod
    def _is_input(cls, g: nx.DiGraph, n: str) -> bool:
        _attrs = g.nodes[n]
        return (
            _attrs.get('type', None) == 'input'
            or (
                _attrs.get('shape', None) == 'octagon'
                and g.in_degree(n) == 0
            )
        )

    @classmethod
    def _is_output(cls, g: nx.DiGraph, n: str) -> bool:
        _attrs = g.nodes[n]
        return (
            _attrs.get('type', None) == 'output'
            or (
                g.nodes[n].get('shape', None) == 'octagon'
                # note: we do not use out_degree==0 as some circuit use output nodes as passthroughs
                and g.in_degree(n) == 1
            )
        )

    @classmethod
    def _is_constant(cls, g: nx.DiGraph, n: str) -> bool:
        _attrs = g.nodes[n]
        return (
            _attrs.get('type', None) == 'constant'
            or (
                _attrs.get('label') in cls._CONSTANT_MAPPING.keys()
            )
        )

    @classmethod
    def _is_wire(cls, g: nx.DiGraph, n: str) -> bool:
        return g.nodes[n].get('shape', None) == 'diamond'

    @classmethod
    def _is_buffer(cls, g: nx.DiGraph, n: str) -> bool:
        return g.nodes[n].get('shape', None) == 'box'

    @classmethod
    def _is_point(cls, g: nx.DiGraph, n: str) -> bool:
        return g.nodes[n].get('shape', None) == 'point'
