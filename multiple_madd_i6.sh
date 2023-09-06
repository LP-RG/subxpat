#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

MADD_6='madd_i6_o4.v'



$PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=1 --subxpat --grid -iterations=6 -app "input/ver/$MADD_6"
$PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=2 --subxpat --grid -iterations=6 -app "input/ver/$MADD_6"
$PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=3 --subxpat --grid -iterations=6 -app "input/ver/$MADD_6"
$PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=4 --subxpat --grid -iterations=6 -app "input/ver/$MADD_6"

$PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=5 --subxpat --grid -iterations=6 -app "input/ver/$MADD_6"
$PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=6 --subxpat --grid -iterations=6 -app "input/ver/$MADD_6"
$PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=7 --subxpat --grid -iterations=6 -app "input/ver/$MADD_6"
$PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=8 --subxpat --grid -iterations=6 -app "input/ver/$MADD_6"

$PYTHON $SCRIPT "input/ver/$MADD_6" -lpp=6 -ppo=6 -et=8 --subxpat --grid -iterations=6 -app "input/ver/$MADD_6" --plot

