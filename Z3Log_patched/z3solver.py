from typing import Dict

import re
import os
import copy
import csv
from os.path import join as path_join

from .utils import get_pure_name
from .graph import Graph

from .config.config import (
    SINGLE, WAE, RANDOM, WRE, OPTIMIZE, MAXIMIZE, BISECTION,
    WHD, WCE, DEFAULT_STRATEGY, QOR,
)

# patched:
from Z3Log.z3solver import Z3solver as _Z3solver


class Z3solver(_Z3solver):
    def __init__(self,
                 circuit_in_graphviz_path: str,
                 approx_circuit_in_graphviz_path: str,
                 temporary_folder_path: str,
                 #
                 samples: list = [],
                 experiment: str = SINGLE,
                 pruned_percentage: int = None, pruned_gates=None, metric: str = WAE, precision: int = 4,
                 optimization: str = None, style: str = 'max',
                 parallel: bool = False, partial: bool = True):
        """

        :param benchmark_name: the input benchmark in gv format
        :param approximate_benchmark_name: the approximate benchmark in gv format
        :param samples: number of samples for the mc evaluation; by defaults it is an empty list
        """
        self.__circuit_name = circuit_name = get_pure_name(circuit_in_graphviz_path)
        self.__graph = Graph(circuit_in_graphviz_path, True)

        self.__pyscript_results_out_path = None

        self.__z3_log_path = path_join(temporary_folder_path, f'{circuit_name}_z3py.log')

        # added
        self.temporary_folder_path = temporary_folder_path

        self.__approximate_graph = None

        if approx_circuit_in_graphviz_path:
            self.__approximate_circuit_name = get_pure_name(approx_circuit_in_graphviz_path)
            self.__approximate_graph = Graph(approx_circuit_in_graphviz_path, True)

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

    @property
    def graph_in_path(self): raise RuntimeError('Why are you using this? talk with Marco')
    @property
    def approximate_in_path(self): raise RuntimeError('Why are you using this? talk with Marco')

    def import_labels(self, constant_value: bool = False) -> Dict:
        label_dict: Dict[str, int] = {}
        folder = path_join(self.temporary_folder_path, 'outreport')
        extension = 'csv'

        all_dirs = [f for f in os.listdir(folder)]
        # print(f'{all_dirs = }')
        relevant_dir = None
        for dir in all_dirs:
            if re.search(f'{self.approximate_benchmark}_{SINGLE}', dir) and os.path.isdir(f'{folder}/{dir}') and re.search(f'{constant_value}', dir):
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

    def convert_gv_to_z3pyscript_test(self):
        self.set_z3_report(path_join(self.temporary_folder_path, f'outreport_{self.name}_test.csv'))
        self.set_out_path(path_join(self.temporary_folder_path, f'outz3_{self.name}_test.py'))
        self.set_pyscript_results_out_path(path_join(self.temporary_folder_path, f'testz3_{self.name}_test.py'))

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
            folder = path_join(self.temporary_folder_path, 'outreport')
            extension = 'csv'
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}.{extension}')
            else:
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}.{extension}')

            folder = path_join(self.temporary_folder_path, 'outz3')
            extension = 'py'
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                self.set_out_path(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}_{self.optimization}.{extension}')
            else:
                self.set_out_path(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_d{self.precision}_{self.strategy}.{extension}')

        else:
            folder = path_join(self.temporary_folder_path, 'outreport')
            extension = 'csv'
            if self.optimization == OPTIMIZE or self.optimization == MAXIMIZE and (self.strategy != BISECTION):
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}_{self.optimization}.{extension}')
            else:
                self.set_z3_report(
                    f'{folder}/{self.approximate_benchmark}_{self.experiment}_{self.metric}_{self.strategy}.{extension}')

            folder = path_join(self.temporary_folder_path, 'outz3')
            extension = 'py'
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

    # TODO
    # Naming problems for more than one gate removal

    def create_pruned_z3pyscript(self, gates: list, constant_value: bool = False):
        self.create_pruned_graph_approximate(gates, constant_value)
        if self.experiment == SINGLE:
            gate = gates[0]
        # TODO
        elif self.experiment == RANDOM:
            gate = 'id0'

        folder = path_join(self.temporary_folder_path, 'outreport')
        extension = 'csv'
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

        folder = path_join(self.temporary_folder_path, 'outz3')
        extension = 'py'
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

        folder = path_join(self.temporary_folder_path, 'outreport')
        extension = 'csv'
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

        folder = path_join(self.temporary_folder_path, 'outz3')
        extension = 'py'
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

    def __repr__(self):
        return (
            f'An object of class Z3solver\n'
            f'{self.name = }\n'
            # f'{self.graph_in_path = }\n'
            f'{self.out_path = }\n'
        )
