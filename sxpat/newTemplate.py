from typing import List, Tuple

import itertools as it

from sxpat.newGraph import *
from sxpat.specifications import Specifications
from sxpat.utils.collections import flat, pairwise


__all__ = [
    'SharedTemplate',
]


class SharedTemplate:
    @classmethod
    def define_template(cls, graph: SGraph, specs: Specifications) -> Tuple[TGraph, CGraph]:
        # get prefixed graph
        a_graph: SGraph = graph.with_prefix('a_')

        # > Template Graph

        # construct products
        products: List[And] = []
        products_p: List[List[Tuple[BoolVariable, BoolVariable]]] = []
        multiplexers: List[Multiplexer] = []
        for prod_i in range(specs.pit):
            # create all multiplexers for the product
            _muxs = []
            products_p.append([])
            for in_i, in_node in enumerate(a_graph.subgraph_inputs):
                products_p[-1].append((
                    (p_s := BoolVariable(f'p_p{prod_i}_i{in_i}_s', in_subgraph=True)),
                    (p_l := BoolVariable(f'p_p{prod_i}_i{in_i}_l', in_subgraph=True)),
                ))
                _muxs.append(Multiplexer(f'mux_p{prod_i}_i{in_i}', in_subgraph=True, items=[in_node, p_s, p_l]))

            # create the product (and store multiplexers)
            products.append(And(f'prod{prod_i}', in_subgraph=True, items=_muxs))
            multiplexers.extend(_muxs)

        # construct sums and constant 0 switch
        consts = {True: BoolConstant('ct', value=True), False: BoolConstant('cf', value=False)}
        sums = []
        sums_p: List[List[BoolVariable]] = []
        switches = []
        outs_p: List[BoolVariable] = []
        outs: List[Switch] = []
        out_successors: List[OperationNode] = []
        for out_i, out_node in enumerate(a_graph.subgraph_outputs):
            # create all switches for the output
            _sws = []
            sums_p.append([])
            for prod_i, prod_node in enumerate(products):
                sums_p[-1].append(param := BoolVariable(f'p_o{out_i}_p{prod_i}', in_subgraph=True))
                _sws.append(Switch(f'sw_o{out_i}_p{prod_i}', in_subgraph=True, items=[prod_node, param, consts[True]]))

            # create the sum and constant 0 switch
            sums.append(_sum := Or(f'sum{out_i}', in_subgraph=True, items=_sws))
            switches.extend(_sws)
            outs_p.append(p_o := BoolVariable(f'p_o{out_i}', in_subgraph=True))
            outs.append(new_out_node := Switch(f'sw_o{out_i}', in_subgraph=True, items=(_sum, p_o, consts[False])))

            # update all output successors to descend from new outputs
            for succ in a_graph.successors(out_node):
                if not succ.in_subgraph:
                    i = succ.items.index(out_node.name)
                    new_items = succ.items[:i] + (new_out_node.name,) + succ.items[i+1:]
                    out_successors.append(succ.copy(items=new_items))

        # create template graph
        succs_names = frozenset(s.name for s in out_successors)
        nodes = it.chain(
            (  # unchanged nodes
                n
                for n in a_graph.nodes
                if not n.in_subgraph
                if n.name not in succs_names
            ),
            # constants
            consts.values(),
            # products and relative items
            flat(products_p),
            multiplexers,
            products,
            # sums and relative items
            flat(sums_p),
            switches,
            sums,
            outs_p,
            outs,
            # updated successors
            out_successors,
        )
        template_graph = TGraph(
            nodes,
            a_graph.inputs_names, a_graph.outputs_names,
            (n.name for n in flat((products_p, sums_p, outs_p)))
        )

        # > Constraints Graph

        # error constraint
        error_nodes = [
            cur_int := ToInt('cur_int', items=graph.outputs_names),
            tem_int := ToInt('tem_int', items=template_graph.outputs_names),
            abs_diff := AbsDiff('abs_diff', items=(cur_int, tem_int,)),
            et := IntConstant('et', value=specs.et),
            error_check := LessEqualThan('error_check', items=(abs_diff, et)),
        ]
        # its constraint
        its_nodes = [
            its := IntConstant('its', value=specs.its),
            at_most_its := AtMost('at_most_its', items=(*flat(sums_p), its)),
        ]
        # multiplexer redundancy
        mux_red_nodes = [
            Implies(f'impl_mux_{im_i}', items=(p_l.name, p_s.name))
            for im_i, prod_p in enumerate(products_p)
            for p_s, p_l in prod_p
        ]
        # constant zero redundancy
        const0_red_nodes = list(flat(
            (
                not_p_o := Not(f'not_{p_o.name}', items=(p_o.name,)),
                or_ps := Or(f'or_sum_in_{sum_i}', items=(n.name for n in p_o_ps)),
                not_or := Not(f'not_{or_ps.name}', items=(or_ps.name,)),
                impl := Implies(f'impl_sum_{sum_i}', items=(not_p_o.name, not_or.name)),
            )
            for sum_i, (p_o, p_o_ps) in enumerate(zip(outs_p, sums_p))
        ))

        # order of products redundancy
        prod_ints = [
            ToInt(f'prod{prod_i}_int', items=flat(prod_p))
            for prod_i, prod_p in enumerate(products_p)
        ]
        prod_ord_nodes = [
            GreaterThan(f'gt_{idx_a}_{idx_b}', items=(prod_a, prod_b))
            for (idx_a, prod_a), (idx_b, prod_b) in pairwise(enumerate(prod_ints))
        ]

        # target definition
        targets = [
            Target(f't_{param.name}', items=(param.name,))
            for param in flat((sums_p, products_p, outs_p, sums_p))
        ]

        nodes = it.chain(
            # placeholders
            (PlaceHolder(node.name) for node in flat((sums_p, products_p, outs_p, sums_p))),
            (PlaceHolder(name) for name in graph.outputs_names),
            (PlaceHolder(name) for name in template_graph.outputs_names),
            # constants
            consts.values(),
            # ints and error
            error_nodes,
            # its constraints
            its_nodes,
            # redundancy constraints
            mux_red_nodes,
            const0_red_nodes,
            prod_ints,
            prod_ord_nodes,
            targets,
        )
        constraint_graph = CGraph(nodes)

        return (template_graph, constraint_graph)


class SOPTemplate:
    """TODO: REVIEW AFTER PIPELINE CHANGES"""

    @classmethod
    def define_template(cls, graph: SGraph, specs: Specifications) -> Tuple[TGraph, CGraph]:
        # get prefixed graph
        a_graph: SGraph = graph.with_prefix('a_')

        # > Template Graph

        # construct products
        products: List[And] = []
        products_p: List[List[List[Tuple[BoolVariable, BoolVariable]]]] = []
        multiplexers: List[Multiplexer] = []
        for out_i in range(a_graph.subgraph_outputs):
            products_p.append([])
            for prod_i in range(specs.ppo):
                # create all multiplexers for the product
                _muxs = []
                products_p.append([])
                for in_i, in_node in enumerate(a_graph.subgraph_inputs):
                    products_p[-1].append((
                        (p_s := BoolVariable(f'p_o{out_i}_t{prod_i}_i{in_i}_s', in_subgraph=True)),
                        (p_l := BoolVariable(f'p_o{out_i}_t{prod_i}_i{in_i}_l', in_subgraph=True)),
                    ))
                    _muxs.append(Multiplexer(f'mux_o{out_i}_t{prod_i}_i{in_i}', in_subgraph=True, items=[in_node, p_s, p_l]))

                # create the product (and store multiplexers)
                products.append(And(f'prod{prod_i}', in_subgraph=True, items=_muxs))
                multiplexers.extend(_muxs)

        # construct sums and constant 0 switch
        consts = {True: BoolConstant('ct', value=True), False: BoolConstant('cf', value=False)}
        sums = []
        switches = []
        outs_p: List[BoolVariable] = []
        outs: List[Switch] = []
        out_successors: List[OperationNode] = []
        for out_i, out_node in enumerate(a_graph.subgraph_outputs):
            # create the sum and constant 0 switch
            _sws = []
            sums.append(_sum := Or(f'sum{out_i}', in_subgraph=True, items=_sws))
            switches.extend(_sws)
            outs_p.append(p_o := BoolVariable(f'p_o{out_i}', in_subgraph=True))
            outs.append(new_out_node := Switch(f'sw_o{out_i}', in_subgraph=True, items=(_sum, p_o, consts[False])))

            # update all output successors to descend from new outputs
            for succ in a_graph.successors(out_node):
                if not succ.in_subgraph:
                    i = succ.items.index(out_node.name)
                    new_items = succ.items[:i] + (new_out_node.name,) + succ.items[i+1:]
                    out_successors.append(succ.copy(items=new_items))

        # create template graph
        succs_names = frozenset(s.name for s in out_successors)
        nodes = it.chain(
            (  # unchanged nodes
                n
                for n in a_graph.nodes
                if not n.in_subgraph
                if n.name not in succs_names
            ),
            # constants
            consts.values(),
            # products and relative items
            flat(products_p),
            multiplexers,
            products,
            # sums and relative items
            switches,
            sums,
            outs_p,
            outs,
            # updated successors
            out_successors,
        )
        template_graph = TGraph(
            nodes,
            a_graph.inputs_names, a_graph.outputs_names,
            (n.name for n in flat((products_p, outs_p)))
        )

        # > Constraints Graph

        # error constraint
        error_nodes = [
            cur_int := ToInt('cur_int', items=graph.outputs_names),
            tem_int := ToInt('tem_int', items=template_graph.outputs_names),
            abs_diff := AbsDiff('abs_diff', items=(cur_int, tem_int,)),
            et := IntConstant('et', value=specs.et),
            error_check := LessEqualThan('error_check', items=(abs_diff, et)),
        ]

        # lpp constraint
        lpp_nodes = list(it.chain(
            (lpp := IntConstant('lpp', value=specs.lpp),),
            (
                AtMost('at_most_lpp', items=([p[0] for p in prod_t], lpp))
                for prod_o in products_p
                for prod_t in prod_o
            )
        ))

        # multiplexer redundancy
        mux_red_nodes = [
            Implies(f'impl_mux_{im_o}_{im_i}', items=(p_l.name, p_s.name))
            for im_o, prod_o in enumerate(products_p)
            for im_i, prod_p in enumerate(prod_o)
            for p_s, p_l in prod_p
        ]
        # constant zero redundancy
        const0_red_nodes = list(flat(
            (
                not_p_o := Not(f'not_{p_o.name}', items=(p_o.name,)),
                or_ps := Or(f'or_sum_in_{sum_i}', items=(n.name for p_o_t_isl in p_o_t for n in p_o_t_isl)),
                not_or := Not(f'not_{or_ps.name}', items=(or_ps.name,)),
                impl := Implies(f'impl_sum_{sum_i}', items=(not_p_o.name, not_or.name)),
            )
            for sum_i, (p_o, p_o_t) in enumerate(zip(outs_p, products_p))
        ))

        # order of products redundancy
        prod_ints = [
            ToInt(f'prod{prod_i}_int', items=flat(prod_p))
            for prod_i, prod_p in enumerate(products_p)
        ]
        prod_ord_nodes = [
            GreaterThan(f'gt_{idx_a}_{idx_b}', items=(prod_a, prod_b))
            for (idx_a, prod_a), (idx_b, prod_b) in pairwise(enumerate(prod_ints))
        ]

        nodes = it.chain(
            # placeholders
            (PlaceHolder(node.name) for node in flat((products_p, outs_p))),
            (PlaceHolder(name) for name in graph.outputs_names),
            (PlaceHolder(name) for name in template_graph.outputs_names),
            # constants
            consts.values(),
            # ints and error
            error_nodes,
            # its constraints
            lpp_nodes,
            # redundancy constraints
            mux_red_nodes,
            const0_red_nodes,
            prod_ints,
            prod_ord_nodes,
        )
        constraint_graph = CGraph(nodes)

        return (template_graph, constraint_graph)
