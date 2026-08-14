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
    #"benchmarks/v/mul_i12_o12.v"
    #"benchmarks/v/madd_i12_o8.v"
    #"benchmarks/v/adder_i28_o15.v"
)

# Common configuration parameters
IMAX=2
OMAX=8

for mode in "${EXTRACTION_MODES[@]}"; do
    echo "# Mode $mode: "
    
    for err in "${ERRORS[@]}"; do
        echo "#=================================================="
        echo "Error Space - $err"
        
        for bench in "${BENCHMARKS[@]}"; do
            if [ ! -f "$bench" ]; then
                continue
            fi
            
            for enc in "${ENCODINGS[@]}"; do
                echo "#=================================================="
                echo "Running: $bench | Encoding: $enc | Mode: $mode | Max Error: $err"
                echo "#=================================================="
                
                CMD=".venv/bin/python main.py $bench --subxpat --encoding=$enc --extraction-mode=$mode --max-labeling --max-lpp=8 --max-ppo=10 --max-error=$err --imax=$IMAX --omax=$OMAX $EXTRA_ARGS"
                echo "$CMD"
                echo "#=================================================="
                echo ""
                
                # Capture output and parse iterations to match your exact format
                output=$(.venv/bin/python main.py "$bench" \
                    --subxpat \
                    --encoding="$enc" \
                    --extraction-mode=$mode \
                    --max-labeling \
                    --max-lpp=8 \
                    --max-ppo=10 \
                    --max-error=$err \
                    --imax=$IMAX \
                    --omax=$OMAX \
                    $EXTRA_ARGS 2>&1)
                
                python3 -c "
import re
text = '''$output'''
curr_it = None
curr_n = None

for line in text.splitlines():
    # Use search instead of match to ignore invisible color codes at the start of the line
    m_it = re.search(r'iteration\s+(\d+)\s+with', line)
    if m_it:
        curr_it = m_it.group(1)
        curr_n = None  # Reset nodes for the new iteration
        
    m_n = re.search(r'#ofNodes\s*=\s*(\d+)', line)
    if m_n:
        curr_n = m_n.group(1)
        
    m_t = re.search(r'subgraph_extraction_time\s*=\s*([0-9.]+)', line)
    if m_t and curr_it and curr_n:
        print(f'iteration {curr_it}: #ofNodes={curr_n} subgraph_extraction_time: {m_t.group(1)}')
        # Reset until the next true iteration header is found
        curr_it = None
        curr_n = None
"
                echo ""
            done
        done
    done
done