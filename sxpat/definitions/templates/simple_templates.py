from typing import Dict, Iterable, Mapping, Sequence

import itertools as it
from sxpat.utils.collections import iterable_replace
from sxpat.converting.utils import prune_unused_keepio, set_prefix_new, node_from_node

from .Template import Template, TemplateBundle
from sxpat.graph.graph import Graph
from sxpat.graph.node import AnyNode, AnyNonEndPoint, AnyOperation, BoolVariable, Xor
from sxpat.graph.components import Weight, IO, Parameter
from sxpat.graph.graphCreators import GraphBuilder


__all__ = ['ConstantTemplate', 'SwitchedTemplate']


circuit_prefix = 'a_'


class SimpleTemplate(Template):
    """
        This is the base class for templates composed of a set of parameters equal to the subgraph outputs and very simple logic.

        @authors: Marco Biasion:
    """

    @classmethod
    def _define_parameters(cls, circuit: Graph, graph_builder: GraphBuilder) -> Sequence[BoolVariable]:
        params = []
        for out_node in circuit.base_components['Subgraph'].subgraph_outputs:
            new_node = node_from_node(BoolVariable, out_node, {'name': f'p_{out_node.name}'})
            params.append(new_node)
            graph_builder.add_new_node(new_node,
                                       in_subgraph=circuit.base_components['Subgraph'].in_subgraph(new_node.name),
                                       weight=circuit.base_components['Weight'].get(new_node.name))
        return tuple(params)

    @classmethod
    def _get_updated_suboutputs_successors(cls, circuit: Graph,
                                           new_subgraph_outputs: Sequence[AnyNonEndPoint],
                                           ) -> Mapping[str, AnyOperation]:

        updated_nodes: Dict[str, AnyOperation] = dict()

        for (new, old) in zip(new_subgraph_outputs, circuit.base_components['Subgraph'].subgraph_outputs):
            for succ in circuit.successors(old):
                if not succ.name in circuit.base_components['Subgraph'].nodes_names():
                    succ = updated_nodes.get(succ.name, succ)
                    new_operands = iterable_replace(succ.operands, old.name, new.name)
                    updated_nodes[succ.name] = succ.copy(operands=new_operands)

        return updated_nodes

    @classmethod
    def _create_parametric_circuit(cls, circuit: Graph,
                                   updated_nodes: Mapping[str, AnyNode],
                                   parameters: Sequence[BoolVariable],
                                   graph_builder: GraphBuilder
                                   ) -> Graph:
    
    
        for n in circuit.nodes:
            node = updated_nodes.get(n.name, n)
            if node is n:
                graph_builder.add_inherited_node(n, circuit)
            else:
                graph_builder.add_new_node(
                    node, 
                    in_subgraph=circuit.base_components['Subgraph'].in_subgraph(node.name),
                    weight=circuit.base_components['Weight'].get(node.name))

        param_circ = graph_builder.create(extra_components=[
                                              IO(circuit.base_components['IO'].inputs_names, 
                                                 circuit.base_components['IO'].outputs_names),
                                              Parameter(tuple(n.name for n in parameters))
                                          ])
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

        # use parameters as subgraph outputs
        updated_nodes = cls._get_updated_suboutputs_successors(circuit, parameters)

        # create the parametric circuit
        parametric_circuit = cls._create_parametric_circuit(circuit, updated_nodes, parameters, graph_builder)
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
            Xor(f'xor{out_i}', operands=[subout, param])
            for (out_i, param, subout) in zip(it.count(), parameters, circuit.base_components['Subgraph'].subgraph_outputs)
        ]
        for node in xors:
            graph_builder.add_new_node(node)

        # COMMENT:from-MARCO: valid. a way to improve this, would be to get the Weight component before the ifs and use it directly (saves on a lot of accesses)
        # from-ILIA: fixed
        weight_component = circuit.base_components['Weight']
        xors_weights = [
            weight_component.get(subout.name)
            for subout in circuit.base_components['Subgraph'].subgraph_outputs
        ]

        # use xors as subgraph outputs
        updated_nodes = cls._get_updated_suboutputs_successors(circuit, xors)

        # create the parametric circuit
        parametric_circuit = cls._create_parametric_circuit(circuit, updated_nodes, parameters, graph_builder)

        new_weights_mapping = dict()
        for xor_node, xor_weight in zip(xors, xors_weights):
            new_weights_mapping[xor_node.name] = xor_weight
        weight_component = parametric_circuit.base_components['Weight']
        for n in parametric_circuit.nodes:
            if not n.name in new_weights_mapping.keys():
                # COMMENT:from-MARCO: valid. a way to improve this, would be to get the Weight component before the ifs and use it directly (saves on a lot of accesses)
                # from-ILIA: fixed
                new_weights_mapping[n.name] = weight_component.get(n.name)
        new_weight_component = Weight(new_weights_mapping)
        parametric_circuit = parametric_circuit.with_base_component(new_weight_component)

        return TemplateBundle(parametric_circuit)
