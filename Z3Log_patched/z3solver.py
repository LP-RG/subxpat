import re
import time
import multiprocessing

from z3 import *
import numpy as np
import os
import copy
import csv
from colorama import Fore, Style
from typing import *
import networkx as nx
from subprocess import PIPE, Popen
from .utils import *
from .graph import *





class Z3solver:
    def __init__(self, benchmark_name: str, approximate_benchmark_name: str = None, samples: list = [],
                 experiment: str = SINGLE,
                 pruned_percentage: int = None, pruned_gates=None, metric: str = WAE, precision: int = 4,
                 optimization: str = None, style: str = 'max',
                 parallel:bool = False, partial: bool = True):
        """

        :param benchmark_name: the input benchmark in gv format
        :param approximate_benchmark_name: the approximate benchmark in gv format
        :param samples: number of samples for the mc evaluation; by defaults it is an empty list
        """
        self.__circuit_name = get_pure_name(benchmark_name)

        folder, extension = OUTPUT_PATH['gv']
        self.__graph_in_path = f'{folder}/{benchmark_name}.{extension}'

        self.__graph = Graph(benchmark_name, True)


        self.__pyscript_results_out_path = None

        folder, extension = LOG_PATH['z3']
        os.makedirs(f'{folder}/{benchmark_name}_{Z3}_{LOG}', exist_ok=True)
        self.__z3_log_path = f'{folder}/{benchmark_name}_{Z3}_{LOG}/{benchmark_name}_{Z3}_{LOG}.{extension}'

        self.__approximate_verilog_in_path = None
        self.__approximate_graph = None

        if approximate_benchmark_name:
            self.__approximate_circuit_name = approximate_benchmark_name
            folder, extension = INPUT_PATH['app_gv']
            self.__approximate_verilog_in_path = f'{folder}/{approximate_benchmark_name}.{extension}'
            self.__approximate_graph = Graph(approximate_benchmark_name, True)

            self.relabel_approximate_graph()

            self.approximate_graph.set_input_dict(self.approximate_graph.extract_inputs())
            self.approximate_graph.set_output_dict(self.approximate_graph.extract_outputs())
            self.approximate_graph.set_gate_dict(self.approximate_graph.extract_gates())
            self.approximate_graph.set_constant_dict(self.approximate_graph.extract_constants())

            self.__labeling_graph = copy.deepcopy(self.approximate_graph)


        self.__experiment = experiment
        self.__pruned_percentage = None
        # TODO
        # Later create and internal method that can generate pruned gates
        self.__pruned_gates = None
        if experiment == RANDOM:
            self.__pruned_percentage = pruned_percentage
            self.__pruned_gates = pruned_gates

        self.__metric = metric
        self.__precision = precision

        self.__z3_report = None

        self.__samples = samples
        self.__sample_results = None

        self.__z3string = None

        self.__z3pyscript = None

        self.__strategy = None

        self.__optimization = optimization

        self.__pyscript_files_for_labeling: list = []

        self.__z3_out_path = None

        self.__style = style

        self.__parallel = parallel

        self.__labels: Dict = {}

        self.__partial: bool = partial

        # print(f'{len(self.approximate_graph.graph.nodes) = }')
        # print(f'{self.approximate_graph.num_gates = }')
        # print(f'{self.approximate_graph.num_inputs = }')
        # print(f'{self.approximate_graph.num_constants = }')
        # print(f'{self.approximate_graph.num_outputs =}')


    @property
    def partial(self):
        return self.__partial

    @property
    def labels(self):
        return self.__labels


    def append_label(self, key, value):
        if key not in self.__labels:
            self.__labels[key] = value
        else:
            print(Fore.LIGHTRED_EX + f'Error! key={key} already exists in the labels dictionary!' + Style.RESET_ALL)


    @property
    def parallel(self):
        return self.__parallel


    @property
    def style(self):
        return self.__style

    @property
    def name(self):
        return self.__circuit_name

    @name.setter
    def name(self, this_name):
        self.__circuit_name = this_name

    @property
    def approximate_benchmark(self):
        return self.__approximate_circuit_name

    @property
    def graph_in_path(self):
        return self.__graph_in_path

    @property
    def out_path(self):
        return self.__z3_out_path

    def set_out_path(self, out_path: str):
        self.__z3_out_path = out_path

    @property
    def z3_log_path(self):
        return self.__z3_log_path

    @property
    def approximate_in_path(self):
        return self.__approximate_verilog_in_path

    @property
    def z3pyscript(self):
        return self.__z3pyscript

    @property
    def strategy(self):
        return self.__strategy

    def set_strategy(self, strategy: str):
        self.__strategy = strategy

    @property
    def optimization(self):
        return self.__optimization

    @optimization.setter
    def optimization(self, optimization):
        self.__optimization = optimization

    @property
    def metric(self):
        return self.__metric

    @metric.setter
    def metric(self, metric):
        self.__metric = metric

    @property
    def precision(self):
        return self.__precision

    @precision.setter
    def precision(self, precision):
        self.__precision = precision

    @property
    def experiment(self):
        return self.__experiment

    @experiment.setter
    def experiment(self, experiment):
        self.__experiment = experiment

    @property
    def pruned_percentage(self):
        return self.__pruned_percentage

    @pruned_percentage.setter
    def pruned_percentage(self, pruned_percentage):
        self.__pruned_percentage = pruned_percentage

    @property
    def pruned_gates(self):
        return self.__pruned_gates

    @pruned_gates.setter
    def pruned_gates(self, pruned_gates: List[int]):
        self.__pruned_gates = pruned_gates

    @property
    def z3_report(self):
        return self.__z3_report

    def set_z3_report(self, z3_report: str):
        self.__z3_report = z3_report

    @property
    def pyscript_files_for_labeling(self):
        return self.__pyscript_files_for_labeling

    def set_pyscript_files_for_labeling(self, pyscript_files_for_labeling):
        self.__pyscript_files_for_labeling = pyscript_files_for_labeling

    def append_pyscript_files_for_labeling(self, pyscript_file):
        self.__pyscript_files_for_labeling.append(pyscript_file)

    # TODO

    @property
    def z3string(self):
        return self.__z3string

    @property
    def samples(self):
        return self.__samples

    def set_samples(self, samples: np.array or list):
        self.__samples = samples

    @property
    def sample_results(self):
        return self.__sample_results

    def set_sample_results(self, results):
        self.__sample_results = results






    def is_input(self, node, graph):
        if graph.graph.nodes[node][SHAPE] == INPUT_SHAPE and re.search('in\d+', node):
            return True
        else:
            return False

    def is_gate(self, node, graph):
        if graph.graph.nodes[node][SHAPE] == GATE_SHAPE and re.search('g\d+', node):
            return True
        else:
            return False

    def is_constant(self, node, graph):
        if graph.graph.nodes[node][SHAPE] == CONSTANT_SHAPE and re.search('g\d+', node):
            return True

    def is_output(self, node, graph):
        if graph.graph.nodes[node][SHAPE] == OUTPUT_SHAPE and re.search('out\d+', node):
            return True
        else:
            return False

    def IntVector(self, prefix, sz, ctx=None, exact: bool = True):
        """Return a list of integer constants of size `sz`.

        >>> X = IntVector('x', 3)
        >>> X
        [x__0, x__1, x__2]
        >>> Sum(X)
        x__0 + x__1 + x__2
        """
        # ctx = _get_ctx(ctx)
        ctx = None
        if exact:
            return [Int("exact_%s%s" % (prefix, i), ctx) for i in range(sz)]
        else:
            return [Int("approx_%s%s" % (prefix, i), ctx) for i in range(sz)]




    def BoolVector(self, prefix, sz, ctx=None, exact: bool = True):
        """Return a list of Boolean constants of size `sz`.

        The constants are named using the given prefix.
        If `ctx=None`, then the global context is used.

        >>> P = BoolVector('p', 3)
        >>> P
        [p__0, p__1, p__2]
        >>> And(P)
        And(p__0, p__1, p__2)
        """
        # print(f'{ctx = }')
        if exact:
            return [Bool("%s%s" % (prefix, i), ctx) for i in range(sz)]
        else:
            return [Bool("app_%s%s" % (prefix, i), ctx) for i in range(sz)]

    def convert_exact_to_implicit_z3_constraints(self, ctx=None):
        # exact circuit
        exact_circuit = []
        # converting exact circuit into
        for node in self.graph.graph.nodes:
            if self.is_gate(node, self.graph):
                functionality = self.graph.graph.nodes[node][LABEL].split('\\')[0]

                assert functionality in Z3_GATES_DICTIONARY, Fore.RED + f'ERROR!!! in ({__name__}): functionality of node {node} is unknown!' + Style.RESET_ALL
                z3_functionality = Z3_GATES_DICTIONARY[functionality]
                predecessor_list = list(self.graph.graph.predecessors(node))
                assert len(predecessor_list) == 1 or len(
                    predecessor_list) == 2, Fore.RED + f'ERROR!!! in ({__name__}):  node {node} has more than 2 (or less than 1) predecessors!' + Style.RESET_ALL
                if len(predecessor_list) == 1:
                    exact_circuit.append(Bool(node, ctx=ctx) == Not(Bool(predecessor_list[0], ctx=ctx), ctx=ctx))
                elif len(predecessor_list) == 2:
                    exact_circuit.append(Bool(node, ctx=ctx) == And(Bool(predecessor_list[0], ctx=ctx), Bool(predecessor_list[1], ctx=ctx)))
            elif self.is_constant(node, self.graph):
                constant = self.graph.graph.nodes[node][LABEL].split('\\')[0]  # 'FALSE\\ng0' -> ['FALSE', 'ng0']
                assert constant in Z3_GATES_DICTIONARY, Fore.RED + f'ERROR!!! in ({__name__}): functionality of node {node} is unknown!' + Style.RESET_ALL
                z3_constant = Z3_GATES_DICTIONARY[constant]
                exact_circuit.append(Bool(node, ctx=ctx) == Bool(z3_constant, ctx=ctx))
            elif self.is_output(node, self.graph):
                predecessor_list = list(self.graph.graph.predecessors(node))
                assert len(
                    predecessor_list) == 1, Fore.RED + f'ERROR!!! in ({__name__}):  node {node} has more/less than 1 predecessors!' + Style.RESET_ALL
                exact_circuit.append(Bool(node, ctx=ctx) == Bool(predecessor_list[0], ctx=ctx))

            elif not self.is_input(node, self.graph):
                print(Fore.RED + f'ERROR!!! in ({__name__}): node {node} is unknown!' + Style.RESET_ALL)

        return exact_circuit


    def convert_approximate_to_implicit_z3_constraints(self, removed_node: str = None, ctx=None):
        approx_circuit = []
        for node in self.approximate_graph.graph.nodes:
            if self.is_gate(node, self.approximate_graph):

                if node != removed_node:
                    functionality = self.approximate_graph.graph.nodes[node][LABEL].split('\\')[0]
                    assert functionality in Z3_GATES_DICTIONARY, Fore.RED + f'ERROR!!! in ({__name__}): functionality of node {node} is unknown!' + Style.RESET_ALL
                    z3_functionality = Z3_GATES_DICTIONARY[functionality]
                    predecessor_list = list(self.approximate_graph.graph.predecessors(node))
                    assert len(predecessor_list) == 1 or len(
                        predecessor_list) == 2, Fore.RED + f'ERROR!!! in ({__name__}):  node {node} has more than 2 (or less than 1) predecessors!' + Style.RESET_ALL
                    if len(predecessor_list) == 1:

                        approx_circuit.append(Bool(node, ctx=ctx) == Not(Bool(predecessor_list[0], ctx=ctx)))
                    elif len(predecessor_list) == 2:
                        # node = And(Bool(predecessor_list[0]), Bool(predecessor_list[1]))
                        approx_circuit.append(Bool(node, ctx=ctx) == And(Bool(predecessor_list[0], ctx=ctx), Bool(predecessor_list[1], ctx=ctx)))
                else:
                    # print(f'{node} is left as a free variable!')
                    pass
            elif self.is_constant(node, self.approximate_graph):
                if node != removed_node:
                    constant = self.approximate_graph.graph.nodes[node][LABEL].split('\\')[
                        0]  # 'FALSE\\ng0' -> ['FALSE', 'ng0']
                    assert constant in Z3_GATES_DICTIONARY, Fore.RED + f'ERROR!!! in ({__name__}): functionality of node {node} is unknown!' + Style.RESET_ALL
                    z3_constant = Z3_GATES_DICTIONARY[constant]
                    approx_circuit.append(Bool(node, ctx=ctx) == Bool(z3_constant, ctx=ctx))
                else:
                    # print(f'{node} is left as a free variable!')
                    pass
            elif self.is_output(node, self.approximate_graph):

                predecessor_list = list(self.approximate_graph.graph.predecessors(node))

                assert len(
                    predecessor_list) == 1, Fore.RED + f'ERROR!!! in ({__name__}):  node {node} has more/less than 1 predecessors!' + Style.RESET_ALL
                approx_circuit.append(Bool(node, ctx=ctx) == Bool(predecessor_list[0], ctx=ctx))

            elif not self.is_input(node, self.approximate_graph):
                print(Fore.RED + f'ERROR!!! in ({__name__}): node {node} is unknown!' + Style.RESET_ALL)
        return approx_circuit


    def integer_circuit_output_to_implicit_z3_constriants(self, integer_out_list, exact : bool = True, ctx=None):
        if exact:
            exact_out = Int('exact_out', ctx=ctx)
            exact_out = IntVal('0', ctx=ctx)
            for i, out in enumerate(integer_out_list):


                exact_out += out* (IntVal(2**i, ctx=ctx) * 2/2)

            return exact_out
        else:
            approx_out = Int('approx_out', ctx=ctx)
            approx_out = IntVal('0', ctx=ctx)
            for i, out in enumerate(integer_out_list):
                approx_out += out * (IntVal(2 ** i,  ctx=ctx) * 2/2)

            return approx_out

    def labler_wrapper(self, args):
        labler, node , queue = args
        labler(node, queue)



    def run_implicit_labeling(self):
        labler = self.implicit_labeling
        num_of_nodes = self.approximate_graph.num_gates + self.approximate_graph.num_constants
        manager = multiprocessing.Manager()
        shared_list = manager.list()
        if self.parallel:
            print(Fore.LIGHTBLUE_EX + f'Labeling (implicit & parallel)... ', end='' + Style.RESET_ALL)
            # Initialize a manager and a shared queue
            manager = multiprocessing.Manager()
            queue = manager.Queue()
            # Define a helper function to pass to the pool
            # Use the number of available CPU cores
            num_workers = multiprocessing.cpu_count()
            # Initialize a Pool of worker processes
            with multiprocessing.Pool(num_workers) as pool:
                # Create all node names to be processed
                args = [(labler, f'app_g{i}', queue) for i in range(num_of_nodes)]
                # Map the helper function to each node name
                pool.map(self.labler_wrapper, args, chunksize=1)
            # Now get the results from the queue
            for _ in range(num_of_nodes):
                node, weight = queue.get()
                shared_list.append((node, weight))
            print(Fore.LIGHTBLUE_EX + 'Done' + Style.RESET_ALL)
        else:
            print(Fore.LIGHTBLUE_EX + f'Labeling (implicit & NOT parallel)... ', end='' + Style.RESET_ALL)
            # Initialize a manager and a shared queue
            manager = multiprocessing.Manager()
            queue = manager.Queue()
            # Define a helper function to pass to the pool
            # Use the number of available CPU cores
            num_workers = 1
            # Initialize a Pool of worker processes
            with multiprocessing.Pool(num_workers) as pool:
                # Create all node names to be processed
                args = [(labler, f'app_g{i}', queue) for i in range(num_of_nodes)]
                # Map the helper function to each node name
                pool.map(self.labler_wrapper, args)
            # Now get the results from the queue
            for _ in range(num_of_nodes):
                node, weight = queue.get()
                shared_list.append((node, weight))
            print(Fore.LIGHTBLUE_EX + 'Done' + Style.RESET_ALL)

        for node_weight in shared_list:
            node, weight = node_weight
            self.append_label(node, weight)




    def implicit_labeling(self, removed_node: str = None, queue = None, this_ctx=None):
        st = time.time()
        if this_ctx is None:

            this_ctx = Context()
        s = Optimize(ctx=this_ctx)
        assert s.ctx == this_ctx
        et = time.time()
        # print(f'define solver time = {et - st}')
        st = time.time()
        f_exact = Function('f_exact', IntSort( ctx=this_ctx), IntSort( ctx=this_ctx))
        f_approx = Function('f_approx', IntSort( ctx=this_ctx), IntSort( ctx=this_ctx))
        f_error = Function('f_error', IntSort( ctx=this_ctx), IntSort( ctx=this_ctx), IntSort( ctx=this_ctx))
        input_list_exact = self.BoolVector('in', self.graph.num_inputs, exact=True, ctx=this_ctx)

        gate_list_exact = self.BoolVector('g', self.graph.num_constants + self.graph.num_gates, exact=True, ctx=this_ctx)
        output_list_exact = self.BoolVector('out', self.graph.num_outputs, exact=True, ctx=this_ctx)
        exact_circuit = self.convert_exact_to_implicit_z3_constraints(ctx=this_ctx)
        exact_output = self.integer_circuit_output_to_implicit_z3_constriants(output_list_exact, exact=True, ctx=this_ctx)




        gate_list_approx = self.BoolVector('g', self.approximate_graph.num_constants + self.approximate_graph.num_gates, exact=False, ctx=this_ctx)
        output_list_approx = self.BoolVector('out', self.approximate_graph.num_outputs, exact=False, ctx=this_ctx)
        approx_circuit = self.convert_approximate_to_implicit_z3_constraints(removed_node, ctx=this_ctx)
        approx_output = self.integer_circuit_output_to_implicit_z3_constriants(output_list_approx, exact=False, ctx=this_ctx)

        et = time.time()


        st = time.time()
        # s.add(input_list_exact)
        # s.add(gate_list_exact)
        # s.add(output_list_exact)
        # s.add(gate_list_approx)
        # s.add(output_list_approx)


        s.add(exact_circuit)
        s.add(approx_circuit)



        if self.style == 'max':
            foundWCE = False
            wce = 0
            st = time.time()
            s.add(f_exact(exact_output) == exact_output)
            s.add(f_approx(approx_output) == approx_output)
            s.add(f_error(exact_output, approx_output) == Abs(exact_output - approx_output))
            while(not foundWCE):


                s.push()
                s.add(f_error(exact_output, approx_output) > wce)
                s.maximize(f_error(exact_output, approx_output))

                # print(f'adding constraints time = {et - st}')

                c = s.check()
                # print(f'{c = }')
                if c == sat:
                    wce = abs((s.model()[f_error].else_value().as_long()))
                    # print(f'{wce}')
                else:
                    foundWCE = True

                # print(f'check time = {et -st}')
                s.pop()
            del s
            if queue:
                et = time.time()
                # print(f'{this_ctx = }')
                # print(f'{removed_node}={wce} is done labeling! in {et - st}')
                queue.put((removed_node, wce))
            else:
                # print(f'{this_ctx = }')
                et = time.time()
                # print(f'{removed_node}={wce} is done labeling! in {et - st}')

                return wce
        else:
            foundBCE = False
            bce = None

            s.push()
            s.add(f_exact(exact_output) == exact_output)
            s.add(f_approx(approx_output) == approx_output)
            s.add(f_error(exact_output, approx_output) == Abs(exact_output - approx_output))
            s.add(f_error(exact_output, approx_output) > 0)
            s.minimize(f_error(exact_output, approx_output))
            et = time.time()
            # print(f'adding constraints time = {et - st}')
            c = s.check()
            et = time.time()
            runtime = et  -  st
            if c == sat:
                bce = abs((s.model()[f_error].else_value().as_long()))
            else:
                foundBCE = True
            s.pop()
            del s
            if queue:
                print(f'{removed_node} is done labeling!')
                queue.put((removed_node, bce))
            else:
                print(f'{removed_node} is done labeling!')
                return bce


    def evaluate(self):
        return self.implicit_labeling()


    def partial_labeling(self):
        pass

    def import_results(self):
        arr = []
        with open(self.pyscript_results_out_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.replace('\n', '')
                arr.append(int(line))
        results = np.array(arr)
        return results

    def append_z3string(self, new_string):
        self.__z3string = f'{self.__z3string}\n' \
                          f'{new_string}'

    def set_z3string(self, new_string):
        self.__z3string = new_string

    @property
    def pyscript_results_out_path(self):
        return self.__pyscript_results_out_path

    def set_pyscript_results_out_path(self, pyscript_results_out_path: str):
        self.__pyscript_results_out_path = pyscript_results_out_path

    @property
    def graph(self):
        return self.__graph

    @property
    def approximate_graph(self):
        return self.__approximate_graph

    def set_approximate_graph(self, tmp_graph):
        self.__approximate_graph = tmp_graph

    @property
    def labeling_graph(self):
        return self.__labeling_graph


    def _get_next_gate(self):
        pass

    def label_circuit(self, constant_value: bool = False, partial: bool = False, et: int = -1):
        self.experiment = SINGLE
        self.set_strategy(MONOTONIC)

        predecessors_to_label = list(
            self.graph.graph.predecessors(self.graph.output_dict[1]))


        if (partial or self.partial) and et != -1:

            already_labeled = set()
            output_dict = self.labeling_graph.output_dict
            sorted_output_dict = dict(sorted(output_dict.items()))



            for output_idx in sorted_output_dict:
                if 2 ** output_idx > et:
                    break
                else:
                    predecessors_to_label = list(self.labeling_graph.graph.predecessors(self.labeling_graph.output_dict[output_idx]))

                    while predecessors_to_label:
                        gate = predecessors_to_label.pop()
                        if not self.is_input(gate, self.labeling_graph):

                            if gate not in already_labeled:
                                removed_gate = [gate]

                                self.create_pruned_z3pyscript_approximate(removed_gate, constant_value)
                                already_labeled.add(gate)
                                # read the label
                                predecessors_to_label.extend(list(self.labeling_graph.graph.predecessors(gate)))
            self.run_z3pyscript_labeling()
            self.import_labels(constant_value)
            
            return self.labels

        else:
            for key in self.labeling_graph.gate_dict:

                removed_gate = [self.labeling_graph.gate_dict[key]]

                self.create_pruned_z3pyscript_approximate(removed_gate, constant_value)
            for key in self.labeling_graph.constant_dict:
                removed_gate = [self.labeling_graph.constant_dict[key]]
                self.create_pruned_z3pyscript_approximate(removed_gate, constant_value)
            self.run_z3pyscript_labeling()
            self.import_labels(constant_value)
            
            return self.labels

    def import_labels(self, constant_value: bool=False) -> Dict:
        label_dict: Dict[str, int] = {}
        folder, extension = OUTPUT_PATH['report']

        all_dirs = [f for f in os.listdir(folder)]
        # print(f'{all_dirs = }')
        relevant_dir = None
        for dir in all_dirs:
            if re.search(f'{self.approximate_benchmark}_labeling', dir) and os.path.isdir(f'{folder}/{dir}') and re.search(f'{constant_value}', dir):
                relevant_dir = f'{folder}/{dir}'

        all_csv = [f for f in os.listdir(relevant_dir)]
        for report in all_csv:
            if re.search(self.approximate_benchmark, report) and report.endswith(extension):
                gate_label = re.search('(g\d+)', report).group(1)

                with open(f'{relevant_dir}/{report}', 'r') as r:
                    csvreader = csv.reader(r)
                    for line in csvreader:
                        if re.search(WCE, line[0]):
                            gate_wce = int(line[1])

                            label_dict[gate_label] = gate_wce
                            self.append_label(gate_label, gate_wce)
        return label_dict




    # TODO
    # Deprecated
    def import_z3_expression(self):
        pass

    def set_z3pyscript(self, this_script):
        self.__z3pyscript = this_script

    def relabel_approximate_graph(self):
        gate_mapping = {}
        constant_mapping = {}
        output_mapping = {}
        for key in self.approximate_graph.gate_dict.keys():
            gate_mapping[self.approximate_graph.gate_dict[key]] = f'app_{self.approximate_graph.gate_dict[key]}'
        for key in self.approximate_graph.constant_dict.keys():
            constant_mapping[
                self.approximate_graph.constant_dict[key]] = f'app_{self.approximate_graph.constant_dict[key]}'
        for key in self.approximate_graph.output_dict.keys():
            output_mapping[self.approximate_graph.output_dict[key]] = f'app_{self.approximate_graph.output_dict[key]}'
        self.approximate_graph.set_graph(nx.relabel_nodes(self.approximate_graph.graph, gate_mapping))
        self.approximate_graph.set_graph(nx.relabel_nodes(self.approximate_graph.graph, constant_mapping))
        self.approximate_graph.set_graph(nx.relabel_nodes(self.approximate_graph.graph, output_mapping))

    def convert_gv_to_z3pyscript_test(self):
        folder, extension = OUTPUT_PATH['report']
        os.makedirs(f'{folder}/{self.name}', exist_ok=True)
        self.set_z3_report(f'{folder}/{self.name}/{self.name}_{TEST}.{extension}')

        folder, extension = OUTPUT_PATH['z3']
        os.makedirs(f'{folder}/{self.name}', exist_ok=True)
        self.set_out_path(f'{folder}/{self.name}/{self.name}_{TEST}.{extension}')

        folder, extension = TEST_PATH['z3']
        os.makedirs(f'{folder}/{self.name}', exist_ok=True)
        self.set_pyscript_results_out_path(f'{folder}/{self.name}/{self.name}_{TEST}.{extension}')

        import_string = self.create_imports()
        abs_function = self.create_abs_function()
        exact_circuit_declaration = self.declare_original_circuit()
        exact_circuit_expression = self.express_original_circuit()
        # TODO: Fix Later
        if self.metric == WHD:
            output_declaration = ''
            print(f'ERROR!!! Right now testing is not possible on WHD!')
        else:
            output_declaration = self.declare_original_output()
        exact_function = self.declare_original_function()
        solver = self.declare_solver()
        sample_expression = self.express_samples()
        store_results = self.store_results()
        self.set_z3pyscript(import_string + abs_function + exact_circuit_declaration + exact_circuit_expression +
                            output_declaration + exact_function + solver + sample_expression + store_results)

    def convert_gv_to_z3pyscript_maxerror_qor(self, strategy: str = DEFAULT_STRATEGY):

        self.experiment = QOR
        self.set_strategy(strategy)

        if self.metric == WRE:
            folder, extension = OUTPUT_PATH['report']
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}.{extension}')
            else:
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}.{extension}')

            folder, extension = OUTPUT_PATH['z3']
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                self.set_out_path(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}.{extension}')
            else:
                self.set_out_path(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}.{extension}')

        else:
            folder, extension = OUTPUT_PATH['report']
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}_{self.optimization}.{extension}')
            else:
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}.{extension}')

            folder, extension = OUTPUT_PATH['z3']
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                self.set_out_path(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}_{self.optimization}.{extension}')
            else:
                self.set_out_path(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}.{extension}')


        import_string = self.create_imports()
        abs_function = self.create_abs_function()

        # exact_part
        original_circuit_declaration = self.declare_original_circuit()
        original_circuit_expression = self.express_original_circuit()
        if self.metric == WHD:
            original_output_declaration = 'Blah Blah Blah\n'
        else:
            original_output_declaration = self.declare_original_output()

        # approximate_part
        approximate_circuit_declaration = self.declare_approximate_circuit()
        approximate_circuit_expression = self.express_approximate_circuit()
        if self.metric == WHD:
            approximate_output_declaration = 'Blah Blah Blah\n'
        else:
            approximate_output_declaration = self.declare_approximate_output()

        # error distance function
        declare_error_distance_function = self.declare_error_distance_function()
        # strategy

        strategy = self.express_strategy()

        self.set_z3pyscript(import_string + abs_function + original_circuit_declaration + original_circuit_expression +
                            original_output_declaration + approximate_circuit_declaration + approximate_circuit_expression +
                            approximate_output_declaration + declare_error_distance_function + strategy)

    def convert_gv_to_z3pyscript_maxerror_labeling(self, strategy: str = DEFAULT_STRATEGY):
        self.experiment = SINGLE
        self.set_strategy(strategy)
        removed_gate = []
        for key in self.graph.input_dict:
            removed_gate = [self.graph.input_dict[key]]
            self.create_pruned_z3pyscript(removed_gate)
        for key in self.graph.gate_dict:
            removed_gate = [self.graph.gate_dict[key]]
            self.create_pruned_z3pyscript(removed_gate)

    def convert_gv_to_z3pyscript_maxerror_random_pruning(self, strategy: str = DEFAULT_STRATEGY):

        self.experiment = RANDOM
        self.set_strategy(strategy)

        removed_gates = []
        for idx in self.pruned_gates:
            if idx < self.graph.num_inputs:  # remove pi
                removed_gates.append(self.graph.input_dict[idx])
            else:  # remove gate
                removed_gates.append(self.graph.gate_dict[idx - self.graph.num_inputs + 1])
        # print(f'{removed_gates}')
        self.create_pruned_z3pyscript(removed_gates)

    # TODO
    # Naming problems for more than one gate removal
    def create_pruned_z3pyscript(self, gates: list, constant_value: bool = False):
        self.create_pruned_graph_approximate(gates, constant_value)
        if self.experiment == SINGLE:
            gate = gates[0]
        # TODO
        elif self.experiment == RANDOM:
            gate = 'id0'
        folder, extension = OUTPUT_PATH['report']
        if self.metric == WRE:
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                folder = f'{folder}/{self.name}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}'
                os.makedirs(folder, exist_ok=True)
                self.set_z3_report(
                    f'{folder}/{self.name}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}_{gate}.{extension}')
            else:
                folder = f'{folder}/{self.name}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}'
                os.makedirs(folder, exist_ok=True)
                self.set_z3_report(
                    f'{folder}/{self.name}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{gate}.{extension}')
        else:

            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                folder = f'{folder}/{self.name}_{self.experiment}_{self.metric}_{self.strategy}_{self.optimization}'
                os.makedirs(folder, exist_ok=True)
                self.set_z3_report(
                    f'{folder}/{self.name}_{self.experiment}_{self.metric}_{self.strategy}_{self.optimization}_{gate}.{extension}')
            else:
                folder = f'{folder}/{self.name}_{self.experiment}_{self.metric}_{self.strategy}'
                os.makedirs(folder, exist_ok=True)
                self.set_z3_report(
                    f'{folder}/{self.name}_{self.experiment}_{self.metric}_{self.strategy}_{gate}.{extension}')

        folder, extension = OUTPUT_PATH['z3']
        if self.metric == WRE:
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                folder = f'{folder}/{self.name}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}'
                os.makedirs(folder, exist_ok=True)
                self.set_out_path(
                    f'{folder}/{self.name}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}_{gate}.{extension}')
            else:
                folder = f'{folder}/{self.name}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}'
                os.makedirs(folder, exist_ok=True)
                self.set_out_path(
                    f'{folder}/{self.name}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{gate}.{extension}')
        else:
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                folder = f'{folder}/{self.name}_{self.experiment}_{self.metric}_{self.strategy}_{self.optimization}'
                os.makedirs(folder, exist_ok=True)
                self.set_out_path(
                    f'{folder}/{self.name}_{self.experiment}_{self.metric}_{self.strategy}_{self.optimization}_{gate}.{extension}')
            else:
                folder = f'{folder}/{self.name}_{self.experiment}_{self.metric}_{self.strategy}'
                os.makedirs(folder, exist_ok=True)
                self.set_out_path(
                    f'{folder}/{self.name}_{self.experiment}_{self.metric}_{self.strategy}_{gate}.{extension}')

        self.append_pyscript_files_for_labeling(self.out_path)

        import_string = self.create_imports()
        abs_function = self.create_abs_function()

        # exact_part
        original_circuit_declaration = self.declare_original_circuit()
        original_circuit_expression = self.express_original_circuit()
        if self.metric == WHD:
            original_output_declaration = f'\n'
        else:
            original_output_declaration = self.declare_original_output()

        approximate_circuit_declaration = self.declare_approximate_circuit()
        approximate_circuit_expression = self.express_approximate_circuit()

        if self.metric == WHD:
            xor_miter_declaration = self.declare_xor_miter()
        else:
            approximate_output_declaration = self.declare_approximate_output()

        # error distance function
        declare_error_distance_function = self.declare_error_distance_function()
        # strategy

        strategy = self.express_strategy()

        if self.metric == WHD:
            self.set_z3pyscript(
                import_string + abs_function + original_circuit_declaration + original_circuit_expression +
                approximate_circuit_expression + xor_miter_declaration + declare_error_distance_function + strategy)
        else:
            self.set_z3pyscript(
                import_string + abs_function + original_circuit_declaration + original_circuit_expression +
                original_output_declaration + approximate_circuit_declaration + approximate_circuit_expression +
                approximate_output_declaration + declare_error_distance_function + strategy)

        self.export_z3pyscript()

    def create_pruned_z3pyscript_approximate(self, gates: list, constant_value: bool = False):
        self.create_pruned_graph_approximate(gates, constant_value)
        if self.experiment == SINGLE:
            gate = gates[0]
        # TODO
        elif self.experiment == RANDOM:
            gate = 'id0'
        folder, extension = OUTPUT_PATH['report']
        if self.metric == WRE:
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                folder = f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}_{constant_value}'
                os.makedirs(folder, exist_ok=True)
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}_{gate}.{extension}')
            else:
                folder = f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{constant_value}'
                os.makedirs(folder, exist_ok=True)
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{gate}.{extension}')
        else:

            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                folder = f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}_{self.optimization}_{constant_value}'
                os.makedirs(folder, exist_ok=True)
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}_{self.optimization}_{gate}.{extension}')
            else:
                folder = f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}_{constant_value}'
                os.makedirs(folder, exist_ok=True)
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}_{gate}.{extension}')

        folder, extension = OUTPUT_PATH['z3']
        if self.metric == WRE:
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                folder = f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}_{constant_value}'
                os.makedirs(folder, exist_ok=True)
                self.set_out_path(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}_{gate}.{extension}')
            else:
                folder = f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{constant_value}'
                os.makedirs(folder, exist_ok=True)
                self.set_out_path(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{gate}.{extension}')
        else:
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                folder = f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}_{self.optimization}_{constant_value}'
                os.makedirs(folder, exist_ok=True)
                self.set_out_path(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}_{self.optimization}_{gate}.{extension}')
            else:
                folder = f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}_{constant_value}'
                os.makedirs(folder, exist_ok=True)
                self.set_out_path(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}_{gate}.{extension}')

        self.append_pyscript_files_for_labeling(self.out_path)

        import_string = self.create_imports()
        abs_function = self.create_abs_function()

        # exact_part
        original_circuit_declaration = self.declare_original_circuit()
        original_circuit_expression = self.express_original_circuit()
        if self.metric == WHD:
            original_output_declaration = f'\n'
        else:
            original_output_declaration = self.declare_original_output()

        approximate_circuit_declaration = self.declare_approximate_circuit()
        approximate_circuit_expression = self.express_approximate_circuit()

        if self.metric == WHD:
            xor_miter_declaration = self.declare_xor_miter()
        else:
            approximate_output_declaration = self.declare_approximate_output()

        # error distance function
        declare_error_distance_function = self.declare_error_distance_function()
        # strategy

        strategy = self.express_strategy()

        if self.metric == WHD:
            self.set_z3pyscript(
                import_string + abs_function + original_circuit_declaration + original_circuit_expression +
                approximate_circuit_expression + xor_miter_declaration + declare_error_distance_function + strategy)
        else:
            self.set_z3pyscript(
                import_string + abs_function + original_circuit_declaration + original_circuit_expression +
                original_output_declaration + approximate_circuit_declaration + approximate_circuit_expression +
                approximate_output_declaration + declare_error_distance_function + strategy)

        self.export_z3pyscript()

    def convert_gv_to_z3pyscript_xpat(self):
        pass

    def create_pruned_graph(self, gates: list):

        tmp_graph = copy.deepcopy(self.graph)
        self.set_approximate_graph(tmp_graph)
        mapping_dict = {}
        for gate in gates:
            if self.graph.is_pi(gate) or self.graph.is_cleaned_pi(gate) or self.graph.is_pruned_pi(gate):
                mapping_dict[gate] = f'app_{gate}'
        for gate in gates:
            self.approximate_graph.graph.nodes[gate][PRUNED] = True
        self.approximate_graph.set_graph(nx.relabel_nodes(self.approximate_graph.graph, mapping_dict))
        self.relabel_approximate_graph()
        self.approximate_graph.set_input_dict(self.approximate_graph.extract_inputs())
        self.approximate_graph.set_output_dict(self.approximate_graph.extract_outputs())
        self.approximate_graph.set_gate_dict(self.approximate_graph.extract_gates())
        self.approximate_graph.set_constant_dict(self.approximate_graph.extract_constants())

    def create_pruned_graph_approximate(self, gates: list, constant_value: bool =False):

        tmp_graph = copy.deepcopy(self.labeling_graph)
        self.set_approximate_graph(tmp_graph)
        mapping_dict = {}
        for gate in gates:
            if self.labeling_graph.is_pi(gate) or self.labeling_graph.is_cleaned_pi(gate) or self.labeling_graph.is_pruned_pi(gate):
                mapping_dict[gate] = f'{gate}'
        for gate in gates:
            self.approximate_graph.graph.nodes[gate][PRUNED] =  constant_value
        self.approximate_graph.set_graph(nx.relabel_nodes(self.approximate_graph.graph, mapping_dict))
        self.relabel_approximate_graph()
        self.approximate_graph.set_input_dict(self.approximate_graph.extract_inputs())
        self.approximate_graph.set_output_dict(self.approximate_graph.extract_outputs())
        self.approximate_graph.set_gate_dict(self.approximate_graph.extract_gates())
        self.approximate_graph.set_constant_dict(self.approximate_graph.extract_constants())

    # TODO
    # for other back-ends as well

    def declare_error_distance_function(self):
        ed_function = ''

        if self.metric == WAE:
            ed_function += f"f_exact = Function('f_exact', IntSort(), IntSort())\n" \
                           f"f_approx = Function('f_approx', IntSort(), IntSort())\n"
            ed_function += f"f_error = Function('f_error', IntSort(), IntSort(), IntSort())\n"
        elif self.metric == WHD:
            ed_function += f"f_error = Function('f_error', IntSort(), "
            for i in range(self.graph.num_outputs):
                if i == self.graph.num_outputs - 1:
                    ed_function += f"IntSort() )\n"
                else:
                    ed_function += f"IntSort(), "
        elif self.metric == WRE:
            ed_function += f"f_exact = Function('f_exact', IntSort(), IntSort())\n" \
                           f"f_approx = Function('f_approx', IntSort(), IntSort())\n"
            ed_function += f"f_error = Function('f_error', IntSort(), IntSort(), RealSort())\n"
        ed_function += f'\n'
        return ed_function

    def express_strategy(self, metric: str = None):
        strategy_expressed = ''
        if re.search(MONOTONIC, self.strategy):
            strategy_expressed += self.express_monotonic_strategy()
        elif re.search(BISECTION, self.strategy):
            strategy_expressed += self.express_bisection_strategy()
        elif re.search(MC, self.strategy):
            strategy_expressed += self.express_mc_strategy()
        elif re.search(KIND_BISECTION, self.strategy):
            strategy_expressed += self.express_kind_bisection_strategy()
        else:
            print(f'ERROR!!! no strategy is specified!')
            exit()
        return strategy_expressed

    def declare_stats(self):
        stats = ''
        stats = f'foundWCE = False\n' \
                f'stats: dict = {{}}\n' \
                f"stats['wce'] = 0\n"

        if self.metric == WAE:
            stats += f"stats['et'] = 0\n"
        elif self.metric == WHD:
            stats += f"stats['et'] = 0\n"
        elif self.metric == WRE:
            stats += f"stats['et'] = float(\"{{:.{self.precision}f}}\".format(0))\n"

        stats += f"stats['num_sats'] = 0\n" \
                 f"stats['num_unsats'] = 0\n" \
                 f"stats['sat_runtime'] = 0.0\n" \
                 f"stats['unsat_runtime'] = 0.0\n" \
                 f"stats['jumps'] = []\n"
        if self.metric == WAE or self.metric == WRE:
            stats += f"max = (2 ** {self.graph.num_outputs}) -1\n"
        elif self.metric == WHD:
            stats += f"max = {self.graph.num_outputs}\n"
        return stats

    def express_mc_while_loop(self):
        loop = ''
        loop += f's=Solver()\n' \
                f'start_whole = time.time()\n'

        for sample in self.samples:
            loop += f's.push()\n' \
                    f's.add(f_error(exact_out, approx_out) == z3_abs(exact_out - approx_out))\n' \
                    f'{self.express_push_input_sample(sample)}' \
                    f'response=s.check()\n' \
                    f'returned_model = s.model()\n' \
                    f'returned_value = abs(int(returned_model[f_error].else_value().as_long()))\n' \
                    f'returned_value_reval = abs(int(returned_model.evaluate(f_error(exact_out, approx_out)).as_long()))\n' \
                    f'if returned_value == returned_value_reval:\n' \
                    f"{TAB}print(f'double-check is passed!')\n" \
                    f"else:\n" \
                    f"{TAB}print(f'ERROR!!! double-check failed! exiting...')\n" \
                    f"{TAB}exit()\n" \
                    f"if returned_value > stats['wce']:\n" \
                    f"{TAB}stats['wce'] = returned_value\n" \
                    f"s.pop()\n" \
                    f"\n" \
                    f""
        loop += self.express_stats()
        return loop

    def express_push_input_sample(self, sample: int):
        sample_expression = ''
        s_expression = [True if i == '1' else False for i in list(f'{sample:0{self.graph.num_inputs}b}')]
        s_expression.reverse()
        sample_expression += f's.add('
        for idx, e in enumerate(s_expression):
            if idx == len(s_expression) - 1:
                sample_expression += f'{self.graph.input_dict[idx]}=={e})\n'
            else:
                sample_expression += f'{self.graph.input_dict[idx]}=={e}, '

        return sample_expression

    def express_kind_bisection_while_loop(self):
        loop = ''
        if self.metric == WAE or self.metric == WRE:
            loop += f'upper_bound = 2**({self.graph.num_outputs}) - 1\n' \
                    f'lower_bound = 0 \n' \
                    f'start_whole = time.time()\n'
        else:
            loop += f'upper_bound = {self.graph.num_outputs}\n' \
                    f'lower_bound = 0 \n' \
                    f'start_whole = time.time()\n'

        loop += f's = Solver()\n'

        loop += f'while(not foundWCE):\n'

        if self.metric == WAE:
            loop += f"{TAB}stats['et'] = (upper_bound + lower_bound) // 2\n"
        elif self.metric == WHD:
            loop += f"{TAB}stats['et'] = (upper_bound + lower_bound) // 2\n"
        elif self.metric == WRE:
            loop += f"{TAB}import math\n"
            loop += f"{TAB}stats['et'] = math.floor((float(upper_bound + lower_bound) / 2) * {10 ** self.precision}) / {10 ** self.precision}\n"



        # Check termination
        if self.metric == WAE:
            loop += f"{TAB}if upper_bound - lower_bound <= 1:\n" \
                    f"{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}stats['wce'] = lower_bound\n" \
                    f"{TAB}{TAB}if stats['et'] in stats['jumps']:\n" \
                    f"{TAB}{TAB}{TAB}break\n"
        elif self.metric == WHD:
            loop += f"{TAB}if upper_bound - lower_bound <= 1:\n" \
                    f"{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}if lower_bound == 0:\n" \
                    f"{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                    f"{TAB}{TAB}else:\n" \
                    f"{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n" \
                    f"{TAB}{TAB}if stats['et'] in stats['jumps']:\n" \
                    f"{TAB}{TAB}{TAB}break\n"
        elif self.metric == WRE:
            loop += f"{TAB}if stats['et'] == lower_bound:\n" \
                    f"{TAB}{TAB}if stats['et'] in stats['jumps']:\n" \
                    f"{TAB}{TAB}{TAB}if lower_bound == 0:\n" \
                    f"{TAB}{TAB}{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                    f"{TAB}{TAB}{TAB}else:\n" \
                    f"{TAB}{TAB}{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n"

            loop += f"{TAB}elif round(upper_bound - lower_bound, 2) <= (10 ** -{self.precision}):\n" \
                    f"{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}stats['wce'] = lower_bound\n" \
                    f"{TAB}{TAB}if stats['et'] in stats['jumps']:\n" \
                    f"{TAB}{TAB}{TAB}break\n"
        loop += f"{TAB}if stats['et'] not in stats['jumps']:\n" \
                f"{TAB}{TAB}stats['jumps'].append(stats['et'])\n"

        loop += f'{TAB}start_iteration = time.time()\n' \
                f'{TAB}s.push()\n'
        if self.metric == WAE or self.metric == WRE:
            loop += f'{TAB}s.add(f_exact(exact_out) == exact_out)\n' \
                    f'{TAB}s.add(f_approx(approx_out) == approx_out)\n'

        if self.metric == WAE:
            loop += f'{TAB}s.add(f_error(exact_out, approx_out) == exact_out - approx_out)\n' \
                    f"{TAB}s.add(z3_abs(f_error(exact_out, approx_out)) > stats['et'])\n"
        elif self.metric == WHD:
            if self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                pass
            else:
                loop += f"{TAB}s.add(f_error("
                for i in range(self.graph.num_outputs):
                    if i == self.graph.num_outputs - 1:
                        loop += f"o{i}_{XOR}_{INT}) == "
                    else:
                        loop += f"o{i}_{XOR}_{INT}, "
                for i in range(self.graph.num_outputs):
                    if i == self.graph.num_outputs - 1:
                        loop += f"o{i}_{XOR}_{INT})\n"
                    else:
                        loop += f"o{i}_{XOR}_{INT} +  "
                loop += f"{TAB}s.add(f_error("
                for i in range(self.graph.num_outputs):
                    if i == self.graph.num_outputs - 1:
                        loop += f"o{i}_{XOR}_{INT}) > stats['et'])\n"
                    else:
                        loop += f"o{i}_{XOR}_{INT}, "
            # TODO
        elif self.metric == WRE:
            loop += f'{TAB}s.add(f_error(exact_out, approx_out) == z3_abs(exact_out - approx_out) / (z3_abs(exact_out) + z3_abs(1.0))  )\n' \
                    f"{TAB}s.add(z3_abs(f_error(exact_out, approx_out)) > stats['et'])\n"

        loop += f"{TAB}response = s.check()\n"
        loop += self.express_kind_bisection_while_loop_sat()
        loop += self.express_kind_bisection_while_loop_unsat()
        loop += self.express_stats()

        return loop

    def express_bisection_while_loop(self):
        loop = ''
        if self.metric == WAE or self.metric == WRE:
            loop += f'upper_bound = 2**({self.graph.num_outputs}) - 1\n' \
                    f'lower_bound = 0 \n' \
                    f'start_whole = time.time()\n'
        else:
            loop += f'upper_bound = {self.graph.num_outputs}\n' \
                    f'lower_bound = 0 \n' \
                    f'start_whole = time.time()\n'

        loop += f's = Solver()\n'

        loop += f'while(not foundWCE):\n'


        if self.metric == WAE:
            loop += f"{TAB}stats['et'] = (upper_bound + lower_bound) // 2\n"
        elif self.metric == WHD:
            loop += f"{TAB}stats['et'] = (upper_bound + lower_bound) // 2\n"
        elif self.metric == WRE:
            loop += f"{TAB}import math\n"
            loop += f"{TAB}stats['et'] = math.floor((float(upper_bound + lower_bound) / 2) * {10 ** self.precision}) / {10 ** self.precision}\n"



        # Check termination
        if self.metric == WAE:
            loop += f"{TAB}if upper_bound - lower_bound <= 1:\n" \
                    f"{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}if lower_bound == 0:\n" \
                    f"{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                    f"{TAB}{TAB}else:\n" \
                    f"{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n" \
                    f"{TAB}{TAB}if stats['et'] in stats['jumps']:\n" \
                    f"{TAB}{TAB}{TAB}break\n"
        elif self.metric == WHD:
            loop += f"{TAB}if upper_bound - lower_bound <= 1:\n" \
                    f"{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}if lower_bound == 0:\n" \
                    f"{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                    f"{TAB}{TAB}else:\n" \
                    f"{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n" \
                    f"{TAB}{TAB}if stats['et'] in stats['jumps']:\n" \
                    f"{TAB}{TAB}{TAB}break\n"
        elif self.metric == WRE:
            loop += f"{TAB}if stats['et'] == lower_bound:\n" \
                    f"{TAB}{TAB}if stats['et'] in stats['jumps']:\n" \
                    f"{TAB}{TAB}{TAB}if lower_bound == 0:\n" \
                    f"{TAB}{TAB}{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                    f"{TAB}{TAB}{TAB}else:\n" \
                    f"{TAB}{TAB}{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n"
            loop += f"{TAB}if round(upper_bound - lower_bound, 2) <= (10 ** -{self.precision}):\n" \
                    f"{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}if lower_bound == 0:\n" \
                    f"{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                    f"{TAB}{TAB}else:\n" \
                    f"{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n" \
                    f"{TAB}{TAB}if stats['et'] in stats['jumps']:\n" \
                    f"{TAB}{TAB}{TAB}break\n"

        loop += f"{TAB}if stats['et'] not in stats['jumps']:\n" \
                f"{TAB}{TAB}stats['jumps'].append(stats['et'])\n"

        loop += f'{TAB}start_iteration = time.time()\n' \
                f'{TAB}s.push()\n'
        if self.metric == WAE or self.metric == WRE:
                loop += f'{TAB}s.add(f_exact(exact_out) == exact_out)\n' \
                        f'{TAB}s.add(f_approx(approx_out) == approx_out)\n'


        if self.metric == WAE:
            loop += f'{TAB}s.add(f_error(exact_out, approx_out) == exact_out - approx_out)\n' \
                    f"{TAB}s.add(z3_abs(f_error(exact_out, approx_out)) > stats['et'])\n"
        elif self.metric == WHD:
            if self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                pass
            else:
                loop += f"{TAB}s.add(f_error("
                for i in range(self.graph.num_outputs):
                    if i == self.graph.num_outputs - 1:
                        loop += f"o{i}_{XOR}_{INT}) == "
                    else:
                        loop += f"o{i}_{XOR}_{INT}, "
                for i in range(self.graph.num_outputs):
                    if i == self.graph.num_outputs - 1:
                        loop += f"o{i}_{XOR}_{INT})\n"
                    else:
                        loop += f"o{i}_{XOR}_{INT} +  "
                loop += f"{TAB}s.add(f_error("
                for i in range(self.graph.num_outputs):
                    if i == self.graph.num_outputs - 1:
                        loop += f"o{i}_{XOR}_{INT}) > stats['et'])\n"
                    else:
                        loop += f"o{i}_{XOR}_{INT}, "
            # TODO
        elif self.metric == WRE:
            loop += f'{TAB}s.add(f_error(exact_out, approx_out) == z3_abs(exact_out - approx_out) / (z3_abs(exact_out) + z3_abs(1.0))  )\n' \
                    f"{TAB}s.add(z3_abs(f_error(exact_out, approx_out)) > stats['et'])\n"

        loop += f"{TAB}response = s.check()\n"

        loop += self.express_bisection_while_loop_sat()
        loop += self.express_bisection_while_loop_unsat()
        loop += self.express_stats()

        return loop

    def express_monotonic_while_loop(self):
        loop = ''

        loop += f'start_whole = time.time()\n'
        # print(f'{self.optimization == MAXIMIZE = }')
        # print(f'{self.optimization = }')
        if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
            loop += f's = Optimize()\n'
        else:
            # print('We are here')
            loop += f's = Solver()\n'

        loop += f"stats['jumps'].append(stats['et'])\n" \
                f'while(not foundWCE):\n' \
                f'{TAB}start_iteration = time.time()\n' \
                f'{TAB}s.push()\n'
        if self.metric == WAE or self.metric == WRE:
            loop += f'{TAB}s.add(f_exact(exact_out) == exact_out)\n' \
                    f'{TAB}s.add(f_approx(approx_out) == approx_out)\n'

        if self.metric == WAE:
            if self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                loop += f'{TAB}s.add(f_error(exact_out, approx_out) == z3_abs(exact_out - approx_out))\n'
                if self.style == 'min':
                    loop += f"{TAB}s.add((f_error(exact_out, approx_out)) <= z3_abs(max))\n" \
                            f"{TAB}s.add((f_error(exact_out, approx_out)) > z3_abs(0))\n" \
                            f"{TAB}s.minimize(z3_abs(f_error(exact_out, approx_out)))\n"
                elif self.style == 'max':
                    loop += f"{TAB}s.add((f_error(exact_out, approx_out)) > z3_abs(stats['et']))\n" \
                            f"{TAB}s.maximize(z3_abs(f_error(exact_out, approx_out)))\n"
            else:
                loop += f'{TAB}s.add(f_error(exact_out, approx_out) == z3_abs(exact_out - approx_out))\n' \
                        f"{TAB}s.add((f_error(exact_out, approx_out)) > z3_abs(stats['et']))\n"

            # TODO add optimization thingy right here
        elif self.metric == WHD:
            if self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                pass
            else:
                loop += f"{TAB}s.add(f_error("
                for i in range(self.graph.num_outputs):
                    if i == self.graph.num_outputs - 1:
                        loop += f"o{i}_{XOR}_{INT}) == "
                    else:
                        loop += f"o{i}_{XOR}_{INT}, "
                for i in range(self.graph.num_outputs):
                    if i == self.graph.num_outputs - 1:
                        loop += f"o{i}_{XOR}_{INT})\n"
                    else:
                        loop += f"o{i}_{XOR}_{INT} +  "
                loop += f"{TAB}s.add(f_error("
                for i in range(self.graph.num_outputs):
                    if i == self.graph.num_outputs - 1:
                        loop += f"o{i}_{XOR}_{INT}) > stats['et'])\n"
                    else:
                        loop += f"o{i}_{XOR}_{INT}, "
            # TODO
        elif self.metric == WRE:
            if self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                loop += f'{TAB}s.add(f_error(exact_out, approx_out) == z3_abs(exact_out - approx_out) / (z3_abs(exact_out) + z3_abs(1.0))  )\n' \
                        f"{TAB}s.add(z3_abs(f_error(exact_out, approx_out)) > stats['et'])\n" \
                        f"{TAB}s.maximize(z3_abs(f_error(exact_out, approx_out)))\n"
            else:
                loop += f'{TAB}s.add(f_error(exact_out, approx_out) == z3_abs(exact_out - approx_out) / (z3_abs(exact_out) + z3_abs(1.0))  )\n' \
                        f"{TAB}s.add(z3_abs(f_error(exact_out, approx_out)) > stats['et'])\n"
        loop += f"{TAB}response = s.check()\n"

        loop += self.express_monotonic_while_loop_sat()
        loop += self.express_monotonic_while_loop_unsat()
        loop += self.express_stats()

        return loop

    def express_kind_bisection_while_loop_sat(self):
        if_sat = ''

        if_sat += f"{TAB}if response == sat:\n" \
                  f"{TAB}{TAB}print(f'sat')\n" \
                  f"{TAB}{TAB}end_iteration = time.time()\n" \
                  f"{TAB}{TAB}returned_model = s.model()\n" \
                  f"{TAB}{TAB}print(f\"{{returned_model[f_error].else_value() = }}\")\n"

        if self.metric == WAE:
            if_sat += f"{TAB}{TAB}returned_value = abs(int(returned_model[f_error].else_value().as_long()))\n" \
                      f"{TAB}{TAB}returned_value_reval = abs(int(returned_model.evaluate(f_error(exact_out, approx_out)).as_long()))\n"
        elif self.metric == WHD:
            if_sat += f"{TAB}{TAB}returned_value = abs(int(returned_model[f_error].else_value().as_long()))\n"

            if_sat += f"{TAB}{TAB}returned_value_reval = abs(int(returned_model.evaluate(f_error("
            for i in range(self.graph.num_outputs):
                if i == self.graph.num_outputs - 1:
                    if_sat += f"o{i}_{XOR}_{INT})).as_long()))\n"
                else:
                    if_sat += f"o{i}_{XOR}_{INT}, "
            # TODO
        elif self.metric == WRE:
            if_sat += f"{TAB}{TAB}returned_value = ((returned_model[f_error].else_value().as_decimal({self.precision})))\n" \
                      f"{TAB}{TAB}returned_value_reval = ((returned_model.evaluate(f_error(exact_out, approx_out)).as_decimal({self.precision})))\n"


        # Double-check
        if_sat += f"{TAB}{TAB}if returned_value == returned_value_reval:\n" \
                  f"{TAB}{TAB}{TAB}print(f'double-check is passed!')\n" \
                  f"{TAB}{TAB}else:\n" \
                  f"{TAB}{TAB}{TAB}print(f'ERROR!!! double-check failed! exiting...')\n" \
                  f"{TAB}{TAB}{TAB}exit()\n"

        if self.metric == WRE:
            if_sat += f"{TAB}{TAB}if returned_value[-1] == '?':\n" \
                      f"{TAB}{TAB}{TAB}print('removing the last question mark!')\n" \
                      f"{TAB}{TAB}{TAB}returned_value = abs(float(returned_value[:-1])) + 10 ** -({self.precision})\n" \
                      f"{TAB}{TAB}else:\n" \
                      f"{TAB}{TAB}{TAB}returned_value = abs(float(returned_value))\n"

        if self.metric == WAE:
            if_sat += f"{TAB}{TAB}if upper_bound - lower_bound <= 1:\n" \
                      f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                      f"{TAB}{TAB}{TAB}stats['wce'] = returned_value\n" \
                      f"{TAB}{TAB}else:\n" \
                      f"{TAB}{TAB}{TAB}lower_bound = returned_value\n"
        elif self.metric == WHD:
            if_sat += f"{TAB}{TAB}if upper_bound - lower_bound <= 1:\n" \
                      f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                      f"{TAB}{TAB}{TAB}stats['wce'] = returned_value\n" \
                      f"{TAB}{TAB}else:\n" \
                      f"{TAB}{TAB}{TAB}lower_bound = returned_value\n"
        elif self.metric == WRE:
            if_sat += f"{TAB}{TAB}if round(upper_bound - lower_bound, 2) <= (10 ** -{self.precision}):\n" \
                      f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                      f"{TAB}{TAB}{TAB}stats['wce'] = float(\"{{:.{self.precision}f}}\".format(returned_value))\n" \
                      f"{TAB}{TAB}else:\n" \
                      f"{TAB}{TAB}{TAB}lower_bound = float(\"{{:.{self.precision}f}}\".format(returned_value))\n"

        if_sat += f"{TAB}{TAB}stats['num_sats'] += 1\n" \
                  f"{TAB}{TAB}stats['sat_runtime'] += (end_iteration - start_iteration)\n" \
                  f"{TAB}{TAB}if stats['et'] == max:\n" \
                  f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                  f"{TAB}{TAB}{TAB}stats['wce'] = stats['et']\n"

        return if_sat

    def express_bisection_while_loop_sat(self):
        if_sat = ''

        if_sat += f"{TAB}if response == sat:\n" \
                  f"{TAB}{TAB}print(f'sat')\n" \
                  f"{TAB}{TAB}end_iteration = time.time()\n" \
                  f"{TAB}{TAB}returned_model = s.model()\n" \
                  f"{TAB}{TAB}print(f'{{returned_model = }}')\n"
        if self.metric == WAE or self.metric == WRE:
            f"{TAB}{TAB}print(f\"{{returned_model[f_exact].else_value() = }}\")\n" \
            f"{TAB}{TAB}print(f\"{{returned_model[f_approx].else_value() = }}\")\n" \
            f"{TAB}{TAB}print(f\"{{returned_model[f_error].else_value() = }}\")\n"
        elif self.metric == WHD:
            f"{TAB}{TAB}print(f\"{{returned_model[f_error].else_value() = }}\")\n"


        if self.metric == WAE:
            if_sat += f"{TAB}{TAB}returned_value = abs(int(returned_model[f_error].else_value().as_long()))\n" \
                      f"{TAB}{TAB}returned_value_reval = abs(int(returned_model.evaluate(f_error(exact_out, approx_out)).as_long()))\n"
        elif self.metric == WHD:
            if_sat += f"{TAB}{TAB}returned_value = abs(int(returned_model[f_error].else_value().as_long()))\n"

            if_sat += f"{TAB}{TAB}returned_value_reval = abs(int(returned_model.evaluate(f_error("
            for i in range(self.graph.num_outputs):
                if i == self.graph.num_outputs - 1:
                    if_sat += f"o{i}_{XOR}_{INT})).as_long()))\n"
                else:
                    if_sat += f"o{i}_{XOR}_{INT}, "
            # TODO
        elif self.metric == WRE:
            if_sat += f"{TAB}{TAB}returned_value = ((returned_model[f_error].else_value().as_decimal({self.precision})))\n" \
                      f"{TAB}{TAB}returned_value_reval = ((returned_model.evaluate(f_error(exact_out, approx_out)).as_decimal({self.precision})))\n"

        if_sat += f"{TAB}{TAB}if returned_value == returned_value_reval:\n" \
                  f"{TAB}{TAB}{TAB}print(f'double-check is passed!')\n" \
                  f"{TAB}{TAB}else:\n" \
                  f"{TAB}{TAB}{TAB}print(f'ERROR!!! double-check failed! exiting...')\n" \
                  f"{TAB}{TAB}{TAB}exit()\n"

        if self.metric == WRE:
            if_sat += f"{TAB}{TAB}if returned_value[-1] == '?':\n" \
                      f"{TAB}{TAB}{TAB}print('removing the last question mark!')\n" \
                      f"{TAB}{TAB}{TAB}returned_value = abs(float(returned_value[:-1])) + 10 ** -(2)\n" \
                      f"{TAB}{TAB}else:\n" \
                      f"{TAB}{TAB}{TAB}returned_value = abs(float(returned_value))\n"


        if self.metric == WAE:
            if_sat += f"{TAB}{TAB}if upper_bound - lower_bound <= 1:\n" \
                      f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                      f"{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n" \
                      f"{TAB}{TAB}else:\n" \
                      f"{TAB}{TAB}{TAB}lower_bound = stats['et']\n"
        elif self.metric == WHD:
            if_sat += f"{TAB}{TAB}if upper_bound - lower_bound <= 1:\n" \
                      f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                      f"{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n" \
                      f"{TAB}{TAB}else:\n" \
                      f"{TAB}{TAB}{TAB}lower_bound = stats['et']\n"
        elif self.metric == WRE:
            if_sat += f'{TAB}{TAB}if round(upper_bound - lower_bound, 2) <= (10 ** - {self.precision}):\n' \
                      f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                      f"{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n" \
                      f"{TAB}{TAB}else:\n" \
                      f"{TAB}{TAB}{TAB}lower_bound = float(stats['et'])\n"

        if_sat += f"{TAB}{TAB}stats['num_sats'] += 1\n" \
                  f"{TAB}{TAB}stats['sat_runtime'] += (end_iteration - start_iteration)\n" \
                  f"{TAB}{TAB}if stats['et'] == max:\n" \
                  f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                  f"{TAB}{TAB}{TAB}stats['wce'] = stats['et']\n"

        return if_sat

    def express_monotonic_while_loop_sat(self):
        if_sat = ''
        if_sat += f"{TAB}if response == sat:\n" \
                  f"{TAB}{TAB}print(f'sat')\n" \
                  f"{TAB}{TAB}end_iteration = time.time()\n" \
                  f"{TAB}{TAB}returned_model = s.model()\n" \
                  f"{TAB}{TAB}print(f'{{returned_model = }}')\n"
        if self.metric == WAE or self.metric == WRE:
                  f"{TAB}{TAB}print(f\"{{returned_model[f_exact].else_value() = }}\")\n" \
                  f"{TAB}{TAB}print(f\"{{returned_model[f_approx].else_value() = }}\")\n" \
                  f"{TAB}{TAB}print(f\"{{returned_model[f_error].else_value() = }}\")\n"
        elif self.metric == WHD:
            f"{TAB}{TAB}print(f\"{{returned_model[f_error].else_value() = }}\")\n"



        if self.metric == WAE:
            if_sat += f"{TAB}{TAB}returned_value = abs(int(returned_model[f_error].else_value().as_long()))\n" \
                      f"{TAB}{TAB}returned_value_reval = abs(int(returned_model.evaluate(f_error(exact_out, approx_out)).as_long()))\n"
        elif self.metric == WHD:
            if_sat += f"{TAB}{TAB}returned_value = abs(int(returned_model[f_error].else_value().as_long()))\n"

            if_sat +=  f"{TAB}{TAB}returned_value_reval = abs(int(returned_model.evaluate(f_error("
            for i in range(self.graph.num_outputs):
                if i == self.graph.num_outputs - 1:
                    if_sat += f"o{i}_{XOR}_{INT})).as_long()))\n"
                else:
                    if_sat += f"o{i}_{XOR}_{INT}, "




        elif self.metric == WRE:
            if_sat += f"{TAB}{TAB}returned_value = ((returned_model[f_error].else_value().as_decimal({self.precision})))\n" \
                      f"{TAB}{TAB}returned_value_reval = ((returned_model.evaluate(f_error(exact_out, approx_out)).as_decimal({self.precision})))\n"

        if_sat += f"{TAB}{TAB}if returned_value == returned_value_reval:\n" \
                  f"{TAB}{TAB}{TAB}print(f'double-check is passed!')\n" \
                  f"{TAB}{TAB}else:\n" \
                  f"{TAB}{TAB}{TAB}print(f'ERROR!!! double-check failed! exiting...')\n" \
                  f"{TAB}{TAB}{TAB}exit()\n"

        if self.metric == WRE:
            if_sat += f"{TAB}{TAB}if returned_value[-1] == '?':\n" \
                      f"{TAB}{TAB}{TAB}print('removing the last question mark!')\n" \
                      f"{TAB}{TAB}{TAB}returned_value = abs(float(returned_value[:-1])) + 10 ** -({self.precision})\n" \
                      f"{TAB}{TAB}else:\n" \
                      f"{TAB}{TAB}{TAB}returned_value = abs(float(returned_value))\n"

        if self.metric == WAE:
            if_sat += f"{TAB}{TAB}stats['et'] = returned_value\n"
        elif self.metric == WHD:
            if_sat += f"{TAB}{TAB}stats['et'] = returned_value\n"
        elif self.metric == WRE:
            if_sat += f"{TAB}{TAB}stats['et'] = \"{{:.{self.precision}f}}\".format(returned_value)\n"

        if_sat += f"{TAB}{TAB}stats['num_sats'] += 1\n" \
                  f"{TAB}{TAB}stats['sat_runtime'] += (end_iteration - start_iteration)\n" \
                  f"{TAB}{TAB}stats['jumps'].append(returned_value)\n"

        if self.style == 'max':
            if_sat += f"{TAB}{TAB}if stats['et'] == max:\n" \
                        f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                        f"{TAB}{TAB}{TAB}stats['wce'] = stats['et']\n"
        elif self.style == 'min':
            if_sat +=   f"{TAB}{TAB}foundWCE = True\n" \
                        f"{TAB}{TAB}stats['wce'] = stats['et']\n"

        return if_sat

    def express_kind_bisection_while_loop_unsat(self):
        if_unsat = ''

        if_unsat += f"\n" \
                    f"{TAB}if response == unsat:\n" \
                    f"{TAB}{TAB}print('unsat')\n" \
                    f"{TAB}{TAB}end_iteration = time.time()\n"

        if self.metric == WAE:
            if_unsat += f"{TAB}{TAB}if upper_bound - lower_bound <= 1:\n" \
                        f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                        f"{TAB}{TAB}{TAB}if lower_bound == 0:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                        f"{TAB}{TAB}{TAB}else:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n"
        elif self.metric == WHD:
            if_unsat += f"{TAB}{TAB}if upper_bound - lower_bound <= 1:\n" \
                        f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                        f"{TAB}{TAB}{TAB}if lower_bound == 0:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                        f"{TAB}{TAB}{TAB}else:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n"
        elif self.metric == WRE:
            if_unsat += f"{TAB}{TAB}if round(upper_bound - lower_bound, 2) <= (10 ** -{self.precision}):\n" \
                        f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                        f"{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                        f"{TAB}{TAB}{TAB}if lower_bound == 0:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                        f"{TAB}{TAB}{TAB}else:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n"

        if_unsat += f"{TAB}{TAB}else:\n" \
                    f"{TAB}{TAB}{TAB}upper_bound = float(stats['et'])\n" \
                    f"{TAB}{TAB}stats['num_unsats'] += 1\n" \
                    f"{TAB}{TAB}stats['unsat_runtime'] += (end_iteration - start_iteration)\n" \
                    f"{TAB}s.pop()\n"
        return if_unsat

    def express_bisection_while_loop_unsat(self):
        if_unsat = ''

        if_unsat += f"\n" \
                    f"{TAB}if response == unsat:\n" \
                    f"{TAB}{TAB}print('unsat')\n" \
                    f"{TAB}{TAB}end_iteration = time.time()\n"

        if self.metric == WAE:
            if_unsat += f"{TAB}{TAB}if upper_bound - lower_bound <= 1:\n" \
                        f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                        f"{TAB}{TAB}{TAB}if lower_bound == 0:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                        f"{TAB}{TAB}{TAB}else:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n"
        elif self.metric == WHD:
            if_unsat += f"{TAB}{TAB}if upper_bound - lower_bound <= 1:\n" \
                        f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                        f"{TAB}{TAB}{TAB}if lower_bound == 0:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                        f"{TAB}{TAB}{TAB}else:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n"
        elif self.metric == WRE:
            if_unsat += f"{TAB}{TAB}if round(upper_bound - lower_bound, 2) <= (10 ** -{self.precision}):\n" \
                        f"{TAB}{TAB}{TAB}foundWCE = True\n" \
                        f"{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                        f"{TAB}{TAB}{TAB}if lower_bound == 0:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = lower_bound\n" \
                        f"{TAB}{TAB}{TAB}else:\n" \
                        f"{TAB}{TAB}{TAB}{TAB}stats['wce'] = upper_bound\n"

        if_unsat += f"{TAB}{TAB}else:\n" \
                    f"{TAB}{TAB}{TAB}upper_bound = float(stats['et'])\n" \
                    f"{TAB}{TAB}stats['num_unsats'] += 1\n" \
                    f"{TAB}{TAB}stats['unsat_runtime'] += (end_iteration - start_iteration)\n" \
                    f"{TAB}s.pop()\n"
        return if_unsat

    def express_monotonic_while_loop_unsat(self):
        if_unsat = ''
        if_unsat += f"\n" \
                    f"{TAB}if response == unsat:\n" \
                    f"{TAB}{TAB}print('unsat')\n" \
                    f"{TAB}{TAB}end_iteration = time.time()\n" \
                    f"{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}stats['num_unsats'] += 1\n" \
                    f"{TAB}{TAB}stats['unsat_runtime'] += (end_iteration - start_iteration)\n"
        if self.style == 'max':
                    if_unsat +=f"{TAB}{TAB}stats['wce'] = stats['et']\n" \
                               f"{TAB}s.pop()\n"
        elif self.style == 'min':
                    if_unsat += f"{TAB}{TAB}stats['wce'] = 0\n" \
                                f"{TAB}s.pop()\n"

        return if_unsat

    def express_stats(self):
        stats = ''
        stats += f"end_whole = time.time()\n" \
                 f"with open('{self.z3_report}', 'w') as f:\n" \
                 f"{TAB}csvwriter = csv.writer(f)\n" \
                 f"{TAB}header = ['field', 'value']\n" \
                 f"{TAB}csvwriter.writerow(['Experiment', '{self.experiment}'])\n" \
                 f"{TAB}csvwriter.writerow(['WCE', stats['wce']])\n" \
                 f"{TAB}csvwriter.writerow(['Total Runtime', end_whole - start_whole])\n" \
                 f"{TAB}csvwriter.writerow(['SAT Runtime', stats['sat_runtime']])\n" \
                 f"{TAB}csvwriter.writerow(['UNSAT Runtime', stats['unsat_runtime']])\n" \
                 f"{TAB}csvwriter.writerow(['Number of SAT calls', stats['num_sats']])\n" \
                 f"{TAB}csvwriter.writerow(['Number of UNSAT calls', stats['num_unsats']])\n" \
                 f"{TAB}csvwriter.writerow(['Jumps', stats['jumps']])\n"
        return stats

    def express_monotonic_strategy(self):
        monotonic_strategy = ''
        monotonic_strategy += self.declare_stats()
        monotonic_strategy += self.express_monotonic_while_loop()
        return monotonic_strategy

    def express_mc_strategy(self):
        mc_strategy = ''
        mc_strategy += self.declare_stats()
        mc_strategy += self.express_mc_while_loop()
        return mc_strategy

    def express_bisection_strategy(self):
        bisection_strategy = ''
        bisection_strategy += self.declare_stats()
        bisection_strategy += self.express_bisection_while_loop()

        return bisection_strategy

    def express_kind_bisection_strategy(self):
        kind_bisection_strategy = ''
        kind_bisection_strategy += self.declare_stats()
        kind_bisection_strategy += self.express_kind_bisection_while_loop()
        return kind_bisection_strategy

    def export_z3pyscript(self):
        with open(self.out_path, 'w') as z:
            z.writelines(self.z3pyscript)

    def __repr__(self):
        return f'An object of class Z3solver\n' \
               f'{self.name = }\n' \
               f'{self.graph_in_path = }\n' \
               f'{self.out_path = }\n'

    def create_imports(self):
        import_string = f'from z3 import *\n' \
                        f'import sys\n' \
                        f'import time\n' \
                        f'import csv\n' \
                        f'\n'
        return import_string

    def create_abs_function(self):
        abs_function = f'def z3_abs(x):\n' \
                       f'\treturn If(x >= 0, x, -x)\n' \
                       f'\n'

        return abs_function

    def declare_original_circuit(self):
        exact_circuit_declaration = ''
        # inputs
        for n in self.graph.graph.nodes:
            if re.search(r'in\d+', self.graph.graph.nodes[n]['label']):
                exact_circuit_declaration = f'{exact_circuit_declaration}' \
                                            f'{self.declare_gate(n)}\n'
        exact_circuit_declaration += f'\n'
        # gates
        for n in self.graph.graph.nodes:
            if re.search(r'g\d+', n):
                exact_circuit_declaration = f'{exact_circuit_declaration}' \
                                            f'{self.declare_gate(n)}\n'
        # outputs
        for n in self.graph.graph.nodes:
            if re.search(r'out\d+', self.graph.graph.nodes[n]['label']):
                exact_circuit_declaration = f'{exact_circuit_declaration}' \
                                            f'{self.declare_gate(n)}\n'
        return exact_circuit_declaration

    def declare_approximate_circuit(self):
        exact_circuit_declaration = ''
        # inputs
        for n in self.approximate_graph.graph.nodes:
            if self.approximate_graph.is_pruned_pi(n):
                exact_circuit_declaration = f'{exact_circuit_declaration}' \
                                            f'{self.declare_gate(n)}\n'
        exact_circuit_declaration += f'\n'
        # gates
        for n in self.approximate_graph.graph.nodes:
            if re.search(r'g\d+', n):
                exact_circuit_declaration = f'{exact_circuit_declaration}' \
                                            f'{self.declare_gate(n)}\n'
        # outputs
        for n in self.approximate_graph.graph.nodes:
            if re.search(r'out\d+', self.approximate_graph.graph.nodes[n]['label']):
                exact_circuit_declaration = f'{exact_circuit_declaration}' \
                                            f'{self.declare_gate(n)}\n'
        return exact_circuit_declaration

    def declare_gate(self, this_key: str):
        declaration = f"{this_key} = {Z3BOOL}('{this_key}')"
        return declaration

    def express_original_circuit(self):
        exact_circuit_function = ''
        for n in self.graph.graph.nodes:
            if self.graph.is_cleaned_gate(n):
                exact_circuit_function += f'{self.express_exact_gate(n)}\n'
            elif self.graph.is_cleaned_constant(n):
                exact_circuit_function += f'{self.express_exact_constant(n)}\n'
            elif self.graph.is_cleaned_po(n):
                exact_circuit_function += f'{self.express_exact_output(n)}\n'
        exact_circuit_function += f'\n'
        return exact_circuit_function

    def express_approximate_circuit(self):
        approximate_circuit_function = ''

        for n in self.approximate_graph.graph.nodes:
            if self.approximate_graph.is_cleaned_pi(n):
                approximate_circuit_function += f'{self.express_approximate_gate(n)}\n'
            elif self.approximate_graph.is_cleaned_gate(n):
                approximate_circuit_function += f'{self.express_approximate_gate(n)}\n'
            elif self.approximate_graph.is_cleaned_constant(n):
                approximate_circuit_function += f'{self.express_approximate_constant(n)}\n'
            elif self.approximate_graph.is_cleaned_po(n):
                approximate_circuit_function += f'{self.express_approximate_output(n)}\n'
        approximate_circuit_function += f'\n'

        return approximate_circuit_function

    def express_exact_output(self, this_key):
        cur_node = ''
        predecessor = list(self.graph.graph.predecessors(this_key))[0]
        cur_node = f'{this_key} = {predecessor}\n'

        return cur_node

    def express_exact_constant(self, this_key):
        cur_node = ''
        this_constant = re.search(r'TRUE|FALSE', self.graph.graph.nodes[this_key][LABEL]).group()
        cur_node += f'{this_key} = {Z3_GATES_DICTIONARY[this_constant]}\n'
        return cur_node

    def express_exact_gate(self, this_key: str):
        # sth like this: g110 = Not(And(g108, g109))
        cur_node = ''
        if self.graph.is_cleaned_gate(this_key):
            this_gate = re.search(POSSIBLE_GATES, self.graph.graph.nodes[this_key]['label']).group()
            cur_gate = Z3_GATES_DICTIONARY[this_gate]
            predecessor_list = list(self.graph.graph.predecessors(this_key))
            cur_node = f"{this_key}={cur_gate}("
            for idx, u in enumerate(predecessor_list):
                cur_node += f'{u}'
                if idx == len(predecessor_list) - 1:
                    cur_node += f')'
                else:
                    cur_node += f','

        elif self.graph.is_cleaned_pi(this_key):
            pass
        elif self.graph.is_cleaned_po(this_key):
            cur_node = f'{this_key}='
            predecessor_list = list(self.graph.graph.predecessors(this_key))
            for idx, u in enumerate(predecessor_list):
                cur_node += f'{u}'
        return cur_node

    def express_approximate_output(self, this_key):
        cur_node = ''
        predecessor = list(self.approximate_graph.graph.predecessors(this_key))[0]
        cur_node = f'{this_key} = {predecessor}\n'

        return cur_node

    def express_approximate_constant(self, this_key):
        cur_node = ''

        if self.approximate_graph.is_pruned_constant(this_key):
            # cur_node = f'{this_key} = {self.approximate_graph.graph.nodes[this_key][PRUNED]}'
            cur_node = f'# {this_key} is left as a free variable'
            # leave it as free variable
            pass
        else:
            # print(f'{this_key = }')
            this_constant = re.search(r'TRUE|FALSE', self.approximate_graph.graph.nodes[this_key][LABEL]).group()
            cur_node += f'{this_key} = {Z3_GATES_DICTIONARY[this_constant]}\n'
            # if self.approximate_graph.graph.nodes[this_key][PRUNED] == False:
            #     print(f'{this_key = }')
        return cur_node

    def express_approximate_gate(self, this_key: str):
        # sth like this: g110 = Not(And(g108, g109))
        cur_node = ''
        if self.approximate_graph.is_pruned_gate(this_key):
            # cur_node = f'{this_key} = {self.approximate_graph.graph.nodes[this_key][PRUNED]}'
            cur_node = f'# {this_key} is left as a free variable'
            # leave it as free variable
            pass

        elif self.approximate_graph.is_cleaned_gate(this_key):
            this_gate = re.search(POSSIBLE_GATES, self.approximate_graph.graph.nodes[this_key]['label']).group()
            cur_gate = Z3_GATES_DICTIONARY[this_gate]
            predecessor_list = list(self.approximate_graph.graph.predecessors(this_key))
            cur_node = f"{this_key}={cur_gate}("
            for idx, u in enumerate(predecessor_list):
                cur_node += f'{u}'
                if idx == len(predecessor_list) - 1:
                    cur_node += f')'
                else:
                    cur_node += f','

        elif self.approximate_graph.is_pruned_pi(this_key):
            cur_node = f'{this_key}= {self.approximate_graph.graph.nodes[this_key][PRUNED]}'
        elif self.approximate_graph.is_cleaned_po(this_key):
            cur_node = f'{this_key}='
            predecessor_list = list(self.approximate_graph.graph.predecessors(this_key))
            for idx, u in enumerate(predecessor_list):
                cur_node += f'{u}'
        return cur_node

    def declare_original_output(self):
        output_declaration = ''
        # print(f'{self.graph.output_dict = }')



        for i in range(self.graph.num_outputs):
            output_declaration += f"exact_out{i}=Int('exact_out{i}')\n"
            output_declaration += f"exact_out{i}={self.graph.output_dict[i]}*{2 ** i}*2/2\n"

        output_declaration += f"exact_out = Int('exact_out')\n"
        output_declaration += f'exact_out='

        for i in range(self.graph.num_outputs):
            if i == self.graph.num_outputs - 1:
                output_declaration += f'exact_out{i}'
            else:
                output_declaration += f'exact_out{i}+'

        output_declaration += f'\n'
        return output_declaration

    def declare_approximate_output(self):
        output_declaration = ''
        # print(f'{self.approximate_graph.output_dict = }')

        for i in range(self.approximate_graph.num_outputs):
            output_declaration += f"approx_out{i}=Int('approx_out{i}')\n"
            output_declaration += f"approx_out{i}={self.approximate_graph.output_dict[i]}*{2 ** i}*2/2\n"
        # print(f'{self.approximate_graph.output_dict = }')
        output_declaration += f"approx_out = Int('approx_out')\n"
        output_declaration += f'approx_out='
        for i in range(self.approximate_graph.num_outputs):
            if i == self.approximate_graph.num_outputs - 1:
                output_declaration += f'approx_out{i}'
            else:
                output_declaration += f'approx_out{i}+'

        output_declaration += f'\n'
        return output_declaration

    def declare_xor_miter(self):

        xor_miter_declaration = f''
        # o0_xor = Bool('o0_xor')
        # o1_xor = Bool('o1_xor')
        # o2_xor = Bool('o2_xor')
        for i in range(self.graph.num_outputs):
            xor_miter_declaration += f"{MITER}_o{i}_{XOR} = {Z3BOOL}('o{i}_{XOR}')\n"


        # o0_xor = Xor(g27, a27)
        # o1_xor = Xor(g105, a105)
        # o2_xor = Xor(g99, a99)
        for i in range(self.graph.num_outputs):
            xor_miter_declaration += f"o{i}_{XOR} = {Z3XOR}({self.graph.output_dict[i]}, app_{self.graph.output_dict[i]})\n"


        # o0_xor_int = Int('o0_xor_int')
        # o0_xor_int = o0_xor * 2 / 2
        # o1_xor_int = Int('o1_xor_int')
        # o1_xor_int = o1_xor * 2 / 2
        # o2_xor_int = Int('o2_xor_int')
        # o2_xor_int = o2_xor * 2 / 2
        for i in range(self.graph.num_outputs):
            xor_miter_declaration += f"o{i}_{XOR}_{INT} = {Z3INT}('o{i}_{XOR}_{INT}')\n" \
                                     f"o{i}_{XOR}_{INT} = o{i}_{XOR} * 2/2\n"

        return xor_miter_declaration





    def declare_original_function(self):
        exact_function = ''
        exact_function += f'results = []\n'
        exact_function += f"f_exact = Function('f', IntSort(), IntSort())"
        exact_function += f'\n'
        return exact_function

    def declare_approximate_function(self):
        exact_function = ''
        exact_function += f'results = []\n'
        exact_function += f"f_exact = Function('f', IntSort(), IntSort())"
        exact_function += f'\n'
        return exact_function

    def declare_solver(self):
        solver = ''
        if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE:
            solver += f's = Optimize()\n'
        else:
            solver += f's = Solver()\n'

        solver += f's.add(f_exact(exact_out) == exact_out)\n'
        solver += f'\n'

        return solver

    def express_samples(self):
        sample_expression = ''
        for s in self.samples:
            sample_expression += f's.push()\n'
            s_expression = [True if i == '1' else False for i in list(f'{s:0{self.graph.num_inputs}b}')]
            # a 1101 is considered as in3,in2,in1,in0 => in3=1, in2=1, in1=0, in0=1
            s_expression.reverse()  # to keep it consistent with the verilog testbench
            sample_expression += f's.add('
            for idx, e in enumerate(s_expression):
                if idx == len(s_expression) - 1:
                    sample_expression += f'{self.graph.input_dict[idx]}=={e})\n'
                else:
                    sample_expression += f'{self.graph.input_dict[idx]}=={e}, '

            sample_expression += f'sol = s.check()\n'
            sample_expression += f'm = s.model()\n'
            sample_expression += f"print(f'{{m = }}')\n"
            sample_expression += f'cur_result = m[f_exact].else_value().as_string()\n'
            sample_expression += f'results.append(cur_result)\n'

            sample_expression += f's.pop()\n\n'

        return sample_expression

    def store_results(self):
        store_results = ''
        store_results += f"with open('{self.pyscript_results_out_path}', 'w') as f:\n" \
                         f"\tfor line in results:\n" \
                         f"\t\tf.write(line)\n" \
                         f"\t\tf.write('\\n')\n"
        store_results += f"print(f'{{results = }}')"
        return store_results

    # TODO: decorators-----------------------------
    def run_z3pyscript_qor(self):
        with open(self.z3_log_path, 'w') as f:
            process = subprocess.run([PYTHON3, self.out_path],  stderr=PIPE, stdout=PIPE)

    def run_z3pyscript_labeling(self):
          # Get the number of CPUs
        active_procs = []
        if self.parallel:
            num_workers = multiprocessing.cpu_count()
            print(Fore.LIGHTBLUE_EX + 'Labeling (explicit & parallel)... ', end='' + Style.RESET_ALL)
            for pyscript in self.pyscript_files_for_labeling:
                # Start a new process
                proc = Popen([PYTHON3, pyscript], stderr=PIPE, stdout=PIPE)
                active_procs.append(proc)

                # If we have reached the max number of workers, wait for one to finish
                if len(active_procs) >= num_workers:
                    finished_proc = active_procs.pop(0)  # Remove the first/oldest proc
                    finished_proc.communicate()  # Wait for it to finish

            # Wait for any remaining processes to finish
            for proc in active_procs:
                proc.communicate()

            print(Fore.LIGHTBLUE_EX + 'Done' + Style.RESET_ALL)
        else:
            print(Fore.LIGHTBLUE_EX + f'Labeling (explicit & sequential)... ', end='' + Style.RESET_ALL)
            num_workers = 1
            for pyscript in self.pyscript_files_for_labeling:
                # Start a new process
                proc = Popen([PYTHON3, pyscript], stderr=PIPE, stdout=PIPE)
                active_procs.append(proc)

                # If we have reached the max number of workers, wait for one to finish
                if len(active_procs) >= num_workers:
                    finished_proc = active_procs.pop(0)  # Remove the first/oldest proc
                    finished_proc.communicate()  # Wait for it to finish

            # Wait for any remaining processes to finish
            for proc in active_procs:
                proc.communicate()
            print(Fore.LIGHTBLUE_EX + f'Done' + Style.RESET_ALL)

    #TODO: Deprecated
    def run_z3pyscript_labeling_old(self):

        if self.parallel:
            print(Fore.LIGHTBLUE_EX + f'Labeling (explicit & parallel)... ', end=''  + Style.RESET_ALL)
            procs_list = [Popen([PYTHON3, pyscript], stderr=PIPE, stdout=PIPE) for pyscript in self.pyscript_files_for_labeling]
            for proc in procs_list:
                proc.wait()
            print(Fore.LIGHTBLUE_EX + f'Done' + Style.RESET_ALL)
        else:
            print(Fore.LIGHTBLUE_EX + f'Labeling (explicit & sequential)... ', end='' + Style.RESET_ALL)


            for pyscript in self.pyscript_files_for_labeling:
                with open(self.z3_log_path, 'w') as f:
                    # process = subprocess.run([PYTHON3, pyscript], stdout=PIPE, stderr=PIPE)
                    process = subprocess.run([PYTHON3, pyscript], stderr=PIPE, stdout=PIPE)

                    if process.stderr:
                        print(Fore.RED + f'ERROR!!! cannot run {pyscript} properly!')
                        print(f'{process.stderr.decode()}')
        # print(f'All pyscript files = {self.pyscript_files_for_labeling = }')
            print(Fore.LIGHTBLUE_EX + f'Done' + Style.RESET_ALL)


    def run_z3pyscript_random(self):
        with open(self.z3_log_path, 'w') as f:
            process = subprocess.run([PYTHON3, self.out_path], stdout=PIPE, stderr=PIPE)

    def run_z3pyscript_test(self):
        with open(self.z3_log_path, 'w') as f:
            # process = subprocess.run([PYTHON3, self.out_path], stdout=PIPE, stderr=PIPE)
            process = subprocess.run([PYTHON3, self.out_path], stderr=PIPE, stdout=PIPE)

        self.set_sample_results(self.import_results())
    # TODO: decorators (end)--------------------------


