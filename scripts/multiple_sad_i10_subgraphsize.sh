#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

SAD_10='sad_i10_o3.v'
for SIZE in 5 10 15 20 25 30 35 40 45 50
do
  $PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=4 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=3 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=2 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=1 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -mode=3 -subgraphsize="$SIZE"
done
