#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

ADDER_10='adder_i10_o6.v'



$PYTHON $SCRIPT "input/ver/$ADDER_10" -lpp=10 -ppo=10 -et=32 --subxpat --grid -iterations=10 -app "input/ver/$ADDER_10"
$PYTHON $SCRIPT "input/ver/$ADDER_10" -lpp=10 -ppo=10 -et=28 --subxpat --grid -iterations=10 -app "input/ver/$ADDER_10"
$PYTHON $SCRIPT "input/ver/$ADDER_10" -lpp=10 -ppo=10 -et=24 --subxpat --grid -iterations=10 -app "input/ver/$ADDER_10"
$PYTHON $SCRIPT "input/ver/$ADDER_10" -lpp=10 -ppo=10 -et=20 --subxpat --grid -iterations=10 -app "input/ver/$ADDER_10"

$PYTHON $SCRIPT "input/ver/$ADDER_10" -lpp=10 -ppo=10 -et=16 --subxpat --grid -iterations=10 -app "input/ver/$ADDER_10"
$PYTHON $SCRIPT "input/ver/$ADDER_10" -lpp=10 -ppo=10 -et=12 --subxpat --grid -iterations=10 -app "input/ver/$ADDER_10"
$PYTHON $SCRIPT "input/ver/$ADDER_10" -lpp=10 -ppo=10 -et=8 --subxpat --grid -iterations=10 -app "input/ver/$ADDER_10"
$PYTHON $SCRIPT "input/ver/$ADDER_10" -lpp=10 -ppo=10 -et=4 --subxpat --grid -iterations=10 -app "input/ver/$ADDER_10"

$PYTHON $SCRIPT "input/ver/$ADDER_10" -lpp=10 -ppo=10 -et=4 --subxpat --grid -iterations=10 -app "input/ver/$ADDER_10" --plot

