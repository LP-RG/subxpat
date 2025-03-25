from abc import abstractmethod
from typing import Type, Callable, Mapping, NoReturn, Optional, Union, TypeVar, Generic
import dataclasses as dc

from bidict import bidict

import itertools as it
import re

from sxpat.graph import *
from sxpat.utils.inheritance import get_all_subclasses, get_all_leaves_subclasses
from sxpat.utils.functions import str_to_bool
from sxpat.utils.collections import MultiDict


__all__ = ['GraphImporter', 'GraphExporter',
           'DotPorter', 'JSONPorter', 'VerilogExporter']

T = TypeVar('T')


_G_CLSS = {c.__name__: c for c in get_all_subclasses(Graph)}
_N_CLSS = {c.__name__: c for c in get_all_leaves_subclasses(Node)}


class GraphImporter(Generic[T]):
    def __new__(cls) -> NoReturn:
        raise TypeError(f'Cannot create instances of class {cls.__name__}')

    @classmethod
    def from_string(cls, string: str) -> T:
        raise NotImplementedError(f'{cls.__name__}.from_string(...) is abstract.')

    @classmethod
    def from_file(cls, filename: str) -> T:
        with open(filename, 'r') as f:
            string = f.read()
        return cls.from_string(string)


class GraphExporter(Generic[T]):
    def __new__(cls) -> NoReturn:
        raise TypeError(f'Cannot create instances of class {cls.__name__}')

    @classmethod
    @abstractmethod
    def to_string(cls, graph: T) -> str:
        raise NotImplementedError(f'{cls.__name__}.to_string(...) is abstract.')

    @classmethod
    def to_file(cls, graph: T, filename: str) -> None:
        string = cls.to_string(graph)
        with open(filename, 'w') as f:
            f.write(string)


class DotPorter(GraphImporter[Graph], GraphExporter[Graph]):
    NODE_SYMBOL = bidict({
        # inputs
        BoolVariable: 'varB',
        IntVariable:  'varI',
        # constants
        BoolConstant: 'constB',
        IntConstant:  'constI',
        # output
        Copy: 'copy',
        Target: 'target',
        # placeholder
        PlaceHolder: 'holder',
        # bool operations
        Not:     'not',
        And:     'and',
        Or:      'or',
        Implies: 'impl',
        # int operations
        ToInt:   'toInt',
        Sum:     'sum',
        AbsDiff: 'absdiff',
        # comparison operations
        Equals:           '==',
        AtLeast:          'atleast',
        AtMost:           'atmost',
        LessThan:         '<',
        LessEqualThan:    '<=',
        GreaterThan:      '>',
        GreaterEqualThan: '>=',
        # branching operations
        Multiplexer: 'mux',
        If:          'if',
    })
    NODE_SHAPE = MultiDict({
        # inputs
        (BoolVariable, IntVariable): 'circle',
        # constants
        (BoolConstant, IntConstant): 'square',
        # output
        (Copy,): 'doublecircle',
        # target
        (Target,): 'star',
        # placeholder
        (PlaceHolder,): 'octagon',
        # bool operations
        (Not, And, Or, Implies): 'invhouse',
        # int operations
        (ToInt, Sum, AbsDiff): 'invtrapezium',
        # comparison operations
        (Equals, AtLeast, AtMost, LessThan,
         LessEqualThan, GreaterThan, GreaterEqualThan): 'invtriangle',
        # branching operations
        (Multiplexer, If): 'diamond',
    })
    NODE_COLOR: Mapping[Type[Graph], Callable[[Graph, Node], Optional[str]]] = {
        Graph: lambda g, n: 'red' if n.in_subgraph else 'white',
        IOGraph: lambda g, n: 'red' if n.in_subgraph else 'white',
        CGraph: lambda g, n: 'red' if n.in_subgraph else 'white',
        SGraph: lambda g, n: 'olive' if n in g.subgraph_inputs else 'skyblue3' if n in g.subgraph_outputs else 'red' if n.in_subgraph else 'white',
        PGraph: lambda g, n: 'olive' if n in g.subgraph_inputs else 'skyblue3' if n in g.subgraph_outputs else 'red' if n.in_subgraph else 'white',
    }

    GRAPH_PATTERN = re.compile(r'strict digraph _(\w+) {(?:\n\s*node \[.*\];)?((?:\n\s*\w+ \[.*\];)+)(?:\n\s*\w+ -> \w+;)+((?:\n\s*\/\/ \w+.*)*)\n}')
    NODE_PATTERN = re.compile(r'\w+ \[label="(.*)".*\]')
    EXTRA_PATTERN = re.compile(r'\/\/ (\w+)\[([\w,]+)\]')

    @classmethod
    def _get_label(cls, node: Node) -> str:
        # base informations
        string = rf'{cls.NODE_SYMBOL[type(node)]}\n{node.name}'

        # extra informations
        if node.weight is not None:
            string += rf'\nw={node.weight}'
        if node.in_subgraph:
            string += rf'\nsub'
        if isinstance(node, OperationNode):
            string += rf'\ni={",".join(node.items)}'
        if isinstance(node, Valued):
            string += rf'\nv={node.value}'

        return string

    @classmethod
    def _parse_label(cls, string: str) -> Node:
        # match label informations
        m = re.match(
            (
                rf'({"|".join(cls.NODE_SYMBOL.inverse)})'  # class
                rf'\\n(\w+)'  # name
                rf'(?:\\nw=([-+]?\d+))?'  # weight
                rf'(?:\\n(sub))?'  # in_subgraph
                rf'(?:\\nv=(?:([-+]?\d+)|(True|False)))?'  # value
                rf'(?:\\ni=(\w+(?:,\w+)*))?'  # items
            ),
            string
        )

        # get type and extract arguments
        type = cls.NODE_SYMBOL.inverse[m[1]]
        arguments = {
            'name': m[2],
            'weight': m[3] and int(m[3]),
            'in_subgraph': bool(m[4]),
            'value': (m[5] and int(m[5])) or (m[6] and str_to_bool(m[6])),
            'items': m[7] and m[7].split(','),
        }

        # create Node using valid arguments
        return type(**{k: v for k, v in arguments.items() if v is not None})

    @classmethod
    def from_string(cls, string: str) -> Graph:
        match = cls.GRAPH_PATTERN.match(string)
        _type = _G_CLSS[match[1]]
        _nodes = [
            cls._parse_label(cls.NODE_PATTERN.search(l)[1])
            for l in match[2].split('\n')
            if l
        ]
        _extra = {
            (m := cls.EXTRA_PATTERN.search(l))[1]: m[2].split(',')
            for l in (match[3].split('\n') if match[3] else ())
            if l
        }

        return _type(_nodes, **_extra)

    @classmethod
    def to_string(cls, graph: Graph) -> str:
        # base data
        node_lines = [
            f'{node.name} [label="{cls._get_label(node)}", shape={cls.NODE_SHAPE[type(node)]}, fillcolor={cls.NODE_COLOR[type(graph)](graph, node)}];'
            for node in graph.nodes
        ]
        edge_lines = [
            f'{src_name} -> {dst.name};'
            for dst in graph.nodes
            if isinstance(dst, OperationNode)
            for src_name in dst.items
        ]

        # extra data
        extra_lines = []
        if isinstance(graph, IOGraph):
            extra_lines.append(f'// inputs_names[{",".join(graph.inputs_names)}]')
            extra_lines.append(f'// outputs_names[{",".join(graph.outputs_names)}]')
        if isinstance(graph, PGraph):
            extra_lines.append(f'// parameters_names[{",".join(graph.parameters_names)}]')

        return '\n'.join(it.chain(
            (f'strict digraph _{type(graph).__name__} {{',),
            (f'    node [style=filled];',),
            (f'    {l}' for l in node_lines),
            (f'    {l}' for l in edge_lines),
            (f'    {l}' for l in extra_lines),
            ('}',),
        ))

    # @classmethod
    # def load_file_clean(cls, filename: str) -> Graph:
    #     with open(filename, 'r') as f:
    #         string = f.read()
    #     return cls.from_string_clean(string)

    # @classmethod
    # def from_string_clean(cls, string: str) -> Graph:
    #     # get elements
    #     body = string.split('{')[1].split('}')[0]
    #     elements = [
    #         s.strip()
    #         for s in re.split(r'(?:;|\n)', body)
    #         if s
    #     ]

    #     # compile patterns and define mappings
    #     NODE_PATTERN = re.compile(r'^((?!node)\w+)\s*\[((?:\w+\s*=\s*[\w"\\n-]+,?\s*)*)\]$')
    #     NODE_SHAPE_PATTERN = re.compile(r'shape\s*=\s*(\w+)')
    #     NODE_FUNC_PATTERN = re.compile(r'label\s*=\s*"(in|out|TRUE|FALSE|not|and|or).*?"')
    #     NODE_SUBG_PATTERN = re.compile(r'subgraph\s*=\s*(\d)')
    #     NODE_COLOR_PATTERN = re.compile(r'fillcolor\s*=\s*([a-zA-Z]+)')  # legacy
    #     NODE_WEIGHT_PATTERN = re.compile(r'weight\s*=\s*([-\d]+)')
    #     EDGE_PATTERN = re.compile(r'^(\w+)\s*->\s*(\w+)$')
    #     SHAPE_FUNC_MAPPING = {
    #         'circle': {
    #             'in': BoolVariable
    #         },
    #         'square': {
    #             'TRUE': ft.partial(BoolConstant, value=True),
    #             'FALSE': ft.partial(BoolConstant, value=False),
    #         },
    #         'invhouse': {
    #             'not': Not,
    #             'and': And,
    #             'or': Or,
    #         },
    #         'doublecircle': {
    #             'out': Copy
    #         },
    #     }
    #     COLOR_MAPPING = {
    #         'white': False,
    #         'olive': False,
    #         'red': True,
    #         'skyblue3': True,
    #     }

    #     # extract node and edge data from elements (keep order in file)
    #     raw_nodes: Dict[str, Union[Node, OperationNode]] = dict()
    #     raw_edges: Dict[str, List[str]] = defaultdict(list)  # {destination: sources}
    #     for el in elements:
    #         if m_node := NODE_PATTERN.match(el):
    #             # extract func (type)
    #             m_shape = NODE_SHAPE_PATTERN.search(el)
    #             m_func = NODE_FUNC_PATTERN.search(el)
    #             func = SHAPE_FUNC_MAPPING[m_shape[1]][m_func[1]]

    #             # extract weight if present
    #             weight = None
    #             if m_weight := NODE_WEIGHT_PATTERN.search(el):
    #                 weight = int(m_weight[1])

    #             # extract subgraph if present
    #             in_subgraph = False
    #             if m_subg := NODE_SUBG_PATTERN.search(el):
    #                 in_subgraph = bool(int(m_subg[1]))
    #             elif m_color := NODE_COLOR_PATTERN.search(el):
    #                 in_subgraph = COLOR_MAPPING[m_color[1]]

    #             raw_nodes[m_node[1]] = ft.partial(func, weight=weight, in_subgraph=in_subgraph)

    #         elif m_edge := EDGE_PATTERN.match(el):
    #             raw_edges[m_edge[2]].append(m_edge[1])

    #     # create nodes (Ω(n) if in topological order, O(n^2) otherwise)
    #     nodes: Dict[str, Union[Node, OperationNode]] = {}
    #     while nodes.keys() != raw_nodes.keys():
    #         for dst, func in raw_nodes.items():
    #             if dst in nodes.keys():  # already generated
    #                 continue

    #             preds = raw_edges[dst]
    #             if len(preds) == 0:  # input or constant node
    #                 nodes[dst] = func(dst)

    #             elif all(p in nodes.keys() for p in preds):  # operation node
    #                 nodes[dst] = func(dst, items=(nodes[p].name for p in preds))

    #     # construct graph
    #     return Graph(nodes.values())


class JSONPorter(GraphImporter[Graph], GraphExporter[Graph]):
    import json

    _CLASS_F = 'class'
    _NODES_F = 'nodes'
    _EXTRA_F = 'extra'

    @classmethod
    def _dict_factory(cls, obj: object) -> dict:
        return {cls._CLASS_F: obj.__class__.__name__, **vars(obj)}

    @classmethod
    def _node_factory(cls, dct: dict) -> Node:
        return _N_CLSS[dct.pop(cls._CLASS_F)](**dct)

    @classmethod
    def from_string(cls, string: str) -> Graph:
        _g: dict = cls.json.loads(string)
        nodes = [cls._node_factory(n) for n in _g.pop(cls._NODES_F)]
        return _G_CLSS[_g.pop(cls._CLASS_F)](nodes=nodes, **_g.pop(cls._EXTRA_F))

    @classmethod
    def to_string(cls, graph: Graph) -> str:
        _g = {
            cls._CLASS_F: graph.__class__.__name__,
            cls._NODES_F: [cls._dict_factory(node) for node in graph.nodes],
            cls._EXTRA_F: {extra_name: getattr(graph, extra_name) for extra_name in graph.EXTRA},
        }
        return cls.json.dumps(_g, indent=4)


class VerilogExporter(GraphExporter[IOGraph]):
    NODE_EXPORT: Mapping[Type[Node], Callable[[Union[Node, OperationNode, Valued]], str]] = {
        # variables
        # BoolVariable: lambda n: None,
        # IntVariable: lambda n: None,
        # constants
        BoolConstant: lambda n: f'1\'b{int(n.value)}',
        # IntConstant: lambda n: f'({n.value')',
        # output
        Copy: lambda n: n.item,
        # Target: lambda n: None,
        # bool-bool operations
        Not: lambda n: f'(~{n.item})',
        And: lambda n: f'({" & ".join(n.items)})',
        Or: lambda n: f'({" | ".join(n.items)})',
        Implies: lambda n: f'(~{n.left} | {n.right})',
        # int-int operations
        Sum: lambda n: f'({" + ".join(n.items)})',
        AbsDiff: lambda n: f'(({n.left} > {n.right}) ? ({n.left} - {n.right}) : ({n.right} - {n.left}))',
        # bool-int operations
        # ToInt: lambda n: None,
        # int-bool operations
        Equals: lambda n: f'({n.left} === {n.right})',
        LessThan: lambda n: f'({n.left} < {n.right})',
        LessEqualThan: lambda n: f'({n.left} <= {n.right})',
        GreaterThan: lambda n: f'({n.left} > {n.right})',
        GreaterEqualThan: lambda n: f'({n.left} >= {n.right})',
        # quantifier operations
        # AtLeast: lambda n: None,
        # AtMost: lambda n: None,
        # branching operations
        Multiplexer: lambda n: f'({n.parameter_usage} ? ({n.parameter_assertion} ? {n.origin} : ~{n.origin}) : {n.parameter_assertion})',
        If: lambda n: f'({n.contition} ? {n.if_true} : {n.if_false})',
    }

    @dc.dataclass(frozen=True, eq=False)
    class VerilogInfo:
        graph_name: str
        model_number: int

    @classmethod
    def to_string(cls, graph: IOGraph, info: VerilogInfo = None) -> str:
        info = info or cls.VerilogInfo('graph', -1)

        return '\n'.join(filter(bool, (
            f'/* model {info.model_number} */' if info.model_number >= 0 else None,
            f'module {info.graph_name} ({", ".join((*graph.inputs_names, *graph.outputs_names))});',
            # declarations
            f'input {", ".join(graph.inputs_names)};',
            f'output {", ".join(graph.outputs_names)};',
            f'wire {", ".join(n.name for n in graph.inners)};',
            # assignments
            * (
                f'assign {node.name} = {cls.NODE_EXPORT[type(node)](node)};'
                for node in graph.nodes
                if node.name not in graph.inputs_names
            ),
            'endmodule',
        )))
