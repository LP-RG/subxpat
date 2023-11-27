#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'


ADD_8='adder_i8_o5.v'
ABS_8='abs_diff_i8_o5.v'
ADD_4='adder_i4_o3.v'
ABS_4='abs_diff_i4_o3.v'

$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -pit=8 -et=4  --grid  -app "input/ver/$ADD_4"  --shared --clean
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -pit=8 -et=3  --grid  -app "input/ver/$ADD_4"   --shared
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -pit=8 -et=2  --grid  -app "input/ver/$ADD_4"   --shared
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -pit=8 -et=1  --grid  -app "input/ver/$ADD_4"   --shared

$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=4  --grid  -app "input/ver/$ADD_4"
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=3  --grid  -app "input/ver/$ADD_4"
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=2  --grid  -app "input/ver/$ADD_4"
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=1  --grid  -app "input/ver/$ADD_4"

$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=4  --grid  -app "input/ver/$ADD_4" --subxpat
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=3  --grid  -app "input/ver/$ADD_4" --subxpat
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=2  --grid  -app "input/ver/$ADD_4" --subxpat
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=1  --grid  -app "input/ver/$ADD_4" --subxpat

$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=4  --grid  -app "input/ver/$ADD_4" --subxpat --shared
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=3  --grid  -app "input/ver/$ADD_4" --subxpat --shared
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=2  --grid  -app "input/ver/$ADD_4" --subxpat --shared
$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=1  --grid  -app "input/ver/$ADD_4" --subxpat --shared
#
#$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -pit=8 -et=4  --grid  -app "input/ver/$ABS_4"   --shared
#$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -pit=8 -et=3  --grid  -app "input/ver/$ABS_4"   --shared
#$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -pit=8 -et=2  --grid  -app "input/ver/$ABS_4"   --shared
#$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -pit=8 -et=1  --grid  -app "input/ver/$ABS_4"   --shared
#
#$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=4  --grid  -app "input/ver/$ABS_4"
#$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=3  --grid  -app "input/ver/$ABS_4"
#$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=2  --grid  -app "input/ver/$ABS_4"
#$PYTHON $SCRIPT "input/ver/$ABS_4" -lpp=4 -ppo=4 -et=1  --grid  -app "input/ver/$ABS_4"

