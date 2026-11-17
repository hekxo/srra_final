"""Проверка metrics.py на примере из задания: 20 запросов за 10 с -> 0,30 / 360 / 0,70."""
import unittest
import metrics


class MetricsExampleTest(unittest.TestCase):
    def test_example_from_assignment(self):
        m = metrics.compute(metrics.load("results/example.csv"))
        self.assertAlmostEqual(m["pofod"], 0.30)
        self.assertEqual(m["episodes"], 1)
        self.assertAlmostEqual(m["rocof"], 360)
        self.assertAlmostEqual(m["avail"], 0.70)
        self.assertEqual((m["p50"], m["p95"], m["p99"]), (45, 1003, 1004))


if __name__ == "__main__":
    unittest.main()
