#!/usr/bin/env bash
# Один прогон: ./experiment.sh off | on   (FAULT задаётся заранее: export FAULT='{"delay_ms": 3000}')
set -euo pipefail
MODE=${1:?usage: ./experiment.sh off|on}
FAULT=${FAULT:-'{"delay_ms": 3000}'}
mkdir -p results

kubectl set env deployment/core PATTERN="$MODE"
kubectl rollout status deployment/core --timeout=120s
kubectl rollout status deployment/dep-a --timeout=120s

kubectl delete job load --ignore-not-found
sed "s|__FAULT__|$FAULT|" load-job.yaml | kubectl apply -f -
kubectl wait --for=condition=complete job/load --timeout=300s
kubectl logs job/load > "results/$MODE.csv"

python3 metrics.py "results/$MODE.csv" | tee "results/$MODE.metrics.txt"
