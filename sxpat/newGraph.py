from __future__ import annotations
from typing import ClassVar, Collection, Dict, FrozenSet, Iterable, List, Mapping, NoReturn, Tuple, Union

from collections import defaultdict
import dataclasses as dc

import networkx as nx
import functools as ft
import itertools as it
import re

# from utils.collections import InheritanceMapping
from sxpat.utils.collections import InheritanceMapping


# > precursors

@dc.dataclass(frozen=True)
class Node:
    name: str
    weight: int = None
    in_subgraph: bool = None
    SYMBOL: ClassVar[str] = 'MISSING'

    def copy(self, **update):
        return type(self)(**{**vars(self), **update})


# NodeOrName = Union[Node, str]


@dc.dataclass(frozen=True, repr=False)
class BoolNode(Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class IntNode(Node):
    pass


# @dc.dataclass(frozen=True)
# class OperationNode(Node):
#     _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = dict()
#     _items: Tuple[Node, ...] = tuple()

#     @ft.cached_property
#     def items(self) -> Tuple[str, ...]:
#         return tuple(item.name for item in self._items)

#     def __post_init__(self):
#         # freeze attributes
#         object.__setattr__(self, '_items', tuple(self._items))

#         # assert that all REQUIRED_CLASSES are respected
#         n = len(self._items)
#         covered_positions = set()
#         for pos, type in self._REQUIRED_CLASSES.items():
#             if pos is None:
#                 assert all(isinstance(item, type) for i, item in enumerate(self._items) if i not in covered_positions), f'Wrong item type in node {self.name} of class {self.__class__.__name__}'
#             else:
#                 covered_positions.add((n + pos) % n)
#                 assert isinstance(self._items[pos], type), f'Wrong item type(item {pos}) in node {self.name} of class {self.__class__.__name__}'

@dc.dataclass(frozen=True)
class OperationNode(Node):
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = dict()
    _items: Tuple[str, ...] = tuple()

    @property
    def items(self) -> Tuple[str, ...]:
        return self._items

    def __post_init__(self):
        object.__setattr__(self, '_items', tuple(self._items))


@dc.dataclass(frozen=True, repr=False)
class Op1Node(OperationNode):
    @property
    def item(self) -> str:
        return self._items[0]

    def __post_init__(self):
        super().__post_init__()
        assert len(self._items) == 1, f'Wrong items count (expected 1) in node {self.name} of class {self.__class__.__name__}'


@dc.dataclass(frozen=True, repr=False)
class Op2Node(OperationNode):
    def __post_init__(self):
        super().__post_init__()
        assert len(self._items) == 2, f'Wrong items count (expected 2) in node {self.name} of class {self.__class__.__name__}'

    @property
    def left(self) -> str:
        return self._items[0]

    @property
    def right(self) -> str:
        return self._items[1]


# > int

@dc.dataclass(frozen=True, repr=False)
class IntInput(IntNode):
    SYMBOL: ClassVar[str] = 'inI'


@dc.dataclass(frozen=True)
class IntConstant(IntNode):
    SYMBOL: ClassVar[str] = 'constI'
    value: int = 0


@dc.dataclass(frozen=True, repr=False)
class ToInt(IntNode, OperationNode):
    SYMBOL: ClassVar[str] = 'toInt'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: BoolNode}


@dc.dataclass(frozen=True, repr=False)
class Sum(IntNode, OperationNode):
    SYMBOL: ClassVar[str] = 'sum'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: IntNode}


@dc.dataclass(frozen=True, repr=False)
class AbsDiff(IntNode, Op2Node):
    SYMBOL: ClassVar[str] = 'absdiff'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: IntNode}

# > bool


@dc.dataclass(frozen=True, repr=False)
class BoolInput(BoolNode):
    SYMBOL: ClassVar[str] = 'inB'


@dc.dataclass(frozen=True)
class BoolConstant(BoolNode):
    SYMBOL: ClassVar[str] = 'constB'
    value: bool = False


@dc.dataclass(frozen=True, repr=False)
class Not(BoolNode, Op1Node):
    SYMBOL: ClassVar[str] = 'not'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: BoolNode}


@dc.dataclass(frozen=True, repr=False)
class And(BoolNode, OperationNode):
    SYMBOL: ClassVar[str] = 'and'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: BoolNode}


@dc.dataclass(frozen=True, repr=False)
class Or(BoolNode, OperationNode):
    SYMBOL: ClassVar[str] = 'or'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: BoolNode}


@dc.dataclass(frozen=True, repr=False)
class Implies(BoolNode, Op2Node):
    SYMBOL: ClassVar[str] = '=>'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: BoolNode}


@dc.dataclass(frozen=True, repr=False)
class Equals(BoolNode, Op2Node):
    SYMBOL: ClassVar[str] = '=='

    def __post_init__(self):
        super().__post_init__()
        # assert self._same_class(), f'The `left` and `right` items in node {self.name} of class {self.__class__.__name__} must be of the same type'

    # def _same_class(self) -> bool:
    #     return (
    #         (isinstance(self.left, IntNode) and isinstance(self.right, IntNode))
    #         or (isinstance(self.left, BoolNode) and isinstance(self.right, BoolNode))
    #     )


@dc.dataclass(frozen=True, repr=False)
class AtLeast(BoolNode, OperationNode):
    SYMBOL: ClassVar[str] = 'atleast'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {-1: IntConstant, None: BoolNode}

    @property
    def items(self) -> Tuple[str, ...]:
        return self._items[:-1]

    @property
    def value(self) -> str:
        return self._items[-1]


@dc.dataclass(frozen=True, repr=False)
class AtMost(BoolNode, OperationNode):
    SYMBOL: ClassVar[str] = 'atmost'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {-1: IntConstant, None: BoolNode}

    @property
    def items(self) -> Tuple[str, ...]:
        return self._items[:-1]

    @property
    def value(self) -> str:
        return self._items[-1]


@dc.dataclass(frozen=True, repr=False)
class LessThan(BoolNode, Op2Node):
    SYMBOL: ClassVar[str] = '<'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: IntNode}


@dc.dataclass(frozen=True, repr=False)
class LessEqualThan(BoolNode, Op2Node):
    SYMBOL: ClassVar[str] = '<='
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: IntNode}


@dc.dataclass(frozen=True, repr=False)
class GreaterThan(BoolNode, Op2Node):
    SYMBOL: ClassVar[str] = '>'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: IntNode}


@dc.dataclass(frozen=True, repr=False)
class GreaterEqualThan(BoolNode, Op2Node):
    SYMBOL: ClassVar[str] = '>='
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: IntNode}


@dc.dataclass(frozen=True, repr=False)
class Multiplexer(BoolNode, OperationNode):
    SYMBOL: ClassVar[str] = 'mux'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: BoolNode}

    def __post_init__(self):
        super().__post_init__()
        assert len(self._items) == 3, f'Wrong items count in node {self.name} of class {self.__class__.__name__}'

    @property
    def origin(self) -> str:
        return self._items[0]

    @property
    def parameter_1(self) -> str:
        return self._items[1]

    @property
    def parameter_2(self) -> str:
        return self._items[2]


@dc.dataclass(frozen=True, repr=False)
class Switch(BoolNode, Op2Node):
    SYMBOL: ClassVar[str] = 'switch'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {None: BoolNode}

    @property
    def origin(self) -> str:
        return self._items[0]

    @property
    def parameter(self) -> str:
        return self._items[1]

# > generic


@dc.dataclass(frozen=True, repr=False)
class If(OperationNode):
    SYMBOL: ClassVar[str] = 'if'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {0: BoolNode}

    def __post_init__(self):
        super().__post_init__()
        assert len(self._items) == 3, f'Wrong items count in node {self.name} of class {self.__class__.__name__}'
        # assert self._same_class(), f'The `if_true` and `if_false` items in node {self.name} of class {self.__class__.__name__} must be of the same type'

    # def _same_class(self) -> bool:
    #     return (
    #         (isinstance(self.if_true, IntNode) and isinstance(self.if_false, IntNode))
    #         or (isinstance(self.if_true, BoolConstant) and isinstance(self.if_false, BoolConstant))
    #     )

    @property
    def contition(self) -> str:
        return self._items[0]

    @property
    def if_true(self) -> str:
        return self._items[1]

    @property
    def if_false(self) -> str:
        return self._items[2]


@dc.dataclass(frozen=True, repr=False)
class Copy(Op1Node, BoolNode, IntNode):
    SYMBOL: ClassVar[str] = 'copy'


@dc.dataclass(frozen=True, repr=False)
class Placeholder(BoolNode, IntNode):
    pass


class Graph:
    """Immutable graph structure."""

    K = object()

    def __init__(self, nodes: Iterable[Node],
                 *, _inner: nx.DiGraph = None
                 ) -> None:
        # generate inner mutable structure
        if _inner is None:
            _inner = nx.DiGraph()
            _inner.add_nodes_from(
                (node.name, {self.K: node})
                for node in nodes
            )
            _inner.add_edges_from(
                (src_name, dst_name)
                for dst_name, data in _inner.nodes(data=True)
                if isinstance(node := data[self.K], OperationNode)
                for src_name in node._items
            )
        self._graph = nx.freeze(_inner)

    def __getitem__(self, key: str) -> Node:
        return self._graph.nodes[key][self.K]

    def __eq__(self, other: object) -> bool:
        return (
            type(self) == type(other)
            and set(self.nodes) == set(other.nodes)
        )

    # @staticmethod
    # def _get_name(node_or_name: NodeOrName) -> str:
    #     return node_or_name if isinstance(node_or_name, str) else node_or_name.name

    @ft.cached_property
    def nodes(self) -> Tuple[Node, ...]:
        return tuple(self._graph.nodes[name][self.K] for name in self._graph.nodes)

    def predecessors(self, node_name: str) -> Tuple[Node, ...]:
        node = self._graph.nodes[node_name][self.K]
        return tuple(sorted(
            (self._graph.nodes[_name][self.K] for _name in self._graph.predecessors(node_name)),
            key=lambda _n: node._items.index(_n.name)
        ))

    def successors(self, node_name: str) -> Tuple[OperationNode, ...]:
        return tuple(self._graph.nodes[_name][self.K] for _name in self._graph.successors(node_name))

    def to_nx_digraph(self, /,  mutable: bool = False) -> nx.DiGraph:
        # TODO: needed?
        return nx.DiGraph(self._graph) if mutable else self._graph


class GGraph(Graph):
    def __init__(self, nodes: Iterable[Node],
                 inputs_names: Iterable[str] = (), outputs_names: Iterable[str] = (),
                 *, _inner: nx.DiGraph = None,
                 ) -> None:
        # construct base
        super().__init__(nodes, _inner=_inner)

        # freeze local instances
        self.inputs_names = tuple(inputs_names)
        self.outputs_names = tuple(outputs_names)

    def __eq__(self, other: object) -> bool:
        return (
            super().__eq__(other)
            and self.inputs_names == other.inputs_names
            and self.outputs_names == other.outputs_names
        )

    @classmethod
    def from_Graph(cls, graph: Graph) -> GGraph:
        inputs_names = (node.name for node in graph.nodes if isinstance(node, BoolInput))
        outputs_names = (node.name for node in graph.nodes if isinstance(node, Copy))
        return cls(None, inputs_names, outputs_names, _inner=graph._graph)

    @ft.cached_property
    def inputs(self) -> Tuple[Node, ...]:
        return tuple(self._graph.nodes[name][self.K] for name in self.inputs_names)

    @ft.cached_property
    def outputs(self) -> Tuple[Node, ...]:
        return tuple(self._graph.nodes[name][self.K] for name in self.outputs_names)

    def with_prefix(self, prefix: str):
        """Returns a copy of the current graph with all nodes names (and items names) updated with the prefix (except the inputs)"""

        nodes = []
        for node in self.nodes:
            if node in self.inputs:
                nodes.append(node)
            elif isinstance(node, OperationNode):
                # TODO:HERE: _items should be given as Iterable[Nodes], fix this line or update to accept names
                # note: i think the fix here is better and cleaner
                items = (name if name in self.inputs_names else f'{prefix}{name}' for name in node._items)
                # todo: hereEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEe
                nodes.append(node.copy(name=f'{prefix}{node.name}', _items=items))
            else:
                nodes.append(node.copy(name=f'{prefix}{node.name}'))

        outputs_names = (f'{prefix}{name}' for name in self.outputs_names)

        print(*zip(self.nodes, nodes), sep='\n')
        # exit()
        return type(self)(nodes, self.inputs_names, outputs_names)


class SGraph(GGraph):
    @ft.cached_property
    def subgraph_nodes(self) -> Tuple[Node, ...]:
        return tuple(node for node in self.nodes if node.in_subgraph)

    @ft.cached_property
    def subgraph_inputs(self) -> Tuple[Node, ...]:
        # if a node is a subgraph input if it is not in the subgraph and any successor is in the subgraph
        return tuple(it.chain.from_iterable(
            (pred for pred in self.predecessors(node) if not pred.in_subgraph)
            for node in self.subgraph_nodes
        ))

    @ft.cached_property
    def subgraph_outputs(self) -> Tuple[Node, ...]:
        # if a subgraph node is a subgraph output if any successor is not in the subgraph
        return tuple(
            node
            for node in self.subgraph_nodes
            if any(not succ.in_subgraph for succ in self.successors(node))
        )


class TGraph(GGraph):
    def __init__(self, nodes: Iterable[Node],
                 inputs_names: Iterable[str] = (), outputs_names: Iterable[str] = (),
                 parameters_names: Iterable[str] = (),
                 ) -> None:

        super().__init__(nodes, inputs_names, outputs_names)

        # freeze local instances
        self.parameters_names = tuple(parameters_names)

    def __eq__(self, other: object) -> bool:
        return (
            super().__eq__(other)
            and self.parameters_names == other.parameters_names
        )

    @ft.cached_property
    def parameters(self) -> Tuple[Node, ...]:
        return tuple(self._graph.nodes[name][self.K] for name in self.parameters_names)


class CGraph(Graph):
    @staticmethod
    def is_placeholder(node: Node) -> bool:
        return isinstance(node, Placeholder)

    @ft.cached_property
    def placeholders(self) -> FrozenSet[Placeholder]:
        return frozenset(node for node in self.nodes if CGraph.is_placeholder(node))


class DotConverter:
    def __new__(cls) -> NoReturn:
        raise TypeError(f'Cannot create instances of class {cls.__name__}')

    @classmethod
    def load_file_clean(cls, filename: str) -> Graph:
        with open(filename, 'r') as f:
            string = f.read()
        return cls.from_string_clean(string)

    @classmethod
    def from_string_clean(cls, string: str) -> Graph:
        # get elements
        body = string.split('{')[1].split('}')[0]
        elements = [
            s.strip()
            for s in re.split(r'(?:;|\n)', body)
            if s
        ]

        # compile patterns and define mappings
        NODE_PATTERN = re.compile(r'^((?!node)\w+)\s*\[((?:\w+\s*=\s*[\w"\\n-]+,?\s*)*)\]$')
        NODE_SHAPE_PATTERN = re.compile(r'shape\s*=\s*(\w+)')
        NODE_FUNC_PATTERN = re.compile(r'label\s*=\s*"(in|out|TRUE|FALSE|not|and|or).*?"')
        NODE_SUBG_PATTERN = re.compile(r'subgraph\s*=\s*(\d)')
        NODE_COLOR_PATTERN = re.compile(r'fillcolor\s*=\s*([a-zA-Z]+)')  # legacy
        NODE_WEIGHT_PATTERN = re.compile(r'weight\s*=\s*([-\d]+)')
        EDGE_PATTERN = re.compile(r'^(\w+)\s*->\s*(\w+)$')
        SHAPE_FUNC_MAPPING = {
            'circle': {
                'in': BoolInput
            },
            'square': {
                'TRUE': ft.partial(BoolConstant, value=True),
                'FALSE': ft.partial(BoolConstant, value=False),
            },
            'invhouse': {
                'not': Not,
                'and': And,
                'or': Or,
            },
            'doublecircle': {
                'out': Copy
            },
        }
        COLOR_MAPPING = {
            'white': False,
            'olive': False,
            'red': True,
            'skyblue3': True,
        }

        # extract node and edge data from elements (keep order in file)
        raw_nodes: Dict[str, Union[Node, OperationNode]] = dict()
        raw_edges: Dict[str, List[str]] = defaultdict(list)  # {destination: sources}
        for el in elements:
            if m_node := NODE_PATTERN.match(el):
                # extract func (type)
                m_shape = NODE_SHAPE_PATTERN.search(el)
                m_func = NODE_FUNC_PATTERN.search(el)
                func = SHAPE_FUNC_MAPPING[m_shape[1]][m_func[1]]

                # extract weight if present
                weight = None
                if m_weight := NODE_WEIGHT_PATTERN.search(el):
                    weight = int(m_weight[1])

                # extract subgraph if present
                in_subgraph = None
                if m_subg := NODE_SUBG_PATTERN.search(el):
                    in_subgraph = bool(int(m_subg[1]))
                elif m_color := NODE_COLOR_PATTERN.search(el):
                    in_subgraph = COLOR_MAPPING[m_color[1]]

                raw_nodes[m_node[1]] = ft.partial(func, weight=weight, in_subgraph=in_subgraph)

            elif m_edge := EDGE_PATTERN.match(el):
                raw_edges[m_edge[2]].append(m_edge[1])

        # create nodes (Ω(n) if in topological order, O(n^2) otherwise)
        nodes: Dict[str, Union[Node, OperationNode]] = {}
        while nodes.keys() != raw_nodes.keys():
            for dst, func in raw_nodes.items():
                if dst in nodes.keys():  # already generated
                    continue

                preds = raw_edges[dst]
                if len(preds) == 0:  # input or constant node
                    nodes[dst] = func(dst)

                elif all(p in nodes.keys() for p in preds):  # operation node
                    nodes[dst] = func(dst, _items=(nodes[p].name for p in preds))

        # construct graph
        return Graph(nodes.values())

    @classmethod
    def save_file(cls, graph: Graph, filename: str) -> None:
        string = cls.to_string(graph)
        with open(filename, 'w') as f:
            f.write(string)

    @classmethod
    def to_string(cls, graph: Graph) -> str:
        SHAPE_MAPPING = InheritanceMapping({
            BoolInput: 'circle',
            BoolConstant: 'square',
            OperationNode: 'invhouse',
            Copy: 'doublecircle',
        })

        node_lines = []
        edge_lines = []
        for n in graph.nodes:
            weight_f, weight_l = '', ''
            if n.weight is not None:
                weight_f = f', weight={n.weight}'
                weight_l = rf'\nw={n.weight}'

            subgraph_f = ''
            fillcolor_f = ''
            if n.in_subgraph is not None:
                subgraph_f = f', in_subgraph={int(n.in_subgraph)}'
                fillcolor_f = ', fillcolor=red' if n.in_subgraph else ', fillcolor=white'

            items_f = ''
            symbol_l = n.SYMBOL
            if isinstance(n, OperationNode):
                items_s = ','.join(n._items)
                items_f = f', items="{items_s}"'
                symbol_l += f'({items_s})'

            # TODO:?: expand for subgraph
            node_lines.append(rf'    {n.name} [label="{symbol_l}\n{n.name}{weight_l}", shape={SHAPE_MAPPING[n.__class__]}{fillcolor_f}{weight_f}{subgraph_f}{items_f}];')
            if isinstance(n, OperationNode):
                edge_lines.extend(f'    {src_name} -> {n.name};' for src_name in n._items)

        return '\n'.join((
            'strict digraph GGraph {',
            '    node [style=filled, fillcolor=white];',
            *node_lines,
            *edge_lines,
            '}',
        ))


if __name__ == '__main__':

    g = DotConverter.load_file_clean('output/gv/adder_i8_o5_Sop1_encz3bvec_si6m0_i7m1.gv')
    DotConverter.save_file(g, 'output/gv/adder_i8_o5_Sop1_encz3bvec_si6m0_i7m1_2.gv')
    g = GGraph.from_Graph(g)

    f = g.with_prefix('zz_')
    DotConverter.save_file(f, 'output/gv/adder_i8_o5_Sop1_encz3bvec_si6m0_i7m1_3.gv')
