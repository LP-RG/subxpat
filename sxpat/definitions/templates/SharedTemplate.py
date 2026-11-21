from typing import Dict, List, Tuple

import itertools as it

from .Template import Template, TemplateBundle

from sxpat.converting import set_prefix
from sxpat.graph import *
from sxpat.graph.node import *
from sxpat.specifications import Specifications
from sxpat.utils.collections import flat, pairwise
from sxpat.graph.components import Subgraph, Parameter, IO


__all__ = ['SharedTemplate']


class SharedTemplate(Template):
    """
        Class for defining the shared template in a subgraph annotated graph.

        TODO: When moving to shared, some of the constraints will need to be checked:
            - constant 0 redundancy for outputs
            - constant 0 redundancy for products
            - add usage of ConstantsType for constant rewriting

        @authors: Marco Biasion
    """

    @classmethod
    def define(cls, graph: Graph, specs: Specifications) -> TemplateBundle:
        # get prefixed graph
        a_graph: Graph = set_prefix(graph, 'a_')
        template_graph_builder = GraphBuilder()
        constraint_graph_builder = GraphBuilder()

        # > Template Graph

        # construct products
        products: List[And] = []
        products_p: List[List[Tuple[BoolVariable, BoolVariable]]] = []
        for prod_i in range(specs.pit):
            # create all multiplexers for the product
            _muxs = []
            products_p.append([])
            for in_i, in_node in enumerate(a_graph.base_components['Subgraph'].subgraph_inputs):
                products_p[-1].append((
                    (p_usage := template_graph_builder.add_node(f'p_p{prod_i}_i{in_i}_u', BoolVariable).add_extras(in_subgraph=True).current), 
                    (p_assert := template_graph_builder.add_node(f'p_p{prod_i}_i{in_i}_a', BoolVariable).add_extras(in_subgraph=True).current), 
                ))
                _muxs.append(
                    template_graph_builder.add_node(
                        f'mux_p{prod_i}_i{in_i}', 
                        Multiplexer
                        ).add_operands(
                            [in_node.name, p_usage.name, p_assert.name]
                            ).add_extras(in_subgraph=True).current
                ) 

            # create the product (and store multiplexers)
            products.append(
                template_graph_builder.add_node(
                    f'prod{prod_i}', 
                    And
                    ).add_operands([n.name for n in _muxs]).add_extras(in_subgraph=True).current
            ) 
            # for node in _muxs:
            #     template_graph_builder.add_new_node(node, in_subgraph=True)

        # construct sums and constant 0 switch
        consts = {True: template_graph_builder.add_node('cT', BoolConstant).add_extras(value=True).current, 
                  False: template_graph_builder.add_node('cF', BoolConstant).add_extras(value=False).current}
        sums = []
        sums_p: List[List[BoolVariable]] = []
        outs_p: List[BoolVariable] = []
        outs: List[If] = []
        out_successors: Dict[str, AnyOperation] = dict()
        for out_i, out_node in enumerate(a_graph.base_components['Subgraph'].subgraph_outputs):
            # create all switches for the output
            _sws = []
            sums_p.append([])
            for prod_i, prod_node in enumerate(products):
                sums_p[-1].append(param := template_graph_builder.add_node(f'p_o{out_i}_p{prod_i}', BoolVariable).add_extras(in_subgraph=True).current) 
                _sws.append(
                    template_graph_builder.add_node(
                        f'sw_o{out_i}_p{prod_i}', 
                        If
                        ).add_operands(
                            [param.name, prod_node.name, consts[True].name]
                            ).add_extras(in_subgraph=True).current
                ) 

            # create the sum and constant 0 switch
            sums.append(
                _sum := template_graph_builder.add_node(
                    f'sum{out_i}', 
                    Or
                    ).add_operands([n.name for n in _sws]).add_extras(in_subgraph=True).current
            ) 
            # for node in _sws:
            #     template_graph_builder.add_new_node(node, in_subgraph=True)
            outs_p.append(
                p_o := template_graph_builder.add_node(f'p_o{out_i}', BoolVariable).add_extras(in_subgraph=True).current
            ) 
            outs.append(
                new_out_node := template_graph_builder.add_node(
                    f'sw_o{out_i}', 
                    If
                    ).add_operands(
                        [p_o.name, _sum.name, consts[False].name]
                        ).add_extras(in_subgraph=True).current
            ) 

            # update all output successors to descend from new outputs
            for succ in a_graph.successors(out_node):
                if not succ.name in a_graph.base_components['Subgraph'].nodes_names():
                    succ = out_successors.get(succ.name, succ)
                    succ_operands = a_graph.base_components['Topology'].operands(succ)
                    new_out_index = succ_operands.index(out_node.name)
                    new_operands = succ_operands[:new_out_index] + [new_out_node.name] + succ_operands[new_out_index + 1:]
                    # out_successors[succ.name] = succ.copy(operands=new_operands)
                    out_successors[succ.name] = template_graph_builder.add_node_from_node(
                        succ,
                        a_graph,
                        operands=new_operands
                        ).current

        # template_graph_builder.add_inherited_nodes([
        #     # unchanged nodes
        #     n
        #     for n in a_graph.nodes
        #     if not n.name in a_graph.base_components['Subgraph'].nodes_names()
        #     if n.name not in out_successors
                        
        # ], a_graph)
        # unchanged nodes
        for n in a_graph.nodes:
            if not n.name in a_graph.base_components['Subgraph'].nodes_names():
                if n.name not in out_successors:
                    template_graph_builder.add_node_from(n, a_graph)

        # template_graph_builder.add_new_nodes(list(consts.values()))

        # template_graph_builder.add_new_nodes(list(flat(products_p))
        #                                      + products
        #                                      + list(flat(sums_p))
        #                                      + sums
        #                                      + outs_p
        #                                      + outs, 
        #                                      in_subgraph=True)

        # for node in out_successors.values():
        #     template_graph_builder.add_new_node(
        #         node, 
        #         in_subgraph=a_graph.base_components['Subgraph'].in_subgraph(node.name),
        #         weight=a_graph.base_components['Weight'].get(node.name)
        #     )

        template_graph_builder.add_base_component(IO({'inputs_names': a_graph.base_components['IO'].inputs_names, 
                                                      'outputs_names': a_graph.base_components['IO'].outputs_names}))
        template_graph_builder.add_base_component(Parameter([n.name for n in flat((products_p, sums_p, outs_p))]))
        template_graph = template_graph_builder.create()

        # > Constraints Graph
        constraint_graph_builder.add_autofill_component('Constraints')
        constraint_graph_builder.add_node('cT', BoolConstant).add_extras(value=True)
        constraint_graph_builder.add_node('cF', BoolConstant).add_extras(value=False)

        # error constraint
        cur_int = constraint_graph_builder.add_node('cur_int', ToInt).add_operands(list(graph.base_components['IO'].outputs_names)).current
        tem_int = constraint_graph_builder.add_node('tem_int', ToInt).add_operands(list(template_graph.base_components['IO'].outputs_names)).current
        abs_diff = constraint_graph_builder.add_node('abs_diff', AbsDiff).add_operands([cur_int.name, tem_int.name]).current
        et = constraint_graph_builder.add_node('et', IntConstant).add_extras(value=specs.et).current
        error_check = constraint_graph_builder.add_node('error_check', LessEqualThan).add_operands([abs_diff.name, et.name]).current

        # its constraint
        at_most_its = constraint_graph_builder.add_node('at_most_its', AtMost).add_operands([n.name for n in flat(sums_p)]).add_extras(value=specs.its).current

        # multiplexer redundancy
        for (prod_i, prod_p) in enumerate(products_p):
            for (p_usage, p_assert) in prod_p:
                constraint_graph_builder.add_node(f'prevent_constF_{prod_i}', Or).add_operands([p_usage.name, p_assert.name]).current
        
        # constant zero redundancy
        for sum_i, (p_o, p_o_ps) in enumerate(zip(outs_p, sums_p)):
            not_p_o = constraint_graph_builder.add_node(f'not_{p_o.name}', Not).add_operands([p_o.name]).current
            or_ps = constraint_graph_builder.add_node(f'or_sum_in_{sum_i}', Or).add_operands([n.name for n in p_o_ps]).current
            not_or = constraint_graph_builder.add_node(f'not_{or_ps.name}', Not).add_operands([or_ps.name]).current
            impl = constraint_graph_builder.add_node(f'impl_sum_{sum_i}', Implies).add_operands([not_p_o.name, not_or.name]).current

        # order of products redundancy
        if len(products_p) >= 2:
            prod_ids = [
                constraint_graph_builder.add_node(f'prod{prod_i}_id', ToInt).add_operands([n.name for n in flat(prod_p)]).current
                for (prod_i, prod_p) in enumerate(products_p)
            ]
            for (idx_a, prod_a), (idx_b, prod_b) in pairwise(enumerate(prod_ids)):
                constraint_graph_builder.add_node(f'id_order_{idx_a}_{idx_b}', GreaterThan).add_operands([prod_a.name, prod_b.name])

        # target definition
        for param in flat((sums_p, products_p, outs_p, sums_p)):
            constraint_graph_builder.add_node(f't_{param.name}', Target).add_operands([param.name])

        # constraint_graph_builder.add_new_nodes([
        #     PlaceHolder(node.name) 
        #     for node in flat((sums_p, products_p, outs_p, sums_p))
        # ])
        # constraint_graph_builder.add_new_nodes([PlaceHolder(name) for name in graph.base_components['IO'].outputs_names])
        # constraint_graph_builder.add_new_nodes([PlaceHolder(name) for name in template_graph.base_components['IO'].outputs_names])

        # placeholders
        for node in flat((sums_p, products_p, outs_p, sums_p)):
            constraint_graph_builder.add_node(node.name, PlaceHolder)
        for name in graph.base_components['IO'].outputs_names:
            constraint_graph_builder.add_node(name, PlaceHolder)
        for name in template_graph.base_components['IO'].outputs_names:
            constraint_graph_builder.add_node(name, PlaceHolder)

        # constraint_graph_builder.add_new_nodes(list(consts.values()) 
        #                                        + error_nodes
        #                                        + its_nodes
        #                                        + mux_red_nodes
        #                                        + const0_red_nodes
        #                                        + prod_ids
        #                                        + prod_ord_nodes
        #                                        + targets)

        constraint_graph = constraint_graph_builder.create()

        return TemplateBundle(template_graph, [constraint_graph])
