from typing import Mapping

from sxpat.annotatedGraph import AnnotatedGraph


def load_from_verilog(verilog_path: str) -> AnnotatedGraph:
    # imports
    import pathlib
    import sxpat.config.paths as sx_paths

    # useful variables
    _vpath = pathlib.Path(verilog_path)
    benchmark_name = _vpath.stem

    # guard
    required_folder = sx_paths.INPUT_PATH['ver'][0]
    actual_folder = str(_vpath.parent)
    if required_folder != actual_folder:
        raise FileNotFoundError(f'The file must be inside {required_folder} for it to be loaded.')

    # load as optimized gatelevel made of And and Not only
    circuit = AnnotatedGraph(benchmark_name)

    return circuit


def compute_weights_z3(circuit: AnnotatedGraph, /, *, run_in_parallel: bool) -> Mapping[str, int]:
    # imports
    import os
    import glob
    #
    from sxpat.utils.filesystem import FS
    from sxpat.utils.collections import reorder_mapping
    #
    import Z3Log.config.config as l_config
    import Z3Log.config.path as l_paths
    from Z3Log.graph import Graph
    from Z3Log.z3solver import Z3solver

    # export as graph
    Graph(circuit.name).export_graph()

    # create and run solver
    style: str = 'max'
    do_partially: bool = False
    z3py_obj = Z3solver(
        circuit.name, circuit.name,
        experiment=l_config.SINGLE, optimization=l_config.MAXIMIZE, style=style,
        partial=do_partially, parallel=run_in_parallel
    )
    weights = z3py_obj.label_circuit(partial=do_partially)

    # sort weights
    weights = reorder_mapping(
        weights,
        lambda k: int(k[1:]),
    )

    # cleanup (folder report/ and z3/)
    for folder in [l_paths.OUTPUT_PATH['report'][0], l_paths.OUTPUT_PATH['z3'][0]]:
        for dir in glob.glob(f'{folder}/*labeling*'):
            if os.path.isdir(dir):
                FS.rmdir(dir, True)

    return weights


def compute_weights_qbf(circuit: AnnotatedGraph) -> Mapping[str, int]:
    # imports
    from sxpat.temp_labelling import labeling
    #
    from sxpat.utils.collections import reorder_mapping

    #
    weights = labeling(circuit.name, circuit.name, 1e100)

    # sort weights
    weights = reorder_mapping(
        weights,
        lambda k: int(k[1:]),
    )

    return weights


def assign_weights(circuit: AnnotatedGraph, weights: Mapping[str, int]) -> AnnotatedGraph:
    """@notes: this function updates the given `circuit`"""

    # imports
    import networkx as nx
    #
    import sxpat.config.config as sx_config

    # assign weights
    inner_graph: nx.DiGraph = circuit.graph
    for (node_name, node_data) in inner_graph.nodes.items():
        if node_name in weights:
            node_data[sx_config.WEIGHT] = weights[node_name]

    return circuit


def assign_trivial_weights(circuit: AnnotatedGraph) -> AnnotatedGraph:
    """
        Assigns weights to the outputs.

        @notes: this function assumes that the circuit has only a single output
        @notes: this function updates the given `circuit`
    """

    # compute input and output weights
    weights = dict(
        **{
            name: 2 ** i
            for (i, name) in circuit.output_dict.items()
        },
        # ...
    )

    #
    return assign_weights(circuit, weights)


def export_as_graphviz(circuit: AnnotatedGraph, destination: str) -> None:
    # imports
    from sxpat.converting.legacy import iograph_from_legacy
    from sxpat.converting.porters import GraphVizPorter

    # convert to new structure
    graph = iograph_from_legacy(circuit)

    # export
    GraphVizPorter.to_file(graph, destination)


if __name__ == '__main__':
    # imports
    import sys
    import os

    # useful variables
    try: verilog_path = sys.argv[1]
    except IndexError: print('You must pass a verilog path to load the circuit from', file=sys.stderr); sys.exit(1)
    try: graphviz_path = sys.argv[2]
    except IndexError: print('You must pass a graphviz path to save the circuit to', file=sys.stderr); sys.exit(1)
    file = os.path.splitext(os.path.basename(verilog_path))[0]

    #
    print(f'loading circuit from {verilog_path!r}')
    circuit = load_from_verilog(verilog_path)

    #
    if False and file.find('_', file.find('_o') + 2) == -1:
        print('computing weights using qbf`')
        weights = compute_weights_qbf(circuit)
    else:
        print('computing weights using z3')
        weights = compute_weights_z3(circuit, run_in_parallel=False)
    print(weights)

    #
    print('assigning weights')
    circuit = assign_weights(circuit, weights)
    circuit = assign_trivial_weights(circuit)

    #
    print(f'exporting weighted circuit to {graphviz_path!r}')
    export_as_graphviz(circuit, graphviz_path)
