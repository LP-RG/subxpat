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
                    lines = text.split('\n')
                    curr_iter = None
                    curr_nodes = None

                    for line in lines:
                        it_m = re.search(r'iteration\s+(\d+)', line, re.IGNORECASE)
                        if it_m:
                            curr_iter = it_m.group(1)
                            
                        n_m = re.search(r'#ofNodes\s*=\s*(\d+)', line)
                        if n_m:
                            curr_nodes = n_m.group(1)
                            
                        t_m = re.search(r'subgraph_extraction_time\s*=\s*([0-9.]+)', line)
                        if t_m and curr_iter and curr_nodes:
                            print(f'iteration {curr_iter}: #ofNodes={curr_nodes} subgraph_extraction_time: {t_m.group(1)}')
                            curr_iter = None
                            curr_nodes = None
                    "
                echo ""
            done
        done
    done
done