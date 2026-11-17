"""Метрики по CSV прогона: POFOD, ROCOF, AVAIL, p50/p95/p99.
Использование: python metrics.py results/off.csv"""
import csv, math, sys

EPISODE_GAP_S = 2.0   # ошибки с промежутком < 2 с — один эпизод отказа


def load(path):
    with open(path, newline="") as f:
        return [{"t": float(r["t"]), "kind": r.get("kind", ""), "code": int(r["code"]),
                 "latency_ms": float(r["latency_ms"])} for r in csv.DictReader(f)]


def percentile(values, p):
    s = sorted(values)
    return s[max(1, math.ceil(p * len(s))) - 1]          # элемент № ⌈p·n⌉


def compute(rows):
    n = len(rows)
    failed = [r for r in rows if r["code"] != 200]
    pofod = len(failed) / n

    episodes, last = 0, None
    for r in sorted(failed, key=lambda r: r["t"]):
        if last is None or r["t"] - last >= EPISODE_GAP_S:
            episodes += 1
        last = r["t"]

    first, end = int(min(r["t"] for r in rows)), int(max(r["t"] for r in rows))
    seconds = end - first + 1
    rocof = episodes / (seconds / 3600)

    ok_seconds = {int(r["t"]) for r in rows if r["code"] == 200}
    avail = len(ok_seconds) / seconds

    lat = [r["latency_ms"] for r in rows]
    return {"n": n, "failed": len(failed), "pofod": pofod, "episodes": episodes, "rocof": rocof,
            "avail": avail, "p50": percentile(lat, .50), "p95": percentile(lat, .95), "p99": percentile(lat, .99)}


def fmt(name, m):
    return (f"{name}: n={m['n']} failed={m['failed']} POFOD={m['pofod']:.4f} episodes={m['episodes']} "
            f"ROCOF={m['rocof']:.0f}/h AVAIL={m['avail']:.4f} "
            f"p50/p95/p99={m['p50']:.0f}/{m['p95']:.0f}/{m['p99']:.0f} ms")


if __name__ == "__main__":
    rows = load(sys.argv[1])
    print(fmt("all", compute(rows)))
    for kind in sorted({r["kind"] for r in rows if r["kind"]}):
        print(fmt(kind, compute([r for r in rows if r["kind"] == kind])))
