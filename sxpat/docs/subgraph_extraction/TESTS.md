# Mode 1: find_subgraph
Tightest Error Space - 4
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=1 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=4 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8 
Iteration 3: #ofNodes=8 
Iteration 4: #ofNodes=8
+ Result: Approximate circuit found!

REFACTORED CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=8
Iteration 4: #ofNodes=8
+ Result: Approximate circuit found!

Strict Error Space - 8
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=1 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=8 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8 
Iteration 3: #ofNodes=8 
Iteration 4: #ofNodes=8
Iteration 5: #ofNodes=8
Iteration 6: #ofNodes=8
Iteration 7: #ofNodes=8 
Iteration 8: #ofNodes=8 
Iteration 9: #ofNodes=8 
Iteration 10: #ofNodes=8 
+ Result: "The error space is exhausted!"

REFACTORED CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=8
Iteration 4: #ofNodes=8
Iteration 5: #ofNodes=8
Iteration 6: #ofNodes=8 
Iteration 7: #ofNodes=8 
Iteration 8: #ofNodes=8 
Iteration 9: #ofNodes=8
+ Result: "The error space is exhausted!"

Baseline Error Space - 16
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=1 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:
iteration 1: #ofNodes=8
iteration 2: #ofNodes=8 
iteration 3: #ofNodes=8 
iteration 4: #ofNodes=8
iteration 5: #ofNodes=8
iteration 6: #ofNodes=8
iteration 7: #ofNodes=8
iteration 8: #ofNodes=8
iteration 9: #ofNodes=8
iteration 10: #ofNodes=8
+ Result: Area zero found! Terminated.

REFACTORED CODE:
iteration 1: #ofNodes=8
iteration 2: #ofNodes=8
iteration 3: #ofNodes=8
iteration 4: #ofNodes=8 
iteration 5: #ofNodes=8
iteration 6: #ofNodes=8
iteration 7: #ofNodes=8
iteration 8: #ofNodes=8 
iteration 9: #ofNodes=8 
iteration 10: #ofNodes=8 
+ Result: "The error space is exhausted!"

Wide Error Space - 32
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=1 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=32 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=8
Iteration 4: #ofNodes=8
Iteration 5: #ofNodes=8
Iteration 6: #ofNodes=7
Iteration 7: #ofNodes=1
+ Result: "Area zero found! Terminated."

REFACTORED CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=14
Iteration 4: #ofNodes=8
Iteration 5: #ofNodes=7
+ Result: "Area zero found! Terminated."

Massive Error Space - 64
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=1 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=64 --imax=2 --omax=8 

ORIGINAL CODE:
teration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=8
Iteration 4: #ofNodes=7
Iteration 5: #ofNodes=7
Result: "Area zero found! Terminated."

REFACTORED CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=8 
Iteration 4: #ofNodes=8
Iteration 5: #ofNodes=8
Iteration 6: #ofNodes=7
+ Result: "Area zero found! Terminated."

#====================================================================================================

# Mode 2: find_subgraph_sensitivity
Tightest Error Space - 4
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=2 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=4 --imax=2 --omax=8 --min-subgraph-size=1 

ORIGINAL CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=1
Iteration 4: #ofNodes=1
Iteration 5: #ofNodes=1
Iteration 6: #ofNodes=1
Iteration 7: #ofNodes=1
Iteration 8: #ofNodes=1
Iteration 9: #ofNodes=1
Iteration 10: #ofNodes=1
Iteration 11: #ofNodes=1
Result: "The error space is exhausted!"

REFACTORED CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=1
Iteration 4: #ofNodes=1
Iteration 5: #ofNodes=1
Iteration 6: #ofNodes=1
Iteration 7: #ofNodes=1
Iteration 8: #ofNodes=1 
+ Result: "The error space is exhausted!"

Strict Error Space - 8
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=2 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=8 --imax=2 --omax=8 --min-subgraph-size=1 

ORIGINAL CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=1
Iteration 4: #ofNodes=1
Iteration 5: #ofNodes=1
Iteration 6: #ofNodes=1
Iteration 7: #ofNodes=1
Iteration 8: #ofNodes=1
Iteration 9: #ofNodes=1
Iteration 10: #ofNodes=1
Iteration 11: #ofNodes=1
Iteration 12: #ofNodes=1
Iteration 13: #ofNodes=1
Iteration 14: #ofNodes=1
Iteration 15: #ofNodes=3
Iteration 16: #ofNodes=4
Iteration 17: #ofNodes=4
Result: "The error space is exhausted!"

REFACTORED CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=1
Iteration 4: #ofNodes=1
Iteration 5: #ofNodes=1
Iteration 6: #ofNodes=1
Iteration 7: #ofNodes=1
Iteration 8: #ofNodes=1 
Iteration 9: #ofNodes=1
Iteration 10: #ofNodes=1
Iteration 11: #ofNodes=1
Iteration 12: #ofNodes=4
Iteration 13: #ofNodes=1
Iteration 14: #ofNodes=3
+ Result: Approximate circuit found!

Baseline Error Space - 16
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=2 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8 --min-subgraph-size=1

ORIGINAL CODE:
iteration 1: #ofNodes=4
iteration 2: #ofNodes=2
iteration 3: #ofNodes=1
iteration 4: #ofNodes=1
iteration 5: #ofNodes=1
iteration 6: #ofNodes=1
iteration 7: #ofNodes=1
iteration 8: #ofNodes=1
iteration 9: #ofNodes=4
iteration 10: #ofNodes=4
iteration 11: #ofNodes=4
iteration 12: #ofNodes=8
iteration 13: #ofNodes=4
iteration 14: #ofNodes=4
iteration 15: #ofNodes=4
iteration 16: #ofNodes=1
iteration 17: #ofNodes=1 
iteration 18: #ofNodes=1 
+ Result: "The error space is exhausted!"

REFACTORED CODE:
iteration 1: #ofNodes=4
iteration 2: #ofNodes=2
iteration 3: #ofNodes=1
iteration 4: #ofNodes=1
iteration 5: #ofNodes=1 
iteration 6: #ofNodes=3
iteration 7: #ofNodes=4
iteration 8: #ofNodes=4
iteration 9: #ofNodes=4
iteration 10: #ofNodes=4
iteration 11: #ofNodes=3
iteration 12: #ofNodes=3
iteration 13: #ofNodes=3
iteration 14: #ofNodes=2
iteration 15: #ofNodes=4
iteration 16: #ofNodes=2 
+ Results: "Area zero found! Terminated."

Wide Error Space - 32
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=2 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=32 --imax=2 --omax=8 --min-subgraph-size=1 

ORIGINAL CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=1
Iteration 4: #ofNodes=4
Iteration 5: #ofNodes=2
Iteration 6: #ofNodes=4
Iteration 7: #ofNodes=3
Iteration 8: #ofNodes=4
Iteration 9: #ofNodes=3
Iteration 10: #ofNodes=1
Result: "Area zero found! Terminated."

REFACTORED CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=1
Iteration 4: #ofNodes=4
Iteration 5: #ofNodes=2
Iteration 6: #ofNodes=4
Iteration 7: #ofNodes=3
Iteration 8: #ofNodes=3
Iteration 9: #ofNodes=1
Iteration 10: #ofNodes=4
Iteration 11: #ofNodes=2
Iteration 12: #ofNodes=4
+ Result: "Area zero found! Terminated."

Massive Error Space - 64
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=2 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=64 --imax=2 --omax=8 --min-subgraph-size=1

ORIGINAL CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=3
Iteration 4: #ofNodes=4
Iteration 5: #ofNodes=4
Iteration 6: #ofNodes=4
Iteration 7: #ofNodes=1
Iteration 8: #ofNodes=1
Result: "Area zero found! Terminated."

REFACTORED CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=3
Iteration 4: #ofNodes=4
Iteration 5: #ofNodes=4
Iteration 6: #ofNodes=4
Iteration 7: #ofNodes=4
Iteration 8: #ofNodes=1
+ Result: "Area zero found! Terminated."

#====================================================================================================

# Mode 3: find_subgraph_sensitivity_no_io_constraints
Tightest Error Space - 4
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=3 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=4 --imax=2 --omax=8 --min-subgraph-size=1 

ORIGINAL CODE:
Iteration 1: #ofNodes=5
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=1
Iteration 4: #ofNodes=1
Iteration 5: #ofNodes=1
Iteration 6: #ofNodes=1
Result: "The error space is exhausted!"

REFACTORED CODE:
Iteration 1: #ofNodes=5
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=1
Iteration 4: #ofNodes=1 
Iteration 5: #ofNodes=1 
+ Result: "The error space is exhausted!"

Strict Error Space - 8
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=3 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=8 --imax=2 --omax=8 --min-subgraph-size=1 

ORIGINAL CODE:
Iteration 1: #ofNodes=5
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=1
Iteration 4: #ofNodes=1
Iteration 5: #ofNodes=1
Iteration 6: #ofNodes=1
Iteration 7: #ofNodes=1
Iteration 8: #ofNodes=1
Iteration 9: #ofNodes=1
Iteration 10: #ofNodes=5
Iteration 11: #ofNodes=11
Iteration 12: #ofNodes=4
Result: "The error space is exhausted!"

REFACTORED CODE:
Iteration 1: #ofNodes=5
Iteration 2: #ofNodes=1
Iteration 3: #ofNodes=1
Iteration 4: #ofNodes=1 
Iteration 5: #ofNodes=1 
Iteration 6: #ofNodes=1 
Iteration 7: #ofNodes=1 
Iteration 8: #ofNodes=1 
Iteration 9: #ofNodes=5
Iteration 10: #ofNodes=11
Iteration 11: #ofNodes=5
+ Result: "The error space is exhausted!"

Baseline Error Space - 16
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=3 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8 --min-subgraph-size=1

ORIGINAL CODE:
iteration 1: #ofNodes=5
iteration 2: #ofNodes=1
iteration 3: #ofNodes=1 
iteration 4: #ofNodes=1 
iteration 5: #ofNodes=5
iteration 6: #ofNodes=2
iteration 7: #ofNodes=5
iteration 8: #ofNodes=2
iteration 9: #ofNodes=8
iteration 10: #ofNodes=8
iteration 11: #ofNodes=8 
iteration 12: #ofNodes=8 
iteration 13: #ofNodes=8 
+ Result: "The error space is exhausted!"

REFACTORED CODE:
iteration 1: #ofNodes=5
iteration 2: #ofNodes=1
iteration 3: #ofNodes=1 
iteration 4: #ofNodes=1 
iteration 5: #ofNodes=5
iteration 6: #ofNodes=11
iteration 7: #ofNodes=5
iteration 8: #ofNodes=5
iteration 9: #ofNodes=6
iteration 10: #ofNodes=6
iteration 11: #ofNodes=6 
iteration 12: #ofNodes=6 
iteration 13: #ofNodes=11 
+ Result: "Area zero found! Terminated."

Wide Error Space - 32
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=3 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=32 --imax=2 --omax=8 --min-subgraph-size=1 

ORIGINAL CODE:
Iteration 1: #ofNodes=5
Iteration 2: #ofNodes=2
Iteration 3: #ofNodes=2
Iteration 4: #ofNodes=5
Iteration 5: #ofNodes=2
Iteration 6: #ofNodes=5
Iteration 7: #ofNodes=1
Iteration 8: #ofNodes=1
Iteration 9: #ofNodes=1
Iteration 10: #ofNodes=5
Iteration 11: #ofNodes=2
Iteration 12: #ofNodes=1
Result: "Area zero found! Terminated."

REFACTORED CODE:
Iteration 1: #ofNodes=5
Iteration 2: #ofNodes=2
Iteration 3: #ofNodes=2
Iteration 4: #ofNodes=5
Iteration 5: #ofNodes=11
Iteration 6: #ofNodes=4
Iteration 7: #ofNodes=5
Iteration 8: #ofNodes=4
Iteration 9: #ofNodes=1
Iteration 10: #ofNodes=1
+ Result: "Area zero found! Terminated."

Massive Error Space - 64
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=3 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=64 --imax=2 --omax=8 --min-subgraph-size=1 

ORIGINAL CODE:
Iteration 1: #ofNodes=5
Iteration 2: #ofNodes=5
Iteration 3: #ofNodes=11
Iteration 4: #ofNodes=4
Iteration 5: #ofNodes=5
Iteration 6: #ofNodes=3
Iteration 7: #ofNodes=1
Result: "Area zero found! Terminated."

REFACTORED CODE:
Iteration 1: #ofNodes=5
Iteration 2: #ofNodes=5
Iteration 3: #ofNodes=11
Iteration 4: #ofNodes=4
Iteration 5: #ofNodes=5
Iteration 6: #ofNodes=3
Iteration 7: #ofNodes=1
+ Result: "Area zero found! Terminated."

#====================================================================================================

# Mode 4: find_subgraph_feasible
Tightest Error Space - 4
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=4 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=4 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=7
Iteration 2: #ofNodes=2
Iteration 3: #ofNodes=7
Iteration 4: #ofNodes=3
Iteration 5: #ofNodes=3
Iteration 6: #ofNodes=3
Iteration 7: #ofNodes=7
+ Result: Approximate circuit found!

REFACTORED CODE:
Iteration 1: #ofNodes=7
Iteration 2: #ofNodes=2
Iteration 3: #ofNodes=7
Iteration 4: #ofNodes=3
Iteration 5: #ofNodes=3
Iteration 6: #ofNodes=8
+ Result: "The error space is exhausted!"

Strict Error Space - 8
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=4 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=8 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=7
Iteration 2: #ofNodes=2
Iteration 3: #ofNodes=7
Iteration 4: #ofNodes=3
Iteration 5: #ofNodes=3
Iteration 6: #ofNodes=3
Iteration 7: #ofNodes=7
Iteration 8: #ofNodes=8
Iteration 9: #ofNodes=7
Iteration 10: #ofNodes=8
Iteration 11: #ofNodes=5
Iteration 12: #ofNodes=5 
Iteration 13: #ofNodes=5 
Iteration 14: #ofNodes=8
Iteration 15: #ofNodes=8
+ Result: "The error space is exhausted!"

REFACTORED CODE:
Iteration 1: #ofNodes=7
Iteration 2: #ofNodes=2
Iteration 3: #ofNodes=7
Iteration 4: #ofNodes=3
Iteration 5: #ofNodes=3
Iteration 6: #ofNodes=8
Iteration 7: #ofNodes=8 
Iteration 8: #ofNodes=8 
Iteration 9: #ofNodes=8 
Iteration 10: #ofNodes=8
+ Result: "The error space is exhausted!"

Baseline Error Space - 16
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=4 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:
iteration 1: #ofNodes=8
iteration 2: #ofNodes=7
iteration 3: #ofNodes=8
iteration 4: #ofNodes=8 
iteration 5: #ofNodes=8 
iteration 6: #ofNodes=8
iteration 7: #ofNodes=8
iteration 8: #ofNodes=8 
iteration 9: #ofNodes=8 
iteration 10: #ofNodes=8 
+ Result: "The error space is exhausted!"

REFACTORED CODE:
iteration 1: #ofNodes=8
iteration 2: #ofNodes=7
iteration 3: #ofNodes=8
iteration 4: #ofNodes=8 
iteration 5: #ofNodes=8
iteration 6: #ofNodes=8
iteration 7: #ofNodes=8
iteration 8: #ofNodes=8
iteration 9: #ofNodes=7
iteration 10: #ofNodes=7
iteration 11: #ofNodes=1
iteration 12: #ofNodes=1 
iteration 13: #ofNodes=1 
+ Result: "The error space is exhausted!"

Wide Error Space - 32
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=4 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=32 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=8
Iteration 4: #ofNodes=8 
Iteration 5: #ofNodes=8 
Iteration 6: #ofNodes=8 
Iteration 7: #ofNodes=8
Iteration 8: #ofNodes=7
Iteration 9: #ofNodes=7
+ Result: "Area zero found! Terminated."

REFACTORED CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=8 
Iteration 4: #ofNodes=8 
Iteration 5: #ofNodes=8
Iteration 6: #ofNodes=8
Iteration 7: #ofNodes=7
+ Result: "Area zero found! Terminated."

Massive Error Space - 64
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=4 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=64 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=8
Iteration 4: #ofNodes=8 
Iteration 5: #ofNodes=8 
Iteration 6: #ofNodes=8 
Iteration 7: #ofNodes=8 
Iteration 8: #ofNodes=8 
Iteration 9: #ofNodes=8 
Iteration 10: #ofNodes=8 
+ Result: "The error space is exhausted!"

REFACTORED CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=8
Iteration 4: #ofNodes=8
Iteration 5: #ofNodes=7
+ Result: "Area zero found! Terminated."

#====================================================================================================

# Mode 5: find_subgraph_feasible_hard
Tightest Error Space - 4
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=5 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=4 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=2
Iteration 3: #ofNodes=4
Iteration 4: #ofNodes=3
Iteration 5: #ofNodes=3 
Iteration 6: #ofNodes=4
+ Result: "The error space is exhausted!"

REFACTORED CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=2
Iteration 3: #ofNodes=4
Iteration 4: #ofNodes=3
Iteration 5: #ofNodes=3 
Iteration 6: #ofNodes=4
+ Result: "The error space is exhausted!"

Strict Error Space - 8
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=5 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=8 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=2
Iteration 3: #ofNodes=4
Iteration 4: #ofNodes=3
Iteration 5: #ofNodes=3
Iteration 6: #ofNodes=4
Iteration 7: #ofNodes=4
Iteration 8: #ofNodes=4
Iteration 9: #ofNodes=4
Iteration 10: #ofNodes=8
+ Result: Approximate circuit found!

REFACTORED CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=2
Iteration 3: #ofNodes=4
Iteration 4: #ofNodes=3
Iteration 5: #ofNodes=3 
Iteration 6: #ofNodes=4
Iteration 7: #ofNodes=4 
Iteration 8: #ofNodes=4
Iteration 9: #ofNodes=4
Iteration 10: #ofNodes=4
Iteration 11: #ofNodes=4 
Iteration 12: #ofNodes=5
+ Result: Approximate circuit found!

Baseline Error Space - 16
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=5 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:
iteration 1: #ofNodes=7
iteration 2: #ofNodes=4
iteration 3: #ofNodes=4
iteration 4: #ofNodes=4 
iteration 5: #ofNodes=3
iteration 6: #ofNodes=3 
iteration 7: #ofNodes=8
iteration 8: #ofNodes=4
iteration 9: #ofNodes=4
iteration 10: #ofNodes=4
iteration 11: #ofNodes=4
iteration 12: #ofNodes=4
iteration 13: #ofNodes=4 
iteration 14: #ofNodes=4 
iteration 15: #ofNodes=5
iteration 16: #ofNodes=3
iteration 17: ("subgraph not found")
+ Result: ("The error space is exhausted!")

REFACTORED CODE:
iteration 1: #ofNodes=7
iteration 2: #ofNodes=4
iteration 3: #ofNodes=4
iteration 4: #ofNodes=4
iteration 5: #ofNodes=3
iteration 6: #ofNodes=3 
iteration 7: #ofNodes=8
iteration 8: #ofNodes=4
iteration 9: #ofNodes=4
iteration 10: #ofNodes=4
iteration 11: #ofNodes=4
iteration 12: #ofNodes=4
iteration 13: #ofNodes=4 
iteration 14: #ofNodes=4 
iteration 15: #ofNodes=5
iteration 16: #ofNodes=3
iteration 17: ("subgraph not found")
+ Result: ("The error space is exhausted!")

✅

Wide Error Space - 32
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=5 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=32 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=7
Iteration 3: #ofNodes=8
Iteration 4: #ofNodes=5
Iteration 5: #ofNodes=4
Iteration 6: #ofNodes=4
Iteration 7: #ofNodes=4
Iteration 8: #ofNodes=4
Iteration 9: #ofNodes=4
Iteration 10: #ofNodes=4
Iteration 11: #ofNodes=4
Result: "The error space is exhausted!"

REFACTORED CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=7
Iteration 3: #ofNodes=8
Iteration 4: #ofNodes=5
Iteration 5: #ofNodes=4
Iteration 6: #ofNodes=4 
Iteration 7: #ofNodes=4 
Iteration 8: #ofNodes=4 
Iteration 9: #ofNodes=4 
Iteration 10: #ofNodes=4 
Iteration 11: #ofNodes=4 
+ Result: "The error space is exhausted!"

Massive Error Space - 64
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=5 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=64 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=7
Iteration 4: #ofNodes=4
Iteration 5: #ofNodes=1
Result: "Area zero found! Terminated."

REFACTORED CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=8
Iteration 3: #ofNodes=7
Iteration 4: #ofNodes=4
Iteration 5: #ofNodes=1
+ Result: "Area zero found! Terminated."

#====================================================================================================

# Mode 55: find_subgraph_feasible_hard_limited_inputs_datatype_bitvec
Tightest Error Space - 4
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=55 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=4 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: subgraph not found (#ofNodes=0 or skipped)
Iteration 2: #ofNodes=4
Iteration 3: #ofNodes=2
Iteration 4: #ofNodes=2
Iteration 5: #ofNodes=4
+ Result: Approximate circuit found!

REFACTORED CODE:

Strict Error Space - 8
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=55 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=8 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: Subgraph not found
Iteration 2: #ofNodes=4
Iteration 3: #ofNodes=2
Iteration 4: #ofNodes=2 
Iteration 5: #ofNodes=4
Iteration 6: #ofNodes=3
Iteration 7: #ofNodes=3
Iteration 8: #ofNodes=4
Iteration 9: #ofNodes=3
Iteration 10: #ofNodes=3
Iteration 11: #ofNodes=4
+ Result: Approximate circuit found!

REFACTORED CODE:

Baseline Error Space - 16
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=55 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:
Iteration 1: #ofNodes=2
Iteration 2: #ofNodes=4
Iteration 3: #ofNodes=4
Iteration 4: #ofNodes=4
Iteration 5: #ofNodes=4 
Iteration 6: #ofNodes=4
Iteration 7: #ofNodes=6
Iteration 8: #ofNodes=5
Iteration 9: #ofNodes=6
Iteration 10: #ofNodes=5
Iteration 11: #ofNodes=6
Iteration 12: #ofNodes=6
Iteration 13: #ofNodes=6
Iteration 14: #ofNodes=8
+ Result: Approximate circuit found!

REFACTORED CODE:

Wide Error Space - 32
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=55 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=32 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=4
Iteration 2: #ofNodes=4
Iteration 3: #ofNodes=8
Iteration 4: #ofNodes=8 
Iteration 5: #ofNodes=8
Iteration 6: #ofNodes=8
Iteration 7: #ofNodes=6
Iteration 8: #ofNodes=6
Iteration 9: #ofNodes=6 
Iteration 10: #ofNodes=8
Iteration 11: #ofNodes=7
+ Result: "The error space is exhausted!"

REFACTORED CODE:

Massive Error Space - 64
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=55 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=64 --imax=2 --omax=8 

ORIGINAL CODE:
Iteration 1: #ofNodes=8
Iteration 2: #ofNodes=7
Iteration 3: #ofNodes=8
Iteration 4: #ofNodes=14
Iteration 5: #ofNodes=8
Iteration 6: #ofNodes=8
Iteration 7: #ofNodes=8
Iteration 8: #ofNodes=8
Iteration 9: #ofNodes=8
Iteration 10: #ofNodes=8
Iteration 11: #ofNodes=8
Iteration 12: #ofNodes=8 (subgraph equal to previous, skipped)
Iteration 13: #ofNodes=5
+ Result: Approximate circuit found!

REFACTORED CODE:

#====================================================================================================

# Mode 6: find_subgraph_feasible_hard_limited_inputs_datatype_bitvec_minthreshold
Tightest Error Space - 4
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=6 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=4 --imax=2 --omax=8 

ORIGINAL CODE:

REFACTORED CODE:

Strict Error Space - 8
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=6 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=8 --imax=2 --omax=8 

ORIGINAL CODE:

REFACTORED CODE:

Baseline Error Space - 16
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=6 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:
iteration 1: #ofNodes=4
iteration 2: #ofNodes=2
iteration 3: #ofNodes=2
iteration 4: #ofNodes=2
iteration 5: #ofNodes=2
iteration 6: #ofNodes=2
iteration 7: #ofNodes=2
iteration 8: #ofNodes=2
iteration 9: #ofNodes=2
iteration 10: #ofNodes=1
iteration 11: #ofNodes=1
iteration 12: #ofNodes=1
iteration 13: #ofNodes=1
iteration 14: #ofNodes=1
iteration 15: #ofNodes=1
iteration 16: #ofNodes=1
iteration 17: #ofNodes=1
iteration 18: #ofNodes=1
iteration 19: #ofNodes=1
iteration 20: #ofNodes=1
iteration 21: #ofNodes=4
iteration 22: #ofNodes=4
iteration 23: #ofNodes=4 
+ Result: "Area zero found! Terminated."

REFACTORED CODE:
iteration 1: #ofNodes=4
iteration 2: #ofNodes=2
iteration 3: #ofNodes=2
iteration 4: #ofNodes=2
iteration 5: #ofNodes=2
iteration 6: #ofNodes=2
iteration 7: #ofNodes=2
iteration 8: #ofNodes=2
iteration 9: #ofNodes=2
iteration 10: #ofNodes=1
iteration 11: #ofNodes=1
iteration 12: #ofNodes=1
iteration 13: #ofNodes=1
iteration 14: #ofNodes=1
iteration 15: #ofNodes=1
iteration 16: #ofNodes=1
iteration 17: #ofNodes=1
iteration 18: #ofNodes=1
iteration 19: #ofNodes=1
iteration 20: #ofNodes=1
iteration 21: #ofNodes=4
iteration 22: #ofNodes=4
iteration 23: #ofNodes=4
+ Result: "Area zero found! Terminated."

✅

Wide Error Space - 32
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=6 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=32 --imax=2 --omax=8 

ORIGINAL CODE:

REFACTORED CODE:

Massive Error Space - 64
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=6 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=64 --imax=2 --omax=8 

ORIGINAL CODE:

REFACTORED CODE:

#====================================================================================================

# Mode 11: find_subgraph_feasible_soft
Tightest Error Space - 4
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=11 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=4 --imax=2 --omax=8 

ORIGINAL CODE:

REFACTORED CODE:

Strict Error Space - 8
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=11 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=8 --imax=2 --omax=8 

ORIGINAL CODE:

REFACTORED CODE:

Baseline Error Space - 16
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=11 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:

REFACTORED CODE:

Wide Error Space - 32
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=11 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=32 --imax=2 --omax=8 > log_adder8_orig_mode11_err32.txt

ORIGINAL CODE:

REFACTORED CODE:

Massive Error Space - 64
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=11 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=64 --imax=2 --omax=8 > log_adder8_orig_mode11_err64.txt

ORIGINAL CODE:

REFACTORED CODE:


AttributeError: 'bool' object has no attribute 'as_ast'

#====================================================================================================

# Mode 12: find_subgraph_feasible_soft_outputs / subgraph candidates
Tightest Error Space - 4
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=12 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=4 --imax=2 --omax=8 

ORIGINAL CODE:

REFACTORED CODE:

Strict Error Space - 8
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=12 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=8 --imax=2 --omax=8 

ORIGINAL CODE:

REFACTORED CODE:

Baseline Error Space - 16
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=12 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:
iteration 1: #ofNodes=8
iteration 2: #ofNodes=7
iteration 3: #ofNodes=8
iteration 4: #ofNodes=8 
iteration 5: #ofNodes=8
iteration 6: #ofNodes=8 
iteration 7: #ofNodes=8 
iteration 8: #ofNodes=8 
iteration 9: #ofNodes=8
iteration 10: #ofNodes=8
iteration 11: #ofNodes=7 
+ Result: "Area zero found! Terminated."

REFACTORED CODE:
iteration 1: #ofNodes=8
iteration 2: #ofNodes=7
iteration 3: #ofNodes=8
iteration 4: #ofNodes=8 
iteration 5: #ofNodes=8 
iteration 6: #ofNodes=8
iteration 7: #ofNodes=8
iteration 8: #ofNodes=8 
iteration 9: #ofNodes=8 
iteration 10: #ofNodes=8 
+ Result: ("The error space is exhausted!")

Wide Error Space - 32
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=12 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=32 --imax=2 --omax=8 

ORIGINAL CODE:

REFACTORED CODE:

Massive Error Space - 64
.venv/bin/python main.py benchmarks/v/mul_i8_o8.v --subxpat --encoding=z3int --extraction-mode=12 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=64 --imax=2 --omax=8 

ORIGINAL CODE:

REFACTORED CODE:

#====================================================================================================

# Mode 42: manual extraction
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=42 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8