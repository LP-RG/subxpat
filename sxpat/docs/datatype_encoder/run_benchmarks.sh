#!/bin/bash

# Define the encodings
ENCODINGS=("z3dint"  "z3dbvec" "z3datatype")

# Define the error spaces
ERRORS=(64)

# Define the extraction modes 
EXTRACTION_MODES=(5)

# Define the benchmark files
BENCHMARKS=(
    #"benchmarks/v/adder_i8_o5.v"
    #"benchmarks/v/adder_i12_o7.v"
    "benchmarks/v/adder_i16_o9.v"
    "benchmarks/v/adder_i28_o15.v"
    "benchmarks/v/adder_i32_o17.v"
    "benchmarks/v/adder_i36_o19.v"
    #"benchmarks/v/adder_i40_o21.v"
    #"benchmarks/v/adder_i44_o23.v"
    #"benchmarks/v/adder_i64_o33.v"
    #"benchmarks/v/mul_i4_o4.v"
    #"benchmarks/v/mul_i6_o6.v"
    "benchmarks/v/mul_i8_o8.v"
    "benchmarks/v/mul_i10_o10.v"
    #"benchmarks/v/mul_i12_o12.v"
    #"benchmarks/v/madd_i6_o4.v"
    #"benchmarks/v/madd_i9_o6.v"
    #"benchmarks/v/madd_i12_o8.v"
    #"benchmarks/v/madd_i15_o10.v"
    #"benchmarks/v/sad_i10_o4.v"
    #"benchmarks/v/sad_i20_o6.v"
    "benchmarks/v/abs_diff_i8_o4.v"
    "benchmarks/v/abs_diff_i10_o5.v"
    #"benchmarks/v/abs_diff_i12_o6.v"
    #"benchmarks/v/abs_diff_i16_o8.v"
    #"benchmarks/v/abs_diff_i20_o10.v"
    #"benchmarks/v/abs_diff_i24_o12.v"
    #"benchmarks/v/abs_diff_i28_o14.v"
    #"benchmarks/v/abs_diff_i32_o16.v"
    #"benchmarks/v/abs_diff_i36_o18.v"
)

# Common configuration parameters
IMAX=8
OMAX=5
lpp=1
ppo=1

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
                
                CMD=".venv/bin/python3 main.py $bench --subxpat --encoding=$enc --extraction-mode=$mode --max-labeling --max-lpp=$lpp --max-ppo=$ppo --max-error=$err --imax=$IMAX --omax=$OMAX --error-partitioning=asc $EXTRA_ARGS"
                echo "$CMD"
                echo "#=================================================="
                echo ""
                
                # Capture output and parse iterations to match your exact format
                output=$(.venv/bin/python main.py "$bench" \
                    --subxpat \
                    --encoding="$enc" \
                    --extraction-mode=$mode \
                    --max-labeling \
                    --max-lpp=$lpp \
                    --max-ppo=$ppo \
                    --max-error=$err \
                    --imax=$IMAX \
                    --omax=$OMAX \
                    --error-partitioning=asc \
                    $EXTRA_ARGS 2>&1)
                
                python3 -c "
import sys
import re

curr_it = None
curr_n = None
total_time = 0.0

for line in sys.stdin:
    # 1. Match the start of an iteration
    m_it = re.search(r'iteration\s+(\d+)\s+with', line)
    if m_it:
        curr_it = m_it.group(1)
        curr_n = None  
        
    # 2. Match the number of nodes (if the solver found a valid subgraph)
    m_n = re.search(r'#ofNodes\s*=\s*(\d+)', line)
    if m_n:
        curr_n = m_n.group(1)
        
    # 3. Catch explicitly failed extractions (UNSAT)
    if re.search(r'subgraph not found', line, re.IGNORECASE):
        curr_n = '0'
        
    # 4. Match the extraction time and sum it
    m_t = re.search(r'subgraph_extraction_time\s*=\s*([0-9.]+)', line)
    if m_t and curr_it:
        if curr_n is None:
            curr_n = '0'
            
        time_val = float(m_t.group(1))
        total_time += time_val
            
        print(f'iteration {curr_it}: #ofNodes={curr_n} subgraph_extraction_time: {m_t.group(1)}')
        
        curr_it = None
        curr_n = None

print(f'---\ntotal_subgraph_extraction_time: {total_time}')
" <<< "$output"
                echo ""
            done
        done
    done
done