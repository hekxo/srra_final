# Вариант 29 — Автономные самосвалы карьера

Паттерн: **Bulkhead + приоритет команд**. Отказ: dep-a, задержка 3000 мс (R=4 = размер отсека телеметрии).

## Тесты (без кластера)
```bash
python -m unittest -v
```

## Эксперимент в Killercoda
```bash
git clone <репозиторий> && cd <папка>
kubectl create configmap code --from-file=dep.py --from-file=core.py --from-file=loadgen.py
kubectl apply -f stand.yaml
export FAULT='{"delay_ms": 3000}'
./experiment.sh off      # без паттерна -> results/off.csv
./experiment.sh on       # с паттерном  -> results/on.csv
```
Если код поменялся: `kubectl delete configmap code` и создать заново, затем `kubectl rollout restart deployment/core deployment/dep-a`.

Тот же прогон без Kubernetes: `./local_experiment.sh off` и `./local_experiment.sh on` (пишет results/local_*.csv).

## Метрики
```bash
python metrics.py results/off.csv
python metrics.py results/on.csv
```
Расчёты заданий 4–6: `python calc.py`. Отчёт: `report.pdf`.
