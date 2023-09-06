#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

ADDER_8='adder_i8_o5.v'



$PYTHON $SCRIPT "input/ver/$ADDER_8" -lpp=8 -ppo=8 -et=2 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_8"
$PYTHON $SCRIPT "input/ver/$ADDER_8" -lpp=8 -ppo=8 -et=4 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_8"
$PYTHON $SCRIPT "input/ver/$ADDER_8" -lpp=8 -ppo=8 -et=6 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_8"
$PYTHON $SCRIPT "input/ver/$ADDER_8" -lpp=8 -ppo=8 -et=8 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_8"

$PYTHON $SCRIPT "input/ver/$ADDER_8" -lpp=8 -ppo=8 -et=10 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_8"
$PYTHON $SCRIPT "input/ver/$ADDER_8" -lpp=8 -ppo=8 -et=12 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_8"
$PYTHON $SCRIPT "input/ver/$ADDER_8" -lpp=8 -ppo=8 -et=14 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_8"
$PYTHON $SCRIPT "input/ver/$ADDER_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_8"

$PYTHON $SCRIPT "input/ver/$ADDER_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=8 -app "input/ver/$ADDER_8" --plot