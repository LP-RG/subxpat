from z3 import *
import sys
from time import time
from typing import Tuple, List, Callable, Any, Union
import json
import csv

ET = int(sys.argv[1])
{{{{ET_ENC}}}}
wanted_models: int = 1 if len(sys.argv) < 3 else int(sys.argv[2])
timeout: float = float(sys.maxsize if len(sys.argv) < 4 else sys.argv[3])
max_possible_ET: int = 2 ** 3 - 1

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
# Using abs_diff
difference = z3_abs_diff(fe({{{{gen_inputs_arguments}}}}), fa({{{{gen_inputs_arguments}}}}))
error = {{{{error}}}}

# Parameters variables declaration
# p_oi = Bool('p_oi')
# p_o0_t0_i0_s = Bool('p_o0_t0_i0_s')
# p_o0_t0_i0_l = Bool('p_o0_t0_i0_l')
{{{{params_declaration}}}}

# wires functions declaration for exact circuit
# ei = Function('ei', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
{{{{exact_wires_declaration}}}}

# wires functions declaration for approximate circuit
# ei = Function('ei', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
{{{{approximate_wires_declaration}}}}

# outputs bitvectors declaration for exact circuit
# eouti = Function ('eouti', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BitVecSort(outputs))
{{{{exact_outputs_declaration}}}}

# outputs bitvectors declaration for approximate circuit
# aouti = Function ('aouti', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BitVecSort(outputs))
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
	# boolean outputs (from the least significant) as bitvectors
	# exact_bitvector_outputs
)


# boolean outputs (from the least significant) as bitvectors
# aouti(ini) == If(a32(in0,in4,a20(in0, in1, in2, in3, in4, in5, in6, in7),a26(in0, in1, in2, in3, in4, in5, in6, in7),a31(in0, in1, in2, in3, in4, in5, in6, in7),a50(in0, in1, in2, in3, in4, in5, in6, in7),a53(in0, in1, in2, in3, in4, in5, in6, in7)), BitVecVal(0b00001, 5), BitVecVal(0b00000, 5)),
{{{{boolean_outputs}}}}

# approximate_bitvec_outputs
# fa(ini) == 
# aouti(ini) + ...
{{{{approximate_outputs}}}}

# forall and verification solvers
forall_solver = {{{{forall_solver}}}}
verification_solver = {{{{verification_solver}}}}

parameters_constraints: List[Tuple[BoolRef, bool]] = []
found_data = []
while(len(found_data) < wanted_models and timeout > 0):
	time_total_start = time()
	
	attempts = 1
	result: CheckSatResult = None
	attempts_times: List[Tuple[float, float, float]] = []

	while result != sat:
		time_attempt_start = time()
		time_parameters_start = time_attempt_start
		# add constrain to prevent the same parameters to happen
		if parameters_constraints:
			forall_solver.add(Or(*map(lambda x: x[0] != x[1], parameters_constraints)))
		parameters_constraints = []
		forall_solver.set("timeout", int(timeout * 1000))
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
			if str(k)[0] == "p":
				parameters_constraints.append((Bool(str(k)), v))
		# verify parameters
		WCE: int = None
		verification_ET: int = 0
		time_verification_start = time()
		# save state
		verification_solver.push()
		# parameters constraints
		verification_solver.add(
			*map(lambda x: x[0] == x[1], parameters_constraints),
		)

		while verification_ET < max_possible_ET:
			# add constraint (difference > verification_ET) or UGE(...)
			verification_solver.add({{{{difference_constraint}}}})
			# run solver
			verification_solver.set("timeout", int(timeout * 1000))
			v_result = verification_solver.check()
			if v_result == unsat:
				# unsat, WCE found
				WCE = verification_ET
				break
			elif v_result == sat:
				# sat, need to search again
				m = verification_solver.model()
				verification_ET = m[error].as_long()
			else:
				 # unknown (probably a timeout)
				WCE = -1
				break

		if WCE is None:
			WCE = max_possible_ET
		# revert state
		verification_solver.pop()
		time_verification = time() - time_verification_start
		time_attempt = time() - time_attempt_start
		timeout -= time_verification  # remove the time used from the timeout
		attempts_times.append((time_attempt, time_parameters, time_verification))
		
		# ==== continue or exit
		if WCE > ET:
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
	data_object = {{{{data_object}}}}
	if result == sat:
		data_object['model'] = dict(map(lambda item: (str(item[0]), is_true(item[1])),
			sorted(parameters_constraints,
			key=key_function)))
	found_data.append(data_object)
	if result != sat:
		break
print(json.dumps(found_data, separators=(",", ":"),))

# Could consider file writing fully dynamically
with open(f'output/json/{{{{output_path}}}}', 'w') as ofile:
	ofile.write(json.dumps(found_data, separators=(",", ":"), indent=4))

with open('./output/report/all_results.csv', 'a') as f:
	csvwriter = csv.writer(f)
	row = []
	row.append('{{{{circuit_name}}}}')
	row.append('{{{{encoding}}}}')
	row.append(str(result))
	row.append('{{{{cell}}}}')
	row.append(time_total)
	row.append(attempts)
	row.append(ET)
	row = tuple(row)
	csvwriter.writerow(row)
