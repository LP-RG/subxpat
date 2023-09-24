#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'


ABS_6='abs_diff_i6_o4.v'
for SIZE in 1 2 3 4 5 10 15 20 25 30 35 40 45 50
do
  $PYTHON $SCRIPT "input/ver/$ABS_6" -lpp=6 -ppo=6 -et=8 --subxpat --grid -iterations=12 -app "input/ver/$ABS_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_6" -lpp=6 -ppo=6 -et=7 --subxpat --grid -iterations=12 -app "input/ver/$ABS_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_6" -lpp=6 -ppo=6 -et=6 --subxpat --grid -iterations=12 -app "input/ver/$ABS_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_6" -lpp=6 -ppo=6 -et=5 --subxpat --grid -iterations=12 -app "input/ver/$ABS_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_6" -lpp=6 -ppo=6 -et=4 --subxpat --grid -iterations=12 -app "input/ver/$ABS_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_6" -lpp=6 -ppo=6 -et=3 --subxpat --grid -iterations=12 -app "input/ver/$ABS_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_6" -lpp=6 -ppo=6 -et=2 --subxpat --grid -iterations=12 -app "input/ver/$ABS_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_6" -lpp=6 -ppo=6 -et=1 --subxpat --grid -iterations=12 -app "input/ver/$ABS_6" -mode=3 -subgraphsize="$SIZE"
done

ABS_8='abs_diff_i8_o5.v'
for SIZE in 1 2 3 4 5 10 15 20 25 30 35 40 45 50
do
  $PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$ABS_8" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=14 --subxpat --grid -iterations=16 -app "input/ver/$ABS_8" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=12 --subxpat --grid -iterations=16 -app "input/ver/$ABS_8" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=10 --subxpat --grid -iterations=16 -app "input/ver/$ABS_8" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=8 --subxpat --grid -iterations=16 -app "input/ver/$ABS_8" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=6 --subxpat --grid -iterations=16 -app "input/ver/$ABS_8" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=4 --subxpat --grid -iterations=16 -app "input/ver/$ABS_8" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=2 --subxpat --grid -iterations=16 -app "input/ver/$ABS_8" -mode=3 -subgraphsize="$SIZE"
done
