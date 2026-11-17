"""dep-a: зависимость системы (модуль планирования диспетчерской).
Ломается по команде: POST /fault с JSON {"delay_ms": 3000} | {"error_rate": 0.3} | {"unavailable": true};
POST /fault с {} — восстановление."""
import json, os, random, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

FAULT = {}


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
        if self.path.startswith("/healthz"):
            return self._send(200, {"ok": True})
        f = dict(FAULT)
        if f.get("unavailable"):
            return self._send(503, {"status": "unavailable"})
        if f.get("delay_ms"):
            time.sleep(f["delay_ms"] / 1000)
        if random.random() < f.get("error_rate", 0):
            return self._send(500, {"status": "error"})
        self._send(200, {"status": "ok"})

    def do_POST(self):
        global FAULT
        n = int(self.headers.get("Content-Length", 0))
        FAULT = json.loads(self.rfile.read(n) or b"{}")
        print("fault set:", FAULT, flush=True)
        self._send(200, {"fault": FAULT})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8081"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
