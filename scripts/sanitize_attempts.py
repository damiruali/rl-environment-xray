"""One-time allowlist redaction of early failed setup runs; keep failures, not reasoning.

Never run on an active evaluation. This is not used to select favourable rollouts.
The listed runs predate the non-editable packaging fix and final paired experiment.
"""

import json
from pathlib import Path

from xray.collector import write_json

EARLY = ["smoke", "smoke-local", "smoke-v1", "broken-smoke", "broken-smoke-qwen"]


def main():
    results = []
    for name in EARLY:
        path = Path("artifacts/prime") / name / "traces.jsonl"
        if not path.exists():
            continue
        records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        sanitized = []
        for record in records:
            if record.get("redacted"):
                sanitized.append(record)
                continue
            for trace in record.get("traces", [record]):
                sanitized.append(
                    {
                        "redacted": True,
                        "excluded_from_baseline": True,
                        "ok": trace.get("ok"),
                        "model": trace.get("agent", {}).get("config", {}).get("model"),
                        "error_types": [e.get("type") for e in trace.get("errors", [])],
                        "actions": [
                            call.get("name")
                            for node in trace.get("nodes", [])
                            for call in node.get("message", {}).get("tool_calls", [])
                        ],
                        "usage": {
                            key: sum(
                                call.get("usage", {}).get(key, 0) or 0
                                for call in trace.get("calls", [])
                            )
                            for key in ("prompt_tokens", "completion_tokens", "reasoning_tokens")
                        },
                    }
                )
        path.write_text("".join(json.dumps(record) + "\n" for record in sanitized))
        results.append({"run": name, "records": sanitized})
    write_json(
        Path("artifacts/initial_attempts.json"),
        {
            "excluded_from_final_comparison": True,
            "reason": "Cloud default, missing tool-server entrypoint, provider errors, then macOS hidden .pth imports; documented engineering attempts, not training results.",
            "runs": results,
        },
    )


if __name__ == "__main__":
    main()
