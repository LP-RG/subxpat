from abc import abstractmethod
from typing import Dict, Iterable, Mapping, Sequence, Tuple
from typing_extensions import Never

import itertools as it
from sxpat.utils.collections import iterable_replace
from sxpat.converting.utils import prune_unused_keepio, set_prefix_new

from .Template import Template
from sxpat.graph.graph import IOGraph
from sxpat.graph import SGraph, PGraph
from sxpat.graph.node import AnyNode, AnyNonEndPoint, AnyOperation, BoolVariable, Xor


__all__ = ['ConstantTemplate', 'SwitchedTemplate']


circuit_prefix = 'a_'


class SimpleTemplate(Template):
    """
        This is the base class for templates composed of a set of parameters equal to the subgraph outputs and very simple logic.

        @authors: Marco Biasion:
    """

    @classmethod
    def _define_parameters(cls, circuit: SGraph) -> Sequence[BoolVariable]:
        return tuple(
            BoolVariable(f'p{sub_i}', weight=out_node.weight, in_subgraph=True)
            for (sub_i, out_node) in enumerate(circuit.subgraph_outputs)
        )

    @classmethod
    def _get_updated_suboutputs_successors(cls, circuit: SGraph,
                                           new_subgraph_outputs: Sequence[AnyNonEndPoint]
                                           ) -> Mapping[str, AnyOperation]:

        updated_nodes: Dict[str, AnyOperation] = dict()

        for (new, old) in zip(new_subgraph_outputs, circuit.subgraph_outputs):
            for succ in circuit.successors(old):
                if not succ.in_subgraph:
                    succ = updated_nodes.get(succ.name, succ)
                    new_operands = iterable_replace(succ.operands, old.name, new.name)
                    updated_nodes[succ.name] = succ.copy(operands=new_operands)

        return updated_nodes

    @classmethod
    def _create_parametric_circuit(cls, circuit: IOGraph,
                                   updated_nodes: Mapping[str, AnyNode],
                                   new_nodes: Iterable[AnyNode],
                                   parameters: Sequence[BoolVariable],
                                   ) -> PGraph:

        # create parametric circuit
        param_circ = PGraph(
            it.chain(
                (  # replace updated nodes
                    updated_nodes.get(n.name, n)
                    for n in circuit.nodes
                ),
                new_nodes,
                parameters,
            ),
            inputs_names=circuit.inputs_names,
            outputs_names=circuit.outputs_names,
            parameters_names=tuple(n.name for n in parameters),
        )
        # prefix all nodes
        param_circ = set_prefix_new(
            param_circ, circuit_prefix,
            param_circ.inputs_names,
        )

        return param_circ

    @classmethod
    @abstractmethod
    def define(cls, graph: SGraph, _unused) -> Tuple[PGraph, Sequence[Never]]:
        """
            Given a graph with subgraph informations,
            returns the parametric graph with the subgraph replaced with the template.
        """
        raise NotImplementedError(f'{cls.__qualname__}.define() is abstract')


class ConstantTemplate(SimpleTemplate):
    """
        This template allows only for constants at the subgraph outputs.

        @authors: Marco Biasion
    """

    @classmethod
    def define(cls, circuit: SGraph, _unused) -> Tuple[PGraph, Sequence[Never]]:

        # define the parameters
        parameters = cls._define_parameters(circuit)

        # use parameters as subgraph outputs
        updated_nodes = cls._get_updated_suboutputs_successors(circuit, parameters)

        # create the parametric circuit
        parametric_circuit = cls._create_parametric_circuit(circuit, updated_nodes, [], parameters)
        # remove unused nodes
        parametric_circuit = prune_unused_keepio(
            parametric_circuit,
            parametric_circuit.parameters_names,
        )

        return (parametric_circuit, [])


class SwitchedTemplate(SimpleTemplate):
    """
        This template allows for a targeted logic break (negating the relative subgraph output)
        where the parameters are true.

        @authors: Marco Biasion, Lorenzo Spada
    """

    @classmethod
    def define(cls, circuit: SGraph, _unused) -> Tuple[PGraph, Sequence[Never]]:

        # define the parameters
        parameters = cls._define_parameters(circuit)

        # define xors (they break the subout when their parameter is true)
        xors = [
            Xor(f'xor{out_i}', operands=[subout, param], weight=subout.weight, in_subgraph=True)
            for (out_i, param, subout) in zip(it.count(), parameters, circuit.subgraph_outputs)
        ]

        # use xors as subgraph outputs
        updated_nodes = cls._get_updated_suboutputs_successors(circuit, xors)

        # create the parametric circuit
        parametric_circuit = cls._create_parametric_circuit(circuit, updated_nodes, xors, parameters)

        return (parametric_circuit, [])
