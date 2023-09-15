#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

ABS_4='abs_diff_i4.v'



$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=9 -ppo=9 -et=32 --subxpat --grid -iterations=9 -app "input/ver/$ABS_4" -mode=3
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=9 -ppo=9 -et=28 --subxpat --grid -iterations=9 -app "input/ver/$ABS_4" -mode=3
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=9 -ppo=9 -et=24 --subxpat --grid -iterations=9 -app "input/ver/$ABS_4" -mode=3
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=9 -ppo=9 -et=20 --subxpat --grid -iterations=9 -app "input/ver/$ABS_4" -mode=3

$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=9 -ppo=9 -et=16 --subxpat --grid -iterations=9 -app "input/ver/$ABS_4" -mode=3
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=9 -ppo=9 -et=12 --subxpat --grid -iterations=9 -app "input/ver/$ABS_4" -mode=3
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=9 -ppo=9 -et=8 --subxpat --grid -iterations=9 -app "input/ver/$ABS_4" -mode=3
$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=9 -ppo=9 -et=4 --subxpat --grid -iterations=9 -app "input/ver/$ABS_4" -mode=3



