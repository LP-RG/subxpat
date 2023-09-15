#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

MUL_12='mul_i12_o12.v'
for SIZE in 5 10 15 20 25 30 35 40 45 50
do
  $PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=12 -ppo=12 -et=2048 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=12 -ppo=12 -et=1792 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=12 -ppo=12 -et=1536 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=12 -ppo=12 -et=1280 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=12 -ppo=12 -et=1024 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=12 -ppo=12 -et=768 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=12 -ppo=12 -et=512 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=12 -ppo=12 -et=256 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -mode=3 -subgraphsize="$SIZE"
done
