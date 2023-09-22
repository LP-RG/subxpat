#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

ADDER_6='adder_i6_o4.v'


IMAX=2
OMAX=1
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=8 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=7 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=6 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=5 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=4 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=3 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=2 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=1 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"


IMAX=2
OMAX=2
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=8 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=7 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=6 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=5 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"

$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=4 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=3 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=2 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$ADDER_6" -lpp=10 -ppo=10 -et=1 --subxpat --grid -iterations=12 -app "input/ver/$ADDER_6" -imax="$IMAX" -omax="$OMAX"

