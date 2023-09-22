#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

ABS_12='adder_i12_o7.v'
for SIZE in 5 10 15 20 25 30 35 40 45 50
do
  $PYTHON $SCRIPT "input/ver/$ABS_12" -lpp=12 -ppo=12 -et=64 --subxpat --grid -iterations=24 -app "input/ver/$ABS_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_12" -lpp=12 -ppo=12 -et=56 --subxpat --grid -iterations=24 -app "input/ver/$ABS_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_12" -lpp=12 -ppo=12 -et=48 --subxpat --grid -iterations=24 -app "input/ver/$ABS_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_12" -lpp=12 -ppo=12 -et=40 --subxpat --grid -iterations=24 -app "input/ver/$ABS_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_12" -lpp=12 -ppo=12 -et=32 --subxpat --grid -iterations=24 -app "input/ver/$ABS_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_12" -lpp=12 -ppo=12 -et=24 --subxpat --grid -iterations=24 -app "input/ver/$ABS_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_12" -lpp=12 -ppo=12 -et=16 --subxpat --grid -iterations=24 -app "input/ver/$ABS_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_12" -lpp=12 -ppo=12 -et=8 --subxpat --grid -iterations=24 -app "input/ver/$ABS_12" -mode=3 -subgraphsize="$SIZE"
done
