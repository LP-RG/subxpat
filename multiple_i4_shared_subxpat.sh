#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

ADDER_4='adder_i4_o3.v'
for SIZE in 5 10 15 20 25 30
do
  $PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=4 --subxpat --shared --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
  $PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=3 --subxpat --shared --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
  $PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=2 --subxpat --shared --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
  $PYTHON $SCRIPT "input/ver/$ADDER_4" -lpp=4 -ppo=4 -et=1 --subxpat --shared --grid -iterations=8 -app "input/ver/$ADDER_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
done

ABS_4='abs_diff_i4_o3.v'
for SIZE in 5 10 15 20 25 30
do
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=4 --subxpat --shared --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=3 --subxpat --shared --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=2 --subxpat --shared --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=1 --subxpat --shared --grid -iterations=8 -app "input/ver/$ABS_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
done

MUL_4='mul_i4_o4.v'
for SIZE in 5 10 15 20 25 30
do
  $PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=8 --subxpat --shared --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
  $PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=7 --subxpat --shared --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
  $PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=6 --subxpat --shared --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
  $PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=5 --subxpat --shared --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
  $PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=4 --subxpat --shared --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
  $PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=3 --subxpat --shared --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
  $PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=2 --subxpat --shared --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
  $PYTHON $SCRIPT "input/ver/$MUL_4" -lpp=4 -ppo=4 -et=1 --subxpat --shared --grid -iterations=8 -app "input/ver/$MUL_4" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10
done
