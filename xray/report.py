"""JSON + offline standalone dashboard. All displayed values come from scan inputs."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from xray.analyzers import (
    coverage,
    history_dependency,
    hodge,
    reachability,
    reward_consistency,
    reward_cycles,
)
from xray.collector import read_jsonl, write_json
from xray.graph_builder import build_graph, episodes
from xray.scoring import score


def scan(path: Path, experimental_hodge=False) -> dict:
    rows = read_jsonl(path)
    if len({row.environment for row in rows}) != 1:
        raise ValueError("scan one environment version at a time")
    graph = build_graph(rows)
    reachable, reach_findings = reachability.analyze(rows)
    findings = (
        reward_cycles.analyze(rows, graph)
        + reward_consistency.analyze(rows)
        + history_dependency.analyze(rows)
        + reach_findings
    )
    groups = episodes(rows)
    summaries = [
        {
            "episode_id": key,
            "source": group[0].source,
            "model": group[0].model,
            "steps": len(group),
            "reward": round(sum(r.reward for r in group), 8),
            "success": group[-1].verifier["business_success"],
            "truncated": group[-1].truncated,
            "actions": [r.action for r in group],
        }
        for key, group in groups.items()
    ]
    positive_nodes = {
        state
        for f in findings
        if f.code == "positive_reward_cycle"
        for cycle in f.evidence["cycles"]
        for state in cycle["states"]
    }
    # A representative witnessed episode graph, not an unreadable hairball or invented graph.
    chosen = next(
        (g for g in groups.values() if any(r.state_id in positive_nodes for r in g)),
        next(iter(groups.values())),
    )
    graph_nodes = list(dict.fromkeys([r.state_id for r in chosen] + [chosen[-1].next_state_id]))
    positions = {}
    for i, node in enumerate(graph_nodes):
        positions[node] = {
            "id": node,
            "label": f"S{i}",
            "x": 85 + (i % 6) * 145,
            "y": 100 + (i // 6) * 125,
            "critical": node in positive_nodes,
        }
    drawing = {
        "height": max(240, 180 + (len(graph_nodes) // 6) * 125),
        "nodes": list(positions.values()),
        "edges": [],
    }
    seen_edges = set()
    for row in chosen:
        key = (row.state_id, row.next_state_id, row.action, row.reward)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        a, b = positions[row.state_id], positions[row.next_state_id]
        drawing["edges"].append(
            {
                "a": a,
                "b": b,
                "loop": a == b,
                "label": f"{row.action} ({row.reward:+g})",
                "action": row.action,
                "reward": row.reward,
                "critical": a == b and row.reward > 0,
            }
        )
    return {
        "report_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "input": str(path),
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "environment": rows[0].environment,
        **score(findings),
        "coverage": coverage.analyze(rows, graph),
        "reachability": reachable,
        "findings": [f.model_dump() for f in findings],
        "episodes": summaries,
        "provenance": {
            source: sum(s["source"] == source for s in summaries)
            for source in sorted({r.source for r in rows})
        },
        "graph_view": drawing,
        "example_episode": chosen[0].episode_id,
        "example_trajectory": [r.model_dump() for r in chosen],
        "experimental_hodge": hodge.analyze(graph) if experimental_hodge else None,
    }


def render(report: dict, output: Path) -> None:
    environment = Environment(
        loader=PackageLoader("xray", "templates"), autoescape=select_autoescape(["html"])
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(environment.get_template("report.html").render(r=report), encoding="utf-8")


def save_report(report: dict, stem: Path) -> None:
    write_json(stem.with_suffix(".json"), report)
    render(report, stem.with_suffix(".html"))
