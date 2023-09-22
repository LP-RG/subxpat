#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

SAD_10='sad_i10_o3.v'


IMAX=2
OMAX=1
$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=4 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=3 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=2 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=1 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"


IMAX=2
OMAX=2

$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=4 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=3 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=2 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=1 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"


IMAX=3
OMAX=1
$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=4 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=3 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=2 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"
$PYTHON $SCRIPT "input/ver/$SAD_10" -lpp=10 -ppo=10 -et=1 --subxpat --grid -iterations=20 -app "input/ver/$SAD_10" -imax="$IMAX" -omax="$OMAX"
