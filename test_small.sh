#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

echo -e "====================================
USAGE:
This script runs subxpat on three small benchmarks, i.e.,
adder_i4_o3, abs_diff_i4_o3, mul_i4_o4
===================================="
ADDER='adder_i4_o3.v'
ABS='abs_diff_i4_o3.v'
MUL='mul_i4_o4.v'
echo $PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat --clean --multiple
$PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat --clean --multiple

echo $PYTHON $SCRIPT "input/ver/$ABS" -app "input/ver/$ABS" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat  --multiple
$PYTHON $SCRIPT "input/ver/$ABS" -app "input/ver/$ABS" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat  --multiple

echo $PYTHON $SCRIPT "input/ver/$MUL" -app "input/ver/$MUL" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat  --multiple
$PYTHON $SCRIPT "input/ver/$MUL" -app "input/ver/$MUL" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat  --multiple
