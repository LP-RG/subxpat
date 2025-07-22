from typing import Dict, Iterable, Mapping
from typing_extensions import override
from enum import IntFlag

from sxpat.annotatedGraph import AnnotatedGraph
from Z3Log.z3solver import Z3solver


class LabellingTarget(IntFlag):
    INPUT = 1
    CONSTANT = 2
    GATE = 4
    ALL = 7


class MyZ3Solver(Z3solver):

    @override
    def label_circuit(self, constant_value: bool = False, partial: bool = False, et: int = -1,
                      to_be_labelled: Iterable[str] = None):
        # imports
        from Z3Log.config.config import SINGLE, MONOTONIC
        import itertools as it

        # run labelling for all nodes (inputs, constants, inners)
        if to_be_labelled is None:

            self.label_circuit(
                constant_value, partial, et,
                it.chain(
                    self.labeling_graph.input_dict.values(),
                    self.labeling_graph.constant_dict.values(),
                    self.labeling_graph.gate_dict.values(),
                )
            )

        # run standard labelling
        if (partial or self.partial) and et != -1:
            return super().label_circuit(constant_value, partial, et)

        else:
            # set specs
            self.experiment = SINGLE
            self.set_strategy(MONOTONIC)

            # create scripts
            for node in to_be_labelled:
                self.create_pruned_z3pyscript_approximate([node], constant_value)

            # run all scripts
            self.run_z3pyscript_labeling()
            #
            self.import_labels(constant_value)

            return self.labels

    @override
    def import_labels(self, constant_value: bool = False) -> Dict[str, int]:
        # imports
        import os
        import re
        import csv
        import glob
        #
        import Z3Log.config.path as l_paths
        from Z3Log.config.config import WCE
        from sxpat.utils.filesystem import FS

        #
        label_dict: Dict[str, int] = {}
        folder, extension = l_paths.OUTPUT_PATH['report']

        # find directory containing the labelling for the wanted circuit
        all_dirs = [f for f in os.listdir(folder)]
        relevant_dir = None
        for dir in all_dirs:
            if (
                re.search(f'{self.approximate_benchmark}_labeling', dir)
                and os.path.isdir(f'{folder}/{dir}')
                and re.search(f'{constant_value}', dir)
            ):
                relevant_dir = f'{folder}/{dir}'
                break

        # extract weights
        all_csv = [f for f in os.listdir(relevant_dir)]
        for report in all_csv:
            if (
                re.search(self.approximate_benchmark, report)
                and report.endswith(extension)
            ):
                gate_label = re.search(r'(g\d+|in\d+|out\d+)', report).group(1)

                with open(f'{relevant_dir}/{report}', 'r') as r:
                    csvreader = csv.reader(r)
                    for line in csvreader:
                        if re.search(WCE, line[0]):
                            gate_wce = int(line[1])
                            label_dict[gate_label] = gate_wce
                            self.append_label(gate_label, gate_wce)
                            break

        # cleanup (folder report/ and z3/)
        for folder in [l_paths.OUTPUT_PATH['report'][0], l_paths.OUTPUT_PATH['z3'][0]]:
            for dir in glob.glob(f'{folder}/{circuit.name}_labeling*'):
                if os.path.isdir(dir):
                    FS.rmdir(dir, True)

        return label_dict


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


def compute_weights_z3(circuit: AnnotatedGraph, labelling_targets: LabellingTarget,
                       /, *, run_in_parallel: bool) -> Mapping[str, int]:
    # imports
    import itertools as it
    #
    import Z3Log.config.config as l_config
    from Z3Log.graph import Graph

    # export as graph
    Graph(circuit.name).export_graph()

    # create solver object
    style: str = 'max'
    do_partially: bool = False
    z3py_obj = MyZ3Solver(
        circuit.name, circuit.name,
        experiment=l_config.SINGLE, optimization=l_config.MAXIMIZE, style=style,
        partial=do_partially, parallel=run_in_parallel
    )

    # select nodes to be labelled
    to_be_labelled = it.chain(
        circuit.input_dict.values() if LabellingTarget.INPUT in labelling_targets else (),
        circuit.constant_dict.values() if LabellingTarget.CONSTANT in labelling_targets else (),
        circuit.gate_dict.values() if LabellingTarget.GATE in labelling_targets else (),
    )

    # run labelling
    weights = z3py_obj.label_circuit(partial=do_partially, to_be_labelled=to_be_labelled)

    return weights


def compute_weights_qbf(circuit: AnnotatedGraph) -> Mapping[str, int]:
    # imports
    from sxpat.temp_labelling import labeling

    #
    weights = labeling(circuit.name, circuit.name, 1e100)

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
        Copy the actual output node weight to the proxy output node (the identity).

        @notes: this function updates the given `circuit`
    """
    # imports
    import sxpat.config.config as sx_config
    import networkx as nx

    #
    _inner: nx.DiGraph = circuit.graph
    weights = {
        name: _inner.nodes[next(_inner.predecessors(name))][sx_config.WEIGHT]
        for name in circuit.output_dict.values()
    }

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
    import json
    #
    from sxpat.utils.collections import reorder_mapping

    # useful variables
    try: verilog_path = sys.argv[1]
    except IndexError: print('You must pass a verilog path to load the circuit from', file=sys.stderr); sys.exit(1)
    try: graphviz_path = sys.argv[2]
    except IndexError: print('You must pass a graphviz path to save the circuit to', file=sys.stderr); sys.exit(1)
    try: data_path = sys.argv[3]
    except: data_path = None
    file = os.path.splitext(os.path.basename(verilog_path))[0]

    #
    print(f'loading circuit from {verilog_path!r}')
    circuit = load_from_verilog(verilog_path)

    # SETTING: select nodes types to be labelled
    labelling_targets = (
        LabellingTarget.INPUT
        # | LabellingTarget.CONSTANT
        # | LabellingTarget.GATE
    )
    print('target:', labelling_targets)

    #
    if False and file.find('_', file.find('_o') + 2) == -1:
        print('computing weights using qbf`')
        weights = compute_weights_qbf(circuit)
    else:
        print('computing weights using z3')
        weights = compute_weights_z3(
            circuit, labelling_targets,
            run_in_parallel=False,
        )

    # sort weights
    weights = reorder_mapping(
        weights,
        lambda k: {
            'i': lambda s: (0, int(s[2:])),
            'g': lambda s: (1, int(s[1:])),
            'o': lambda s: (2, int(s[3:])),
        }[k[0]](k)
    )
    print(weights)

    # save weights (optionally)
    if data_path:
        with open(data_path, 'w') as f:
            json.dump({'weights': weights, 'time': t}, f)


    #
    print('assigning weights')
    circuit = assign_weights(circuit, weights)
    circuit = assign_trivial_weights(circuit)

    #
    print(f'exporting weighted circuit to {graphviz_path!r}')
    export_as_graphviz(circuit, graphviz_path)
