#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

MUL_8='mul_i8_o8.v'



$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=128 --subxpat --grid -iterations=8 -app "input/ver/$MUL_8"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=112 --subxpat --grid -iterations=8 -app "input/ver/$MUL_8"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=96 --subxpat --grid -iterations=8 -app "input/ver/$MUL_8"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=80 --subxpat --grid -iterations=8 -app "input/ver/$MUL_8"

$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=64 --subxpat --grid -iterations=8 -app "input/ver/$MUL_8"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=48 --subxpat --grid -iterations=8 -app "input/ver/$MUL_8"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=8 -app "input/ver/$MUL_8"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=8 -app "input/ver/$MUL_8"



