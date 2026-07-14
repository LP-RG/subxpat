from typing import ClassVar, Dict, Optional, Union

import os
from os.path import join as path_join

import networkx as nx
from collections import deque
from sxpat.utils.string import partial_format, dedent

import subprocess
from threading import Lock
from multiprocessing.pool import ThreadPool

from sxpat.graph import IOGraph
from sxpat.graph.node import BoolConstant, Node, And, Not, BoolVariable
from sxpat.specifications import Specifications


class Labelling:
    """
    :authors: Lorenzo Spada, Marco Biasion
    """

    __slots__ = [
        #
        'reference', 'to_be_labelled',
        #
        '_minimise', '_use_func',
        #
        '_base_path',
        #
        '__base_script', '__cached_weights', '__lock',
    ]

    REFERENCE_PREFIX: ClassVar = 'r_'
    LABELLING_PREFIX: ClassVar = 'l_'
    NODES_TO_Z3PY: ClassVar = {
        And: 'And',
        Not: 'Not',
        BoolConstant: 'BoolVal',
    }

    SCRIPT_TEMPLATE: ClassVar = dedent("""\
        from z3 import *

        # inputs
        {input_variables_definition}
        # numeric constants
        {constants_definition}

        # reference circuit
        {reference_circuit}

        # circuit to be labelled
        {to_be_labelled_circuit}

        # solver
        solver = Optimize()
        # error definition
        {error_definition}
        # objective definition
        {objective_definition}

        # execution and extraction
        solver.check()
        model = solver.model()
        print(opt_objective.value())
    """)

    def __init__(
        self,
        reference: IOGraph, to_be_labelled: IOGraph,
        specs: Specifications,
        *,
        minimise: bool,
        use_functions: bool = True,
    ):
        # prepare folder
        self._base_path = path_join(specs.path.run.solver_scripts, f'labelling{specs.iteration}')
        os.makedirs(self._base_path, exist_ok=True)

        #
        self.reference = reference
        self.to_be_labelled = to_be_labelled
        #
        self._minimise = minimise
        self._use_func = use_functions

        #
        self.__base_script: Optional[str] = None
        self.__cached_weights = dict()
        self.__lock = Lock()

    def label_node(self, target_node: str) -> int:
        """
        Compute the weight of the `target_node` inside the `to_be_labelled` circuit,
        in relation to the `reference` circuit.
        """

        if target_node in self.__cached_weights:
            return self.__cached_weights[target_node]

        if self.__base_script is None:
            with self.__lock:
                if self.__base_script is None:
                    strings = list()
                    num_outputs = len(self.to_be_labelled.outputs_names)

                    #
                    inputs_str = '\n'.join(
                        f'{inp} = Bool(\'{inp}\')'
                        for inp in self.reference.inputs_names
                    )
                    #
                    constants_str = '\n'.join([
                        f'constf = BitVecVal(0, {num_outputs})'
                    ] + [
                        f'const{i} = BitVecVal({2**i}, {num_outputs})'
                        for i in range(num_outputs)
                    ])

                    if self._use_func:
                        #
                        error_str = f'error = Function("error", BitVecSort({num_outputs}), BitVecSort({num_outputs}), BitVecSort({num_outputs}))\n'
                        #
                        if self._minimise:
                            objective_str = dedent(f"""
                                solver.add(UGT(error(r_out, l_out), BitVecVal(0, {num_outputs})))
                                opt_objective = solver.minimize(error(r_out, l_out))
                            """)
                        else:
                            objective_str = 'opt_objective = solver.maximize(error(r_out, l_out))'
                    else:
                        #
                        error_str = 'error = If(UGE(r_out, l_out), r_out - l_out, l_out - r_out)'
                        #
                        if self._minimise:
                            objective_str = dedent(f"""
                                solver.add(UGT(error, BitVecVal(0, {num_outputs})))
                                opt_objective = solver.minimize(error)
                            """)
                        else:
                            objective_str = 'opt_objective = solver.maximize(error)'

                    self.__base_script = partial_format(
                        self.SCRIPT_TEMPLATE,
                        #
                        input_variables_definition=inputs_str,
                        constants_definition=constants_str,
                        #
                        reference_circuit=self._circuit_to_z3str(self.reference),
                        #
                        error_definition=error_str,
                        objective_definition=objective_str,
                    )

        # complete script
        _circuit_z3str = self._circuit_to_z3str(self.to_be_labelled, target_node)
        script = self.__base_script.format(to_be_labelled_circuit=_circuit_z3str)

        # save script
        script_path = self._get_script_path(target_node)
        with open(script_path, 'w') as f: f.write(script)
        # run script
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True, text=True,
            check=True,
        )

        # parse result
        self.__cached_weights[target_node] = _w = int(result.stdout)
        return _w

    def label_graph(
        self, *,
        partial_cutoff: Optional[int] = None,
        parallelism: int = 1,
    ) -> Dict[str, int]:
        """
            Compute the weights for the entire graph.  

            :param partial_cutoff: optionally, a threshold for outputs under which their ancestors will be labelled.
            :param parallel: if the labelling should be parallelized, and how much
        """

        # select nodes to label (all non-input ancestors of outputs under the cutoff)
        if partial_cutoff is None: partial_cutoff = 2**len(self.to_be_labelled.outputs_names)
        nodes_to_label = []
        for (i, output) in enumerate(self.to_be_labelled.outputs_names):
            if 2**i <= partial_cutoff:
                for ancestor in nx.ancestors(self.to_be_labelled._inner, output):
                    if not isinstance(self.to_be_labelled[ancestor], BoolVariable):
                        nodes_to_label.append(ancestor)

        # label nodes
        weights: Dict[str, int] = dict()
        if not parallelism or parallelism <= 1:
            for n in nodes_to_label:
                weights[n] = self.label_node(n)
        else:
            with ThreadPool(parallelism) as pool:
                weights.update(pool.map(lambda n: (n, self.label_node(n)), nodes_to_label))

        return weights

    def _get_script_path(self, id: str) -> str:
        return path_join(self._base_path, f'{id}.py')

    @classmethod
    def _node_to_z3str(cls, circuit: IOGraph, node: Node, prefix: str = REFERENCE_PREFIX) -> str:
        # prepare arguments string
        if isinstance(node, BoolConstant):
            args = str(node.value)
        else:
            args = ', '.join(
                pred.name if isinstance(pred, BoolVariable) else f'{prefix}{pred.name}'
                for pred in circuit.predecessors(node)
            )
        # compose node string
        return f'{cls.NODES_TO_Z3PY.get(type(node))}({args})'

    @classmethod
    def _circuit_to_z3str(cls, circuit: IOGraph, target_node: Optional[str] = None) -> str:
        strings = list()

        # custom bfs, enqueue only when all predecessors have been visited
        remaining_predecessors_count = dict((n.name, len(circuit.predecessors(n))) for n in circuit.nodes)
        nodes_queue: deque[Union[Not, And, BoolConstant]] = deque()

        def _enqueue_valid_children(node: str):
            for succ in circuit.successors(node):
                name = succ.name
                remaining_predecessors_count[name] -= 1
                if remaining_predecessors_count[name] == 0 and name not in circuit.outputs_names:
                    assert isinstance(succ, (Not, And, BoolConstant))
                    nodes_queue.append(succ)

        #
        if target_node is None:
            prefix = cls.REFERENCE_PREFIX
        else:
            prefix = cls.LABELLING_PREFIX

        # enqueue children of inputs
        for n in circuit.inputs_names:
            _enqueue_valid_children(n)

        # enqueue constants
        for n in circuit.constants:
            assert isinstance(n, BoolConstant)
            nodes_queue.append(n)

        # write remaining connected gates/constants
        while len(nodes_queue) > 0:
            node: Union[Not, And, BoolConstant] = nodes_queue.popleft()
            node_z3str = cls._node_to_z3str(circuit, node, prefix)

            if node.name == target_node:
                strings.append(f'{prefix}{node.name} = Bool("target")\n')
            else:
                strings.append(f'{prefix}{node.name} = {node_z3str}\n')

            _enqueue_valid_children(node.name)

        # write outputs and integer conversion
        names = list()
        for (i, output) in enumerate(circuit.outputs_names):
            proutput = prefix + output
            if isinstance(circuit.predecessors(output)[0], BoolVariable):
                strings.append(f'{proutput} = {circuit.predecessors(output)[0].name}\n')
            else:
                strings.append(f'{proutput} = {prefix}{circuit.predecessors(output)[0].name}\n')

            names.append(name := f'if_{proutput}')
            strings.append(f'{name} = If({proutput}, const{i}, constf)\n')
        strings.append(f'{prefix}out = Sum({", ".join(names)})\n')

        #
        return ''.join(strings)
