#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

echo -e "====================================
USAGE:
1- benchmark-path input/ver/abs_diff_i4_o3.ver
2- Maximum LPP; e.g., 4
3- Maximum PPO; e.g., 4
4- ET; e.g., 2
5- Partitioning-Percentage; e.g., 10
6- Timeout in seconds; e.g., 3600
===================================="


BENCH=$1
MAX_LPP=$2
MAX_PPO=$3
ET=$4
PAP=$5



for (( ET=1; PPO<=$MAX_PPO; PPO++ ))
do
  echo $PYTHON $SCRIPT $BENCH -et=$ET -lpp=$MAX_LPP -ppo0=$MAX_PPO -pap=$PAP --grid --subxpat
done