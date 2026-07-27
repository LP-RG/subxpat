# Mode 1: find_subgraph
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=1 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:
iteration 1: #ofNodes=8
iteration 2: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 3: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
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
iteration 4: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 5: #ofNodes=8
iteration 6: #ofNodes=8
iteration 7: #ofNodes=8
iteration 8: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 9: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 10: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
+ Result: "The error space is exhausted!"

✅

# Mode 2: find_subgraph_sensitivity
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
iteration 17: #ofNodes=1 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 18: #ofNodes=1 ("The subgraph is equal to the previous one. Skipping iteration ...")
+ Result: "The error space is exhausted!"

REFACTORED CODE:
iteration 1: #ofNodes=4
iteration 2: #ofNodes=2
iteration 3: #ofNodes=1
iteration 4: #ofNodes=1
iteration 5: #ofNodes=1 ("The subgraph is equal to the previous one. Skipping iteration ...")
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

# Mode 3: find_subgraph_sensitivity_no_io_constraints
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=3 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8 --min-subgraph-size=1

ORIGINAL CODE:
iteration 1: #ofNodes=5
iteration 2: #ofNodes=1
iteration 3: #ofNodes=1 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 4: #ofNodes=1 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 5: #ofNodes=5
iteration 6: #ofNodes=2
iteration 7: #ofNodes=5
iteration 8: #ofNodes=2
iteration 9: #ofNodes=8
iteration 10: #ofNodes=8
iteration 11: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 12: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 13: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
+ Result: "The error space is exhausted!"

REFACTORED CODE:
iteration 1: #ofNodes=5
iteration 2: #ofNodes=1
iteration 3: #ofNodes=1 (Aici a dat "The subgraph is equal to the previous one. Skipping iteration ...")
iteration 4: #ofNodes=1 (Aici a dat "The subgraph is equal to the previous one. Skipping iteration ...")
iteration 5: #ofNodes=5
iteration 6: #ofNodes=11
iteration 7: #ofNodes=5
iteration 8: #ofNodes=5
iteration 9: #ofNodes=6
iteration 10: #ofNodes=6
iteration 11: #ofNodes=6 (Aici a dat "The subgraph is equal to the previous one. Skipping iteration ...")
iteration 12: #ofNodes=6 (Aici a dat "The subgraph is equal to the previous one. Skipping iteration ...")
iteration 13: #ofNodes=11 
+ Result: "Area zero found! Terminated."

# Mode 4: find_subgraph_feasible
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=4 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:
iteration 1: #ofNodes=8
iteration 2: #ofNodes=7
iteration 3: #ofNodes=8
iteration 4: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 5: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 6: #ofNodes=8
iteration 7: #ofNodes=8
iteration 8: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 9: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 10: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
+ Result: "The error space is exhausted!"

# Mode 5: find_subgraph_feasible_hard (deja testat)
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=5 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:
iteration 1: #ofNodes=7
iteration 2: #ofNodes=4
iteration 3: #ofNodes=4
iteration 4: #ofNodes=4
iteration 5: #ofNodes=3
iteration 6: #ofNodes=3 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 7: #ofNodes=8
iteration 8: #ofNodes=4
iteration 9: #ofNodes=4
iteration 10: #ofNodes=4
iteration 11: #ofNodes=4
iteration 12: #ofNodes=4
iteration 13: #ofNodes=4 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 14: #ofNodes=4 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 15: #ofNodes=5
iteration 16: #ofNodes=3
iteration 17: ("subgraph not found")
+ Result: ("The error space is exhausted!")

# Mode 55: find_subgraph_feasible_hard_limited_inputs_datatype_bitvec
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=55 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:
iteration 1: #ofNodes=7
iteration 2: #ofNodes=4
iteration 3: #ofNodes=4
iteration 4: #ofNodes=4
iteration 5: #ofNodes=4
iteration 6: #ofNodes=3
iteration 7: #ofNodes=3 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 8: #ofNodes=8
iteration 9: #ofNodes=4
iteration 10: #ofNodes=4
iteration 11: #ofNodes=4
iteration 12: #ofNodes=4
iteration 13: #ofNodes=4
iteration 14: #ofNodes=4
iteration 15: #ofNodes=4 
+ Result: "Area zero found! Terminated."

# Mode 6: find_subgraph_feasible_hard_limited_inputs_datatype_bitvec_minthreshold
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=6 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

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

# Mode 11: find_subgraph_feasible_soft
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=11 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

AttributeError: 'bool' object has no attribute 'as_ast'

# Mode 12: find_subgraph_feasible_soft_outputs / subgraph candidates
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=12 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

ORIGINAL CODE:
iteration 1: #ofNodes=8
iteration 2: #ofNodes=7
iteration 3: #ofNodes=8
iteration 4: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 5: #ofNodes=8
iteration 6: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 7: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 8: #ofNodes=8 ("The subgraph is equal to the previous one. Skipping iteration ...")
iteration 9: #ofNodes=8
iteration 10: #ofNodes=8
iteration 11: #ofNodes=7 
+ Result: "Area zero found! Terminated."

# Mode 42: manual extraction
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=42 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8