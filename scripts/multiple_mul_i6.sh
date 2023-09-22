#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

MUL_6='mul_i6_o6.v'


IMAX=2
OMAX=1
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=28 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=24 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=20 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=12 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=8 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=4 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"

IMAX=2
OMAX=2
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=28 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=24 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=20 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=12 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=8 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=4 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"

IMAX=3
OMAX=1
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=28 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=24 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=20 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=12 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=8 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=4 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"

IMAX=3
OMAX=2
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=28 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=24 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=20 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=12 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=8 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=8 -ppo=8 -et=4 --subxpat --grid -iterations=16 -app "input/ver/$MUL_6" -imax="$IMAX" -omax="$OMAX"

