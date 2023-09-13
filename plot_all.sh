#!/bin/bash

python3 main.py input/ver/mul_i4_o4.v -app input/ver/mul_i4_o4.v  -lpp=4 -ppo=4 -et=8 -iterations=3 --grid --subxpat   -imax=2 -omax=1  --multiple --plot
python3 main.py input/ver/mul_i8_o8.v -app input/ver/mul_i8_o8.v  -lpp=4 -ppo=4 -et=8 -iterations=3 --grid --subxpat   -imax=2 -omax=1  --multiple --plot
python3 main.py input/ver/mul_i12_o12.v -app input/ver/mul_i12_o12.v  -lpp=4 -ppo=4 -et=8 -iterations=3 --grid --subxpat   -imax=2 -omax=1  --multiple --plot

python3 main.py input/ver/madd_i9_o6.v -app input/ver/madd_i9_o6.v  -lpp=4 -ppo=4 -et=8 -iterations=3 --grid --subxpat   -imax=2 -omax=1  --multiple --plot

python3 main.py input/ver/adder_i8_o5.v -app input/ver/adder_i8_o5.v  -lpp=4 -ppo=4 -et=8 -iterations=3 --grid --subxpat   -imax=2 -omax=1  --multiple --plot
python3 main.py input/ver/adder_i12_o7.v -app input/ver/adder_i12_o7.v  -lpp=4 -ppo=4 -et=8 -iterations=3 --grid --subxpat   -imax=2 -omax=1  --multiple --plot

python3 main.py input/ver/abs_diff_i8_o5.v -app input/ver/abs_diff_i8_o5.v  -lpp=4 -ppo=4 -et=8 -iterations=3 --grid --subxpat   -imax=2 -omax=1  --multiple --plot
python3 main.py input/ver/abs_diff_i4_o3.v -app input/ver/abs_diff_i4_o3.v  -lpp=4 -ppo=4 -et=8 -iterations=3 --grid --subxpat   -imax=2 -omax=1  --multiple --plot

python3 main.py input/ver/sad_i10_o3.v -app input/ver/sad_i10_o3.v  -lpp=4 -ppo=4 -et=8 -iterations=3 --grid --subxpat   -imax=2 -omax=1  --multiple --plot


