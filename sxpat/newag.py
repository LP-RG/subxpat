from typing import ClassVar

from sxpat.graph.graph import SGraph
from sxpat.graph.node import And, BoolConstant, Extras, Node, Not
from sxpat.specifications import Paths

from sxpat.utils.filesystem import FS
from os.path import join as path_join

from sxpat.utils.names import extract_name
from sxpat.utils.formats.dot import load_yosys_dot
from sxpat.utils.formats.verilog import synthesize_verilog_to_notand_gate_level, convert_verilog_to_dot
from sxpat.converting.legacy import iograph_from_digraph


def load_circuit_from_yosysdot(circuit_dot_path: str):
    # load the Yosys dot
    digraph = load_yosys_dot(circuit_dot_path)

    # convert to iograph
    return iograph_from_digraph(digraph)


def load_circuit_from_notand_verilog(circuit_verilog_path: str, run_paths: Paths.RunFiles):
    circuit_name = extract_name(circuit_verilog_path)

    # convert the not-and gate level Verilog into a Yosys dot
    convert_verilog_to_dot(
        circuit_verilog_path,
        tmp_gv := path_join(run_paths.temporary, f'{circuit_name}.dot'),
        run_paths.temporary,
    )

    #
    return load_circuit_from_yosysdot(tmp_gv)


def load_circuit_from_verilog(circuit_verilog_path: str, run_paths: Paths.RunFiles):
    circuit_name = extract_name(circuit_verilog_path)

    # prepare a not-and gate level Verilog
    synthesize_verilog_to_notand_gate_level(
        circuit_verilog_path,
        tmp_v := path_join(run_paths.temporary, f'{circuit_name}.v'),
    )

    #
    return load_circuit_from_notand_verilog(tmp_v, run_paths)


class _Node(Node, Extras): ...


class export_annotated_graph:
    """
    exports the graph (annotated with a subgraph) in the GraphViz (.dot/.gv) format.

    :authors: Marco Biasion, Morteza Rezaalipour
    """

    DOT_BASE: ClassVar = '\n'.join((
        'strict digraph "" {{',
        'node [colorscheme=set13, style=filled, fillcolor=white, shape=invhouse];',
        '{nodes}',
        '',
        'edge [colorscheme=set13, dir=both, arrowtail=inv];',
        '{edges}',
        '}}',
    ))

    def __new__(cls, circuit: SGraph, path: str):
        inputs = frozenset(circuit.inputs_names)
        outputs = frozenset(circuit.outputs_names)
        subgraph_inputs = frozenset(_n.name for _n in circuit.subgraph_inputs)
        subgraph_outputs = frozenset(_n.name for _n in circuit.subgraph_outputs)
        subgraph_nodes = frozenset(_n.name for _n in circuit.subgraph_nodes)
        edge_color = {
            # s, d
            (False, True): 3,
            (True, False): 2,
            (True, True): 1,
        }

        def _node_tostr(n: _Node):
            name = n.name
            fillcolor_str = 3 if name in subgraph_inputs else \
                2 if name in subgraph_outputs else \
                1 if isinstance(n, Extras) and n.in_subgraph else ''
            if fillcolor_str != '': fillcolor_str = f', fillcolor={fillcolor_str}'
            weight_str = f'\\n{n.weight}' if Extras.has_weight(n) else ''

            if name in inputs:
                return rf'{name} [label={name}, shape=circle{fillcolor_str}];'
            elif name in outputs:
                return rf'{name} [label={name}, shape=doublecircle{fillcolor_str}];'
            elif isinstance(n, BoolConstant):
                return rf'{name} [label="{str(n.value).upper()}\n{name}{weight_str}", shape=square{fillcolor_str}];'
            elif isinstance(n, Not):
                return rf'{name} [label="not\n{name}{weight_str}"{fillcolor_str}];'
            elif isinstance(n, And):
                return rf'{name} [label="and\n{name}{weight_str}"{fillcolor_str}];'
            else:
                raise RuntimeError(f'stringification failed of node {n}')

        def _edge_tostr(s: _Node, d: _Node):
            sname = s.name
            dname = d.name

            ec = edge_color.get((sname in subgraph_nodes, dname in subgraph_nodes), None)
            if ec is None:
                return rf'{sname} -> {dname};'
            else:
                return rf'{sname} -> {dname} [fillcolor={ec}];'

        _s = cls.DOT_BASE.format(
            nodes='\n'.join(_node_tostr(_n) for _n in circuit.nodes),  # type: ignore
            edges='\n'.join(_edge_tostr(circuit[_s], circuit[_d])  # type: ignore
                            for (_s, _d) in circuit._inner.edges()),  # type: ignore
        )
        FS.writefile(path, _s, overwrite=True)
