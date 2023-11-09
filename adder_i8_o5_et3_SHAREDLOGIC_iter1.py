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
in0 = Bool('in0')
in1 = Bool('in1')
in2 = Bool('in2')
in3 = Bool('in3')
in4 = Bool('in4')
in5 = Bool('in5')
in6 = Bool('in6')
in7 = Bool('in7')

# Integer function declaration
fe = Function('fe', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), IntSort())
# Integer function declaration
fa = Function('fa', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), IntSort())
# utility variables
difference = z3_abs(fe(in0, in1, in2, in3, in4, in5, in6, in7) - fa(in0, in1, in2, in3, in4, in5, in6, in7))
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
p_pr0_i4_s = Bool('p_pr0_i4_s')
p_pr0_i4_l = Bool('p_pr0_i4_l')
p_pr0_i5_s = Bool('p_pr0_i5_s')
p_pr0_i5_l = Bool('p_pr0_i5_l')
p_pr0_o0 = Bool('p_pr0_o0')
p_pr0_o1 = Bool('p_pr0_o1')

# wires functions declaration for exact circuit
e8 = Function('e8', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e9 = Function('e9', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e10 = Function('e10', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e11 = Function('e11', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e12 = Function('e12', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e13 = Function('e13', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e14 = Function('e14', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e15 = Function('e15', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e16 = Function('e16', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e17 = Function('e17', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e18 = Function('e18', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e19 = Function('e19', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e20 = Function('e20', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e21 = Function('e21', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e22 = Function('e22', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e23 = Function('e23', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e24 = Function('e24', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e25 = Function('e25', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e26 = Function('e26', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e27 = Function('e27', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e28 = Function('e28', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e29 = Function('e29', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e30 = Function('e30', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e31 = Function('e31', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e32 = Function('e32', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e33 = Function('e33', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e34 = Function('e34', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e35 = Function('e35', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e36 = Function('e36', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e37 = Function('e37', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e38 = Function('e38', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e39 = Function('e39', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e40 = Function('e40', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e41 = Function('e41', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e42 = Function('e42', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e43 = Function('e43', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e44 = Function('e44', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e45 = Function('e45', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e46 = Function('e46', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e47 = Function('e47', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e48 = Function('e48', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e49 = Function('e49', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e50 = Function('e50', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e51 = Function('e51', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e52 = Function('e52', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e53 = Function('e53', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e54 = Function('e54', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e55 = Function('e55', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e56 = Function('e56', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e57 = Function('e57', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e58 = Function('e58', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e59 = Function('e59', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e60 = Function('e60', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e61 = Function('e61', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e62 = Function('e62', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e63 = Function('e63', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e64 = Function('e64', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e65 = Function('e65', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e66 = Function('e66', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e67 = Function('e67', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e68 = Function('e68', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e69 = Function('e69', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e70 = Function('e70', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e71 = Function('e71', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e72 = Function('e72', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
e73 = Function('e73', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())

# wires functions declaration for approximate circuit
a8 = Function('a8', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a9 = Function('a9', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a10 = Function('a10', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a11 = Function('a11', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a12 = Function('a12', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a13 = Function('a13', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a14 = Function('a14', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a15 = Function('a15', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a16 = Function('a16', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a17 = Function('a17', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a18 = Function('a18', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a19 = Function('a19', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a20 = Function('a20', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a21 = Function('a21', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a22 = Function('a22', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a23 = Function('a23', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a24 = Function('a24', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a25 = Function('a25', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a26 = Function('a26', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a27 = Function('a27', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a28 = Function('a28', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a29 = Function('a29', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a30 = Function('a30', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a31 = Function('a31', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a32 = Function('a32', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a33 = Function('a33', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a34 = Function('a34', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a35 = Function('a35', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a36 = Function('a36', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a37 = Function('a37', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a38 = Function('a38', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a39 = Function('a39', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a40 = Function('a40', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a41 = Function('a41', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a42 = Function('a42', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a43 = Function('a43', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a44 = Function('a44', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a45 = Function('a45', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a46 = Function('a46', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a47 = Function('a47', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a48 = Function('a48', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a49 = Function('a49', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a50 = Function('a50', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a51 = Function('a51', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a52 = Function('a52', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a53 = Function('a53', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a54 = Function('a54', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a55 = Function('a55', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a56 = Function('a56', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a57 = Function('a57', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a58 = Function('a58', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a59 = Function('a59', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a60 = Function('a60', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a61 = Function('a61', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a62 = Function('a62', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a63 = Function('a63', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a64 = Function('a64', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a65 = Function('a65', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a66 = Function('a66', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a67 = Function('a67', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a68 = Function('a68', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a69 = Function('a69', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a70 = Function('a70', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a71 = Function('a71', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a72 = Function('a72', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
a73 = Function('a73', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())

# outputs functions declaration for exact circuit
eout0 = Function ('eout0', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
eout1 = Function ('eout1', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
eout2 = Function ('eout2', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
eout3 = Function ('eout3', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
eout4 = Function ('eout4', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())

# outputs functions declaration for approximate circuit
aout0 = Function ('aout0', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
aout1 = Function ('aout1', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
aout2 = Function ('aout2', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
aout3 = Function ('aout3', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())
aout4 = Function ('aout4', BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort(), BoolSort())

# exact circuit constraints
exact_circuit = And(
	# wires
	e8(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in7), 
	e9(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in6), 
	e10(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in5), 
	e11(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in4), 
	e12(in0,in1,in2,in3,in4,in5,in6,in7) == And(in7, in3),
	e13(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in3), 
	e14(in0,in1,in2,in3,in4,in5,in6,in7) == And(in6, in2),
	e15(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in2), 
	e16(in0,in1,in2,in3,in4,in5,in6,in7) == And(in5, in1),
	e17(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in1), 
	e18(in0,in1,in2,in3,in4,in5,in6,in7) == And(in4, in0),
	e19(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in0), 
	e20(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e12(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e21(in0,in1,in2,in3,in4,in5,in6,in7) == And(e8(in0,in1,in2,in3,in4,in5,in6,in7), e13(in0,in1,in2,in3,in4,in5,in6,in7)),
	e22(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e14(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e23(in0,in1,in2,in3,in4,in5,in6,in7) == And(e9(in0,in1,in2,in3,in4,in5,in6,in7), e15(in0,in1,in2,in3,in4,in5,in6,in7)),
	e24(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e16(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e25(in0,in1,in2,in3,in4,in5,in6,in7) == And(e10(in0,in1,in2,in3,in4,in5,in6,in7), e17(in0,in1,in2,in3,in4,in5,in6,in7)),
	e26(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e18(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e27(in0,in1,in2,in3,in4,in5,in6,in7) == And(e11(in0,in1,in2,in3,in4,in5,in6,in7), e19(in0,in1,in2,in3,in4,in5,in6,in7)),
	e28(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e21(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e29(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e23(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e30(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e25(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e31(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e26(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e32(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e27(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e33(in0,in1,in2,in3,in4,in5,in6,in7) == And(e28(in0,in1,in2,in3,in4,in5,in6,in7), e20(in0,in1,in2,in3,in4,in5,in6,in7)),
	e34(in0,in1,in2,in3,in4,in5,in6,in7) == And(e29(in0,in1,in2,in3,in4,in5,in6,in7), e22(in0,in1,in2,in3,in4,in5,in6,in7)),
	e35(in0,in1,in2,in3,in4,in5,in6,in7) == And(e30(in0,in1,in2,in3,in4,in5,in6,in7), e24(in0,in1,in2,in3,in4,in5,in6,in7)),
	e36(in0,in1,in2,in3,in4,in5,in6,in7) == And(e32(in0,in1,in2,in3,in4,in5,in6,in7), e26(in0,in1,in2,in3,in4,in5,in6,in7)),
	e37(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e33(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e38(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e34(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e39(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e35(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e40(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e36(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e41(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e37(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e42(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e38(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e43(in0,in1,in2,in3,in4,in5,in6,in7) == And(e39(in0,in1,in2,in3,in4,in5,in6,in7), e26(in0,in1,in2,in3,in4,in5,in6,in7)),
	e44(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e39(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e45(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e40(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e46(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e43(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e47(in0,in1,in2,in3,in4,in5,in6,in7) == And(e44(in0,in1,in2,in3,in4,in5,in6,in7), e31(in0,in1,in2,in3,in4,in5,in6,in7)),
	e48(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e47(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e49(in0,in1,in2,in3,in4,in5,in6,in7) == And(e46(in0,in1,in2,in3,in4,in5,in6,in7), e48(in0,in1,in2,in3,in4,in5,in6,in7)),
	e50(in0,in1,in2,in3,in4,in5,in6,in7) == And(e48(in0,in1,in2,in3,in4,in5,in6,in7), e24(in0,in1,in2,in3,in4,in5,in6,in7)),
	e51(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e49(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e52(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e50(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e53(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e51(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e54(in0,in1,in2,in3,in4,in5,in6,in7) == And(e42(in0,in1,in2,in3,in4,in5,in6,in7), e52(in0,in1,in2,in3,in4,in5,in6,in7)),
	e55(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e52(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e56(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e54(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e57(in0,in1,in2,in3,in4,in5,in6,in7) == And(e55(in0,in1,in2,in3,in4,in5,in6,in7), e38(in0,in1,in2,in3,in4,in5,in6,in7)),
	e58(in0,in1,in2,in3,in4,in5,in6,in7) == And(e56(in0,in1,in2,in3,in4,in5,in6,in7), e22(in0,in1,in2,in3,in4,in5,in6,in7)),
	e59(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e57(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e60(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e58(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e61(in0,in1,in2,in3,in4,in5,in6,in7) == And(e59(in0,in1,in2,in3,in4,in5,in6,in7), e56(in0,in1,in2,in3,in4,in5,in6,in7)),
	e62(in0,in1,in2,in3,in4,in5,in6,in7) == And(e41(in0,in1,in2,in3,in4,in5,in6,in7), e60(in0,in1,in2,in3,in4,in5,in6,in7)),
	e63(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e60(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e64(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e61(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e65(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e62(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e66(in0,in1,in2,in3,in4,in5,in6,in7) == And(e63(in0,in1,in2,in3,in4,in5,in6,in7), e37(in0,in1,in2,in3,in4,in5,in6,in7)),
	e67(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e64(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e68(in0,in1,in2,in3,in4,in5,in6,in7) == And(e65(in0,in1,in2,in3,in4,in5,in6,in7), e20(in0,in1,in2,in3,in4,in5,in6,in7)),
	e69(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e66(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e70(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e68(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e71(in0,in1,in2,in3,in4,in5,in6,in7) == And(e69(in0,in1,in2,in3,in4,in5,in6,in7), e65(in0,in1,in2,in3,in4,in5,in6,in7)),
	e72(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e71(in0,in1,in2,in3,in4,in5,in6,in7)), 
	e73(in0,in1,in2,in3,in4,in5,in6,in7) == Not(e72(in0,in1,in2,in3,in4,in5,in6,in7)), 

	# boolean outputs (from the least significant)
	eout0(in0,in1,in2,in3,in4,in5,in6,in7) == e45(in0,in1,in2,in3,in4,in5,in6,in7),
	eout1(in0,in1,in2,in3,in4,in5,in6,in7) == e53(in0,in1,in2,in3,in4,in5,in6,in7),
	eout2(in0,in1,in2,in3,in4,in5,in6,in7) == e67(in0,in1,in2,in3,in4,in5,in6,in7),
	eout3(in0,in1,in2,in3,in4,in5,in6,in7) == e73(in0,in1,in2,in3,in4,in5,in6,in7),
	eout4(in0,in1,in2,in3,in4,in5,in6,in7) == e70(in0,in1,in2,in3,in4,in5,in6,in7),

	# exact_integer_outputs
	fe(in0,in1,in2,in3,in4,in5,in6,in7) == 
	1 * eout0(in0,in1,in2,in3,in4,in5,in6,in7) +
	2 * eout1(in0,in1,in2,in3,in4,in5,in6,in7) +
	4 * eout2(in0,in1,in2,in3,in4,in5,in6,in7) +
	8 * eout3(in0,in1,in2,in3,in4,in5,in6,in7) +
	16 * eout4(in0,in1,in2,in3,in4,in5,in6,in7),

)
# approximate circuit constraints
approximate_circuit = And(
	# wires
	a8(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in7), 
	a9(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in6), 
	a12(in0,in1,in2,in3,in4,in5,in6,in7) == And(in7, in3),
	a13(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in3), 
	a14(in0,in1,in2,in3,in4,in5,in6,in7) == And(in6, in2),
	a15(in0,in1,in2,in3,in4,in5,in6,in7) == Not(in2), 
	a16(in0,in1,in2,in3,in4,in5,in6,in7) == And(in5, in1),
	a18(in0,in1,in2,in3,in4,in5,in6,in7) == And(in4, in0),
	a20(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a12(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a21(in0,in1,in2,in3,in4,in5,in6,in7) == And(a8(in0,in1,in2,in3,in4,in5,in6,in7), a13(in0,in1,in2,in3,in4,in5,in6,in7)),
	a22(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a14(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a23(in0,in1,in2,in3,in4,in5,in6,in7) == And(a9(in0,in1,in2,in3,in4,in5,in6,in7), a15(in0,in1,in2,in3,in4,in5,in6,in7)),
	a24(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a16(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a26(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a18(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a28(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a21(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a29(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a23(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a31(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a26(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a33(in0,in1,in2,in3,in4,in5,in6,in7) == And(a20(in0,in1,in2,in3,in4,in5,in6,in7), a28(in0,in1,in2,in3,in4,in5,in6,in7)),
	a34(in0,in1,in2,in3,in4,in5,in6,in7) == And(a22(in0,in1,in2,in3,in4,in5,in6,in7), a29(in0,in1,in2,in3,in4,in5,in6,in7)),
	a37(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a33(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a38(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a34(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a39(in0,in1,in4,in5,a24(in0, in1, in2, in3, in4, in5, in6, in7),a26(in0, in1, in2, in3, in4, in5, in6, in7)) == And (p_o0, Or(And(p_pr0_o0,Or(Not(p_pr0_i0_s), p_pr0_i0_l == in0),Or(Not(p_pr0_i1_s), p_pr0_i1_l == in1),Or(Not(p_pr0_i2_s), p_pr0_i2_l == in4),Or(Not(p_pr0_i3_s), p_pr0_i3_l == in5),Or(Not(p_pr0_i4_s), p_pr0_i4_l == a24(in0, in1, in2, in3, in4, in5, in6, in7)),Or(Not(p_pr0_i5_s), p_pr0_i5_l == a26(in0, in1, in2, in3, in4, in5, in6, in7))))),
	a41(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a37(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a42(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a38(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a43(in0,in1,in2,in3,in4,in5,in6,in7) == And(a26(in0,in1,in2,in3,in4,in5,in6,in7), a39(in0,in1,in4,in5,a24(in0, in1, in2, in3, in4, in5, in6, in7),a26(in0, in1, in2, in3, in4, in5, in6, in7))),
	a44(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a39(in0,in1,in4,in5,a24(in0, in1, in2, in3, in4, in5, in6, in7),a26(in0, in1, in2, in3, in4, in5, in6, in7))), 
	a45(in0,in1,in4,in5,a24(in0, in1, in2, in3, in4, in5, in6, in7),a26(in0, in1, in2, in3, in4, in5, in6, in7)) == And (p_o1, Or(And(p_pr0_o1,Or(Not(p_pr0_i0_s), p_pr0_i0_l == in0),Or(Not(p_pr0_i1_s), p_pr0_i1_l == in1),Or(Not(p_pr0_i2_s), p_pr0_i2_l == in4),Or(Not(p_pr0_i3_s), p_pr0_i3_l == in5),Or(Not(p_pr0_i4_s), p_pr0_i4_l == a24(in0, in1, in2, in3, in4, in5, in6, in7)),Or(Not(p_pr0_i5_s), p_pr0_i5_l == a26(in0, in1, in2, in3, in4, in5, in6, in7))))),
	a46(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a43(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a47(in0,in1,in2,in3,in4,in5,in6,in7) == And(a31(in0,in1,in2,in3,in4,in5,in6,in7), a44(in0,in1,in2,in3,in4,in5,in6,in7)),
	a48(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a47(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a49(in0,in1,in2,in3,in4,in5,in6,in7) == And(a46(in0,in1,in2,in3,in4,in5,in6,in7), a48(in0,in1,in2,in3,in4,in5,in6,in7)),
	a50(in0,in1,in2,in3,in4,in5,in6,in7) == And(a24(in0,in1,in2,in3,in4,in5,in6,in7), a48(in0,in1,in2,in3,in4,in5,in6,in7)),
	a51(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a49(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a52(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a50(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a53(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a51(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a54(in0,in1,in2,in3,in4,in5,in6,in7) == And(a42(in0,in1,in2,in3,in4,in5,in6,in7), a52(in0,in1,in2,in3,in4,in5,in6,in7)),
	a55(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a52(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a56(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a54(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a57(in0,in1,in2,in3,in4,in5,in6,in7) == And(a38(in0,in1,in2,in3,in4,in5,in6,in7), a55(in0,in1,in2,in3,in4,in5,in6,in7)),
	a58(in0,in1,in2,in3,in4,in5,in6,in7) == And(a22(in0,in1,in2,in3,in4,in5,in6,in7), a56(in0,in1,in2,in3,in4,in5,in6,in7)),
	a59(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a57(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a60(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a58(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a61(in0,in1,in2,in3,in4,in5,in6,in7) == And(a56(in0,in1,in2,in3,in4,in5,in6,in7), a59(in0,in1,in2,in3,in4,in5,in6,in7)),
	a62(in0,in1,in2,in3,in4,in5,in6,in7) == And(a41(in0,in1,in2,in3,in4,in5,in6,in7), a60(in0,in1,in2,in3,in4,in5,in6,in7)),
	a63(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a60(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a64(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a61(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a65(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a62(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a66(in0,in1,in2,in3,in4,in5,in6,in7) == And(a37(in0,in1,in2,in3,in4,in5,in6,in7), a63(in0,in1,in2,in3,in4,in5,in6,in7)),
	a67(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a64(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a68(in0,in1,in2,in3,in4,in5,in6,in7) == And(a20(in0,in1,in2,in3,in4,in5,in6,in7), a65(in0,in1,in2,in3,in4,in5,in6,in7)),
	a69(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a66(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a70(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a68(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a71(in0,in1,in2,in3,in4,in5,in6,in7) == And(a65(in0,in1,in2,in3,in4,in5,in6,in7), a69(in0,in1,in2,in3,in4,in5,in6,in7)),
	a72(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a71(in0,in1,in2,in3,in4,in5,in6,in7)), 
	a73(in0,in1,in2,in3,in4,in5,in6,in7) == Not(a72(in0,in1,in2,in3,in4,in5,in6,in7)), 

	# boolean outputs (from the least significant)
	aout0(in0,in1,in2,in3,in4,in5,in6,in7) == a45(in0,in1,in4,in5,a24(in0, in1, in2, in3, in4, in5, in6, in7),a26(in0, in1, in2, in3, in4, in5, in6, in7)),
	aout1(in0,in1,in2,in3,in4,in5,in6,in7) == a53(in0,in1,in2,in3,in4,in5,in6,in7),
	aout2(in0,in1,in2,in3,in4,in5,in6,in7) == a67(in0,in1,in2,in3,in4,in5,in6,in7),
	aout3(in0,in1,in2,in3,in4,in5,in6,in7) == a73(in0,in1,in2,in3,in4,in5,in6,in7),
	aout4(in0,in1,in2,in3,in4,in5,in6,in7) == a70(in0,in1,in2,in3,in4,in5,in6,in7),

	# approximate_integer_outputs
	fa(in0,in1,in2,in3,in4,in5,in6,in7) == 
	1 * aout0(in0,in1,in2,in3,in4,in5,in6,in7) +
	2 * aout1(in0,in1,in2,in3,in4,in5,in6,in7) +
	4 * aout2(in0,in1,in2,in3,in4,in5,in6,in7) +
	8 * aout3(in0,in1,in2,in3,in4,in5,in6,in7) +
	16 * aout4(in0,in1,in2,in3,in4,in5,in6,in7),

)
# forall solver
forall_solver = Solver()
forall_solver.add(ForAll(
	[in0,in1,in2,in3,in4,in5,in6,in7],
	And(

		# error constraints
		difference <= ET,

		# circuits
		exact_circuit,
		approximate_circuit,

		# AtMost constraints
		(If(p_pr0_i0_s, 1, 0) + If(p_pr0_i1_s, 1, 0) + If(p_pr0_i2_s, 1, 0) + If(p_pr0_i3_s, 1, 0) + If(p_pr0_i4_s, 1, 0) + If(p_pr0_i5_s, 1, 0)) <= 0,


		# Redundancy constraints
		# remove double no-care
		Implies(p_pr0_i0_l, p_pr0_i0_s), Implies(p_pr0_i1_l, p_pr0_i1_s), Implies(p_pr0_i2_l, p_pr0_i2_s), Implies(p_pr0_i3_l, p_pr0_i3_s), Implies(p_pr0_i4_l, p_pr0_i4_s), Implies(p_pr0_i5_l, p_pr0_i5_s), 

		# remove constant 0 parameters permutations
		Implies(Not(p_o0), Not(Or(p_pr0_o0))), 
		Implies(Not(p_o1), Not(Or(p_pr0_o1))), 

		# remove unused products
		Implies(Not(Or(p_pr0_o0, p_pr0_o1)), Not(Or(p_pr0_i0_s, p_pr0_i0_l, p_pr0_i1_s, p_pr0_i1_l, p_pr0_i2_s, p_pr0_i2_l, p_pr0_i3_s, p_pr0_i3_l, p_pr0_i4_s, p_pr0_i4_l, p_pr0_i5_s, p_pr0_i5_l))), 
		# set order of pits
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
		pr_id = extract_info(r'_pr(\d+)', p, int, 0)
		i_id = extract_info(r'_i(\d+)', p, int, 0)
		typ = extract_info(r'_(l|s)', p, {'s': 1, 'l': 2}.get, 0)
		if o_id < 0:
			return (pr_id * 1000 + i_id * 10 + typ)
		return (o_id * 100000
				+ pr_id * 1000
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

with open('output/json/adder_i8_o5_et3_SHAREDLOGIC_iter1.json', 'w') as ofile:
	ofile.write(json.dumps(found_data, separators=(",", ":"), indent=4))

