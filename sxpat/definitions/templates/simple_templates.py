from typing import Dict, Sequence

import itertools as it
from sxpat.utils.collections import iterable_replace
from sxpat.converting.utils import prune_unused_keepio, set_prefix_new

from .Template import Template, TemplateBundle
from sxpat.graph.graph import Graph, GraphBuilder
from sxpat.graph.node import AnyNonEndPoint, AnyOperation, BoolVariable, Xor
from sxpat.graph.components import Weight, IO, Parameter


__all__ = ['ConstantTemplate', 'SwitchedTemplate']


circuit_prefix = 'a_'


class SimpleTemplate(Template):
    """
        This is the base class for templates composed of a set of parameters equal to the subgraph outputs and very simple logic.

        @authors: Marco Biasion, Ilia Zeller
    """

    @classmethod
    def _define_parameters(cls, circuit: Graph, graph_builder: GraphBuilder) -> Sequence[BoolVariable]:
        params = []
        for out_node in circuit.base_components['Subgraph'].subgraph_outputs:
            new_node = graph_builder.add_node_copy(
                out_node,
                circuit, 
                name=f'p_{out_node.name}', 
                node_type=BoolVariable).current
            params.append(new_node)
        return tuple(params)

    @classmethod
    def _get_updated_suboutputs_successors(cls, circuit: Graph,
                                           new_subgraph_outputs: Sequence[AnyNonEndPoint],
                                           graph_builder: GraphBuilder
                                           ) -> None:

        updated_nodes: Dict[str, AnyOperation] = dict()

        for (new, old) in zip(new_subgraph_outputs, circuit.base_components['Subgraph'].subgraph_outputs):
            for succ in circuit.successors(old):
                if not succ.name in circuit.base_components['Subgraph'].nodes_names():
                    succ = updated_nodes.get(succ.name, succ)
                    succ_operands = circuit.base_components['Topology'].operands(succ.name)
                    new_operands = iterable_replace(succ_operands, old.name, new.name)
                    updated_nodes[succ.name] = graph_builder.add_node_copy(
                                        succ,
                                        circuit,
                                        operands=list(new_operands)).current
        for n in circuit.nodes:
            if not n.name in updated_nodes:
                graph_builder.add_node_from(n, circuit)
                


    @classmethod
    def _create_parametric_circuit(cls, circuit: Graph,
                                   parameters: Sequence[BoolVariable],
                                   graph_builder: GraphBuilder
                                   ) -> Graph:

        graph_builder.add_base_component(IO({'inputs_names': circuit.base_components['IO'].inputs_names, 
                                             'outputs_names': circuit.base_components['IO'].outputs_names}))
        graph_builder.add_base_component(Parameter(list(n.name for n in parameters)))
        param_circ = graph_builder.create()

        # prefix all nodes
        param_circ = set_prefix_new(
            param_circ, circuit_prefix,
            param_circ.base_components['IO'].inputs_names,
        )

        return param_circ


class ConstantTemplate(SimpleTemplate):
    """
        This template allows only for constants at the subgraph outputs.

        @authors: Marco Biasion
    """

    @classmethod
    def define(cls, circuit: Graph, _unused=...) -> TemplateBundle:
        """The `TemplateBundle` returned from this method contains only the circuit."""

        graph_builder = GraphBuilder()

        # define the parameters
        parameters = cls._define_parameters(circuit, graph_builder)

        # add the parametric circuit nodes (use parameters as subgraph outputs)
        cls._get_updated_suboutputs_successors(circuit, parameters, graph_builder)

        # create the parametric circuit
        parametric_circuit = cls._create_parametric_circuit(circuit, parameters, graph_builder)

        # remove unused nodes
        parametric_circuit = prune_unused_keepio(
            parametric_circuit,
            parametric_circuit.base_components['Parameter'].parameters_names,
        )

        return TemplateBundle(parametric_circuit)


class SwitchedTemplate(SimpleTemplate):
    """
        This template allows for a targeted logic break (negating the relative subgraph output)
        where the parameters are true.

        @authors: Marco Biasion, Lorenzo Spada
    """

    @classmethod
    def define(cls, circuit: Graph, _unused=...) -> TemplateBundle:

        graph_builder = GraphBuilder()

        # define the parameters
        parameters = cls._define_parameters(circuit, graph_builder)

        # define xors (they break the subout when their parameter is true)
        xors = [
            graph_builder.add_node(f'xor{out_i}', Xor).add_operands([subout.name, param.name]).current
            for (out_i, param, subout) in zip(it.count(), parameters, circuit.base_components['Subgraph'].subgraph_outputs)
        ]

        weight_component = circuit.base_components['Weight']
        xors_weights = [
            weight_component.get(subout.name)
            for subout in circuit.base_components['Subgraph'].subgraph_outputs
        ]

        # add the parametric circuit nodes (use xors as subgraph outputs)
        cls._get_updated_suboutputs_successors(circuit, xors, graph_builder)

        # create the parametric circuit
        parametric_circuit = cls._create_parametric_circuit(circuit, parameters, graph_builder)

        new_weights_mapping = dict()
        for xor_node, xor_weight in zip(xors, xors_weights):
            new_weights_mapping[xor_node.name] = xor_weight
        weight_component = parametric_circuit.base_components['Weight']
        for n in parametric_circuit.nodes:
            if not n.name in new_weights_mapping.keys():
                new_weights_mapping[n.name] = weight_component.get(n.name)
        new_weight_component = Weight(new_weights_mapping)
        parametric_circuit = parametric_circuit.with_base_component(new_weight_component)

        return TemplateBundle(parametric_circuit)
