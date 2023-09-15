#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

MUL_10='mul_i10_o10.v'
for SIZE in 5 10 15 20 25 30 35 40 45 50
do
  $PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=512 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=448 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=384 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=320 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=256 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=192 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=128 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=64 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -mode=3 -subgraphsize="$SIZE"
done
