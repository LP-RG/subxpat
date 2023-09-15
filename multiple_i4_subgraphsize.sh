#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

ADDER_4='adder_i4_o3.v'
SUBGRAPHSIZE=5
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=10
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=15
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=20
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=25
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=30
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"

ABS_4='abs_diff_i4_o3.v'
SUBGRAPHSIZE=5
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=10
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=15
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=20
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=25
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=30
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"


MUL_4='mul_i4_o4.v'
SUBGRAPHSIZE=5
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=8 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=7 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=6 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=5 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=10
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=8 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=7 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=6 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=5 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=15
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=8 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=7 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=6 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=5 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=20
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=8 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=7 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=6 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=5 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=25
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=8 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=7 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=6 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=5 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
SUBGRAPHSIZE=30
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=8 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=7 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=6 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=5 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=3 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"
$PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=1 --subxpat --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SUBGRAPHSIZE"