from typing import ClassVar, Dict, List, Optional, Union

import os
from os.path import join as path_join
import subprocess
import networkx as nx
from threading import Lock
from itertools import chain
from collections import deque
from multiprocessing.pool import ThreadPool

from sxpat.graph import IOGraph
from sxpat.graph.node import BoolConstant, Node, And, Not, BoolVariable


class Labelling:
    """
        @author: Lorenzo Spada, Marco Biasion
    """

    __slots__ = [
        #
        'reference', 'to_be_labelled',
        #
        '_minimize', '_use_func',
        #
        '_base_path',
        #
        '__base_script', '__cached_weights', '__lock',
    ]

    __id: ClassVar[int] = -1

    REFERENCE_PREFIX: ClassVar = 'r_'
    LABELLING_PREFIX: ClassVar = 'l_'
    NODES_TO_Z3PY: ClassVar = {
        And: 'And',
        Not: 'Not',
        BoolConstant: 'BoolVal',
    }

    def __init__(
        self,
        reference: IOGraph, to_be_labelled: IOGraph,
        scripts_folder: str,
        *,
        minimize: bool,
        use_functions: bool = True,
    ):
        # prepare folder
        type(self).__id += 1
        self._base_path = path_join(scripts_folder, f'labelling{self.__id}')
        os.makedirs(self._base_path, exist_ok=True)

        #
        self.reference = reference
        self.to_be_labelled = to_be_labelled
        #
        self._minimize = minimize
        self._use_func = use_functions

        #
        self.__base_script = None
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

                    # setup
                    strings.append('from z3 import *\n\n')

                    # consts/vars
                    strings.append('# variables (inputs, parameters)\n')
                    for inp in self.reference.inputs_names:
                        strings.append(f'{inp} = Bool(\'{inp}\')\n')
                    strings.append('# numberic constants\n')
                    strings.append(f'constf = BitVecVal(0, {num_outputs})\n')
                    for i in range(num_outputs):
                        strings.append(f'const{i} = BitVecVal({2**i}, {num_outputs})\n')
                    strings.append('\n')

                    # reference circuit
                    strings.append(self._circuit_to_z3str(self.reference))
                    strings.append('\n')

                    # circuit to label
                    strings.append('{to_be_labelled_z3str}')
                    strings.append('\n')

                    # solver
                    if self._use_func:
                        strings.append('solver = Optimize()\n\n')
                        # error
                        strings.append(f'error = Function("error", BitVecSort({num_outputs}), BitVecSort({num_outputs}), BitVecSort({num_outputs}))\n')
                        strings.append('solver.add(error(r_out, l_out) == If(UGE(r_out, l_out), r_out - l_out, l_out - r_out))\n')
                        if self._minimize:
                            strings.append('solver.add(error(r_out, l_out) > 0)\n')
                            strings.append('handle = solver.minimize(error(r_out, l_out))\n\n')
                        else:
                            strings.append('handle = solver.maximize(error(r_out, l_out))\n\n')
                        # run
                        strings.append('solver.check()\n')
                        strings.append('model = solver.model()\n')
                        strings.append('print(solver.lower(handle))\n')
                    else:
                        strings.append('solver = Optimize()\n\n')
                        # error
                        strings.append('error = If(UGE(r_out, l_out), r_out - l_out, l_out - r_out)\n')
                        if self._minimize:
                            strings.append('solver.add(error > 0)\n')
                            strings.append('handle = solver.minimize(error)\n\n')
                        else:
                            strings.append('handle = solver.maximize(error)\n\n')
                        # run
                        strings.append('solver.check()\n')
                        strings.append('model = solver.model()\n')
                        strings.append('print(solver.lower(handle))\n')

                    self.__base_script = ''.join(strings)

        # complete script
        to_be_labelled_z3str = self._circuit_to_z3str(self.to_be_labelled, target_node)
        script = self.__base_script.format(to_be_labelled_z3str=to_be_labelled_z3str)

        # save script
        script_path = self._get_script_path(target_node)
        with open(script_path, 'w') as f: f.write(script)
        # run script
        result = subprocess.run(['python3', script_path], capture_output=True, text=True)
        if result.returncode != 0: raise RuntimeError(f'Unable to run labelling script {script_path}')

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
            strings.append(f'{proutput} = {prefix}{circuit.predecessors(output)[0].name}\n')

            names.append(name := f'if_{proutput}')
            strings.append(f'{name} = If({proutput}, const{i}, constf)\n')
        strings.append(f'{prefix}out = Sum({", ".join(names)})\n')

        #
        return ''.join(strings)
