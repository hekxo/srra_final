"""Тесты паттерна Bulkhead + приоритет команд — без кластера и без сети."""
import threading, time, unittest
import core

ORIGINAL_CALL_DEP = core.call_dep


def slow_dep(kind="telemetry", timeout=10.0):
    time.sleep(min(timeout, 3.0))          # dep-a тормозит на 3 с (отказ варианта 29)
    raise TimeoutError("dep-a timeout")


def ok_dep(kind="telemetry", timeout=10.0):
    return {"status": "ok"}


class BulkheadTest(unittest.TestCase):
    def setUp(self):
        core.PATTERN = True
        core.TIMEOUT, core.STOP_TIMEOUT = 1.0, 0.3
        core.telemetry_pool = threading.BoundedSemaphore(4)
        core.stop_pool = threading.BoundedSemaphore(8)

    def tearDown(self):
        core.call_dep = ORIGINAL_CALL_DEP

    def test_stop_is_fast_when_dep_is_slow(self):
        core.call_dep = slow_dep
        start = time.time()
        r = core.do_work("stop")
        self.assertLess(time.time() - start, 1.5)
        self.assertEqual(r["status"], "stopped_local")

    def test_stop_works_when_telemetry_bulkhead_is_full(self):
        core.call_dep = slow_dep
        for _ in range(4):                  # занимаем все 4 слота телеметрии
            core.telemetry_pool.acquire()
        with self.assertRaises(core.Rejected):
            core.do_work("telemetry")
        start = time.time()
        self.assertEqual(core.do_work("stop")["status"], "stopped_local")
        self.assertLess(time.time() - start, 1.5)

    def test_telemetry_rejected_fast_when_bulkhead_full(self):
        core.call_dep = slow_dep
        errors = []
        def worker():
            try:
                core.do_work("telemetry")
            except Exception as e:
                errors.append(e)
        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        time.sleep(0.1)                     # 4 потока заняли отсек
        start = time.time()
        with self.assertRaises(core.Rejected):
            core.do_work("telemetry")
        self.assertLess(time.time() - start, 0.1)
        for t in threads:
            t.join()

    def test_slot_released_after_dep_error(self):
        core.call_dep = slow_dep
        core.telemetry_pool = threading.BoundedSemaphore(1)
        with self.assertRaises(TimeoutError):
            core.do_work("telemetry")
        core.call_dep = ok_dep
        self.assertEqual(core.do_work("telemetry")["status"], "ok")

    def test_normal_dep_gives_normal_answer(self):
        core.call_dep = ok_dep
        self.assertEqual(core.do_work("stop")["status"], "ok")
        self.assertEqual(core.do_work("telemetry")["status"], "ok")

    def test_pattern_off_calls_dep_directly(self):
        core.PATTERN = False
        calls = []
        core.call_dep = lambda kind="telemetry", timeout=10.0: calls.append((kind, timeout)) or {"status": "ok"}
        core.do_work("stop")
        self.assertEqual(calls, [("stop", 10.0)])


if __name__ == "__main__":
    unittest.main()
