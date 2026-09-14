"""Final local acceptance audit; no provider calls and no secret values printed."""

import hashlib
import json
import os
from pathlib import Path

from xray.collector import read_jsonl, write_json
from xray.graph_builder import episodes


def main():
    root = Path("artifacts")
    comparison = json.loads((root / "xray/comparison.json").read_text())
    assert comparison["broken"]["status"] == "FAIL"
    assert comparison["fixed"]["status"] == "PASS"
    totals = {}
    task_sets = []
    for variant in ("broken", "fixed"):
        side = "baseline" if variant == "broken" else "fixed"
        rows = read_jsonl(root / side / "eval.jsonl")
        groups = episodes(rows)
        assert len(groups) == 6 and {r.source for r in rows} == {"model"}
        task_sets.append({r.task_id for r in rows})
        summary = json.loads((root / side / "eval_summary.json").read_text())
        assert summary["errors"] == [] and summary["usage"]["prompt_tokens"] > 0
        assert summary["provider_usage"]["prompt_tokens"] == summary["usage"]["prompt_tokens"]
        report = json.loads((root / "xray" / f"{variant}_report.json").read_text())
        data_path = root / "trajectories" / f"{variant}_env.jsonl"
        assert report["input_sha256"] == hashlib.sha256(data_path.read_bytes()).hexdigest()
        assert report["provenance"] == {"model": 6, "scripted_probe": 7}
        totals[variant] = {
            "model_episodes": len(groups),
            "model_transitions": len(rows),
            "health": report["health"],
            "status": report["status"],
        }
    assert task_sets[0] == task_sets[1]
    screenshots = json.loads((root / "screenshots/manifest.json").read_text())
    assert len(screenshots) == 6
    for item in screenshots:
        assert (root / "screenshots" / item["file"]).stat().st_size > 1000
    for path in root.rglob("traces.jsonl"):
        content = path.read_text()
        assert '"reasoning_content"' not in content, str(path)
    secret_values = [
        value.encode()
        for name, value in os.environ.items()
        if ("API_KEY" in name or "TOKEN" in name) and len(value) >= 20
    ]
    for folder in (
        Path("artifacts"),
        Path("environments/support_preflight/support_preflight"),
        Path("xray"),
    ):
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix in (
                ".json",
                ".jsonl",
                ".html",
                ".md",
                ".py",
                ".toml",
            ):
                blob = path.read_bytes()
                assert not any(secret in blob for secret in secret_values), (
                    f"Secret detected in {path}"
                )
    result = {
        "acceptance": "PASS",
        "matched_task_ids": sorted(task_sets[0]),
        "model_and_probe_evidence_separated": True,
        "screenshots": len(screenshots),
        "secret_scan": "no configured API key/token values found in inspected artifacts/source",
        "native_reasoning_redacted": True,
        "results": totals,
        "scope": "Local acceptance; no training, no Hub push, no safety certification",
    }
    write_json(root / "acceptance.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
