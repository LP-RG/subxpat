from typing import Dict, List, Sequence, Tuple, Union

import itertools as it

from .Template import Template, TemplateBundle

from sxpat.converting import set_prefix
from sxpat.graph import *
from sxpat.graph.node import *
from sxpat.specifications import ConstantsType, Specifications
from sxpat.utils.collections import flat, iterable_replace, pairwise
from sxpat.graph.components import Subgraph, Parameter, IO


__all__ = ['NonSharedFOutTemplate', 'NonSharedFProdTemplate']


class _NonSharedBase:
    """
       Base class for non shared templates.
       Includes common utilities.

       @authors: Marco Biasion
    """

    @classmethod
    def construct_products(cls, a_graph: Graph, products_per_output: int, graph_builder: GraphBuilder
                           ) -> Tuple[List[List[And]], List[List[List[Tuple[BoolVariable, BoolVariable]]]], List[Multiplexer]]:
        """
            Generates the products and all relative multiplexers and parameters.
        """

        products: List[List[And]] = []
        out_prod_mux_params: List[List[List[Tuple[BoolVariable, BoolVariable]]]] = []
        multiplexers: List[Multiplexer] = []

        # for all outputs
        for out_i, _ in enumerate(a_graph.base_components['Subgraph'].subgraph_outputs):

            # for all products
            products.append([])
            out_prod_mux_params.append([])
            for prod_i in range(products_per_output):

                # create all multiplexers and relative parameters for the product
                _muxs, parameters = [], []
                for in_i, in_node in enumerate(a_graph.base_components['Subgraph'].subgraph_inputs):
                    parameters.append((
                        (p_usage := graph_builder.add_node(
                            f'p_o{out_i}_t{prod_i}_i{in_i}_u', 
                            BoolVariable
                            ).add_extras(in_subgraph=True).current),
                        (p_assert := graph_builder.add_node(
                            f'p_o{out_i}_t{prod_i}_i{in_i}_a',
                            BoolVariable
                        ).add_extras(in_subgraph=True).current),
                    ))
                    n = graph_builder.add_node(
                        f'mux_o{out_i}_t{prod_i}_i{in_i}',
                        Multiplexer
                        ).add_operands(
                            [in_node.name, p_usage.name, p_assert.name]
                            ).add_extras(in_subgraph=True).current
                    _muxs.append(n) 
                out_prod_mux_params[-1].append(parameters)
                multiplexers.extend(_muxs)

                # create the product
                n = graph_builder.add_node(
                    f'o{out_i}_p{prod_i}', 
                    And
                    ).add_operands([m.name for m in _muxs]).add_extras(in_subgraph=True).current
                products[-1].append(n)

        # for node in flat(products):
        #     graph_builder.add_new_node(node, in_subgraph=True)
        # for node in flat(out_prod_mux_params):
        #     graph_builder.add_new_node(node, in_subgraph=True)
        # for node in multiplexers:
        #     graph_builder.add_new_node(node, in_subgraph=True)

        return (
            products,
            out_prod_mux_params,
            multiplexers,
        )

    @classmethod
    def construct_sums(cls, a_graph: Graph, products: List[List[And]], graph_builder: GraphBuilder
                       ) -> List[Or]:
        or_list = [
            graph_builder.add_node(
                f'sum{out_i}', 
                Or
                ).add_operands(
                    [n.name for n in products[out_i]]
                    ).add_extras(in_subgraph=True).current
            for out_i, _ in enumerate(a_graph.base_components['Subgraph'].subgraph_outputs)
        ]

        # for node in or_list:
        #     graph_builder.add_new_node(node, in_subgraph=True)

        return or_list
        

    @classmethod
    def constants_rewriting(cls, a_graph: Graph, 
                            updated_nodes: Dict[str, AnyOperation], 
                            specs: Specifications,
                            template_graph_builder: GraphBuilder
                            ) -> List[BoolVariable]:
        """
            Generates the nodes for constants rewriting, will update `updated_nodes` inplace with the changed successors (if any).
        """

        # skip if constant rewriting is not needed
        if specs.constants is not ConstantsType.ALWAYS: return []

        constants_parameters = []

        # for all constants
        for const in a_graph.constants:
            # if the constants is at the graph output
            if len(succs := a_graph.successors(const)) == 1 and (out_i := a_graph.base_components['IO'].output_index_of(succ := succs[0])) >= 0:
                constants_parameters.append(const_rew := template_graph_builder.add_node(f'p_c{out_i}', BoolVariable).current)
                # updated_nodes[succ.name] = succ.copy(operands=(const_rew,))  
                updated_nodes[succ.name] = template_graph_builder.add_node_from_node(   # by definition, the output node has no other operand
                    succ, 
                    a_graph,
                    operands=[const_rew.name]
                    ).current

        return constants_parameters

    @classmethod
    def atmost_lpp_constraints(cls, out_prod_mux_params: List[List[List[Tuple[BoolVariable, BoolVariable]]]], literals_per_product: int
                               ) -> Sequence[Union[AtMost, Constraint]]:
        return tuple(flat(
            (
                at_most := AtMost(f'at_most_lpp_o{out_i}_p{prod_i}', operands=(p[0] for p in prod_params), value=literals_per_product),
                Constraint.of(at_most),
            )
            for (out_i, out_params) in enumerate(out_prod_mux_params)
            for (prod_i, prod_params) in enumerate(out_params)
        ))

    @classmethod
    def products_order_redundancy(cls, out_prod_mux_params: List[List[List[Tuple[BoolVariable, BoolVariable]]]]
                                  ) -> Sequence[Union[Node, Constraint]]:

        # skip if we have only one product
        if len(out_prod_mux_params[0]) < 2: return []

        nodes: List[Node] = []

        # for all outputs
        for (out_i, out_params) in enumerate(out_prod_mux_params):
            # generate an integer identifier for each product
            nodes.extend(_prod_ids := [
                ToInt(f'out{out_i}_prod{prod_i}_id', operands=flat(prod_params))
                for (prod_i, prod_params) in enumerate(out_params)
            ])
            # set the order of the identifiers ( a >= b >= c ... )
            nodes.extend(flat(
                (
                    gt := GreaterEqualThan(f'force_product_order_o{out_i}_{idx_a}_{idx_b}', operands=(prod_a, prod_b)),
                    Constraint.of(gt),
                )
                for (idx_a, prod_a), (idx_b, prod_b) in pairwise(enumerate(_prod_ids))
            ))

        return nodes


class NonSharedFOutTemplate(Template, _NonSharedBase):
    """
        Class for defining the non-shared template in a subgraph annotated graph.

        @authors: Marco Biasion, Francesco Costa
    """

    @classmethod
    def define(cls, s_graph: Graph, specs: Specifications) -> TemplateBundle:
        # get prefixed graph
        a_graph: Graph = set_prefix(s_graph, 'a_')
        template_graph_builder = GraphBuilder()
        constraint_graph_builder = GraphBuilder()

        # > Template Graph

        # construct products
        (products, out_prod_mux_params, multiplexers) = cls.construct_products(a_graph, specs.ppo, template_graph_builder)

        # construct sums
        sums = cls.construct_sums(a_graph, products, template_graph_builder)

        # construct output switches (for constant False output)
        outs_p: List[BoolVariable] = []
        outs: List[If] = []
        updated_nodes: Dict[str, AnyOperation] = dict()
        for (out_i, (out_node, sum_node)) in enumerate(zip(a_graph.base_components['Subgraph'].subgraph_outputs, sums)):
            # create the constant False switch
            outs_p.append(p_o := template_graph_builder.add_node(
                f'p_o{out_i}', 
                BoolVariable
                ).add_extras(in_subgraph=True).current)
            outs.append(new_out_node := template_graph_builder.add_node(
                f'sw_o{out_i}', 
                And
                ).add_operands([p_o.name, sum_node.name]).add_extras(in_subgraph=True).current)

            # update all output successors to descend from new outputs
            for succ in filter(lambda n: not n.name in a_graph.base_components['Subgraph'].nodes_names(), a_graph.successors(out_node)):
                succ = updated_nodes.get(succ.name, succ)
                succ_operands = a_graph.base_components['Topology'].operands(succ)
                new_operands = iterable_replace(succ_operands, out_node.name, new_out_node.name)
                # updated_nodes[succ.name] = succ.copy(operands=new_operands)
                updated_nodes[succ.name] = template_graph_builder.add_node_from_node(
                    succ, 
                    a_graph,
                    operands=list(new_operands)
                    ).current

        # constants rewriting
        constants_rewriting = cls.constants_rewriting(a_graph, updated_nodes, specs, template_graph_builder)

        parameters = list(it.chain(flat(out_prod_mux_params), outs_p, constants_rewriting))  

        # template_graph_builder.add_inherited_nodes([
        #     # unchanged nodes
        #     n
        #     for n in a_graph.nodes
        #     if not n.name in a_graph.base_components['Subgraph'].nodes_names()
        #     if n.name not in updated_nodes
                            
        # ], a_graph)

        unchanged_nodes = [
            n
            for n in a_graph.nodes
            if not n.name in a_graph.base_components['Subgraph'].nodes_names()
            if n.name not in updated_nodes                     
        ]
        for n in unchanged_nodes:
            template_graph_builder.add_node_from(n, a_graph)

        # for node in updated_nodes.values():
        #     template_graph_builder.add_new_node(
        #         node, 
        #         in_subgraph=a_graph.base_components['Subgraph'].in_subgraph(node.name),
        #         weight=a_graph.base_components['Weight'].get(node.name)
        #     )

        # template_graph_builder.add_new_nodes(outs_p, in_subgraph=True)

        # template_graph_builder.add_new_nodes(outs, in_subgraph=True)

        # template_graph_builder.add_new_nodes(constants_rewriting)

        template_graph_builder.add_base_component(IO({'inputs_names': a_graph.base_components['IO'].inputs_names, 
                                                      'outputs_names': a_graph.base_components['IO'].outputs_names}))
        template_graph_builder.add_base_component(Parameter([n.name for n in parameters]))
        template_graph = template_graph_builder.create()

        # > Constraints Graph
        constraint_graph_builder.add_autofill_component('Constraints')

        # multiplexer redundancy
        # mux_red_nodes = tuple(it.chain.from_iterable(
        #     (
        #         prevent_n := Or(f'prevent_constF_{out_i}_{prod_i}_{in_i}', operands=(p_usage.name, p_assert.name)),
        #         Constraint.of(prevent_n),
        #     )
        #     for (out_i, prod_o) in enumerate(out_prod_mux_params)
        #     for (prod_i, prod_p) in enumerate(prod_o)
        #     for (in_i, (p_usage, p_assert)) in enumerate(prod_p)
        # ))
        for (out_i, prod_o) in enumerate(out_prod_mux_params):
            for (prod_i, prod_p) in enumerate(prod_o):
                for (in_i, (p_usage, p_assert)) in enumerate(prod_p):
                    prevent_n = constraint_graph_builder.add_node(
                        f'prevent_constF_{out_i}_{prod_i}_{in_i}', 
                        Or
                        ).add_operands([p_usage.name, p_assert.name]).current
                    constraint_name, operands = Constraint.of(prevent_n)
                    constraint_graph_builder.add_node(constraint_name, Constraint).add_operands(operands)

        # constant zero redundancy
        # const0_red_nodes = list(it.chain.from_iterable(
        #     (
        #         not_p_o := Not(f'not_{p_o.name}', operands=(p_o.name,)),
        #         or_ps := Or(f'or_sum_in_{sum_i}', operands=(p_usage.name for prods_p in p_o_t for (p_usage, p_assert) in prods_p)),
        #         not_or := Not(f'not_{or_ps.name}', operands=(or_ps.name,)),
        #         impl := Implies(f'impl_sum_{sum_i}', operands=(not_p_o.name, not_or.name)),
        #         Constraint.of(impl),
        #     )
        #     for sum_i, (p_o, p_o_t) in enumerate(zip(outs_p, out_prod_mux_params))
        # ))
        for sum_i, (p_o, p_o_t) in enumerate(zip(outs_p, out_prod_mux_params)):
            not_p_o = constraint_graph_builder.add_node(f'not_{p_o.name}', Not).add_operands([p_o.name]).current
            or_ps = constraint_graph_builder.add_node(f'or_sum_in_{sum_i}', Or).add_operands([p_usage.name for prods_p in p_o_t for (p_usage, p_assert) in prods_p]).current
            not_or = constraint_graph_builder.add_node(f'not_{or_ps.name}', Not).add_operands([or_ps.name]).current
            impl = constraint_graph_builder.add_node(f'impl_sum_{sum_i}', Implies).add_operands([not_p_o.name, not_or.name]).current
            constraint_name, operands = Constraint.of(impl)
            constraint_graph_builder.add_node(constraint_name, Constraint).add_operands(operands)

        # constraint_graph_builder.add_new_nodes([
        #     # placeholders
        #     PlaceHolder(name) 
        #     for name in it.chain(
        #         (p.name for p in parameters),
        #         s_graph.base_components['IO'].inputs_names,
        #         s_graph.base_components['IO'].outputs_names,
        #         template_graph.base_components['IO'].outputs_names
        #     )
        # ])
        for name in it.chain((p.name for p in parameters),
                             s_graph.base_components['IO'].inputs_names,
                             s_graph.base_components['IO'].outputs_names,
                             template_graph.base_components['IO'].outputs_names):
            constraint_graph_builder.add_node(name, PlaceHolder)


        # constraint_graph_builder.add_new_nodes(cls.atmost_lpp_constraints(out_prod_mux_params, specs.lpp))
        for n in cls.atmost_lpp_constraints(out_prod_mux_params, specs.lpp):
            constraint_graph_builder.add_node(n.name, type(n))

        # constraint_graph_builder.add_new_nodes(mux_red_nodes)

        # constraint_graph_builder.add_new_nodes(const0_red_nodes)

        # constraint_graph_builder.add_new_nodes(cls.products_order_redundancy(out_prod_mux_params))
        for n in cls.products_order_redundancy(out_prod_mux_params):
            constraint_graph_builder.add_node(n.name, type(n))

        constraint_graph = constraint_graph_builder.create()

        return TemplateBundle(template_graph, [constraint_graph])


class NonSharedFProdTemplate(Template, _NonSharedBase):
    """
        Base class for defining the non-shared template in a subgraph annotated graph.
        This variant changes how the constant false can appear.

        @authors: Marco Biasion, Francesco Costa
    """

    @classmethod
    def define(cls, s_graph: Graph, specs: Specifications) -> TemplateBundle:
        # get prefixed graph
        a_graph: Graph = set_prefix(s_graph, 'a_')
        template_graph_builder = GraphBuilder()
        constraint_graph_builder = GraphBuilder()

        # > Template Graph

        # construct products
        (products, out_prod_mux_params, multiplexers) = cls.construct_products(a_graph, specs.ppo, template_graph_builder)

        # construct sums
        sums = cls.construct_sums(a_graph, products, template_graph_builder)

        # update all output successors to descend from new outputs (sums)
        updated_nodes: Dict[str, AnyOperation] = dict()
        for (out_node, sum_node) in zip(a_graph.base_components['Subgraph'].subgraph_outputs, sums):
            for succ in filter(lambda n: not n.name in a_graph.base_components['Subgraph'].nodes_names(), a_graph.successors(out_node)):
                succ = updated_nodes.get(succ.name, succ)
                succ_operands = a_graph.base_components['Topology'].operands(succ)
                new_operands = iterable_replace(succ_operands, out_node.name, sum_node.name)
                updated_nodes[succ.name] = template_graph_builder.add_node(
                    succ.name, 
                    type(succ)
                    ).add_operands(list(new_operands)).add_extras(
                        in_subgraph=a_graph.base_components['Subgraph'].in_subgraph(succ.name),
                        weight=a_graph.base_components['Weight'].get(succ.name)
                    ).current

        # constants rewriting
        constants_rewriting = cls.constants_rewriting(a_graph, updated_nodes, specs, template_graph_builder)

        parameters = list(it.chain(flat(out_prod_mux_params), constants_rewriting))

        # template_graph_builder.add_inherited_nodes([
        #     # unchanged nodes
        #     n
        #     for n in a_graph.nodes
        #     if not n.name in a_graph.base_components['Subgraph'].nodes_names()
        #     if n.name not in updated_nodes
                            
        # ], a_graph)
        # unchanged nodes
        for n in a_graph.nodes:
            if not n.name in a_graph.base_components['Subgraph'].nodes_names():
                if n.name not in updated_nodes:
                    template_graph_builder.add_node_from(n, a_graph)

        # for node in updated_nodes.values():
        #     template_graph_builder.add_new_node(
        #         node,
        #         in_subgraph=a_graph.base_components['Subgraph'].in_subgraph(node.name),
        #         weight=a_graph.base_components['Weight'].get(node.name)
        #     )

        # template_graph_builder.add_new_nodes(constants_rewriting)

        template_graph_builder.add_base_component(IO({'inputs_names': a_graph.base_components['IO'].inputs_names, 
                                                      'outputs_names': a_graph.base_components['IO'].outputs_names}))
        template_graph_builder.add_base_component(Parameter([n.name for n in parameters]))
        template_graph = template_graph_builder.create()

        # > Constraints Graph
        constraint_graph_builder.add_autofill_component('Constraints')

        # multiplexer constF redundancy and product constF redundancy
        for (out_i, prod_o) in enumerate(out_prod_mux_params):
            firsts_false: List[Node] = []
            for (prod_i, prod_p) in enumerate(prod_o):
                first, *rest = enumerate(prod_p)

                # prevent multiplexer constF for all except first
                for (in_i, (p_usage, p_assert)) in rest:
                    # prevent_mux_constF
                    constraint_graph_builder.add_node(
                        f'prevent_constF_o{out_i}_p{prod_i}_i{in_i}', 
                        Or).add_operands([p_usage.name, p_assert.name])

                # if the first multiplexer outputs constF, force all other multiplexers to output the constant too
                (_, (first_usage_p, first_assert_p)) = first
                # constF_red_nodes:
                # first is const false
                is_not_constF = constraint_graph_builder.add_node(
                    f'is_not_constF_o{out_i}_p{prod_i}', 
                    Or).add_operands([first_usage_p.name, first_assert_p.name]).current
                is_first_false = constraint_graph_builder.add_node(
                    f'first_false_o{out_i}_p{prod_i}', 
                    Not
                    ).add_operands([is_not_constF.name]).current
                # rest is constant
                any_use = constraint_graph_builder.add_node(
                    f'any_usage_o{out_i}_p{prod_i}', 
                    Or
                    ).add_operands([p_usage.name for (p_usage, _) in prod_p]).current
                not_any_use = constraint_graph_builder.add_node(
                    f'not_{any_use.name}', 
                    Not
                    ).add_operands([any_use.name]).current
                force_if_false = constraint_graph_builder.add_node(
                    f'force_o{out_i}_p{prod_i}_const_if_first_mux_false', 
                    Implies
                    ).add_operands([is_first_false.name, not_any_use.name]).current
                
                
                firsts_false.append(is_first_false)

            # force products to be either all constants or noone constant
            # constF_red_nodes
            all_prods_const = constraint_graph_builder.add_node(
                f'all_prods_const_o{out_i}', 
                And
                ).add_operands([n.name for n in firsts_false]).current
            some_prods_const = constraint_graph_builder.add_node(
                f'some_prods_const_o{out_i}', 
                Or
                ).add_operands([n.name for n in firsts_false]).current
            none_prod_const = constraint_graph_builder.add_node(
                f'none_prod_const_o{out_i}', 
                Not
                ).add_operands([some_prods_const.name]).current
            all_or_none = constraint_graph_builder.add_node(
                f'all_or_none_const_o{out_i}', 
                Or
                ).add_operands([all_prods_const.name, none_prod_const.name]).current

        # constraint_graph_builder.add_new_nodes([
        #     # placeholders
        #     PlaceHolder(name) 
        #     for name in it.chain(
        #         (p.name for p in parameters),
        #         s_graph.base_components['IO'].inputs_names,
        #         s_graph.base_components['IO'].outputs_names,
        #         template_graph.base_components['IO'].outputs_names
        #     )
        # ])
        # placeholders
        for name in it.chain((p.name for p in parameters),
                             s_graph.base_components['IO'].inputs_names,
                             s_graph.base_components['IO'].outputs_names,
                             template_graph.base_components['IO'].outputs_names):
            constraint_graph_builder.add_node(name, PlaceHolder)

        # constraint_graph_builder.add_new_nodes(cls.atmost_lpp_constraints(out_prod_mux_params, specs.lpp))
        for c in cls.atmost_lpp_constraints(out_prod_mux_params, specs.lpp):
            template_graph_builder.add_node(c.name, type(c))

        # constraint_graph_builder.add_new_nodes(prevent_mux_constF)

        # constraint_graph_builder.add_new_nodes(constF_red_nodes)

        # constraint_graph_builder.add_new_nodes(cls.products_order_redundancy(out_prod_mux_params))
        for c in cls.products_order_redundancy(out_prod_mux_params):
            template_graph_builder.add_node(c.name, type(c))

        constraint_graph = constraint_graph_builder.create()

        return TemplateBundle(template_graph, [constraint_graph])
