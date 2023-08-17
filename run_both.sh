#!/bin/bash

BENCH=$1
LPP=$2
PPO=$3
PIT=$4



python3 main.py $BENCH -lpp=$2 -pit=$4 --all --shared --clean --multiple -tt=1800
python3 main.py $BENCH -lpp=$2 -ppo=$3 --multiple -tt=188
