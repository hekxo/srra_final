"""core: диспетчерская автономных самосвалов (вариант 29).
Ключевая функция — аварийная остановка (kind=stop). Остальные запросы — телеметрия (kind=telemetry).
Паттерн варианта: Bulkhead + приоритет команд."""
import json, os, threading, urllib.request
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PATTERN = os.environ.get("PATTERN", "off") == "on"
DEP_URL = os.environ.get("DEP_URL", "http://127.0.0.1:8081")
BULKHEAD_SIZE = int(os.environ.get("BULKHEAD_SIZE", "4"))      # R=4: одновременных вызовов dep-a для телеметрии
STOP_POOL_SIZE = int(os.environ.get("STOP_POOL_SIZE", "8"))    # отдельный отсек для аварийной остановки
TIMEOUT = float(os.environ.get("TIMEOUT_S", "1.0"))            # таймаут телеметрии
STOP_TIMEOUT = float(os.environ.get("STOP_TIMEOUT_S", "0.3"))  # таймаут команды остановки


class Rejected(Exception):
    """Отсек переполнен — запрос отклонён сразу (503)."""


def call_dep(kind="telemetry", timeout=10.0):
    with urllib.request.urlopen(f"{DEP_URL}/work?kind={kind}", timeout=timeout) as r:
        return json.loads(r.read())


telemetry_pool = threading.BoundedSemaphore(BULKHEAD_SIZE)
stop_pool = threading.BoundedSemaphore(STOP_POOL_SIZE)


def do_work(kind="telemetry"):
    if not PATTERN:
        return call_dep(kind)                       # все запросы ждут dep-a до 10 с

    # Приоритет: аварийная остановка — в своём отсеке и никогда не ждёт dep-a дольше STOP_TIMEOUT
    if kind == "stop":
        if not stop_pool.acquire(blocking=False):
            return {"status": "stopped_local"}
        try:
            return call_dep(kind, timeout=STOP_TIMEOUT)
        except Exception:
            return {"status": "stopped_local"}      # команда уходит на борт напрямую, без dep-a
        finally:
            stop_pool.release()

    # Bulkhead: телеметрия занимает не больше BULKHEAD_SIZE слотов, лишнее отклоняется сразу
    if not telemetry_pool.acquire(blocking=False):
        raise Rejected()
    try:
        return call_dep(kind, timeout=TIMEOUT)
    finally:
        telemetry_pool.release()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except ConnectionError:
            pass                                    # клиент уже ушёл по своему таймауту

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/healthz":                  # readiness/liveness: только сам процесс, dep-a не проверяем
            return self._send(200, {"ok": True})
        kind = parse_qs(url.query).get("kind", ["telemetry"])[0]
        try:
            self._send(200, do_work(kind))
        except Rejected:
            self._send(503, {"status": "rejected"})
        except Exception as e:
            self._send(500, {"status": "error", "detail": str(e)})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"core: PATTERN={'on' if PATTERN else 'off'} BULKHEAD_SIZE={BULKHEAD_SIZE}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
