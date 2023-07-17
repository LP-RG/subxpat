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
===================================="

BENCH=$1
MAX_LPP=$2
MAX_PPO=$3
ET=$4
PAP=$5

for (( LPP=1; LPP<=$MAX_LPP; LPP++ ))
do
  for (( PPO=1; PPO<=$MAX_PPO; PPO++ ))
  do
  echo $PYTHON $SCRIPT $BENCH -et=$ET -lpp=$LPP -ppo=$PPO -pap=$PAP
  $PYTHON $SCRIPT $BENCH -et=$ET -lpp=$LPP -ppo=$PPO -pap=$PAP

  done
done

