import networkx as nx
import os
from sxpat.labelling.partition_and_propagate import compute  # 导入 compute 函数


def load_digraph(circuit_name: str) -> nx.digraph.DiGraph:
    """
        Load and return the circuit matching the `circuit_name`.

        warning: `circuit_name` must be the name of a verilog circuit inside the folder `input/ver`

        example: to load the circuit `input/ver/adder_i8_o5.v`, `circuit_name` must be `adder_i8_o5`
    """

    # imports
    from sxpat.annotatedGraph import AnnotatedGraph
    import os

    # prepare folders for intermediary steps
    os.makedirs('output/gv', exist_ok=True)
    os.makedirs('output/ver', exist_ok=True)
    os.makedirs('test/ver', exist_ok=True)

    # load the AnnotatedGraph
    legacy_graph = AnnotatedGraph(circuit_name)

    # extract and update the inner digraph
    digraph = legacy_graph.graph
    for node, data in digraph.nodes(data=True):
        del data['weight']

    return digraph


def load_example() -> nx.digraph.DiGraph:
    """Load and return a simple circuit (the one showed in the meeting of march 6)"""
    return load_digraph('adder_i8_o5')


if __name__ == '__main__':
    digraph = load_example()

    weights, sub_id_graph, all_subgraph_objects = compute(digraph) 


    # change the subid into a color, so different id show different color
    import hashlib
    def get_unique_color(subid):
        hash_object = hashlib.md5(str(subid).encode())
        return f"#{hash_object.hexdigest()[:6]}"

    for node in digraph.nodes:
        subid = digraph.nodes[node].get('subgraph_id', 'default')
        label_type = digraph.nodes[node].get('label', '') 
        
        # fill the node different color
        digraph.nodes[node]['style'] = 'filled'
        digraph.nodes[node]['fillcolor'] = get_unique_color(subid)
        
        # the nodes name
        digraph.nodes[node]['label'] = f"{node}\n({label_type})"
        
        # save picture
    nx.nx_agraph.write_dot(digraph, 'partitioned_circuit.gv')
    os.system('dot -Tpng -opartitioned_circuit.png partitioned_circuit.gv')

    # draw sub_id_graph
    for node in sub_id_graph.nodes:
        sub_id_graph.nodes[node]['style'] = 'filled'
        sub_id_graph.nodes[node]['fillcolor'] = get_unique_color(node)
        sub_id_graph.nodes[node]['label'] = f"Sub_{node}"

    # save picture
    nx.nx_agraph.write_dot(sub_id_graph, 'subgraph_dependency.gv')
    os.system('dot -Tpng -osubgraph_dependency.png subgraph_dependency.gv')