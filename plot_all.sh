#!/bin/bash


#BENCH='adder_i4_o3.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#BENCH='adder_i6_o4.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#BENCH='adder_i8_o5.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#BENCH='adder_i10_o6.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#
#BENCH='abs_diff_i4_o3.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#BENCH='abs_diff_i6_o4.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#BENCH='abs_diff_i8_o5.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#BENCH='abs_diff_i10_o6.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#
#BENCH='mul_i4_o4.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#BENCH='mul_i6_o6.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#BENCH='mul_i8_o8.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#BENCH='mul_i10_o10.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
#
#BENCH='madd_i6_o4.v'
#python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot
BENCH='madd_i9_o6.v'
python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot


BENCH='sad_i10_o3.v'
python3 main.py "input/ver/$BENCH" -app "input/ver/$BENCH"  --plot