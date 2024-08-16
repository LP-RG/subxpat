from z3 import *
import sys
from time import time
from typing import Tuple, List, Callable, Any, Union
import json
import csv

et = int(sys.argv[1])
et_encoded = {{{{et_encoded}}}}
wanted_models: int = 1 if len(sys.argv) < 3 else int(sys.argv[2])
timeout: float = float(sys.maxsize if len(sys.argv) < 4 else sys.argv[3])
max_possible_et: int = 2 ** {{{{num_outputs}}}} - 1

# Encoding abs_diff method to generate
def z3_abs_diff(a, b):
	return {{{{abs_diff_def}}}}

# Inputs variables declaration
{{{{ini_defs}}}}

# Bitvector function declaration
fe = {{{{function_exact}}}}
# Bitvector function declaration
fa = {{{{function_approximate}}}}
# utility variables
difference = z3_abs_diff(fe({{{{gen_inputs_arguments}}}}), fa({{{{gen_inputs_arguments}}}}))
error = {{{{error}}}}

# Parameters variables declaration
{{{{params_declaration}}}}
params_list = {{{{params_list}}}}

# wires functions declaration for exact circuit
{{{{exact_wires_declaration}}}}

# wires functions declaration for approximate circuit
{{{{approximate_wires_declaration}}}}

# outputs bitvectors declaration for exact circuit
{{{{exact_outputs_declaration}}}}

# outputs bitvectors declaration for approximate circuit
{{{{approximate_outputs_declaration}}}}

# exact circuit constraints
exact_circuit = And(
	# wires
	{{{{exact_wires_constraints}}}}
	
	# output bits (from the least significant)
	{{{{exact_output_constraints}}}}
	
	# aggregated output
	{{{{exact_aggregated_output}}}}
)

# approximate circuit constraints
approximate_circuit = And(
	# wires
	{{{{approximate_wires_constraints}}}}

	# output bits (from the least significant)
	{{{{approximate_output_constraints}}}}
	
	# aggregated output
	{{{{approximate_aggregated_output}}}}
)

verification_solver = {{{{solver}}}}
verification_solver.add(
	error == difference,
	exact_circuit,
	approximate_circuit,
)

parameters_constraints: List[Tuple[BoolRef, bool]] = []
all_parameters_constraints = []
found_data = []
while(len(found_data) < wanted_models and timeout > 0):
	time_total_start = time()
	
	attempts = 1
	result: CheckSatResult = None
	attempts_times: List[Tuple[float, float, float]] = []

	while result != sat:
		time_attempt_start = time()
		time_parameters_start = time_attempt_start

		# forall and verification solvers
		forall_solver = {{{{solver}}}}
		forall_solver.add(ForAll(
			[{{{{inputs}}}}],
			And(
				# error constraints
				{{{{difference_less_equal_etenc}}}},

				# circuits
				exact_circuit,
				approximate_circuit,

				{{{{logic_dependant_constraint1}}}}
				
				#> redundancy constraints

				# remove double no-care
				{{{{remove_double_constraint}}}}

				# remove constant 0 parameters permutations
				{{{{remove_zero_permutations_constraint}}}}

				# set order of products
				{{{{product_order_constraint}}}}
			)
		))

		# add constrain to prevent the same parameters to happen
		if all_parameters_constraints:
			for pc in all_parameters_constraints:
				forall_solver.add(Or(*map(lambda x: x[0] != x[1], pc)))
		forall_solver.set('timeout', int(timeout * 1000))
		result = forall_solver.check()
		time_parameters = time() - time_attempt_start
		time_attempt = time() - time_attempt_start
		timeout -= time_parameters # removed the time used from the timeout
		if result != sat:
			attempts_times.append((time_attempt, time_parameters, None))
			break
		m = forall_solver.model()
		parameters_constraints = []
		for k, v in map(lambda k: (k, m[k]), m):
			if str(k)[0] == 'p':
				parameters_constraints.append((Bool(str(k)), v))
		all_parameters_constraints.append(parameters_constraints)
		# verify parameters
		WCE: int = None
		verification_et: int = 0
		time_verification_start = time()
		# save state
		verification_solver.push()
		# parameters constraints
		verification_solver.add(
			*map(lambda x: x[0] == x[1], parameters_constraints),
		)

		while verification_et < max_possible_et:
			# add constraint
			verification_solver.add({{{{difference_greater_veret}}}})
			# run solver
			verification_solver.set('timeout', int(timeout * 1000))
			v_result = verification_solver.check()
			if v_result == unsat:
				# unsat, WCE found
				WCE = verification_et
				break
			elif v_result == sat:
				# sat, need to search again
				m = verification_solver.model()
				verification_et = m[error].as_long()
			else:
				 # unknown (probably a timeout)
				WCE = -1
				break

		if WCE is None:
			WCE = max_possible_et
		# revert state
		verification_solver.pop()
		time_verification = time() - time_verification_start
		time_attempt = time() - time_attempt_start
		timeout -= time_verification  # remove the time used from the timeout
		attempts_times.append((time_attempt, time_parameters, time_verification))
		
		# ==== continue or exit
		if WCE > et:
			# Z3 hates us and decided it doesn't like being appreciated
			result = None
			attempts += 1
			invalid_parameters = parameters_constraints
		elif WCE < 0:  # caused by unknown
			break

	# store data
	def extract_info(pattern: Union[Pattern, str], string: str,
				parser: Callable[[Any], Any] = lambda x: x,
				default: Union[Callable[[], None], Any] = None) -> Any:
		import re
		return (parser(match[1]) if (match := re.search(pattern, string))
				else (default() if callable(default) else default))

	def key_function(parameter_constraint):
		p = str(parameter_constraint[0])
		o_id = extract_info(r'_o(\d+)', p, int, -1)
		t_id = extract_info(r'_t(\d+)', p, int, 0)
		i_id = extract_info(r'_i(\d+)', p, int, 0)
		typ = extract_info(r'_(l|s)', p, {'s': 1, 'l': 2}.get, 0)
		if o_id < 0:
			return 0
		return (o_id * 100000
				+ t_id * 1000
				+ i_id * 10
				+ typ)

	time_total = time() - time_total_start
	data_object = {
		'benchmark_name': '{{{{benchmark_name}}}}',
		'encoding': '{{{{encoding}}}}',
		'cell': '{{{{cell}}}}',
		'result': str(result),
		'total_time': time_total,
		'attempts': attempts,
		'attempts_times': [list(map(lambda tup: [*tup], attempts_times))]
	}
	if result == sat:
		data_object['model'] = {str(p): is_true(m[p]) for p in params_list}
	found_data.append(data_object)
	if result != sat:
		break
print(json.dumps(found_data, separators=(',', ':'),))

# Could consider file writing fully dynamically
with open('{{{{output_path}}}}', 'w') as ofile:
	ofile.write(json.dumps(found_data, separators=(',', ':'), indent=4))
