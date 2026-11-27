from typing import Collection, Iterable, Optional, Sequence, Tuple, Union
from typing_extensions import override

import itertools as it
from sxpat.utils.collections import first, formatted_int_range

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import Graph, GraphBuilder
from sxpat.graph import error as g_error
from sxpat.graph.node import AbsDiff, AnyExtras, If, IntConstant, PlaceHolder, Sum, Node


__all__ = ['AbsoluteDifferenceOfWeightedSum']


class AbsoluteDifferenceOfWeightedSum(DistanceSpecification):
    """
        Defines a distance as the absolute difference of the wanted nodes of the circuits where each node is valued using its weight.

        # COMMENT:from-MARCO: for the classes/methods you change, you can append your name to the authors if you want, or if you completely rewrite/adapt the method, you can prepend it
        # from-ILIA: done!
        
        @authors: Marco Biasion, Ilia Zeller
    """

    @override
    @classmethod
    def _define(cls, graph_a: Graph, graph_b: Graph,
                wanted_a: Collection[str], wanted_b: Collection[str],
                ) -> Tuple[Graph, str]:

        # useful variables
        w_nodes_a: Collection[Node] = tuple(graph_a[n] for n in wanted_a)  # type: ignore
        w_nodes_b: Collection[Node] = tuple(graph_b[n] for n in wanted_b)  # type: ignore

        graph_a_weights = graph_a.base_components['Weight']
        graph_b_weights = graph_b.base_components['Weight']
        # guard
        if (broken := first(lambda x: not graph_a_weights.has_weight(x), w_nodes_a, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph_a ({graph_a}) has no weight.')
        elif (broken := first(lambda x: not graph_b_weights.has_weight(x), w_nodes_b, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph_b ({graph_b}) has no weight.')

        graph_builder = GraphBuilder()
        graph_builder.add_autofill_component('Constraints')

        # values
        a_name = cls._define_value(graph_a, w_nodes_a, 'a', graph_builder)
        b_name = cls._define_value(graph_b, w_nodes_b, 'b', graph_builder)

        # distance
        distance = graph_builder.add_node('dist_distance', AbsDiff).add_operands([a_name, b_name]).current

        # construct Constraints Graph
        dist_func = graph_builder.create()

        return (dist_func, distance.name)

    @classmethod
    def define_value(cls, graph: Graph, wanted: Optional[Collection[str]] = None
                     ) -> Tuple[Graph, str]:
        """
            Define an individual weighted sum given the graph and an optional specific collection of nodes to use.

            @notes: if it becomes standard to generate simple expressions (eg. a weighted sum) could make sense to move this logic (and all others like this one) to their own module
        """

        # default
        if wanted is None: wanted = graph.base_components['IO'].outputs_names

        # useful variables
        w_nodes: Sequence[Node] = tuple(graph[n] for n in wanted)  # type: ignore

        # guard
        if (broken := first(graph.base_components['Weight'].has_weight, w_nodes, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph ({graph}) has no weight.')

        graph_builder = GraphBuilder()
        graph_builder.add_autofill_component('Constraints')

        value_name = cls._define_value(graph, w_nodes, 'v', graph_builder)

        # construct Constraints Graph
        value_func = graph_builder.create()

        return (value_func, value_name)

    @classmethod
    def _define_value(cls, 
                      graph: Graph, 
                      wanted_nodes: Sequence[AnyExtras], 
                      value_id: str,
                      graph_builder: GraphBuilder) -> str:

        # graph int
        bits_n = []
        weight_component = graph.base_components['Weight']
        for (i, node) in zip(
            formatted_int_range(len(wanted_nodes)),
            wanted_nodes,
        ):
            # create constants
            val: int = weight_component.get(node.name) # type: ignore
            const_0 = graph_builder.add_node(f'dist_{value_id}{i}_const_0', IntConstant).add_extras(value=0).current 
            const_n = graph_builder.add_node(f'dist_{value_id}{i}_const_{val}', IntConstant).add_extras(value=val).current

            # create node that reflects the weight if the bit is true, or 0
            bits_n.append(
                graph_builder.add_node(
                    f'dist_{value_id}{i}', If
                ).add_operands([node.name, const_n.name, const_0.name]).current
            )
        int_n = graph_builder.add_node(f'dist_int_{value_id}', Sum).add_operands([n.name for n in bits_n]).current

        # placeholders
        for node in wanted_nodes:
            graph_builder.add_node(node.name, PlaceHolder)
        
        return int_n.name
