#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

MUL_12='mul_i12_o12.v'


IMAX=2
OMAX=1
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=2048 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=1792 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=1536 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=1280 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=1024 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=768 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=512 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=256 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"

IMAX=2
OMAX=2
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=2048 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=1792 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=1536 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=1280 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=1024 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=768 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=512 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$MUL_12" -lpp=10 -ppo=10 -et=256 --subxpat --grid -iterations=24 -app "input/ver/$MUL_12" -imax="$IMAX" -omax="$OMAX"
