#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

echo -e "====================================
USAGE:
This script runs subxpat on three medium benchmarks, i.e.,
adder_i8_o5, abs_diff_i8_o5, mul_i8_o8
===================================="
ADDER='adder_i8_o5.v'
ABS='abs_diff_i8_o5.v'
MUL='mul_i8_o8.v'
echo $PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=6 -ppo=6 -iterations=5 --grid --subxpat --clean --multiple
timeout 1s $PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=6 -ppo=6 -iterations=5 --grid --subxpat --clean --multiple
if [[ $? -eq 124 ]]; then
    echo "TIMEOUT!"
fi

echo $PYTHON $SCRIPT "input/ver/$ABS" -app "input/ver/$ABS" -lpp=6 -ppo=6 -iterations=5 --grid --subxpat  --multiple
timeout 1s $PYTHON $SCRIPT "input/ver/$ABS" -app "input/ver/$ABS" -lpp=6 -ppo=6 -iterations=5 --grid --subxpat  --multiple
if [[ $? -eq 124 ]]; then
    echo "TIMEOUT!"
fi

echo $PYTHON $SCRIPT "input/ver/$MUL" -app "input/ver/$MUL" -lpp=6 -ppo=6 -iterations=5 --grid --subxpat  --multiple
timeout 1s $PYTHON $SCRIPT "input/ver/$MUL" -app "input/ver/$MUL" -lpp=6 -ppo=6 -iterations=5 --grid --subxpat  --multiple
if [[ $? -eq 124 ]]; then
    echo "TIMEOUT!"
fi