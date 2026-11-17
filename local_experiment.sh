#!/usr/bin/env bash
# Тот же прогон без Kubernetes — для проверки на своём компьютере: ./local_experiment.sh off | on
set -euo pipefail
MODE=${1:?usage: ./local_experiment.sh off|on}
export FAULT=${FAULT:-'{"delay_ms": 3000}'}
PY=${PY:-python}
mkdir -p results

PORT=8081 $PY dep.py & DEP=$!
PORT=8080 PATTERN=$MODE DEP_URL=http://127.0.0.1:8081 $PY core.py & CORE=$!
trap 'kill $DEP $CORE 2>/dev/null || true' EXIT
sleep 2

$PY loadgen.py > "results/local_$MODE.csv"
$PY metrics.py "results/local_$MODE.csv" | tee "results/local_$MODE.metrics.txt"
