from sxpat.graph.graph import IOGraph
from sxpat.specifications import Paths, Specifications


def new_labelling(circuit: IOGraph, specs: Specifications):
    from sxpat.labelling.solver_labelling import Labelling

    # construct the labeller object
    labeller = Labelling(
        circuit, circuit,
        specs=specs,
    )

    # run the labelling for a few nodes
    weights = dict()
    weights['g0'] = labeller.label_node('g0')
    weights['g1'] = labeller.label_node('g1')
    weights['g2'] = labeller.label_node('g2')

    return weights


if __name__ == '__main__':
    import os
    from types import SimpleNamespace
    from sxpat.annotatedGraph import AnnotatedGraph
    from sxpat.converting.legacy import iograph_from_legacy

    # simplified Specifications object
    specs = SimpleNamespace(
        min_labeling=True,
        iteration=0, sub_iteration='',
        path=SimpleNamespace(run=Paths.RunFiles('example', debug=True)),
    )
    # prepare folders
    os.makedirs('output/example/tmp', exist_ok=True)
    os.makedirs('output/example/verilog', exist_ok=True)
    os.makedirs('output/example/scripts', exist_ok=True)

    # load circuit
    circuit_path = 'benchmarks/v/adder_i8_o5.v'
    circuit = iograph_from_legacy(AnnotatedGraph(circuit_path, specs.path.run))

    #
    weights = new_labelling(circuit, specs)
    print(weights)
