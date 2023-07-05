#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

BENCH=$1

for LPP in {1..4}
do
  for PPO in {1..4}
  do
    for ET in {0..8}
    do
      $PYTHON $SCRIPT $BENCH -et=$ET -lpp=$LPP -ppo=$PPO
    done
  done
done

for ET in {0..8}
do
  $PYTHON $SCRIPT $BENCH -et=$ET -lpp=0 -ppo=1
done