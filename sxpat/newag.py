from typing import ClassVar, Dict, Mapping, TypeVar

from sxpat.graph.graph import IOGraph, SGraph
from sxpat.graph.node import And, BoolConstant, Constant, Extras, Node, Not
from sxpat.specifications import Paths

import re
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


# TODO: move the following things somewhere else

T = TypeVar('T')
K = TypeVar('K')
class _Node(Node, Extras): ...


class z3log_graph_substitute:
    @classmethod
    def get_all(cls, circuit: IOGraph):
        """
        Extract all relevant Z3Log.Graph.* helper structure from the IOGraph.

        :return: input_dict, output_dict, gate_dict, constant_dict
        """

        return (
            cls.get_input_dict(circuit),
            cls.get_output_dict(circuit),
            cls.get_gate_dict(circuit),
            cls.get_constant_dict(circuit),
        )

    @classmethod
    def get_input_dict(cls, circuit: IOGraph):
        return dict(enumerate(circuit.inputs_names))

    @classmethod
    def get_output_dict(cls, circuit: IOGraph):
        return dict(enumerate(circuit.outputs_names))

    @classmethod
    def get_gate_dict(cls, circuit: IOGraph):
        idx_patt = re.compile(r'\d+')
        return dict(
            (
                int(idx_patt.search(n.name).group()),  # type: ignore
                n.name,
            )
            for n in circuit.nodes
            if n.name not in circuit.inputs_names
            if n.name not in circuit.outputs_names
            if not isinstance(n, Constant)
        )

    @classmethod
    def get_constant_dict(cls, circuit: IOGraph):
        idx_patt = re.compile(r'\d+')
        return dict(
            (
                int(idx_patt.search(n.name).group()),  # type: ignore
                n.name,
            )
            for n in circuit.constants
        )

    @staticmethod
    def sort_dict(mapping: Mapping[K, T]) -> Dict[K, T]:
        return dict(sorted(mapping.items(), key=lambda x: x[0]))


class z3log_annotatedgraph_substitute(z3log_graph_substitute):
    @classmethod
    def get_all(cls, circuit: SGraph):
        return (
            *super().get_all(circuit),
            cls.get_subgraph_input_dict(circuit),
            cls.get_subgraph_output_dict(circuit),
            cls.extract_subgraph_gates(circuit),
        )

    @classmethod
    def get_subgraph_input_dict(cls, circuit: SGraph) -> Dict[int, str]:
        """
        Extract subgraph inputs, returning them as an int->str mapping.  
        A node is a subgraph input if it is not in the subgraph and at least one of its successors is.
        """

        indexes = iter(range(len(circuit.nodes)))
        return {
            next(indexes): n.name
            for n in circuit.nodes
            if (  # if is_subgraph_input
                not circuit[n].in_subgraph  # type: ignore
                and any(
                    s.in_subgraph  # type: ignore
                    for s in circuit.successors(n)
                )
            )
        }

    @classmethod
    def get_subgraph_output_dict(cls, circuit: SGraph) -> Dict[int, str]:
        """
        Extract subgraph outputs, returning them as an int->str mapping.  
        A node is a subgraph output if it is in the subgraph and at least one of its successors is not.
        """

        indexes = iter(range(len(circuit.nodes)))
        return {
            next(indexes): n.name
            for n in circuit.nodes
            if (  # if is_subgraph_output
                circuit[n].in_subgraph  # type: ignore
                and any(
                    not s.in_subgraph  # type: ignore
                    for s in circuit.successors(n)
                )
            )
        }

    @classmethod
    def extract_subgraph_gates(cls, circuit: SGraph) -> Dict[int, str]:
        """
        extracts subgraph gates and stores them in a dictionary where keys are indices and values are gate labels
        :return: a dictionary; ex: gate_dict = {gate_idx0: gate_label0, ..., gate_idxn: gate_labeln}
        """
        raise
        # TODO
        s_gates_dict: Dict[int, str] = {}
        graph_gate_list: List[str] = list(self.gate_dict.values())

        for n in self.subgraph.nodes:
            if SUBGRAPH in self.subgraph.nodes[n] and self.subgraph.nodes[n][SUBGRAPH] == 1:
                s_gates_dict[graph_gate_list.index(n)] = n

        return s_gates_dict

    DOT_BASE: ClassVar = '\n'.join((
        'strict digraph "" {{',
        'node [colorscheme=set13, style=filled, fillcolor=white, shape=invhouse];',
        '{nodes}',
        '',
        'edge [colorscheme=set13, dir=both, arrowtail=inv];',
        '{edges}',
        '}}',
    ))

    @classmethod
    def export_annotated_graph(cls, circuit: SGraph, path: str):
        """
        exports the graph (annotated with a subgraph) in the GraphViz (.dot/.gv) format.

        :authors: Marco Biasion, Morteza Rezaalipour
        """

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
            fillcolor_str = 3 if name in subgraph_inputs else 2 if name in subgraph_outputs else 1 if isinstance(n, Extras) and n.in_subgraph else ''
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

        with open(path, 'w') as f:
            f.write(
                cls.DOT_BASE.format(
                    nodes='\n'.join(_node_tostr(_n) for _n in circuit.nodes),  # type: ignore
                    edges='\n'.join(_edge_tostr(circuit[_s], circuit[_d]) for (_s, _d) in circuit._inner.edges()),  # type: ignore
                )
            )
