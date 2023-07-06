#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

BENCH=$1

done

for ET in {2..2}
do
  for PAP in {10..90..10}
      do

        $PYTHON $SCRIPT $BENCH -et=$ET -lpp=0 -ppo=1 -pap=$PAP
    done
done