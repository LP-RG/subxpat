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
T=$6

echo $PYTHON $SCRIPT $BENCH -et=$ET -lpp=0 -ppo=1 -pap=$PAP
timeout $T $PYTHON $SCRIPT $BENCH -et=$ET -lpp=0 -ppo=1 -pap=$PAP
if (($? == 0));
  then
    FOUND='SAT'
    SAT_LPP=$LPP
    SAT_PPO=$PPO
    echo "$FOUND at (0, 1)"
    exit
fi

for (( PPO=1; PPO<=$MAX_PPO; PPO++ ))
do
  for (( LPP=1; LPP<=$MAX_LPP; LPP++ ))
  do
  echo $PYTHON $SCRIPT $BENCH -et=$ET -lpp=$LPP -ppo0=$PPO -pap=$PAP
  timeout $T $PYTHON $SCRIPT $BENCH -et=$ET -lpp=$LPP -ppo=$PPO -pap=$PAP

  if (($? == 0));
  then
    FOUND='SAT'
    SAT_LPP=$LPP
    SAT_PPO=$PPO
    echo "$FOUND at ($LPP, $PPO)"

    break 2
  fi




  done
done

echo "exploring the non-dominating cells..."
for (( LPP=$SAT_LPP-1; LPP>0; LPP-- ))
do
  for (( PPO=$SAT_PPO; PPO<=$MAX_PPO; PPO++ ))
  do
  echo $PYTHON $SCRIPT $BENCH -et=$ET -lpp=$LPP -ppo=$PPO -pap=$PAP
  timeout $T $PYTHON $SCRIPT $BENCH -et=$ET -lpp=$LPP -ppo=$PPO -pap=$PAP
  done
done


