"""«Пользователи»: 20 запросов/с, ожидание ответа не дольше 1,5 с.
Каждый 5-й запрос — аварийная остановка (kind=stop), остальные — телеметрия.
На 30-й секунде ломает dep-a (FAULT), на 60-й — восстанавливает. CSV пишет в stdout."""
import json, os, sys, threading, time, urllib.request, urllib.error

CORE_URL = os.environ.get("CORE_URL", "http://127.0.0.1:8080")
DEP_URL = os.environ.get("DEP_URL", "http://127.0.0.1:8081")
FAULT = os.environ.get("FAULT", '{"delay_ms": 3000}')
RPS = int(os.environ.get("RPS", "20"))
DURATION = int(os.environ.get("DURATION_S", "90"))
FAULT_FROM, FAULT_TO = int(os.environ.get("FAULT_FROM_S", "30")), int(os.environ.get("FAULT_TO_S", "60"))
CLIENT_TIMEOUT = 1.5

rows, lock = [], threading.Lock()


def set_fault(body):
    req = urllib.request.Request(f"{DEP_URL}/fault", data=body.encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5).read()


def one(i, t0):
    kind = "stop" if i % 5 == 0 else "telemetry"
    start = time.time()
    try:
        with urllib.request.urlopen(f"{CORE_URL}/work?kind={kind}", timeout=CLIENT_TIMEOUT) as r:
            r.read()
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception:
        code = 0                                   # клиент не дождался ответа (таймаут 1,5 с)
    lat = (time.time() - start) * 1000
    with lock:
        rows.append((start - t0, kind, code, lat))


def main():
    set_fault("{}")
    t0 = time.time()
    threads, fault_on, fault_off = [], False, False
    for i in range(RPS * DURATION):
        target = t0 + i / RPS
        now = time.time()
        if target > now:
            time.sleep(target - now)
        el = time.time() - t0
        if not fault_on and el >= FAULT_FROM:
            set_fault(FAULT); fault_on = True
        if not fault_off and el >= FAULT_TO:
            set_fault("{}"); fault_off = True
        th = threading.Thread(target=one, args=(i, t0)); th.start(); threads.append(th)
    for th in threads:
        th.join()
    set_fault("{}")
    out = sys.stdout
    out.write("t,kind,code,latency_ms\n")
    for t, kind, code, lat in sorted(rows):
        out.write(f"{t:.3f},{kind},{code},{lat:.1f}\n")


if __name__ == "__main__":
    main()
