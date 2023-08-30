#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

echo -e "====================================
USAGE:
This script runs subxpat on three medium benchmarks, i.e.,
adder_i12_o7, abs_diff_i12_o7, mul_i12_o12
===================================="
ADDER='adder_i12_o7.v'
ABS='abs_diff_i12_o7.v'
MUL='mul_i12_o12.v'
echo $PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=8 -ppo=8 -iterations=8 --grid --subxpat --clean --multiple
$PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=8 -ppo=8 -iterations=8 --grid --subxpat --clean --multiple

echo $PYTHON $SCRIPT "input/ver/$ABS" -app "input/ver/$ABS" -lpp=8 -ppo=8 -iterations=8 --grid --subxpat  --multiple
$PYTHON $SCRIPT "input/ver/$ABS" -app "input/ver/$ABS" -lpp=8 -ppo=8 -iterations=8 --grid --subxpat  --multiple

echo $PYTHON $SCRIPT "input/ver/$MUL" -app "input/ver/$MUL" -lpp=8 -ppo=8 -iterations=8 --grid --subxpat  --multiple
$PYTHON $SCRIPT "input/ver/$MUL" -app "input/ver/$MUL" -lpp=8 -ppo=8 -iterations=8 --grid --subxpat  --multiple
