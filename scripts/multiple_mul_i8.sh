#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

MUL_8='mul_i8_o8.v'


IMAX=2
OMAX=1
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=128 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=112 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=96 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=80 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=64 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=48 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"


IMAX=2
OMAX=2
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=128 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=112 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=96 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=80 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=64 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=48 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"


IMAX=3
OMAX=1
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=128 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=112 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=96 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=80 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=64 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=48 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

IMAX=3
OMAX=2
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=128 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=112 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=96 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=80 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=64 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=48 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

IMAX=3
OMAX=3
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=128 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=112 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=96 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=80 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=64 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=48 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

IMAX=4
OMAX=1
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=128 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=112 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=96 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=80 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=64 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=48 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

IMAX=4
OMAX=2
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=128 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=112 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=96 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=80 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=64 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=48 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

IMAX=4
OMAX=3
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=128 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=112 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=96 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=80 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=64 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=48 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -ppo=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -imax="$IMAX" -omax="$OMAX"