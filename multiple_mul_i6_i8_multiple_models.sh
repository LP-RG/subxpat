#!/bin/bash

PYTHON='python3'
SCRIPT='main.py'

MUL_6='mul_i6_o6.v'
for SIZE in 1 2 3 4 5 10 15 20 25 30 35 40 45 50
do
  $PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=6 -pit=6 -et=32 --subxpat --grid -iterations=12 -app "input/ver/$MUL_6" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=6 -pit=6 -et=28 --subxpat --grid -iterations=12 -app "input/ver/$MUL_6" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=6 -pit=6 -et=24 --subxpat --grid -iterations=12 -app "input/ver/$MUL_6" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=6 -pit=6 -et=20 --subxpat --grid -iterations=12 -app "input/ver/$MUL_6" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=6 -pit=6 -et=16 --subxpat --grid -iterations=12 -app "input/ver/$MUL_6" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=6 -pit=6 -et=12 --subxpat --grid -iterations=12 -app "input/ver/$MUL_6" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=6 -pit=6 -et=8 --subxpat --grid -iterations=12 -app "input/ver/$MUL_6" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_6" -lpp=6 -pit=6 -et=4 --subxpat --grid -iterations=12 -app "input/ver/$MUL_6" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
done

MUL_8='mul_i8_o8.v'
for SIZE in 1 2 3 4 5 10 15 20 25 30 35 40 45 50
do
  $PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -pit=8 -et=128 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -pit=8 -et=112 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -pit=8 -et=96 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -pit=8 -et=80 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -pit=8 -et=64 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -pit=8 -et=48 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -pit=8 -et=32 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
  $PYTHON $SCRIPT "input/ver/$MUL_8" -lpp=8 -pit=8 -et=16 --subxpat --grid -iterations=16 -app "input/ver/$MUL_8" -mode=3 -subgraphsize="$SIZE" -population=4 -num_models=10 --shared
done
