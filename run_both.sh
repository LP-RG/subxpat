#!/bin/bash

BENCH=$1
LPP=$2
PPO=$3
PIT=$4



python3 main.py "$BENCH" -lpp="$LPP" -pit="$PIT" --all --shared --clean --multiple -tt=1800
python3 main.py "$BENCH" -lpp="$LPP" -ppo="$PPO" --multiple -tt=1800

python3 main.py "$BENCH" -lpp="$LPP" -ppo="$PPO" -pit="$PIT" --plot


