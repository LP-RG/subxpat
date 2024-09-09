from typing import ClassVar, Collection, Dict, Iterable, List, Mapping, NoReturn, Union
import dataclasses as dc
from collections import defaultdict

import networkx as nx
import functools as ft
import itertools as it
import re

from sxpat.utils.collections import InheritanceMapping


# > precursors

@dc.dataclass(frozen=True)
class Node:
    name: str
    weight: int
    in_subgraph: bool
    SYMBOL: ClassVar[str] = 'MISSING'

    def __post_init__(self) -> None:
        object.__setattr__(self, 'weight', int(self.weight))
        object.__setattr__(self, 'in_subgraph', bool(self.in_subgraph))

    def copy(self, **update):
        return type(self)(**{**vars(self), **update})


@dc.dataclass(frozen=True, repr=False)
class BoolNode(Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class IntNode(Node):
    pass


@dc.dataclass(frozen=True)
class OperationNode(Node):
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = dict()
    _items: Iterable[Node] = tuple()

    @property
    def items(self) -> Collection[str]:
        return self._items

    def __post_init__(self):
        # assert that all REQUIRED_CLASSES are respected
        n = len(self._items)
        items = tuple(self._items)
        covered_positions = set()
        for pos, type in self._REQUIRED_CLASSES.items():
            if pos is None:
                assert all(isinstance(item, type) for i, item in enumerate(items) if i not in covered_positions), f'Wrong item type in node {self.name} of class {self.__class__.__name__}'
            else:
                covered_positions.add((n + pos) % n)
                assert isinstance(items[pos], type), f'Wrong item type(item {pos}) in node {self.name} of class {self.__class__.__name__}'

        # store items names
        object.__setattr__(self, '_items', tuple(node.name for node in self._items))


@dc.dataclass(frozen=True, repr=False)
class Op1Node(OperationNode):
    @property
    def item(self) -> Node:
        return self._items[0]

    def __post_init__(self):
        super().__post_init__()
        assert len(self._items) == 1, f'Wrong item count (expected 1) in node {self.name} of class {self.__class__.__name__}'


@dc.dataclass(frozen=True, repr=False)
class Op2Node(OperationNode):
    def __post_init__(self):
        super().__post_init__()
        assert len(self._items) == 2, f'Wrong item count (expected 2) in node {self.name} of class {self.__class__.__name__}'

    @property
    def left(self) -> Node:
        return self._items[0]

    @property
    def right(self) -> Node:
        return self._items[1]


# > int

@dc.dataclass(frozen=True, repr=False)
class IntInput(IntNode):
    SYMBOL: ClassVar[str] = 'inI'


@dc.dataclass(frozen=True)
class IntConstant(IntNode):
    SYMBOL: ClassVar[str] = 'constI'
    value: int


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
    value: bool


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
        assert self._same_class(), f'The `left` and `right` items in node {self.name} of class {self.__class__.__name__} must be of the same type'

    def _same_class(self) -> bool:
        return (
            (isinstance(self.left, IntNode) and isinstance(self.right, IntNode))
            or (isinstance(self.left, BoolNode) and isinstance(self.right, BoolNode))
        )


@dc.dataclass(frozen=True, repr=False)
class AtLeast(BoolNode, OperationNode):
    SYMBOL: ClassVar[str] = 'atleast'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {-1: IntConstant, None: BoolNode}

    @property
    def items(self) -> Collection[Node]:
        return self._items[:-1]

    @property
    def value(self) -> IntConstant:
        return self._items[-1]


@dc.dataclass(frozen=True, repr=False)
class AtMost(BoolNode, OperationNode):
    SYMBOL: ClassVar[str] = 'atmost'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {-1: IntConstant, None: BoolNode}

    @property
    def items(self) -> Collection[Node]:
        return self._items[:-1]

    @property
    def value(self) -> IntConstant:
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
        assert len(self._items) == 3, f'Wrong item count in node {self.name} of class {self.__class__.__name__}'

    @property
    def origin(self) -> BoolNode:
        return self._items[0]

    @property
    def parameter_1(self) -> BoolNode:
        return self._items[1]

    @property
    def parameter_2(self) -> BoolNode:
        return self._items[2]


# > generic

@dc.dataclass(frozen=True, repr=False)
class If(OperationNode):
    SYMBOL: ClassVar[str] = 'if'
    _REQUIRED_CLASSES: ClassVar[Mapping[int, type]] = {0: BoolNode}

    def __post_init__(self):
        super().__post_init__()
        assert len(self._items) == 3, f'Wrong item count in node {self.name} of class {self.__class__.__name__}'
        assert self._same_class(), f'The `if_true` and `if_false` items in node {self.name} of class {self.__class__.__name__} must be of the same type'

    def _same_class(self) -> bool:
        return (
            (isinstance(self.if_true, IntNode) and isinstance(self.if_false, IntNode))
            or (isinstance(self.if_true, BoolConstant) and isinstance(self.if_false, BoolConstant))
        )

    @property
    def contition(self) -> BoolNode:
        return self._items[0]

    @property
    def if_true(self) -> Node:
        return self._items[1]

    @property
    def if_false(self) -> Node:
        return self._items[2]


@dc.dataclass(frozen=True, repr=False)
class Copy(Op1Node):
    SYMBOL: ClassVar[str] = 'copy'


class GGraph:
    """Immutable graph structure."""

    K = object()

    def __init__(self, nodes: Iterable[Node], /,
                 input_names: Iterable[str] = (), output_names: Iterable[str] = ()
                 ) -> None:
        # generate inner mutable structure
        self._graph = nx.DiGraph()
        self._graph.add_nodes_from(
            (node.name, {'type': type(node), **vars(node)})
            for node in nodes
        )
        self._graph.add_edges_from(
            (src_name, dst_name)
            for dst_name, data in self._graph.nodes(data=True)
            if isinstance(data[self.K], OperationNode)
            for src_name in data[self.K].items
        )

        # freeze local instances
        self._graph = nx.freeze(self._graph)
        self._input_names = tuple(input_names)
        self._output_names = tuple(output_names)

    def __getitem__(self, key: str) -> Node:
        return self._graph.nodes[key][self.K]

    def predecessors(self, node_or_name: Union[Node, str]) -> Collection[Node]:
        name = node_or_name if isinstance(node_or_name, str) else node_or_name.name
        return tuple(self._graph.nodes[_name][self.K] for _name in self._graph.predecessors(name))

    def successors(self, node_or_name: Union[Node, str]) -> Collection[Node]:
        name = node_or_name if isinstance(node_or_name, str) else node_or_name.name
        return tuple(self._graph.nodes[_name][self.K] for _name in self._graph.successors(name))

    @ft.cached_property
    def nodes(self) -> Collection[Node]:
        return tuple(self._graph.nodes[name][self.K] for name in self._graph.nodes)

    @ft.cached_property
    def inputs(self) -> Collection[Node]:
        return tuple(self._graph.nodes[name][self.K] for name in self._input_names)

    @ft.cached_property
    def outputs(self) -> Collection[Node]:
        return tuple(self._graph.nodes[name][self.K] for name in self._output_names)

    @ft.cached_property
    def subgraph_nodes(self) -> Collection[Node]:
        return tuple(node for node in self.nodes if node.in_subgraph)

    @ft.cached_property
    def subgraph_inputs(self) -> Collection[Node]:
        # if a node is a subgraph input if it is not in the subgraph and any successor is in the subgraph
        return tuple(it.chain.from_iterable(
            (pred for pred in self.predecessors(node) if not pred.in_subgraph)
            for node in self.subgraph_nodes
        ))

    @ft.cached_property
    def subgraph_outputs(self) -> Collection[Node]:
        # if a subgraph node is a subgraph output if any successor is not in the subgraph
        return tuple(
            node
            for node in self.subgraph_nodes
            if any(not succ.in_subgraph for succ in self.successors(node))
        )

    def to_nx_digraph(self, /,  mutable: bool = False) -> nx.DiGraph:
        return nx.DiGraph(self._graph) if mutable else self._graph


class DotManager:
    def __new__(cls) -> NoReturn:
        raise TypeError(f'Cannot create instances of class {cls.__name__}')

    @classmethod
    def load_file_clean(cls, filename: str) -> GGraph:
        with open(filename, 'r') as f:
            string = f.read()
        return cls.from_string_clean(string)

    @classmethod
    def from_string_clean(cls, string: str) -> GGraph:
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
        NODE_COLOR_PATTERN = re.compile(r'fillcolor\s*=\s*([[:alpha:]]+)')  # legacy
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
                    nodes[dst] = func(dst, _items=(nodes[p] for p in preds))

        # construct graph
        return GGraph(nodes.values())

    @classmethod
    def save_to_file(cls, graph: GGraph, filename: str) -> None:
        string = cls.to_string(graph)
        with open(filename, 'w') as f:
            f.write(string)

    @classmethod
    def to_string(cls, graph: GGraph) -> str:
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
                items_s = ','.join(i.name for i in n._items)
                items_f = f', items="{items_s}"'
                symbol_l += f'({items_s})'

            # TODO:?: expand for subgraph
            node_lines.append(rf'    {n.name} [label="{symbol_l}\n{n.name}{weight_l}", shape={SHAPE_MAPPING[n.__class__]}{fillcolor_f}{weight_f}{subgraph_f}{items_f}];')
            if isinstance(n, OperationNode):
                edge_lines.extend(f'    {src.name} -> {n.name};' for src in n._items)

        return '\n'.join((
            'strict digraph GGraph {',
            '    node [style=filled, fillcolor=white];',
            *node_lines,
            *edge_lines,
            '}',
        ))


if __name__ == '__main__':
    g = DotManager.load_file_clean('output/gv/adder_i8_o5_Sop1_encz3bvec_si6m0_i7m1.gv')
    DotManager.save_to_file(g, 'output/gv/adder_i8_o5_Sop1_encz3bvec_si6m0_i7m1_2.gv')
