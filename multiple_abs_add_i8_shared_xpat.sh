#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'


ADD_8='adder_i8_o5.v'
ABS_8='abs_diff_i8_o5.v'
ADD_4='adder_i4_o3.v'
ABS_4='abs_diff_i4_o3.v'

#$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -pit=8 -et=4  --grid  -app "input/ver/$ADD_4"  --shared --clean
#$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -pit=8 -et=3  --grid  -app "input/ver/$ADD_4"   --shared
#$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -pit=8 -et=2  --grid  -app "input/ver/$ADD_4"   --shared
#$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -pit=8 -et=1  --grid  -app "input/ver/$ADD_4"   --shared
#
#$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=4  --grid  -app "input/ver/$ADD_4"
#$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=3  --grid  -app "input/ver/$ADD_4"
#$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=2  --grid  -app "input/ver/$ADD_4"
#$PYTHON $SCRIPT "input/ver/$ADD_4" -lpp=4 -ppo=4 -et=1  --grid  -app "input/ver/$ADD_4"
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


#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -pit=16 -et=16  --grid  -app "input/ver/$ABS_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -pit=16 -et=14  --grid  -app "input/ver/$ABS_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -pit=16 -et=12  --grid  -app "input/ver/$ABS_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -pit=16 -et=10  --grid  -app "input/ver/$ABS_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -pit=16 -et=8  --grid  -app "input/ver/$ABS_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -pit=16 -et=6  --grid  -app "input/ver/$ABS_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -pit=16 -et=4  --grid  -app "input/ver/$ABS_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -pit=16 -et=2  --grid  -app "input/ver/$ABS_8"   --shared

#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=16  --grid  -app "input/ver/$ABS_8"
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=14  --grid  -app "input/ver/$ABS_8"
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=12  --grid  -app "input/ver/$ABS_8"
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=10  --grid  -app "input/ver/$ABS_8"
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=8  --grid  -app "input/ver/$ABS_8"
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=6  --grid  -app "input/ver/$ABS_8"
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=4  --grid  -app "input/ver/$ABS_8"
#$PYTHON $SCRIPT "input/ver/$ABS_8" -lpp=8 -ppo=8 -et=2  --grid  -app "input/ver/$ABS_8"



#$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -pit=16 -et=16  --grid  -app "input/ver/$ADD_8"  --shared
#$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -pit=16 -et=14  --grid  -app "input/ver/$ADD_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -pit=16 -et=12  --grid  -app "input/ver/$ADD_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -pit=16 -et=10  --grid  -app "input/ver/$ADD_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -pit=16 -et=8  --grid  -app "input/ver/$ADD_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -pit=16 -et=6  --grid  -app "input/ver/$ADD_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -pit=16 -et=4  --grid  -app "input/ver/$ADD_8"   --shared
#$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -pit=16 -et=2  --grid  -app "input/ver/$ADD_8"   --shared

$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -ppo=8 -et=16  --grid  -app "input/ver/$ADD_8"
$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -ppo=8 -et=14  --grid  -app "input/ver/$ADD_8"
$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -ppo=8 -et=12  --grid  -app "input/ver/$ADD_8"
$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -ppo=8 -et=10  --grid  -app "input/ver/$ADD_8"
$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -ppo=8 -et=8  --grid  -app "input/ver/$ADD_8"
$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -ppo=8 -et=6  --grid  -app "input/ver/$ADD_8"
$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -ppo=8 -et=4  --grid  -app "input/ver/$ADD_8"
$PYTHON $SCRIPT "input/ver/$ADD_8" -lpp=8 -ppo=8 -et=2  --grid  -app "input/ver/$ADD_8"