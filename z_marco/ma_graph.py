# typing
from __future__ import annotations
from typing import Any, Dict, FrozenSet, Iterable, List, Literal, Mapping, Optional, Sequence, Set, Tuple, Union
from enum import Enum
import dataclasses as dc

# utilities
from functools import cached_property, lru_cache
from itertools import chain, islice
import re

# network utilities
import networkx as nx
import networkx.drawing as nx_draw

from Z3Log.graph import Graph
from sxpat.annotatedGraph import AnnotatedGraph

from z_marco.utils import static, static


# class Operation(Enum):
#     OR = 'or'
#     NOT = 'not'
#     AND = 'and'
#     INPUT = 'input'
#     OUTPUT = 'output'
#     CONST0 = 'wip_0'
#     CONST1 = 'wip_1'


# @dc.dataclass
# class MaNode:
#     name: str
#     operation: Operation

#     def to_gv_line(self) ->str:
#         shape = {
#             Operation.OR: 'invhouse',
#             Operation.NOT: 'invhouse',
#             Operation.AND: 'invhouse',
#             Operation.INPUT: 'circle',
#             Operation.OUTPUT: 'doublecircle',
#             Operation.CONST0: 'star',
#             Operation.CONST1: 'star',
#         }
#         label = {

#         }
ALIAS_PREFIX = 'ref'


@dc.dataclass(frozen=True)
class MaGraph:

    class NodeType(Enum):
        INPUT = 0
        GATE = 1
        CONSTANT = 2
        OUTPUT = 3
    # TODO: this class is a subclass of Graph?, but does not really fit in the inheritance,
    # TODO: in the future should be refactored to behave like the parents, or made its own class

    inputs: Sequence[str]
    gates: Sequence[str]
    outputs: Sequence[str]
    constants: Sequence[Tuple[str, bool]]
    _info: Mapping[str, Mapping[str, Any]]
    edges: Sequence[Tuple[str, str]]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'inputs', tuple(self.inputs))
        object.__setattr__(self, 'gates', tuple(self.gates))
        object.__setattr__(self, 'outputs', tuple(self.outputs))
        object.__setattr__(self, 'constants', tuple((name, value) for name, value in self.constants))
        object.__setattr__(self, '_info', {name: dict(data) for name, data in self._info.items()})
        object.__setattr__(self, 'edges', tuple((src, dst) for src, dst in self.edges))

    @classmethod
    def from_gv(cls, gv_path: str) -> MaGraph:
        return cls.from_digraph(
            nx.drawing.nx_agraph.read_dot(gv_path)
        )

    @classmethod
    def from_digraph(cls, digraph: nx.DiGraph, *, sort_inputs: bool = True, sort_outputs: bool = True) -> MaGraph:
        inputs = tuple(
            name
            for name, data in digraph.nodes(data=True)
            if data["shape"] == "circle"
        )
        if sort_inputs:
            inputs = tuple(sorted(inputs, key=lambda s: int(re.sub("[^0-9]", "", s))))

        gates = tuple(
            name
            for name, data in digraph.nodes(data=True)
            if data["shape"] == "invhouse"
        )

        const_map = {'TRUE': True, 'FALSE': False}
        constants = tuple(
            (name, const_map[data['label']])
            for name, data in digraph.nodes(data=True)
            if data["shape"] == "square"
        )

        outputs = tuple(
            name
            for name, data in digraph.nodes(data=True)
            if data["shape"] == "doublecircle"
        )
        if sort_outputs:
            outputs = tuple(sorted(outputs, key=lambda s: int(re.sub("[^0-9]", "", s))))

        _functions = {'not', 'and', 'or'}
        info = {name: dict() for name in digraph.nodes}
        for node_name, data in info.items():
            data['function'] = next((
                part.strip()
                for part in digraph.nodes[node_name]["label"].split("\\n")
                if part in _functions
            ), None)

        edges = digraph.edges

        return cls(inputs, gates, outputs, constants, info, edges)
        # return cls(inputs, gates, outputs, [], info, edges)

    def successors(self, node_name: str) -> Tuple[str]:
        # used only in insert_subgraph
        return tuple(
            dst
            for src, dst in self.edges
            if src == node_name
        )

    def predecessors(self, node_name: str) -> Tuple[str]:
        # used in phase1_creator and xpat_creator_function
        return tuple(
            src
            for src, dst in self.edges
            if dst == node_name
        )

    @property
    def unaliased_outputs(self) -> Sequence[str]:
        # used in insert_subgraph
        if not all(n.startswith(f'{ALIAS_PREFIX}_') for n in self.outputs):
            raise RuntimeError('trying to unaliasing not alias')

        return tuple(n[len(ALIAS_PREFIX)+1:] for n in self.outputs)

    def function_of(self, node_name: str) -> Optional[str]:
        # used in xpat_creator_function
        return self._info[node_name]['function']


def draw_gv(graph: MaGraph, path: str) -> None:
    nx_graph = nx.DiGraph()
    nx_graph.add_nodes_from(((n, {'shape': 'circle'}) for n in graph.inputs))
    nx_graph.add_nodes_from(((n, {'shape': 'doublecircle'}) for n in graph.outputs))
    nx_graph.add_nodes_from(((n, {'shape': 'pentagon', 'label': f"{n}\\n{v}"}) for n, v in graph.constants))
    nx_graph.add_nodes_from(((n, {'shape': 'invhouse', 'label': f"{n}\\n{graph.function_of(n)}"}) for n in graph.gates))
    nx_graph.add_edges_from(graph.edges)
    nx.nx_agraph.write_dot(nx_graph, path)


def outputs_reordered(original: MaGraph, outputs: Sequence[str]) -> MaGraph:
    if set(original.outputs) != set(outputs):
        raise RuntimeError("Invalid outputs for the given graph.")

    return MaGraph(
        original.inputs,
        original.gates,
        outputs,
        original.constants,
        original._info,
        original.edges
    )

    # # incrementally finds the longest common prefix
    # prefix = ""
    # valid = True
    # while valid:
    #     prefix_candidate = graph.outputs[0][:len(prefix)+1]
    #     for name in graph.outputs[1:]:
    #         if not name.startswith(prefix_candidate):
    #             valid = False
    #             break
    #     prefix = prefix_candidate


def xpat_model_to_magraph(model: Dict[str, bool], *, iter_id: int = 1) -> MaGraph:
    """The resulting MaGraph will have nodes in topological order"""

    # equivalent to c++ static
    @static(numbering={t: 0 for t in ['not', 'and', 'or', 'const']})
    def define_node(node_type: str) -> str:
        assert node_type in define_node.numbering

        define_node.numbering[node_type] += 1
        return f'{node_type}_{iter_id}_{define_node.numbering[node_type]-1}'

    def define_tree(tree_parameters: Dict[str, Dict[str, bool]]
                    ) -> Tuple[str, List[str], List[Tuple[str, str]], List[Tuple[str, bool]]]:
        # returns the root of the tree and the needed gates, edges, constants

        gates = []
        edges = []

        input_literals = []
        for in_name, in_parameters in tree_parameters.items():
            if in_parameters['s']:
                if not in_parameters['l']:
                    # negation
                    pred = define_node('not')
                    gates.append(pred)
                    edges.append((in_name, pred))
                else:
                    pred = in_name
                input_literals.append(pred)

        if len(input_literals) == 0:
            const = define_node('const')
            return const, [], [], [(const, True)]

        else:
            # generate and gate(s)
            last = input_literals[0]
            for in_lit in input_literals[1:]:
                and_gate = define_node('and')
                gates.append(and_gate)
                edges.append((last, and_gate))
                edges.append((in_lit, and_gate))
                last = and_gate
            return last, gates, edges, []

    def define_output(output_parameters: Dict[int, Dict[str, Dict[str, bool]]]
                      ) -> Tuple[str, List[str], List[Tuple[str, str]], List[Tuple[str, bool]]]:
        # returns the root of the output and the needed gates, edges, constants

        gates = []
        edges = []

        # define trees, every tree is a product (AND) of inputs or NOT inputs
        trees_roots = []
        for tree_i, tree_parameters in output_parameters.items():
            root, _gates, _edges, _constants = define_tree(tree_parameters)
            if len(_constants) > 0:
                # product is constant 1, return constant 1
                return root, [], [], _constants

            else:
                trees_roots.append(root)
                gates.extend(_gates)
                edges.extend(_edges)

        # generate OR gate(s)
        last = trees_roots[0]
        for root in trees_roots[1:]:
            or_gate = define_node('or')
            gates.append(or_gate)
            edges.append((last, or_gate))
            edges.append((root, or_gate))
            last = or_gate
        return last, gates, edges, []

    output_parameter_pattern = r'^p_(.+)$'
    leaf_parameter_pattern = r'^p_(.+)_t(\d+)_(.+)_(l|s)$'
    output_parameters = dict()
    leaf_parameters = dict()

    inputs = set()
    outputs = set()
    gates = list()
    constants = list()
    edges = list()

    # extract parameters, inputs and outputs
    for k, v in model.items():
        if match := re.match(leaf_parameter_pattern, k):
            # store parameter
            leaf_parameters.setdefault(
                match[1], dict()
            ).setdefault(
                int(match[2]), dict()
            ).setdefault(
                match[3], dict()
            )[match[4]] = v
            # store input and output
            inputs.add(match[3])
            outputs.add(match[1])
            continue

        if match := re.match(output_parameter_pattern, k):
            # store parameter
            output_parameters[match[1]] = v
            # store output
            outputs.add(match[1])

    # define template graph
    for out_name, used in output_parameters.items():
        if used:
            # define output (includes all trees and leaves)
            _root, _gates, _edges, _constants = define_output(leaf_parameters[out_name])
            # store generated items
            gates.extend(_gates)
            constants.extend(_constants)
            edges.extend(_edges)
            # add edge from output_product to output
            edges.append((_root, out_name))

        else:
            # output is constant 0
            constant = (define_node('const'), False)
            constants.append(constant)
            edges.append((constant[0], out_name))

    # define data of new gates
    info = dict()
    for gate_name in gates:
        if gate_name.startswith('or_'):
            info[gate_name] = {'function': 'or'}
        elif gate_name.startswith('and_'):
            info[gate_name] = {'function': 'and'}
        elif gate_name.startswith('not_'):
            info[gate_name] = {'function': 'not'}
        else:
            raise RuntimeError('Invalid gate name.')

    return MaGraph(inputs, gates, outputs, constants, info, edges)


def extract_subgraph(graph: AnnotatedGraph) -> MaGraph:
    gg: nx.DiGraph = graph.graph
    new_graph = nx.DiGraph()

    # add inputs
    inputs = [
        # (name, {**gg.nodes[name], "shape": "circle", "label": ""})
        (name, {**gg.nodes[name], "shape": "circle", "label": name})
        for name in graph.subgraph_input_dict.values()
    ]
    new_graph.add_nodes_from(inputs)

    # add inner gates
    gates = [
        (name, {**gg.nodes[name], "label": f"{name}\\n{gg.nodes[name]['label']}"})
        # (name, {**gg.nodes[name]})
        for name in graph.subgraph_gate_dict.values()
    ]
    new_graph.add_nodes_from(gates)

    # add outputs
    outputs_names = list(graph.subgraph_output_dict.values())
    new_graph.add_nodes_from(
        (f"{ALIAS_PREFIX}_{name}", {"label": f"{ALIAS_PREFIX}_{name}", "shape": "doublecircle"})
        for name in outputs_names
    )

    # add subgraph edges (destination being in the subgraph)
    subgraph_gates = set(graph.subgraph_gate_dict.values())
    for src, dst in gg.edges:
        if dst in subgraph_gates:
            new_graph.add_edge(src, dst)
    # add output edges (output to ref_output)
    for out_name in outputs_names:
        new_graph.add_edge(out_name, f"{ALIAS_PREFIX}_{out_name}")

    return MaGraph.from_digraph(new_graph)


def insert_subgraph(full_graph: MaGraph, sub_graph: MaGraph) -> MaGraph:
    gates = list(full_graph.gates)
    edges = list(full_graph.edges)
    constants = list(chain(full_graph.constants, sub_graph.constants))
    info = dict(chain(full_graph._info.items(), sub_graph._info.items()))

    # remove edges and gates of the full_graph where the sub_graph should be
    # we start from the subgraph outputs and iterate back, stopping at the subgraph inputs
    discarded_dst = list(sub_graph.unaliased_outputs)
    for d_dst in discarded_dst:
        for src, dst in edges[:]:
            # edge ends on a destination to discard
            if dst == d_dst:
                # remove edge
                edges.remove((src, dst))

                # if src is not a subgraph_inputs (it is an inner gate)
                if src not in sub_graph.inputs and src not in discarded_dst:
                    discarded_dst.append(src)
                    gates.remove(src)

    # add inner edges of the subgraph
    for src, dst in sub_graph.edges:
        if dst not in sub_graph.outputs:
            edges.append((src, dst))
    # add inner gates of the subgraph
    gates.extend(sub_graph.gates)
    # remove sub_output gates
    for sub_out in sub_graph.unaliased_outputs:
        gates.remove(sub_out)

    # replaces edges out->succs with out.pred->succs
    for sub_out, full_out in zip(sub_graph.outputs, sub_graph.unaliased_outputs):
        print(sub_out, full_out)
        sub_pred = sub_graph.predecessors(sub_out)[0]
        full_succs = full_graph.successors(full_out)
        provina = [n for n in full_succs if n not in gates]
        if len(provina) > 0:
            print(sub_pred, full_succs, provina)
            raise RuntimeError("MISSING NODE, BUG FOUND <><><><><><><><><><><><><><>")

        for suc in full_succs:
            i = edges.index((full_out, suc))
            edges[i] = (sub_pred, suc)

    # reorder gates and edges in topological order
    nx_graph = nx.DiGraph()
    nx_graph.add_nodes_from(chain(full_graph.inputs, gates, full_graph.outputs, constants))
    nx_graph.add_edges_from(edges)
    # gates
    topological_nodes = nx.topological_sort(nx_graph)
    gates = [n for n in topological_nodes if n in gates]
    # edges
    edges = list(nx.topological_sort(nx.line_graph(nx_graph)))

    return MaGraph(
        full_graph.inputs,
        gates,
        full_graph.outputs,
        constants,
        info,
        edges
    )
