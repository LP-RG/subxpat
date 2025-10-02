from typing import Dict

import re
import os
import csv

from Z3Log.z3solver import Z3solver
from Z3Log.config.path import *
from Z3Log.config.config import *


 
class Z3solverRef(Z3solver):

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
            return self.import_labels(constant_value)
            

        else:
            for key in self.labeling_graph.gate_dict:

                removed_gate = [self.labeling_graph.gate_dict[key]]

                self.create_pruned_z3pyscript_approximate(removed_gate, constant_value)
            for key in self.labeling_graph.constant_dict:
                removed_gate = [self.labeling_graph.constant_dict[key]]
                self.create_pruned_z3pyscript_approximate(removed_gate, constant_value)
            self.run_z3pyscript_labeling()
            return self.import_labels(constant_value)

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
                            f"{TAB}handle = s.minimize(z3_abs(f_error(exact_out, approx_out)))\n"
                elif self.style == 'max':
                    loop += f"{TAB}s.add((f_error(exact_out, approx_out)) > z3_abs(stats['et']))\n" \
                            f"{TAB}handle = s.maximize(z3_abs(f_error(exact_out, approx_out)))\n"
            else:
                loop += f'{TAB}s.add(f_error(exact_out, approx_out) == z3_abs(exact_out - approx_out))\n' \
                        f"{TAB}s.add((f_error(exact_out, approx_out)) > z3_abs(stats['et']))\n"

        loop += f"{TAB}response = s.check()\n"

        loop += self.express_monotonic_while_loop_sat()
        loop += self.express_monotonic_while_loop_unsat()
        loop += self.express_stats()

        return loop

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

        if self.metric == WAE:
            if_sat += f"{TAB}{TAB}returned_value = handle.upper()\n" \
                      f"{TAB}{TAB}returned_value_reval = abs(int(returned_model[f_error].else_value().as_long()))\n"


        if_sat += f"{TAB}{TAB}if returned_value == returned_value_reval:\n" \
                  f"{TAB}{TAB}{TAB}print(f'double-check is passed!')\n" \
                  f"{TAB}{TAB}{TAB}double_check = True\n" \
                  f"{TAB}{TAB}else:\n" \
                  f"{TAB}{TAB}{TAB}print(f'ERROR!!! double-check failed! exiting...')\n" \
                  f"{TAB}{TAB}{TAB}double_check = False\n" \

        if self.metric == WAE:
            if_sat += f"{TAB}{TAB}stats['et'] = returned_value\n"

        if_sat += f"{TAB}{TAB}stats['num_sats'] += 1\n" \
                  f"{TAB}{TAB}stats['sat_runtime'] += (end_iteration - start_iteration)\n" \
                  f"{TAB}{TAB}stats['jumps'].append(returned_value)\n"

        if_sat +=   f"{TAB}{TAB}foundWCE = True\n" \
                    f"{TAB}{TAB}stats['wce'] = stats['et']\n"

        return if_sat

    def express_stats(self):
        stats = ''
        stats += f"end_whole = time.time()\n" \
                 f"with open('{self.z3_report}', 'w') as f:\n" \
                 f"{TAB}csvwriter = csv.writer(f)\n" \
                 f"{TAB}header = ['field', 'value']\n" \
                 f"{TAB}csvwriter.writerow(['Experiment', '{self.experiment}'])\n" \
                 f"{TAB}csvwriter.writerow(['WCE', stats['wce']])\n" \
                 f"{TAB}csvwriter.writerow(['double_check', double_check])\n" \
                 f"{TAB}csvwriter.writerow(['Total Runtime', end_whole - start_whole])\n" \
                 f"{TAB}csvwriter.writerow(['SAT Runtime', stats['sat_runtime']])\n" \
                 f"{TAB}csvwriter.writerow(['UNSAT Runtime', stats['unsat_runtime']])\n" \
                 f"{TAB}csvwriter.writerow(['Number of SAT calls', stats['num_sats']])\n" \
                 f"{TAB}csvwriter.writerow(['Number of UNSAT calls', stats['num_unsats']])\n" \
                 f"{TAB}csvwriter.writerow(['Jumps', stats['jumps']])\n"
        return stats

    def import_labels(self, constant_value: bool=False):


        label_dict: Dict[str, int] = {}
        double_check_dict: Dict[str, bool] = {}
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
                        
                        if re.search('double_check', line[0]):
                            double_check = bool(line[1])
                            double_check_dict[gate_label] = double_check

        return (label_dict, double_check_dict)