#!/usr/bin/env bash
set -e
mkdir -p results
> results/times_par.csv || true
for n in 1 2 4 8; do
  for rep in 1 2 3; do
    echo "Running with $n cores (rep $rep)"
    mpiexec -n $n python parallel.py
  done
done
python ../scripts/plot_speedup.py ../results/times_par.csv ../results/times_seq.csv
