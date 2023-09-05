#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

echo -e "====================================
===================================="
ADDER='adder_i8_o5.v'
MADD='madd_i6_o4.v'
echo $PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat --clean --multiple -subgraphsize=10 -sensitivity=1
$PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat --clean --multiple -subgraphsize=10 -sensitivity=1

echo $PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat --clean --multiple -subgraphsize=20 -sensitivity=2
$PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat --clean --multiple -subgraphsize=20 -sensitivity=2

echo $PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat --clean --multiple -subgraphsize=30 -sensitivity=4
$PYTHON $SCRIPT "input/ver/$ADDER" -app "input/ver/$ADDER" -lpp=4 -ppo=4 -iterations=4 --grid --subxpat --clean --multiple -subgraphsize=30 -sensitivity=4




#
echo $PYTHON $SCRIPT "input/ver/$MADD" -app "input/ver/$MADD" -lpp=6 -ppo=6 -iterations=6 --grid --subxpat  --multiple -subgraphsize=10 -sensitivity=1
$PYTHON $SCRIPT "input/ver/$MADD" -app "input/ver/$MADD" -lpp=6 -ppo=6 -iterations=6 --grid --subxpat  --multiple -subgraphsize=10 -sensitivity=1

echo $PYTHON $SCRIPT "input/ver/$MADD" -app "input/ver/$MADD" -lpp=6 -ppo=6 -iterations=6 --grid --subxpat  --multiple -subgraphsize=20 -sensitivity=2
$PYTHON $SCRIPT "input/ver/$MADD" -app "input/ver/$MADD" -lpp=6 -ppo=6 -iterations=6 --grid --subxpat  --multiple -subgraphsize=20 -sensitivity=2

echo $PYTHON $SCRIPT "input/ver/$MADD" -app "input/ver/$MADD" -lpp=6 -ppo=6 -iterations=6 --grid --subxpat  --multiple -subgraphsize=30 -sensitivity=4
$PYTHON $SCRIPT "input/ver/$MADD" -app "input/ver/$MADD" -lpp=6 -ppo=6 -iterations=6 --grid --subxpat  --multiple -subgraphsize=30 -sensitivity=4