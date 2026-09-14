import argparse
import sys
from pathlib import Path

from xray.report import save_report, scan


def main():
    parser = argparse.ArgumentParser(description="RL Environment X-Ray — pre-flight diagnostics")
    subs = parser.add_subparsers(dest="command", required=True)
    scan_cmd = subs.add_parser("scan", help="Scan one environment version; FAIL exits 1, REVIEW 2")
    scan_cmd.add_argument("trajectory", type=Path)
    scan_cmd.add_argument("--output", type=Path)
    scan_cmd.add_argument("--experimental-hodge", action="store_true")
    demo = subs.add_parser(
        "demo", help="Offline replay by default; --live makes small paid API calls"
    )
    demo.add_argument("--live", action="store_true")
    demo.add_argument("--output", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    try:
        if args.command == "demo":
            from xray.demo import run

            run(args.output, args.live)
            return 0
        report = scan(args.trajectory, args.experimental_hodge)
        output = args.output or args.trajectory.with_suffix(".report")
        save_report(report, output)
        print(f"RL ENVIRONMENT X-RAY — {report['environment']}")
        print(f"{report['health']}/100 | {report['status']} | {report['decision']}")
        for finding in report["findings"]:
            print(f"{finding['severity']}: {finding['title']}")
        print(
            f"Observed: {report['coverage']['states']} states / {report['coverage']['transitions']} transitions. Total coverage unknown."
        )
        print(f"HTML: {output.with_suffix('.html')}")
        return {"PASS": 0, "FAIL": 1, "REVIEW": 2}[report["status"]]
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
