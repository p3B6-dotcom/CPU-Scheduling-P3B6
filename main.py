"""
CPU Scheduling Simulator - Group P3B6
Algorithms: FCFS and non-preemptive SJF
Input format: PID ARRIVAL BURST PRIORITY
"""

from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import sys


@dataclass(frozen=True)
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int
    order: int


@dataclass
class Result:
    process: Process
    start: int
    finish: int
    waiting: int
    turnaround: int
    response: int


def read_processes(file_path: str) -> list[Process]:
    """Read and validate processes from input.txt; ignore blank lines and comments."""
    processes = []
    seen = set()

    try:
        lines = Path(file_path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"Cannot open input file '{file_path}': {exc}") from exc

    for line_no, raw_line in enumerate(lines, start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) != 4:
            raise ValueError(
                f"Line {line_no}: expected 4 fields (PID ARRIVAL BURST PRIORITY), "
                f"but found {len(parts)}."
            )

        pid = parts[0]
        if pid in seen:
            raise ValueError(f"Line {line_no}: duplicate process ID '{pid}'.")
        seen.add(pid)

        try:
            arrival, burst, priority = map(int, parts[1:])
        except ValueError as exc:
            raise ValueError(f"Line {line_no}: arrival, burst and priority must be integers.") from exc

        if arrival < 0:
            raise ValueError(f"Line {line_no}: arrival time cannot be negative.")
        if burst <= 0:
            raise ValueError(f"Line {line_no}: burst time must be greater than zero.")

        processes.append(Process(pid, arrival, burst, priority, len(processes)))

    if not processes:
        raise ValueError("The input file contains no processes.")

    return processes


def simulate_fcfs(processes: list[Process]) -> list[Result]:
    """First Come, First Served: non-preemptive, ordered by arrival time."""
    ordered = sorted(processes, key=lambda p: (p.arrival, p.order))
    time = 0
    results = []

    for p in ordered:
        start = max(time, p.arrival)  # CPU may be idle before this process arrives.
        finish = start + p.burst
        results.append(Result(
            process=p,
            start=start,
            finish=finish,
            waiting=start - p.arrival,
            turnaround=finish - p.arrival,
            response=start - p.arrival
        ))
        time = finish

    return results


def simulate_sjf(processes: list[Process]) -> list[Result]:
    """
    Non-preemptive Shortest Job First.
    At each decision point, select the arrived process with the smallest burst.
    Ties: earlier arrival first, then original input order.
    """
    remaining = list(processes)
    time = 0
    results = []

    while remaining:
        ready = [p for p in remaining if p.arrival <= time]

        if not ready:
            # No process has arrived yet: move time to the next arrival.
            time = min(p.arrival for p in remaining)
            ready = [p for p in remaining if p.arrival <= time]

        chosen = min(ready, key=lambda p: (p.burst, p.arrival, p.order))
        start = time
        finish = start + chosen.burst

        results.append(Result(
            process=chosen,
            start=start,
            finish=finish,
            waiting=start - chosen.arrival,
            turnaround=finish - chosen.arrival,
            response=start - chosen.arrival
        ))

        time = finish
        remaining.remove(chosen)

    return results


def average(results: list[Result], field: str) -> float:
    return sum(getattr(r, field) for r in results) / len(results)


def make_timeline(results: list[Result]) -> list[tuple[str, int, int]]:
    """Return timeline segments as (label, start, finish), including CPU idle time."""
    segments = []
    cursor = 0

    for r in sorted(results, key=lambda item: item.start):
        if r.start > cursor:
            segments.append(("IDLE", cursor, r.start))
        segments.append((r.process.pid, r.start, r.finish))
        cursor = r.finish

    return segments


def print_gantt(results: list[Result], title: str) -> None:
    segments = make_timeline(results)
    print(f"\n{title} - GANTT CHART")
    print(" " + "------".join("+--------" for _ in segments) + "+")
    print(" " + "".join(f"|{label:^8}" for label, _, _ in segments) + "|")
    print(" " + "------".join("+--------" for _ in segments) + "+")
    print(f"{segments[0][1]:<9}", end="")
    for _, _, finish in segments:
        print(f"{finish:<9}", end="")
    print()


def print_results(results: list[Result], title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")
    print(f"{'PID':<8}{'Arrival':>10}{'Burst':>10}{'Start':>10}{'Finish':>10}"
          f"{'Waiting':>10}{'Turnaround':>12}{'Response':>10}")
    print("-" * 80)

    # Display in original process order, not execution order.
    for r in sorted(results, key=lambda item: item.process.order):
        p = r.process
        print(f"{p.pid:<8}{p.arrival:>10}{p.burst:>10}{r.start:>10}{r.finish:>10}"
              f"{r.waiting:>10}{r.turnaround:>12}{r.response:>10}")

    print("-" * 80)
    print(f"{'AVERAGE':<48}{average(results, 'waiting'):>10.2f}"
          f"{average(results, 'turnaround'):>12.2f}"
          f"{average(results, 'response'):>10.2f}")


def print_comparison(fcfs: list[Result], sjf: list[Result]) -> None:
    print("\n" + "=" * 58)
    print("ALGORITHM COMPARISON")
    print("=" * 58)
    print(f"{'Metric':<22}{'FCFS':>16}{'SJF':>16}")
    print("-" * 58)
    for label, field in [
        ("Average waiting", "waiting"),
        ("Average turnaround", "turnaround"),
        ("Average response", "response"),
    ]:
        print(f"{label:<22}{average(fcfs, field):>16.2f}{average(sjf, field):>16.2f}")

    fcfs_wait = average(fcfs, "waiting")
    sjf_wait = average(sjf, "waiting")
    if sjf_wait < fcfs_wait:
        print(f"\nSJF has the lower average waiting time by {fcfs_wait - sjf_wait:.2f} time units.")
    elif fcfs_wait < sjf_wait:
        print(f"\nFCFS has the lower average waiting time by {sjf_wait - fcfs_wait:.2f} time units.")
    else:
        print("\nBoth algorithms have the same average waiting time.")


def export_csv(results: list[Result], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "PID", "Arrival", "Burst", "Priority", "Start", "Finish",
            "Waiting", "Turnaround", "Response"
        ])
        for r in sorted(results, key=lambda item: item.process.order):
            p = r.process
            writer.writerow([
                p.pid, p.arrival, p.burst, p.priority, r.start, r.finish,
                r.waiting, r.turnaround, r.response
            ])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CPU Scheduling Simulator for Group P3B6 (FCFS vs non-preemptive SJF)."
    )
    parser.add_argument(
        "-i", "--input", default="input.txt",
        help="Path to input file (default: input.txt)"
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Export per-algorithm result tables to CSV files."
    )
    args = parser.parse_args()

    try:
        processes = read_processes(args.input)
        fcfs = simulate_fcfs(processes)
        sjf = simulate_sjf(processes)

        print("\nCPU SCHEDULING SIMULATOR | GROUP P3B6")
        print(f"Processes loaded: {len(processes)}")
        print("Algorithms: FCFS and non-preemptive SJF")

        print_results(fcfs, "FCFS")
        print_gantt(fcfs, "FCFS")
        print_results(sjf, "SJF (NON-PREEMPTIVE)")
        print_gantt(sjf, "SJF")
        print_comparison(fcfs, sjf)

        if args.export:
            export_csv(fcfs, "fcfs_results.csv")
            export_csv(sjf, "sjf_results.csv")
            print("\nCSV files created: fcfs_results.csv, sjf_results.csv")

    except ValueError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
