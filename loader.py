import networkx as nx


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
    import os

    # load the example graph
    digraph = load_example()
    # print each node with its data
    for n, d in digraph.nodes(data=True):
        print(n, d['label'], d)

    # save the loaded circuit
    # note: this line will work on the server, but may not on your local machine
    nx.nx_agraph.write_dot(digraph, 'loaded_circuit.gv')
    os.system('dot -Tpng -oloaded_circuit.png loaded_circuit.gv')
