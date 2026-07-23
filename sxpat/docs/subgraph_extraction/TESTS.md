# Mode 1: find_subgraph
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=1 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

# Mode 2: find_subgraph_sensitivity
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=2 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8 --min-subgraph-size=1

# Mode 3: find_subgraph_sensitivity_no_io_constraints
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=3 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

# Mode 4: find_subgraph_feasible
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=4 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

# Mode 5: find_subgraph_feasible_hard (deja testat)
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=5 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

# Mode 55: find_subgraph_feasible_hard_limited_inputs_datatype_bitvec
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=55 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

# Mode 6: find_subgraph_feasible_hard_limited_inputs_datatype_bitvec_minthreshold
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=6 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

# Mode 100: slash_to_kill
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=100 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

# Mode 11: find_subgraph_feasible_soft
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=11 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

# Mode 12: find_subgraph_feasible_soft_outputs / subgraph candidates
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=12 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8

# Mode 42: manual extraction
.venv/bin/python main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=42 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8