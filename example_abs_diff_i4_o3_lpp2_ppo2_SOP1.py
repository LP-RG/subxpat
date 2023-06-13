from z3 import *
import sys
from time import time
from typing import Tuple, List, Callable, Any, Union
import json

ET = int(sys.argv[1])
wanted_models: int = 1 if len(sys.argv) < 3 else int(sys.argv[2])
timeout: float = float(sys.maxsize if len(sys.argv) < 4 else sys.argv[3])
max_possible_ET: int = 2 ** 3 - 1

def z3_abs(x: ArithRef) -> ArithRef:
	return If(x >= 0, x, -x)

# Inputs variables declaration
in3 = Bool('in3')
in2 = Bool('in2')
in1 = Bool('in1')
in0 = Bool('in0')

# Integer function declaration
fe = Function('fe', BoolSort(), BoolSort(), BoolSort(), BoolSort(), IntSort())
# Integer function declaration
fa = Function('fa', BoolSort(), BoolSort(), BoolSort(), BoolSort(), IntSort())
# utility variables
difference = z3_abs(fe(in3, in2, in1, in0) - fa(in3, in2, in1, in0))
error = Int('error')

# Parameters variables declaration
p_o0 = Bool('p_o0')
p_o1 = Bool('p_o1')
p_pr0_i0_s = Bool('p_pr0_i0_s')
p_pr0_i0_l = Bool('p_pr0_i0_l')
p_pr0_i1_s = Bool('p_pr0_i1_s')
p_pr0_i1_l = Bool('p_pr0_i1_l')
p_pr0_i2_s = Bool('p_pr0_i2_s')
p_pr0_i2_l = Bool('p_pr0_i2_l')
p_pr0_i3_s = Bool('p_pr0_i3_s')
p_pr0_i3_l = Bool('p_pr0_i3_l')
p_pr1_i0_s = Bool('p_pr1_i0_s')
p_pr1_i0_l = Bool('p_pr1_i0_l')
p_pr1_i1_s = Bool('p_pr1_i1_s')
p_pr1_i1_l = Bool('p_pr1_i1_l')
p_pr1_i2_s = Bool('p_pr1_i2_s')
p_pr1_i2_l = Bool('p_pr1_i2_l')
p_pr1_i3_s = Bool('p_pr1_i3_s')
p_pr1_i3_l = Bool('p_pr1_i3_l')
p_pr0_o0 = Bool('p_pr0_o0')
p_pr1_o0 = Bool('p_pr1_o0')
p_pr0_o1 = Bool('p_pr0_o1')
p_pr1_o1 = Bool('p_pr1_o1')

# wires functions declaration for exact circuit
e4 = Function('e4', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e5 = Function('e5', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e6 = Function('e6', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e7 = Function('e7', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e8 = Function('e8', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e9 = Function('e9', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e10 = Function('e10', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e11 = Function('e11', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e12 = Function('e12', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e13 = Function('e13', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e14 = Function('e14', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e15 = Function('e15', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e16 = Function('e16', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e17 = Function('e17', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e18 = Function('e18', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e19 = Function('e19', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e20 = Function('e20', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e21 = Function('e21', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e22 = Function('e22', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e23 = Function('e23', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())

# outputs functions declaration for exact circuit
eout0 = Function ('eout0', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
eout1 = Function ('eout1', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())

# exact circuit constraints
exact_circuit = And(
	# wires
	e4(in3,in2,in1,in0) == Not(in3), 
	e5(in3,in2,in1,in0) == Not(in2), 
	e6(in3,in2,in1,in0) == Not(in1), 
	e7(in3,in2,in1,in0) == Not(in0), 
	e8(in3,in2,in1,in0) == And(e4(in3,in2,in1,in0), in1),
	e9(in3,in2,in1,in0) == And(e5(in3,in2,in1,in0), in0),
	e10(in3,in2,in1,in0) == And(in3, e6(in3,in2,in1,in0)),
	e11(in3,in2,in1,in0) == And(in2, e7(in3,in2,in1,in0)),
	e12(in3,in2,in1,in0) == Not(e9(in3,in2,in1,in0)), 
	e13(in3,in2,in1,in0) == Not(e9(in3,in2,in1,in0)), 
	e14(in3,in2,in1,in0) == Not(e11(in3,in2,in1,in0)), 
	e15(in3,in2,in1,in0) == Not(e11(in3,in2,in1,in0)), 
	e16(in3,in2,in1,in0) == And(e12(in3,in2,in1,in0), e10(in3,in2,in1,in0)),
	e17(in3,in2,in1,in0) == And(e14(in3,in2,in1,in0), e8(in3,in2,in1,in0)),
	e18(in3,in2,in1,in0) == And(e13(in3,in2,in1,in0), e15(in3,in2,in1,in0)),
	e19(in3,in2,in1,in0) == Not(e16(in3,in2,in1,in0)), 
	e20(in3,in2,in1,in0) == Not(e17(in3,in2,in1,in0)), 
	e21(in3,in2,in1,in0) == Not(e18(in3,in2,in1,in0)), 
	e22(in3,in2,in1,in0) == And(e20(in3,in2,in1,in0), e19(in3,in2,in1,in0)),
	e23(in3,in2,in1,in0) == Not(e22(in3,in2,in1,in0)), 

	# boolean outputs (from the least significant)
	eout0(in3,in2,in1,in0) == e21(in3,in2,in1,in0),
	eout1(in3,in2,in1,in0) == e23(in3,in2,in1,in0),

	# exact_integer_outputs
	fe(in3,in2,in1,in0) == 
	1 * eout0(in3,in2,in1,in0) +
	2 * eout1(in3,in2,in1,in0),

)
# Approximate circuit
# constraints
approximate_circuit = And(
	fa(in3,in2,in1,in0) == 
	Sum(IntVal(1) * And (p_o0, Or(And(p_pr0_o0,Or(Not(p_pr0_i0_s), p_pr0_i0_l == in0),Or(Not(p_pr0_i1_s), p_pr0_i1_l == in1),Or(Not(p_pr0_i2_s), p_pr0_i2_l == in2),Or(Not(p_pr0_i3_s), p_pr0_i3_l == in3)),And(p_pr1_o0,Or(Not(p_pr1_i0_s), p_pr1_i0_l == in0),Or(Not(p_pr1_i1_s), p_pr1_i1_l == in1),Or(Not(p_pr1_i2_s), p_pr1_i2_l == in2),Or(Not(p_pr1_i3_s), p_pr1_i3_l == in3)))),
		IntVal(2) * And (p_o1, Or(And(p_pr0_o1,Or(Not(p_pr0_i0_s), p_pr0_i0_l == in0),Or(Not(p_pr0_i1_s), p_pr0_i1_l == in1),Or(Not(p_pr0_i2_s), p_pr0_i2_l == in2),Or(Not(p_pr0_i3_s), p_pr0_i3_l == in3)),And(p_pr1_o1,Or(Not(p_pr1_i0_s), p_pr1_i0_l == in0),Or(Not(p_pr1_i1_s), p_pr1_i1_l == in1),Or(Not(p_pr1_i2_s), p_pr1_i2_l == in2),Or(Not(p_pr1_i3_s), p_pr1_i3_l == in3)))))
)
# forall solver
forall_solver = Solver()
forall_solver.add(ForAll(
	[in3,in2,in1,in0],
	And(

		# error constraints
		difference <= ET,

		# circuits
		exact_circuit,
		approximate_circuit,

		# AtMost constraints
		(If(p_pr0_i0_s, 1, 0) + If(p_pr0_i1_s, 1, 0) + If(p_pr0_i2_s, 1, 0) + If(p_pr0_i3_s, 1, 0)) <= 2,
		(If(p_pr1_i0_s, 1, 0) + If(p_pr1_i1_s, 1, 0) + If(p_pr1_i2_s, 1, 0) + If(p_pr1_i3_s, 1, 0)) <= 2,


		# Redundancy constraints
		# remove double no-care
		Implies(p_pr0_i0_l, p_pr0_i0_s), Implies(p_pr0_i1_l, p_pr0_i1_s), Implies(p_pr0_i2_l, p_pr0_i2_s), Implies(p_pr0_i3_l, p_pr0_i3_s), Implies(p_pr1_i0_l, p_pr1_i0_s), Implies(p_pr1_i1_l, p_pr1_i1_s), Implies(p_pr1_i2_l, p_pr1_i2_s), Implies(p_pr1_i3_l, p_pr1_i3_s), 

		# remove constant 0 parameters permutations
		Implies(Not(p_o0), Not(Or(p_o0_pr0_i0_s, p_o0_pr0_i0_l, p_o0_pr0_i1_s, p_o0_pr0_i1_l, p_o0_pr0_i2_s, p_o0_pr0_i2_l, p_o0_pr0_i3_s, p_o0_pr0_i3_l, p_o0_pr1_i0_s, p_o0_pr1_i0_l, p_o0_pr1_i1_s, p_o0_pr1_i1_l, p_o0_pr1_i2_s, p_o0_pr1_i2_l, p_o0_pr1_i3_s, p_o0_pr1_i3_l))),
		Implies(Not(p_o1), Not(Or(p_o1_pr0_i0_s, p_o1_pr0_i0_l, p_o1_pr0_i1_s, p_o1_pr0_i1_l, p_o1_pr0_i2_s, p_o1_pr0_i2_l, p_o1_pr0_i3_s, p_o1_pr0_i3_l, p_o1_pr1_i0_s, p_o1_pr1_i0_l, p_o1_pr1_i1_s, p_o1_pr1_i1_l, p_o1_pr1_i2_s, p_o1_pr1_i2_l, p_o1_pr1_i3_s, p_o1_pr1_i3_l))),

		# Implies(a, b) => if a is true then b is true
		# 				if it rains, I will carry an umbrella (if p then q)
		# 				if I dont have an umbrella on me, its not raining (if ~q then ~p)

		# if p_o is disabled then everything is forcefully set to false
		# in the previous version without sharing this "everything" was _s and _l parameters

		# what is this "everything" in the logic sharing template?
		# answer:
		# 		"""
		# 		Implies(Not(p_o0), Not(Or(p_pr0_o0, p_pr1_o0, ..., p_prk_o0)))
		# 		Implies(Not(p_o1), Not(Or(p_pr0_o1, p_pr1_o1, ..., p_prk_o1)))
		# 			...
		# 		Implies(Not(p_om), Not(Or(p_pr0_om, p_pr1_om, ..., p_prk_om)))
		# 		"""


		# set order of trees
		(IntVal(1) * p_o0_pr0_i0_s + IntVal(2) * p_o0_pr0_i0_l + IntVal(4) * p_o0_pr0_i1_s + IntVal(8) * p_o0_pr0_i1_l + IntVal(16) * p_o0_pr0_i2_s + IntVal(32) * p_o0_pr0_i2_l + IntVal(64) * p_o0_pr0_i3_s + IntVal(128) * p_o0_pr0_i3_l) >= (IntVal(1) * p_o0_pr1_i0_s + IntVal(2) * p_o0_pr1_i0_l + IntVal(4) * p_o0_pr1_i1_s + IntVal(8) * p_o0_pr1_i1_l + IntVal(16) * p_o0_pr1_i2_s + IntVal(32) * p_o0_pr1_i2_l + IntVal(64) * p_o0_pr1_i3_s + IntVal(128) * p_o0_pr1_i3_l),
		(IntVal(1) * p_o1_pr0_i0_s + IntVal(2) * p_o1_pr0_i0_l + IntVal(4) * p_o1_pr0_i1_s + IntVal(8) * p_o1_pr0_i1_l + IntVal(16) * p_o1_pr0_i2_s + IntVal(32) * p_o1_pr0_i2_l + IntVal(64) * p_o1_pr0_i3_s + IntVal(128) * p_o1_pr0_i3_l) >= (IntVal(1) * p_o1_pr1_i0_s + IntVal(2) * p_o1_pr1_i0_l + IntVal(4) * p_o1_pr1_i1_s + IntVal(8) * p_o1_pr1_i1_l + IntVal(16) * p_o1_pr1_i2_s + IntVal(32) * p_o1_pr1_i2_l + IntVal(64) * p_o1_pr1_i3_s + IntVal(128) * p_o1_pr1_i3_l),

	)
))

verification_solver = Solver()
verification_solver.add(
	error == difference,
	exact_circuit,
	approximate_circuit,
)
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
			# add constraint
			verification_solver.add(difference > verification_ET)
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
	data_object = {
		'result': str(result),
		'total_time': time_total,
		'attempts': attempts,
		'attempts_times': [list(map(lambda tup: [*tup], attempts_times))]
	}
	if result == sat:
		data_object['model'] = dict(map(lambda item: (str(item[0]), is_true(item[1])),
			sorted(parameters_constraints,
			key=key_function)))
	found_data.append(data_object)
	if result != sat:
		break
print(json.dumps(found_data, separators=(",", ":"),))

with open('output/json/abs_diff_i4_o3_lpp2_ppo2_SOP1.json', 'w') as ofile:
	ofile.write(json.dumps(found_data, separators=(",", ":"), indent=4))

