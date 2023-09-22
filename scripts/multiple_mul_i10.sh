#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

MUL_10='mul_i10_o10.v'


IMAX=2
OMAX=1
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=512 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=448 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=384 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=320 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=256 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=192 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=128 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=64 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"

IMAX=2
OMAX=2
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=512 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=448 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=384 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=320 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=256 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=192 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=128 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_10" -lpp=10 -ppo=10 -et=64 --subxpat --grid -iterations=20 -app "input/ver/$MUL_10" -imax="$IMAX" -omax="$OMAX"
