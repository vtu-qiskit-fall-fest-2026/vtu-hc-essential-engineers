"""Run the Nirikshak monitor on a telemetry file.

    python -m nirikshak.monitor --demo results/monitor_demo.jsonl   # write the demo network's telemetry
    python -m nirikshak.monitor results/monitor_demo.jsonl          # monitor it: status and alarm log
"""

from __future__ import annotations

import argparse
from pathlib import Path

from nirikshak.monitor import NetworkMonitor, read_jsonl, write_jsonl
from nirikshak.monitor.synthetic import demo_network

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="telemetry file (JSON Lines)")
    ap.add_argument("--demo", action="store_true", help="write the demo network's telemetry to PATH and exit")
    ap.add_argument("--alpha", type=float, default=0.05, help="false-alarm budget per link and window")
    ap.add_argument("--window", type=int, default=20, help="key blocks per verdict window")
    args = ap.parse_args()

    if args.demo:
        records, links = demo_network(ROOT / "data" / "hardware")
        n = write_jsonl(records, args.path)
        print(f"wrote {n} records for {len(links)} links to {args.path}")
        print(links.to_string(index=False))
        return

    mon = NetworkMonitor(alpha=args.alpha, window=args.window).run(read_jsonl(args.path))
    print("== Link status")
    print(mon.status().to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    log = mon.alarm_log()
    print(f"\n== Alarm log ({len(log)} alarms, budget {args.alpha:.0%} per link and window)")
    if len(log):
        print(log[["link_id", "t_start", "t_end", "key_qber", "ref_qber", "p_value", "blocks_flagged"]]
              .to_string(index=False, float_format=lambda x: f"{x:.4f}"))


if __name__ == "__main__":
    main()
