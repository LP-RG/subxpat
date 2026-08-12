#!/bin/bash

# Define the encodings
ENCODINGS=("z3datatype" "z3dbvec")

# Define the error spaces
ERRORS=(4 8 16 32 64)

# Define the extraction modes 
EXTRACTION_MODES=(1)

# Define the benchmark files: One adder and one multiplier
BENCHMARKS=(
    "benchmarks/v/adder_i8_o5.v"
    "benchmarks/v/mul_i8_o8.v"
)

# Common configuration parameters
IMAX=2
OMAX=8

# Loop through each benchmark circuit
for bench in "${BENCHMARKS[@]}"; do
    # Check if file exists before running
    if [ ! -f "$bench" ]; then
        echo "Skipping $bench (file not found)"
        continue
    fi

    # Loop through each Z3 encoding approach
    for enc in "${ENCODINGS[@]}"; do
        
        # Loop through each extraction mode
        for mode in "${EXTRACTION_MODES[@]}"; do
            
            # Loop through each error tolerance value
            for err in "${ERRORS[@]}"; do
                echo "=================================================="
                echo "Running: $bench | Encoding: $enc | Mode: $mode | Max Error: $err"
                echo "=================================================="

                # Conditionally apply --min-subgraph-size=1 only for modes 2 and 3
                EXTRA_ARGS=""
                if [ "$mode" -eq 2 ] || [ "$mode" -eq 3 ]; then
                    EXTRA_ARGS="--min-subgraph-size=1"
                fi

                .venv/bin/python main.py "$bench" \
                    --subxpat \
                    --encoding="$enc" \
                    --extraction-mode=$mode \
                    --max-labeling \
                    --max-lpp=8 \
                    --max-ppo=10 \
                    --max-error=$err \
                    --imax=$IMAX \
                    --omax=$OMAX \
                    $EXTRA_ARGS

                echo "Finished execution for $bench ($enc, mode=$mode, error=$err)."
                echo ""
            done
            
        done
        
    done
done

echo "All benchmark, extraction mode, and error-space sweeps have finished successfully!"