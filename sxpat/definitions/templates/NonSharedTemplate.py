from typing import Dict, List, Sequence, Tuple, Union

import itertools as it

from .Template import Template, TemplateBundle

from sxpat.converting import set_prefix
from sxpat.graph import *
from sxpat.graph.node import *
from sxpat.specifications import ConstantsType, Specifications
from sxpat.utils.collections import flat, iterable_replace, pairwise
from sxpat.graph.components import Subgraph


__all__ = ['NonSharedFOutTemplate', 'NonSharedFProdTemplate']


class _NonSharedBase:
    """
       Base class for non shared templates.
       Includes common utilities.

       @authors: Marco Biasion
    """

    @classmethod
    def construct_products(cls, a_graph: IOGraph, products_per_output: int, graph_builder: GraphBuilder
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
                        # COMMENT:from-MARCO: valid, but we have to make sure that we will mark these nodes as being in the subgraph
                        # from-ILIA: fixed by using 'subgraph_set'
                        (p_usage := BoolVariable(f'p_o{out_i}_t{prod_i}_i{in_i}_u')), #HERE MARK SUBGRAPH
                        (p_assert := BoolVariable(f'p_o{out_i}_t{prod_i}_i{in_i}_a')), #HERE MARK SUBGRAPH
                    ))
                    _muxs.append(Multiplexer(f'mux_o{out_i}_t{prod_i}_i{in_i}', operands=[in_node, p_usage, p_assert])) #HERE MARK SUBGRAPH
                out_prod_mux_params[-1].append(parameters)
                multiplexers.extend(_muxs)

                # create the product
                products[-1].append(And(f'o{out_i}_p{prod_i}', operands=_muxs)) #HERE MARK SUBGRAPH

        for node in flat(products):
            graph_builder.add_new_node(node, in_subgraph=True)
        for node in flat(out_prod_mux_params):
            graph_builder.add_new_node(node, in_subgraph=True)
        for node in multiplexers:
            graph_builder.add_new_node(node, in_subgraph=True)

        return (
            products,
            out_prod_mux_params,
            multiplexers,
        )

    @classmethod
    def construct_sums(cls, a_graph: IOGraph, products: List[List[And]], graph_builder: GraphBuilder
                       ) -> List[Or]:
        or_list = [
            Or(f'sum{out_i}', operands=products[out_i]) #HERE MARK SUBGRAPH
            for out_i, _ in enumerate(a_graph.base_components['Subgraph'].subgraph_outputs)
        ]

        for node in or_list:
            graph_builder.add_new_node(node, in_subgraph=True)

        return or_list
        

    @classmethod
    def constants_rewriting(cls, a_graph: IOGraph, updated_nodes: Dict[str, AnyOperation], specs: Specifications
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
            if len(succs := a_graph.successors(const)) == 1 and (out_i := a_graph.output_index_of(succ := succs[0])) >= 0:
                constants_parameters.append(const_rew := BoolVariable(f'p_c{out_i}'))
                # NODE COPY
                updated_nodes[succ.name] = succ.copy(operands=(const_rew,))  # by definition, the output node has no other operand

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
    def define(cls, s_graph: IOGraph, specs: Specifications) -> TemplateBundle:
        # get prefixed graph
        # a_graph: IOGraph = set_prefix(s_graph, 'a_') TODO: fix the rename issue!!
        a_graph: IOGraph = s_graph
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
            # COMMENT:from-MARCO: valid but we have to make sure we mark these nodes as being in the subgraph
            # from-ILIA: fixed by using 'template_subgraph_set' and 'constraint_subgraph_set'
            outs_p.append(p_o := BoolVariable(f'p_o{out_i}')) #HERE MARK SUBGRAPH
            outs.append(new_out_node := And(f'sw_o{out_i}', operands=(p_o, sum_node))) #HERE MARK SUBGRAPH

            # update all output successors to descend from new outputs
            for succ in filter(lambda n: not n.name in a_graph.base_components['Subgraph'].nodes_names(), a_graph.successors(out_node)):
                succ = updated_nodes.get(succ.name, succ)
                new_operands = iterable_replace(succ.operands, out_node.name, new_out_node.name)
                updated_nodes[succ.name] = succ.copy(operands=new_operands) # NODE COPY

        # constants rewriting
        constants_rewriting = cls.constants_rewriting(a_graph, updated_nodes, specs)

        parameters = list(it.chain(flat(out_prod_mux_params), outs_p, constants_rewriting))  

        template_graph_builder.add_inherited_nodes([
            # unchanged nodes
            n
            for n in a_graph.nodes
            if not n.name in a_graph.base_components['Subgraph'].nodes_names()
            if n.name not in updated_nodes
                            
        ], a_graph)

        for node in updated_nodes.values():
            template_graph_builder.add_new_node(
                node, 
                in_subgraph=a_graph.base_components['Subgraph'].in_subgraph(node.name),
                weight=a_graph.base_components['Weight'].get(node.name)
            )

        template_graph_builder.add_new_nodes(outs_p, in_subgraph=True)

        template_graph_builder.add_new_nodes(outs, in_subgraph=True)

        template_graph_builder.add_new_nodes(constants_rewriting)

        template_graph = template_graph_builder.create(PGraph, 
                                                        a_graph.inputs_names, 
                                                        a_graph.outputs_names,
                                                        (n.name for n in parameters))

        # # create template graph
        # # GRAPH CREATION/COPY
        # template_graph = PGraph(
        #     it.chain(  # nodes
        #         (  # unchanged nodes
        #             n
        #             for n in a_graph.nodes
        #             if not n.name in a_graph.base_components['Subgraph'].nodes_names()
        #             if n.name not in updated_nodes
        #         ),
        #         # changed nodes
        #         updated_nodes.values(),
        #         # products and relative operands
        #         multiplexers, flat(products),
        #         flat(out_prod_mux_params),
        #         # sums and relative operands
        #         sums, outs_p, outs,
        #         # output constant rewriting
        #         constants_rewriting,
        #     ),
        #     a_graph.inputs_names, a_graph.outputs_names,
        #     (n.name for n in parameters),
        #     # COMMENT:from-MARCO: given the comments about marking subgraph nodes, here we should read the subgraph component, with the relevant added nodes
        #     [Subgraph(template_subgraph_set)],
        # )

        # > Constraints Graph

        # multiplexer redundancy
        mux_red_nodes = tuple(it.chain.from_iterable(
            (
                prevent_n := Or(f'prevent_constF_{out_i}_{prod_i}_{in_i}', operands=(p_usage.name, p_assert.name)),
                Constraint.of(prevent_n),
            )
            for (out_i, prod_o) in enumerate(out_prod_mux_params)
            for (prod_i, prod_p) in enumerate(prod_o)
            for (in_i, (p_usage, p_assert)) in enumerate(prod_p)
        ))

        # constant zero redundancy
        const0_red_nodes = list(it.chain.from_iterable(
            (
                not_p_o := Not(f'not_{p_o.name}', operands=(p_o.name,)),
                or_ps := Or(f'or_sum_in_{sum_i}', operands=(p_usage.name for prods_p in p_o_t for (p_usage, p_assert) in prods_p)),
                not_or := Not(f'not_{or_ps.name}', operands=(or_ps.name,)),
                impl := Implies(f'impl_sum_{sum_i}', operands=(not_p_o.name, not_or.name)),
                Constraint.of(impl),
            )
            for sum_i, (p_o, p_o_t) in enumerate(zip(outs_p, out_prod_mux_params))
        ))

        constraint_graph_builder.add_new_nodes([
            # placeholders
            PlaceHolder(name) 
            for name in it.chain(
                (p.name for p in parameters),
                s_graph.inputs_names,
                s_graph.outputs_names,
                template_graph.outputs_names
            )
        ])

        constraint_graph_builder.add_new_nodes(cls.atmost_lpp_constraints(out_prod_mux_params, specs.lpp))

        constraint_graph_builder.add_new_nodes(mux_red_nodes)

        constraint_graph_builder.add_new_nodes(const0_red_nodes)

        constraint_graph_builder.add_new_nodes(cls.products_order_redundancy(out_prod_mux_params))

        constraint_graph = constraint_graph_builder.create(CGraph)

        # # create constraints graph
        # # GRAPH CREATION/COPY
        # constraint_graph = CGraph(
        #     it.chain(  # nodes
        #         # placeholders
        #         (PlaceHolder(name) for name in it.chain(
        #             (p.name for p in parameters),
        #             s_graph.inputs_names,
        #             s_graph.outputs_names,
        #             template_graph.outputs_names
        #         )),
        #         # behavioural constraints
        #         cls.atmost_lpp_constraints(out_prod_mux_params, specs.lpp),
        #         # redundancy constraints
        #         mux_red_nodes,
        #         const0_red_nodes,
        #         cls.products_order_redundancy(out_prod_mux_params),
        #     ),
        #     [Subgraph(constraint_subgraph_set)],
        # )

        return TemplateBundle(template_graph, [constraint_graph])


class NonSharedFProdTemplate(Template, _NonSharedBase):
    """
        Base class for defining the non-shared template in a subgraph annotated graph.
        This variant changes how the constant false can appear.

        @authors: Marco Biasion, Francesco Costa
    """

    @classmethod
    def define(cls, s_graph: IOGraph, specs: Specifications) -> TemplateBundle:
        # get prefixed graph
        a_graph: IOGraph = set_prefix(s_graph, 'a_')
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
                new_operands = iterable_replace(succ.operands, out_node.name, sum_node.name)
                updated_nodes[succ.name] = succ.copy(operands=new_operands) # NODE COPY

        # constants rewriting
        constants_rewriting = cls.constants_rewriting(a_graph, updated_nodes, specs)

        parameters = list(it.chain(flat(out_prod_mux_params), constants_rewriting))

        template_graph_builder.add_inherited_nodes([
            # unchanged nodes
            n
            for n in a_graph.nodes
            if not n.name in a_graph.base_components['Subgraph'].nodes_names()
            if n.name not in updated_nodes
                            
        ], a_graph)

        for node in updated_nodes.values():
            template_graph_builder.add_new_node(
                node,
                in_subgraph=a_graph.base_components['Subgraph'].in_subgraph(node.name),
                weight=a_graph.base_components['Weight'].get(node.name)
            )

        template_graph_builder.add_new_nodes(constants_rewriting)

        template_graph = template_graph_builder.create(PGraph,
                                                       a_graph.inputs_names, 
                                                       a_graph.outputs_names,
                                                       (n.name for n in parameters))

        # # create template graph
        # # GRAPH CREATION/COPY
        # template_graph = PGraph(
        #     it.chain(  # nodes
        #         (  # unchanged nodes
        #             n
        #             for n in a_graph.nodes
        #             if not n.name in a_graph.base_components['Subgraph'].nodes_names()
        #             if n.name not in updated_nodes
        #         ),
        #         # changed nodes
        #         updated_nodes.values(),
        #         # products and relative operands
        #         multiplexers, flat(products),
        #         flat(out_prod_mux_params),
        #         # sums and relative operands
        #         sums,
        #         # output constant rewriting
        #         constants_rewriting,
        #     ),
        #     a_graph.inputs_names, a_graph.outputs_names,
        #     (n.name for n in parameters),
        #     [Subgraph(template_subgraph_set)],
        # )

        # > Constraints Graph

        # multiplexer constF redundancy and product constF redundancy
        prevent_mux_constF = []
        constF_red_nodes = []
        for (out_i, prod_o) in enumerate(out_prod_mux_params):
            firsts_false: List[Node] = []
            for (prod_i, prod_p) in enumerate(prod_o):
                first, *rest = enumerate(prod_p)

                # prevent multiplexer constF for all except first
                for (in_i, (p_usage, p_assert)) in rest:
                    prevent_mux_constF.append(Or(f'prevent_constF_o{out_i}_p{prod_i}_i{in_i}', operands=(p_usage, p_assert)))

                # if the first multiplexer outputs constF, force all other multiplexers to output the constant too
                (_, (first_usage_p, first_assert_p)) = first
                constF_red_nodes.extend((
                    # first is const false
                    is_not_constF := Or(f'is_not_constF_o{out_i}_p{prod_i}', operands=(first_usage_p, first_assert_p)),
                    is_first_false := Not(f'first_false_o{out_i}_p{prod_i}', operands=(is_not_constF,)),
                    # rest is constant
                    any_use := Or(f'any_usage_o{out_i}_p{prod_i}', operands=(p_usage for (p_usage, _) in prod_p)),
                    not_any_use := Not(f'not_{any_use.name}', operands=(any_use,)),
                    force_if_false := Implies(f'force_o{out_i}_p{prod_i}_const_if_first_mux_false', operands=(is_first_false, not_any_use)),
                ))
                firsts_false.append(is_first_false)

            # force products to be either all constants or noone constant
            constF_red_nodes.extend((
                all_prods_const := And(f'all_prods_const_o{out_i}', operands=firsts_false),
                some_prods_const := Or(f'some_prods_const_o{out_i}', operands=firsts_false),
                none_prod_const := Not(f'none_prod_const_o{out_i}', operands=(some_prods_const,)),
                all_or_none := Or(f'all_or_none_const_o{out_i}', operands=(all_prods_const, none_prod_const)),
            ))

        constraint_graph_builder.add_new_nodes([
            # placeholders
            PlaceHolder(name) 
            for name in it.chain(
                (p.name for p in parameters),
                s_graph.inputs_names,
                s_graph.outputs_names,
                template_graph.outputs_names
            )
        ])

        constraint_graph_builder.add_new_nodes(cls.atmost_lpp_constraints(out_prod_mux_params, specs.lpp))

        constraint_graph_builder.add_new_nodes(prevent_mux_constF)

        constraint_graph_builder.add_new_nodes(constF_red_nodes)

        constraint_graph_builder.add_new_nodes(cls.products_order_redundancy(out_prod_mux_params))

        constraint_graph = constraint_graph_builder.create(CGraph)

        # # create constraints graph
        # # GRAPH CREATION/COPY
        # constraint_graph = CGraph(
        #     it.chain(  # nodes
        #         # placeholders
        #         (PlaceHolder(name) for name in it.chain(
        #             (p.name for p in parameters),
        #             s_graph.inputs_names,
        #             s_graph.outputs_names,
        #             template_graph.outputs_names
        #         )),
        #         # behavioural constraints
        #         cls.atmost_lpp_constraints(out_prod_mux_params, specs.lpp),
        #         # redundancy constraints
        #         prevent_mux_constF,
        #         constF_red_nodes,
        #         cls.products_order_redundancy(out_prod_mux_params),
        #     ),
        #     [Subgraph(constraint_subgraph_set)],
        # )

        return TemplateBundle(template_graph, [constraint_graph])
