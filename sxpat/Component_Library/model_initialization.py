import networkx as nx
import re
from z3 import Bool

class ModelInitialization:
    
    @staticmethod
    def prepare_circuit_model(tmp_graph, constant_dict, opt):
        """
        Initialize literals, edge structures, the DiGraph gate graph
        and set boundaries to False in the Z3 solver.
        """
        input_literals = {}
        gate_literals = {}
        output_literals = {}

        input_edges = {}
        gate_edges = {}
        output_edges = {}

        # Generate all literals
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Generate literal for each input node
                in_id = int(e[0][2:])
                if in_id not in input_literals:
                    input_literals[in_id] = Bool("in_%s" % str(in_id))
            if 'g' in e[0]:  # Generate literal for each gate in the circuit
                g_id = int(e[0][1:])
                if g_id not in gate_literals and g_id not in constant_dict:  # Not in constant_dict since we don't care about constants
                    gate_literals[g_id] = Bool("g_%s" % str(g_id))

            if 'out' in e[1]:  # Generate literal for each output node
                out_id = int(e[1][3:])
                if out_id not in output_literals:
                    output_literals[out_id] = Bool("out_%s" % str(out_id))

        # Generate structures holding edge information
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Populate input_edges structure
                in_id = int(e[0][2:])

                if in_id not in input_edges:
                    input_edges[in_id] = []
                # input_edges[in_id].append(int(e[1][1:])) # this is a bug for a case where e = (in1, out1)
                # Morteza added ==============
                try:
                    input_edges[in_id].append(int(e[1][1:]))
                except:
                    if re.search('g(\d+)', e[1]):
                        my_id = int(re.search('g(\d+)', e[1]).group(1))
                        input_edges[in_id].append(my_id)
                # =============================

            if 'g' in e[0] and 'g' in e[1]:  # Populate gate_edges structure
                ns_id = int(e[0][1:])
                nd_id = int(e[1][1:])

                if ns_id in constant_dict:
                    print("ERROR: Constants should only be connected to output nodes")
                    raise
                if ns_id not in gate_edges:
                    gate_edges[ns_id] = []
                # try:
                gate_edges[ns_id].append(nd_id)

            if 'out' in e[1]:  # Populate output_edges structure
                out_id = int(e[1][3:])
                if out_id not in output_edges:
                    output_edges[out_id] = []
                # output_edges[out_id].append(int(e[0][1:]))
                # Morteza added ==============
                try:
                    output_edges[out_id].append(int(e[0][1:]))
                except:
                    my_id = int(re.search('(\d+)', e[0]).group(1))
                    output_edges[out_id].append(my_id)

        # Create graph of the cicuit without input and output nodes
        G = nx.DiGraph()
        # print(f'{tmp_graph.edges = }')
        for e in tmp_graph.edges:
            if 'g' in str(e[0]) and 'g' in str(e[1]):
                source = int(e[0][1:])
                destination = int(e[1][1:])

                G.add_edge(source, destination)
        # Morteza added =====================
        for e in tmp_graph.edges:
            if 'g' in str(e[0]):
                source = int(e[0][1:])
                if source in constant_dict:
                    continue
                G.add_node(source)
        # ===================================

        # Set input nodes to False
        for input_node_id in input_literals:
            opt.add(input_literals[input_node_id] == False)

        # Set output nodes to False
        for output_node_id in output_literals:
            opt.add(output_literals[output_node_id] == False)

        return G, input_literals, gate_literals, output_literals, input_edges, gate_edges, output_edges