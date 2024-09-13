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
        a_graph = graph.with_prefix('a_')

        # > Template Graph

        # construct products
        products: List[And] = []
        products_p: List[List[Tuple[BoolInput, BoolInput]]] = []
        multiplexers: List[Multiplexer] = []
        for prod_i in range(specs.pit):
            # create all multiplexers for the product
            _muxs = []
            products_p.append([])
            for in_i, in_node in enumerate(a_graph.subgraph_inputs):
                products_p[-1].append((
                    (p_s := BoolInput(f'p_p{prod_i}_i{in_i}_s', in_subgraph=True)),
                    (p_l := BoolInput(f'p_p{prod_i}_i{in_i}_l', in_subgraph=True)),
                ))
                _muxs.append(Multiplexer(f'mux_p{prod_i}_i{in_i}', in_subgraph=True, items=[in_node, p_s, p_l]))

            # create the product (and store multiplexers)
            products.append(And(f'prod{prod_i}', in_subgraph=True, items=_muxs))
            multiplexers.extend(_muxs)

        # construct sums and constant 0 switch
        sums = []
        sums_p: List[List[BoolInput]] = []
        switches = []
        outs_p: List[BoolInput] = []
        outs: List[Switch] = []
        out_successors: List[OperationNode] = []
        for out_i, out_node in enumerate(a_graph.subgraph_outputs):
            # create all switches for the output
            _sws = []
            sums_p.append([])
            for prod_i, prod_node in enumerate(products):
                sums_p[-1].append(param := BoolInput(f'p_o{out_i}_p{prod_i}', in_subgraph=True))
                _sws.append(Switch(f'sw_o{out_i}_p{prod_i}', in_subgraph=True, items=[prod_node, param], value=True))

            # create the sum and constant 0 switch
            sums.append(_sum := Or(f'sum{out_i}', in_subgraph=True, items=_sws))
            switches.extend(_sws)
            outs_p.append(p_o := BoolInput(f'p_o{out_i}', in_subgraph=True))
            outs.append(new_out_node := Switch(f'sw_o{out_i}', in_subgraph=True, items=(_sum, p_o), value=False))

            # update all output successors to descend from new outputs
            for succ in a_graph.successors(out_node):
                i = succ.items.index(out_node.name)
                new_items = succ.items[:i] + (new_out_node.name,) + succ.items[i+1:]
                out_successors.append(succ.copy(items=new_items))

        # create template graph
        succs_names = set(s.name for s in out_successors)
        nodes = it.chain(
            (  # unchanged nodes
                n
                for n in a_graph.nodes
                if n not in a_graph.subgraph_nodes
                if n.name not in succs_names
            ),
            # products and relative items
            products,
            flat(products_p),
            multiplexers,
            # sums and relative items
            sums,
            flat(sums_p),
            switches,
            outs_p,
            outs,
            # updated successors
            out_successors,
        )
        template_graph = TGraph(
            nodes,
            a_graph.inputs_names, a_graph.outputs_names,
            (n.name for n in flat((products_p, sums_p)))
        )

        # > Constraints Graph

        # error constraint
        error_nodes = [
            cur_int := ToInt('cur_int', items=graph.outputs_names),
            tem_int := ToInt('tem_int', items=template_graph.outputs_names),
            abs_diff := AbsDiff('abs_diff', items=(cur_int.name, tem_int.name,)),
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

        constraint_graph = CGraph(it.chain(
            (PlaceHolder(node.name) for node in flat((sums_p, products_p, outs_p, sums_p))),
            (PlaceHolder(name) for name in graph.outputs_names),
            (PlaceHolder(name) for name in template_graph.outputs_names),
            error_nodes,
            its_nodes,
            mux_red_nodes,
            const0_red_nodes,
            prod_ints,
            prod_ord_nodes,
        ))

        return (template_graph, constraint_graph)
