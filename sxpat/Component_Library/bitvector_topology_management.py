import math
import networkx as nx
from z3 import Datatype, BitVecSort, BoolSort, BitVecVal, BoolVal, And, Not, Bool, If, Or, Implies, is_true, sat, Sum
import pprint
import re
from sxpat.utils.graph import is_selection_convex

class BitvectorTopologyManagement:
    
    @staticmethod
    def datatype_model_initialization(graph, weight_key, input_dict, gate_dict, output_dict, constant_dict, opt, num_outputs, num_gates):
        """
        i) Architecture Initialization & ii) Graph Data Ingestion using Z3 Datatype and BitVec.
        """
        # loose bound but since it's logarithmic it's still ok
        NUM_BITS = num_outputs + math.ceil(math.log2(num_gates))

        Node = Datatype('Node')
        Node.declare('mk_node', ('id', BitVecSort(NUM_BITS)), ('weight', BitVecSort(NUM_BITS)), ('in_subgraph', BoolSort()))
        Node = Node.create()

        # Define a custom datatype for Edge
        Edge = Datatype('Edge')
        Edge.declare('mk_edge', ('source', Node), ('target', Node))
        Edge = Edge.create()

        nodes = {}
        edges = []

        # Graph Data Ingestion for Inputs
        for in_idx in input_dict:
            node_label = input_dict[in_idx]
            weight = graph.nodes[node_label][weight_key]
            node = Node.mk_node(BitVecVal(in_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(in_idx, NUM_BITS))

            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node

        # Graph Data Ingestion for Gates
        for g_idx in gate_dict:
            node_label = gate_dict[g_idx]
            weight = graph.nodes[node_label][weight_key]
            node = Node.mk_node(BitVecVal(g_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(g_idx, NUM_BITS))
            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            if weight == -1:
                opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node

        # Graph Data Ingestion for Outputs
        for o_idx in output_dict:
            node_label = output_dict[o_idx]
            weight = graph.nodes[node_label][weight_key]
            node = Node.mk_node(BitVecVal(o_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(o_idx, NUM_BITS))

            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node

        # Graph Data Ingestion for Constants
        for c_idx in constant_dict:
            node_label = constant_dict[c_idx]
            weight = graph.nodes[node_label][weight_key]
            node = Node.mk_node(BitVecVal(c_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(c_idx, NUM_BITS))

            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node

        # Edge Ingestion
        for src, des in graph.edges:
            edge = Edge.mk_edge(nodes[src], nodes[des])
            opt.add(Edge.source(edge) == nodes[src])
            opt.add(Edge.target(edge) == nodes[des])
            edges.append(edge)

        return Node, Edge, nodes, edges, NUM_BITS

    @staticmethod
    def datatype_signal_propagation_constraints (graph, nodes, Node, NUM_BITS):
        """
        iii) Symbolic Cut & Flow Analysis
        """
        unique_outgoing_edges = []
        unique_incoming_edges = []

        for node_label in nodes:
            node = nodes[node_label]
            outgoing_conditions = []
            incoming_conditions = []

            for src, des in graph.edges(node_label):
                if src == node_label:
                    outgoing_conditions.append(And(Node.in_subgraph(nodes[src]), Not(Node.in_subgraph(nodes[des]))))
                if src == node_label:
                    incoming_conditions.append(And(Not(Node.in_subgraph(nodes[src])), Node.in_subgraph(nodes[des])))

            if outgoing_conditions:
                unique_outgoing_edges.append(If(Or(outgoing_conditions), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS)))
            if incoming_conditions:
                unique_incoming_edges.append(If(Or(incoming_conditions), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS)))

        # incoming_edges = [If(And(Not(Node.in_subgraph(Edge.source(edge))), Node.in_subgraph(Edge.target(edge))), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS))
        #                   for edge in edges]
        # outgoint_edges = [If(And(Node.in_subgraph(Edge.source(edge)), Not(Node.in_subgraph(Edge.target(edge)))), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS))
        #                   for edge in edges]
        max_nodes = [If(Node.in_subgraph(node), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS)) for node in nodes.values()]

        # max_nodes = [  for edge in edges]
        # max_nodes = [BitVecVal(ToInt(Node.in_subgraph(node)), NUM_BITS) for node in nodes.values()]

        return unique_incoming_edges, unique_outgoing_edges, max_nodes
        
    @staticmethod
    def datatype_convexity_and_structural_constraints(graph, nodes, Node, opt):
        """
        iv) Node-Level Structural Integrity
        """
        descendants = {}
        ancestors = {}
        for node in nodes:
            if node not in descendants:
                descendants[node] = sorted(nx.descendants(graph, node))
            if node not in ancestors:
                ancestors[node] = sorted(nx.ancestors(graph, node))

        for src in nodes:
            for des in graph.successors(src):
                if len(descendants[des]) > 0:
                    not_descendants = [Not(Node.in_subgraph(nodes[l])) for l in descendants[des]]
                    not_descendants.append(Not(Node.in_subgraph(nodes[des])))
                    descendant_condition = Implies(
                        And(Node.in_subgraph(nodes[src]), Not(Node.in_subgraph(nodes[des]))),
                        And(not_descendants)
                    )
                    opt.add(descendant_condition)
                if len(ancestors[src]) > 0:
                    not_ancestors = [Not(Node.in_subgraph(nodes[l])) for l in ancestors[src]]
                    not_ancestors.append(Not(Node.in_subgraph(nodes[src])))
                    ancestor_condition = Implies(
                        And(Not(Node.in_subgraph(nodes[src])), Node.in_subgraph(nodes[des])),
                        And(not_ancestors)
                    )
                    opt.add(ancestor_condition)

    @staticmethod
    def datatype_optimization_and_selection_constraints(opt, max_nodes, graph, gate_dict, imax=None, omax=None, 
        unique_incoming_edges=None, unique_outgoing_edges=None, apply_io_limits=False):
        """
        vi) Optimization & Maximization Objective & vii)  Structural Integrity Audit (Global Graph Context)
        """
        if apply_io_limits:
            if unique_incoming_edges is not None and imax is not None:
                opt.add(Sum(unique_incoming_edges) <= imax)
            if unique_outgoing_edges is not None and omax is not None:
                opt.add(Sum(unique_outgoing_edges) <= omax)

        h = opt.maximize(Sum(max_nodes))

        # inputs = Int('inputs')
        # outputs = Int('outputs')
        # num_nodes = Int('num_nodes')
        #
        # num_nodes = BitVec('num_nodes', NUM_BITS)
        # inputs = BitVec('inputs', NUM_BITS)
        # outputs = BitVec('outputs', NUM_BITS)

        # feasibility_constraints = [
        #     Implies(Node.in_subgraph(node), Node.weight(node) <= BitVecVal(feasibility_threshold, NUM_BITS)) for node in
        #     nodes.values()
        # ]

        res = opt.check()

        node_partition = []
        if res == sat:
            n_nodes = 0
            m = opt.model()
            model_maximized = m.eval(Sum(max_nodes), model_completion=True).as_long()
            correct_maximum = h.upper().as_long()
            
            if correct_maximum != model_maximized:
                pprint.info2("\nmodel isn't maximized, running another solver call")
                opt.add(Sum(max_nodes) == correct_maximum)
                start = time.perf_counter()
                if opt.check() == sat:
                    print(f'Subgraph_extraction_second_call_time = {time.perf_counter() - start}')
                    m = opt.model()
                else:
                    raise Exception("Impossible, error in z3py")

            # print(f'{m = }')
            for t in m.decls():
                # print(f'{type(t) = }')
                # print(f'{t = }')
                print(f"Variable found in pattern: {str(t)}")
                if str(t).startswith('g'):  # Look only the literals associate to the gates
                    if is_true(m[t]):
                        node_partition.append(str(t))
                        n_nodes += 1

        # Check partition convexity
        if not is_selection_convex(graph, node_partition):
            raise RuntimeError('the subgraph extraction resulted in a non-convex subgraph')

        node_partition_idx = [int(re.search('g(\d+)', node).group(1)) for node in node_partition]

        return [gate_dict[idx] for idx in node_partition_idx]
    
    @staticmethod
    def datatype_feasibility_and_filtering_constraints(edges, Node, Edge, NUM_BITS, feasibility_threshold, sum_mode=False):
        if sum_mode:
            feasibility_sum = Sum([
                If(
                    And(Node.in_subgraph(Edge.source(edge)), Not(Node.in_subgraph(Edge.target(edge)))),
                    Node.weight(Edge.source(edge)),
                    BitVecVal(0, NUM_BITS)
                )
                for edge in edges
            ])
            return feasibility_sum <= BitVecVal(feasibility_threshold, NUM_BITS)
        else:
            feasibility_constraints = [
                Implies(
                    And(Node.in_subgraph(Edge.source(edge)), Not(Node.in_subgraph(Edge.target(edge)))),
                    Node.weight(Edge.source(edge)) <= BitVecVal(feasibility_threshold, NUM_BITS)
                )
                for edge in edges
            ]
            return And(feasibility_constraints)
        
    @staticmethod
    def datatype_parent_child_constraints(graph, nodes, Node, opt):
        for parent in nodes:
            children = list(graph.successors(parent))
            if not children:
                continue
            in_subgraph_children = [Node.in_subgraph(nodes[child]) for child in children]

            # If parent is in the subgraph and at least one child is in, then all children must be in
            opt.add(
                Implies(
                    And(
                        Node.in_subgraph(nodes[parent]),
                        Or(in_subgraph_children)
                    ),
                    And(in_subgraph_children)
                )
            )