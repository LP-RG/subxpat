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
        # Data structures containing the literals
        input_literals = {}  # literals associated to the input nodes
        gate_literals = {}  # literals associated to the gates in the circuit
        output_literals = {}  # literals associated to the output nodes

        # Data structures containing the edges
        input_edges = {}  # key = input node id, value = array of id. Contains id of gates in the circuit connected with the input node (childs)
        gate_edges = {}  # key = gate id, value = array of id. Contains the successors gate (childs)
        output_edges = {}  # key = output node id, value = array of id. Contains id of gates in the circuit connected with the output node (parents)

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
    
    @staticmethod
    def extract_gate_weights(G, tmp_graph, gate_dict, weight_key):
        """
        Extract weights for each gate in the circuit graph.
        """
        # Generate structure with gate weights
        # for n in self.graph.nodes:
        #     print(f'{self.graph.nodes[n][WEIGHT] = }, {n =}')
        # print(f'{self.gate_dict = }')
        gate_weight = {}
        for gate_idx in G.nodes:
            if gate_idx not in gate_weight:
                gate_weight[gate_idx] = tmp_graph.nodes[gate_dict[gate_idx]][weight_key]
            # print("Gate", gate_idx, " value ", gate_weight[gate_idx])
        return gate_weight