#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

BENCH=$1

for LPP in {1..4}
do
  for PPO in {1..4}
  do
    for ET in {2..2}
    do
      for PAP in {10..90..10}
      do
        $PYTHON $SCRIPT $BENCH -et=$ET -lpp=$LPP -ppo=$PPO -pap=$PAP
      done
    done
  done
done
