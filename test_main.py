import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from main import Process, read_processes, simulate_fcfs, simulate_sjf, average


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.processes = [
            Process("P1", 0, 8, 4, 0),
            Process("P2", 3, 9, 4, 1),
            Process("P3", 5, 4, 3, 2),
            Process("P4", 8, 9, 3, 3),
            Process("P5", 10, 7, 1, 4),
            Process("P6", 11, 7, 4, 5),
        ]

    def test_fcfs_average_waiting(self):
        results = simulate_fcfs(self.processes)
        self.assertAlmostEqual(average(results, "waiting"), 12.6666666667)

    def test_sjf_execution_order(self):
        results = simulate_sjf(self.processes)
        order = [r.process.pid for r in results]
        self.assertEqual(order, ["P1", "P3", "P5", "P6", "P2", "P4"])

    def test_sjf_average_waiting(self):
        results = simulate_sjf(self.processes)
        self.assertAlmostEqual(average(results, "waiting"), 10.5)

    def test_idle_time_is_handled(self):
        processes = [
            Process("A", 3, 2, 1, 0),
            Process("B", 8, 1, 1, 1),
        ]
        results = simulate_fcfs(processes)
        self.assertEqual([(r.start, r.finish) for r in results], [(3, 5), (8, 9)])

    def test_input_reader(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "input.txt"
            path.write_text("# comment\nA 0 3 2\nB 2 4 1\n", encoding="utf-8")
            processes = read_processes(str(path))
            self.assertEqual(len(processes), 2)
            self.assertEqual(processes[1].pid, "B")


if __name__ == "__main__":
    unittest.main()
