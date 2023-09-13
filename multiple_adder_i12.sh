#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

ADDER_12='adder_i12_o7.v'


IMAX=2
OMAX=1
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=64 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=56 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=48 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=40 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=32 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=24 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=16 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=8 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"



IMAX=2
OMAX=2
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=64 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=56 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=48 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=40 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=32 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=24 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=16 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_12" -lpp=10 -ppo=10 -et=8 --subxpat --grid -iterations=24 -app "input/ver/$ADDER_12" -imax="$IMAX" -omax="$OMAX"

