#!/bin/bash

# Define the encodings
ENCODINGS=("z3datatype" "z3dbvec")

# Define the error spaces
ERRORS=(4 8 16 32 64)

# Define the extraction modes 
EXTRACTION_MODES=(1)

# Define the benchmark files
BENCHMARKS=(
    "benchmarks/v/adder_i8_o5.v"
    "benchmarks/v/mul_i8_o8.v"
)

# Common configuration parameters
IMAX=2
OMAX=8

for mode in "${EXTRACTION_MODES[@]}"; do
    echo "# Mode $mode: "
    
    for err in "${ERRORS[@]}"; do
        echo "#=================================================="
        echo "Error Space - $err"
        echo "#=================================================="
        
        for bench in "${BENCHMARKS[@]}"; do
            if [ ! -f "$bench" ]; then
                continue
            fi
            
            for enc in "${ENCODINGS[@]}"; do
                echo "Running: $bench | Encoding: $enc | Mode: $mode | Max Error: $err"
                echo "#=================================================="
                
                CMD=".venv/bin/python main.py $bench --subxpat --encoding=$enc --extraction-mode=$mode --max-labeling --max-lpp=8 --max-ppo=10 --max-error=$err --imax=$IMAX --omax=$OMAX"                
                echo "$CMD"
                echo "#=================================================="
                echo ""
                
                # Capture output and parse iterations to match your exact format
                output=$(eval "$CMD" 2>&1)
                
                python3 -c "
import re
text = '''$output'''
matches = re.findall(r'iteration\s+(\d+).*?#ofNodes\s*=\s*(\d+).*?subgraph_extraction_time\s*=\s*([0-9.]+)', text, re.DOTALL)
for it, nodes, t in matches:
    print(f'iteration {it}: #ofNodes={nodes} subgraph_extraction_time: {t}')
"
                echo ""
            done
        done
    done
done