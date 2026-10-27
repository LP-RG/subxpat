from typing import Dict, Iterable, Mapping, Sequence

import itertools as it
from sxpat.utils.collections import iterable_replace
from sxpat.converting.utils import prune_unused_keepio, set_prefix_new, node_from_node

from .Template import Template, TemplateBundle
from sxpat.graph.graph import IOGraph
from sxpat.graph import PGraph
from sxpat.graph.node import AnyNode, AnyNonEndPoint, AnyOperation, BoolVariable, Xor
from sxpat.graph.components import Weight


__all__ = ['ConstantTemplate', 'SwitchedTemplate']


circuit_prefix = 'a_'


class SimpleTemplate(Template):
    """
        This is the base class for templates composed of a set of parameters equal to the subgraph outputs and very simple logic.

        @authors: Marco Biasion:
    """

    @classmethod
    def _define_parameters(cls, circuit: IOGraph) -> Sequence[BoolVariable]:
        return tuple(
            node_from_node(BoolVariable, out_node, {'name': f'p_{out_node.name}'})
            for out_node in circuit.base_components['Subgraph'].subgraph_outputs
        )

    @classmethod
    def _get_updated_suboutputs_successors(cls, circuit: IOGraph,
                                           new_subgraph_outputs: Sequence[AnyNonEndPoint]
                                           ) -> Mapping[str, AnyOperation]:

        updated_nodes: Dict[str, AnyOperation] = dict()

        for (new, old) in zip(new_subgraph_outputs, circuit.base_components['Subgraph'].subgraph_outputs):
            for succ in circuit.successors(old):
                if not succ.name in circuit.base_components['Subgraph'].nodes_names():
                    succ = updated_nodes.get(succ.name, succ)
                    new_operands = iterable_replace(succ.operands, old.name, new.name)
                    updated_nodes[succ.name] = succ.copy(operands=new_operands) # NODE COPY

        return updated_nodes

    @classmethod
    def _create_parametric_circuit(cls, circuit: IOGraph,
                                   updated_nodes: Mapping[str, AnyNode],
                                   new_nodes: Iterable[AnyNode],
                                   parameters: Sequence[BoolVariable],
                                   ) -> PGraph:

        # create parametric circuit
        # GRAPH CREATION/COPY
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


class ConstantTemplate(SimpleTemplate):
    """
        This template allows only for constants at the subgraph outputs.

        @authors: Marco Biasion
    """

    @classmethod
    def define(cls, circuit: IOGraph, _unused=...) -> TemplateBundle:
        """The `TemplateBundle` returned from this method contains only the circuit."""

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

        return TemplateBundle(parametric_circuit)


class SwitchedTemplate(SimpleTemplate):
    """
        This template allows for a targeted logic break (negating the relative subgraph output)
        where the parameters are true.

        @authors: Marco Biasion, Lorenzo Spada
    """

    @classmethod
    def define(cls, circuit: IOGraph, _unused=...) -> TemplateBundle:

        # define the parameters
        parameters = cls._define_parameters(circuit)

        # define xors (they break the subout when their parameter is true)
        xors = [
            Xor(f'xor{out_i}', operands=[subout, param])
            for (out_i, param, subout) in zip(it.count(), parameters, circuit.base_components['Subgraph'].subgraph_outputs)
        ]

        # COMMENT:from-MARCO: valid. a way to improve this, would be to get the Weight component before the ifs and use it directly (saves on a lot of accesses)
        xors_weights = [
            circuit.base_components['Weight'].get(subout.name)
            for subout in circuit.base_components['Subgraph'].subgraph_outputs
        ]

        # use xors as subgraph outputs
        updated_nodes = cls._get_updated_suboutputs_successors(circuit, xors)

        # create the parametric circuit
        parametric_circuit = cls._create_parametric_circuit(circuit, updated_nodes, xors, parameters)

        new_weights_mapping = dict()
        for xor_node, xor_weight in zip(xors, xors_weights):
            new_weights_mapping[xor_node.name] = xor_weight
        for n in parametric_circuit.nodes:
            if not n.name in new_weights_mapping.keys():
                # COMMENT:from-MARCO: valid. a way to improve this, would be to get the Weight component before the ifs and use it directly (saves on a lot of accesses)
                new_weights_mapping[n.name] = parametric_circuit.base_components['Weight'].get(n.name)
        new_weight_component = Weight(new_weights_mapping)
        parametric_circuit = parametric_circuit.with_base_component(new_weight_component)

        return TemplateBundle(parametric_circuit)
