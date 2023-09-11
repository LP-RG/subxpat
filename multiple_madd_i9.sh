#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

MADD_9='madd_i9_o6.v'



$PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=32 --subxpat --grid -iterations=9 -app "input/ver/$MADD_9"
$PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=28 --subxpat --grid -iterations=9 -app "input/ver/$MADD_9"
$PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=24 --subxpat --grid -iterations=9 -app "input/ver/$MADD_9"
$PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=20 --subxpat --grid -iterations=9 -app "input/ver/$MADD_9"

$PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=16 --subxpat --grid -iterations=9 -app "input/ver/$MADD_9"
$PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=12 --subxpat --grid -iterations=9 -app "input/ver/$MADD_9"
$PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=8 --subxpat --grid -iterations=9 -app "input/ver/$MADD_9"
$PYTHON $SCRIPT "input/ver/$MADD_9" -lpp=9 -ppo=9 -et=4 --subxpat --grid -iterations=9 -app "input/ver/$MADD_9"



