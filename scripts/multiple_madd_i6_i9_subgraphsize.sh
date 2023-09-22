#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'


MADD_6='madd_i6_o4.v'
for SIZE in 5 10 15 20 25 30 35 40 45 50
do
  $PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=8 --subxpat --grid -iterations=12 -app "input/ver/$MADD_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=7 --subxpat --grid -iterations=12 -app "input/ver/$MADD_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=6 --subxpat --grid -iterations=12 -app "input/ver/$MADD_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=5 --subxpat --grid -iterations=12 -app "input/ver/$MADD_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=4 --subxpat --grid -iterations=12 -app "input/ver/$MADD_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=3 --subxpat --grid -iterations=12 -app "input/ver/$MADD_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=2 --subxpat --grid -iterations=12 -app "input/ver/$MADD_6" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=1 --subxpat --grid -iterations=12 -app "input/ver/$MADD_6" -mode=3 -subgraphsize="$SIZE"
done

MADD_9='madd_i9_o6.v'
for SIZE in 5 10 15 20 25 30 35 40 45 50
do
  $PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=32 --subxpat --grid -iterations=18 -app "input/ver/$MADD_9" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=28 --subxpat --grid -iterations=18 -app "input/ver/$MADD_9" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=24 --subxpat --grid -iterations=18 -app "input/ver/$MADD_9" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=20 --subxpat --grid -iterations=18 -app "input/ver/$MADD_9" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=16 --subxpat --grid -iterations=18 -app "input/ver/$MADD_9" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=12 --subxpat --grid -iterations=18 -app "input/ver/$MADD_9" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=8 --subxpat --grid -iterations=18 -app "input/ver/$MADD_9" -mode=3 -subgraphsize="$SIZE"
  $PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=4 --subxpat --grid -iterations=18 -app "input/ver/$MADD_9" -mode=3 -subgraphsize="$SIZE"
done
