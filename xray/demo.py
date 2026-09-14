"""Reproducible paired experiment; model evidence and scripted probes stay separate."""

from __future__ import annotations

import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path

from support_preflight.environment import Scenario, SupportEnvironment

from xray.collector import read_jsonl, write_json, write_jsonl
from xray.models import Transition
from xray.report import save_report, scan

MODEL = "qwen/qwen3.8-27b"


def probes(variant: str) -> list[Transition]:
    fixtures = [
        ("repeat-policy", False, ["check_refund_policy"] * 6),
        ("repeat-search", False, ["search_knowledge_base"] * 6),
        ("premature-close", False, ["resolve_ticket"]),
        (
            "hidden-auto",
            False,
            ["get_ticket", "get_billing_history", "check_refund_policy", "issue_refund"],
        ),
        (
            "hidden-manual",
            True,
            ["get_customer", "get_billing_history", "check_refund_policy", "issue_refund"],
        ),
        (
            "happy-path",
            False,
            [
                "get_ticket",
                "get_customer",
                "get_billing_history",
                "search_knowledge_base",
                "check_refund_policy",
                "issue_refund",
                "add_internal_note",
                "send_customer_reply",
                "resolve_ticket",
            ],
        ),
        (
            "approved-path",
            True,
            [
                "get_billing_history",
                "check_refund_policy",
                "escalate_ticket",
                "issue_refund",
                "send_customer_reply",
                "resolve_ticket",
            ],
        ),
    ]
    rows = []
    # Matched hidden-state probes intentionally have identical visible task identity.
    for name, manual, actions in fixtures:
        scenario = Scenario(task_id="probe-duplicate", manual_approval=manual)
        env = SupportEnvironment(scenario, variant)
        for action in actions:
            rows.append(
                Transition(
                    episode_id=f"{variant}-probe-{name}",
                    task_id=scenario.task_id,
                    environment=f"support-preflight-{variant}",
                    source="scripted_probe",
                    **env.step(action),
                )
            )
    return rows


def summarize(rows: list[Transition], *, usage=None, model=MODEL, scope="model") -> dict:
    from xray.graph_builder import episodes

    groups = episodes(rows)
    return {
        "source": scope,
        "model": model,
        "episodes": len(groups),
        "tasks": len({r.task_id for r in rows}),
        "max_turns": 16,
        "business_successes": sum(g[-1].verifier["business_success"] for g in groups.values()),
        "mean_reward": sum(r.reward for r in rows) / len(groups),
        "transitions": len(rows),
        "usage": usage,
        "cost_usd": None,
        "cost_note": "No invoice cost supplied by provider; not estimated as zero.",
        "training_performed": False,
    }


def strip_model_text(value):
    """Retain native structured records without assistant text / reasoning / raw HTTP payloads."""
    if isinstance(value, list):
        return [strip_model_text(item) for item in value]
    if not isinstance(value, dict):
        return value
    blocked = {"reasoning", "reasoning_content", "analysis", "raw_response", "raw_request"}
    return {
        key: (
            "[assistant text not retained]"
            if key == "content" and value.get("role") == "assistant"
            else strip_model_text(item)
        )
        for key, item in value.items()
        if key not in blocked
    }


def export_prime(run_dir: Path, variant: str, output: Path, label: str) -> dict:
    raw_path = run_dir / "traces.jsonl"
    records = [json.loads(line) for line in raw_path.read_text().splitlines() if line.strip()]
    rows = []
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0}
    traces = []
    for record in records:
        traces.extend(record.get("traces", [record]))
    errors = []
    for i, trace in enumerate(traces):
        errors.extend(e.get("type", "trace_error") for e in trace.get("errors", []))
        raw_rows = trace.get("info", {}).get("xray_transitions", [])
        # Typed state is authoritative if finalize did not run after an interruption.
        raw_rows = raw_rows or trace.get("state", {}).get("transitions", [])
        requested = [
            call
            for node in trace.get("nodes", [])
            for call in node.get("message", {}).get("tool_calls", [])
        ]
        for raw in raw_rows:
            match = next((c for c in requested if c.get("name") == raw["action"]), None)
            if match:
                requested.remove(match)
                try:
                    args = json.loads(match.get("arguments", "{}"))
                    if isinstance(args, dict):
                        raw["requested_action_args"] = args
                except (ValueError, TypeError):
                    pass
            rows.append(
                Transition(
                    episode_id=f"{variant}-{label}-{i:02}",
                    task_id=raw["internal_state"]["ticket"]["id"],
                    environment=f"support-preflight-{variant}",
                    source="model",
                    model=MODEL,
                    **raw,
                )
            )
        for call in trace.get("calls", []):
            for key in usage:
                usage[key] += call.get("usage", {}).get(key, 0) or 0
    if not rows:
        raise RuntimeError(
            f"No tool transitions in {run_dir}; errors={errors}. Not a valid model eval."
        )
    write_jsonl(output, rows)
    summary = summarize(rows, usage=usage if any(usage.values()) else None)
    summary.update(
        {
            "framework": "verifiers.v1",
            "framework_version": importlib.metadata.version("verifiers"),
            "run_dir": str(run_dir),
            "errors": errors,
        }
    )
    # Native raw traces can contain provider reasoning; remove them after neutral export.
    # Keep an audit record with only allowlisted metadata, not a misleading resumable trace.
    sanitized = [
        {
            "redacted": True,
            "resume_supported": False,
            "trace_id": t.get("id"),
            "ok": t.get("ok"),
            "rewards": t.get("rewards"),
            "metrics": t.get("metrics"),
            "stop_condition": t.get("stop_condition"),
            "info": {"xray_transitions": t.get("info", {}).get("xray_transitions", [])},
            "calls": [
                {
                    "model": c.get("model"),
                    "usage": c.get("usage"),
                    "finish_reason": c.get("finish_reason"),
                }
                for c in t.get("calls", [])
            ],
            "error_types": [e.get("type") for e in t.get("errors", [])],
        }
        for t in traces
    ]
    raw_path.write_text("".join(json.dumps(r) + "\n" for r in sanitized))
    if errors:
        raise RuntimeError(
            f"Native eval had errors: {errors}; partial data is not a successful eval"
        )
    return summary


def native_eval(root: Path, variant: str, tasks: int, rollouts: int, label: str) -> dict:
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is required for --live; offline replay remains available")
    run_dir = root / "prime" / f"{variant}-{label}-qwen"
    if run_dir.exists():
        raise FileExistsError(
            f"Refusing to overwrite model run {run_dir}; use another --output directory"
        )
    command = [
        str(Path(sys.executable).with_name("eval")),
        "support-preflight",
        "-m",
        MODEL,
        "--client.base-url",
        "https://api.groq.com/openai/v1",
        "--client.api-key-var",
        "GROQ_API_KEY",
        "--env.agent.harness.id",
        "null",
        "--env.agent.runtime.type",
        "subprocess",
        "--env.taskset.variant",
        variant,
        "-n",
        str(tasks),
        "-r",
        str(rollouts),
        "-c",
        "1",
        "--sampling.temperature",
        "0",
        "--sampling.reasoning-effort",
        "none",
        "--sampling.max-tokens",
        "600",
        "--no-rich",
        "--no-push",
        "--output-dir",
        str(root / "prime"),
        "--run.dir",
        f"{variant}-{label}-qwen",
    ]
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join(
        [str(Path(sys.executable).parent), str(Path.cwd() / ".bootstrap/bin"), env.get("PATH", "")]
    )
    print(f"Native V1 eval: {variant} {tasks} task(s) × {rollouts} rollout(s)", flush=True)
    from xray.provider_proxy import groq_proxy

    with groq_proxy() as (endpoint, proxy_stats):
        command[command.index("--client.base-url") + 1] = endpoint
        # V1 prints failed traces to stdout. Capture rather than leaking reasoning to logs/UI.
        completed = subprocess.run(
            command, check=False, timeout=900, env=env, capture_output=True, text=True
        )
        print(
            "\n".join(line for line in completed.stderr.splitlines() if " INFO " in line),
            flush=True,
        )
        if completed.returncode:
            raise RuntimeError(
                f"Native eval exited {completed.returncode}; inspect sanitized run metadata"
            )
    directory = root / ("baseline" if variant == "broken" else "fixed")
    summary = export_prime(run_dir, variant, directory / f"{label}.jsonl", label)
    summary["command"] = command
    summary["provider_usage"] = proxy_stats
    if summary["episodes"] != tasks * rollouts:
        raise RuntimeError("Missing native episodes; refusing a partial paired evaluation")
    write_json(directory / f"{label}_summary.json", summary)
    return summary


def run(root: Path, live=False):
    if live:
        native_eval(root, "broken", 1, 2, "smoke")
        for variant in ("broken", "fixed"):
            native_eval(root, variant, 6, 1, "eval")
    reports = {}
    for variant in ("broken", "fixed"):
        directory = root / ("baseline" if variant == "broken" else "fixed")
        model_path = directory / "eval.jsonl"
        model_rows = read_jsonl(model_path) if model_path.exists() else []
        if not model_rows:
            print(
                f"{variant}: no model evidence found; generating SCRIPTED-ONLY report", flush=True
            )
        probe_rows = probes(variant)
        write_jsonl(directory / "probes.jsonl", probe_rows)
        trajectory = root / "trajectories" / f"{variant}_env.jsonl"
        write_jsonl(trajectory, model_rows + probe_rows)
        report = scan(trajectory, experimental_hodge=True)
        save_report(report, root / "xray" / f"{variant}_report")
        if model_rows:
            save_report(scan(model_path), root / "xray" / f"{variant}_model_only")
        reports[variant] = report
    comparison = {
        v: {
            key: report[key]
            for key in (
                "health",
                "status",
                "decision",
                "provenance",
                "coverage",
                "findings",
                "reachability",
            )
        }
        for v, report in reports.items()
    }
    comparison["paired_tasks"] = True
    comparison["same_scripted_actions"] = True
    comparison["model_trajectories_identical"] = False
    comparison["training_performed"] = False
    write_json(root / "xray" / "comparison.json", comparison)
    from xray.assets import create_assets

    summaries = {}
    for variant in ("broken", "fixed"):
        summary_path = root / ("baseline" if variant == "broken" else "fixed") / "eval_summary.json"
        if summary_path.exists():
            summaries[variant] = json.loads(summary_path.read_text())
    create_assets(root, reports, summaries)
    print(
        json.dumps(
            {v: {k: reports[v][k] for k in ("health", "status", "provenance")} for v in reports},
            indent=2,
        )
    )
