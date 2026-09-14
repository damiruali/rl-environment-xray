import json
import subprocess
import sys

import networkx as nx
import pytest

from xray.analyzers.hodge import analyze as hodge
from xray.analyzers.reachability import analyze_reference, reference_reachability
from xray.analyzers.reward_cycles import analyze as cycles
from xray.collector import read_jsonl, write_jsonl
from xray.demo import probes
from xray.graph_builder import build_graph
from xray.report import render, scan


def test_positive_reward_cycle_and_fixed_removed():
    broken, fixed = probes("broken"), probes("fixed")
    findings = cycles(broken, build_graph(broken))
    assert findings[0].severity == "CRITICAL"
    # 6 policy + 6 search probes, plus one unchanged search on the happy path.
    assert findings[0].evidence["occurrences"] == 13
    assert findings[0].evidence["cycles"][0]["total_reward"] == 0.2
    assert cycles(fixed, build_graph(fixed)) == []


def test_reachability_scope():
    graph = nx.DiGraph([("start", "approved"), ("approved", "pending")])
    assert reference_reachability(graph, ["start"], {"approved"}, exhaustive=True) == "reachable"
    assert reference_reachability(graph, ["start"], {"approved_and_processed"}) == "unknown"
    assert (
        reference_reachability(graph, ["start"], {"approved_and_processed"}, exhaustive=True)
        == "unreachable"
    )
    status, findings = analyze_reference(
        graph, ["start"], {"approved_and_processed"}, exhaustive=True
    )
    assert status == "unreachable" and findings[0].severity == "CRITICAL"
    assert analyze_reference(graph, ["start"], {"approved_and_processed"}) == ("unknown", [])


def test_roundtrip_graph_preserves_parallel_edges(tmp_path):
    rows = probes("broken")
    path = tmp_path / "rows.jsonl"
    write_jsonl(path, rows)
    loaded = read_jsonl(path)
    assert rows == loaded
    graph = build_graph(loaded)
    assert isinstance(graph, nx.MultiDiGraph)
    assert graph.number_of_edges() == len(rows)
    assert graph.number_of_edges(rows[0].state_id, rows[0].next_state_id) >= 6


def test_empty_invalid_and_discontinuous_are_not_pass(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("")
    with pytest.raises(ValueError, match="no transitions"):
        scan(path)
    path.write_text('{"schema_version":"99"}\n')
    with pytest.raises(ValueError, match="invalid transition"):
        scan(path)
    rows = probes("fixed")
    with pytest.raises(ValueError, match="contiguous"):
        build_graph(rows[1:])


def test_no_stitched_cycle_claim():
    rows = probes("fixed")
    # No positive reward loop in the actual contiguous fixed episodes.
    assert not cycles(rows, build_graph(rows))


def test_scan_report_goal_mismatch_hidden_and_scope(tmp_path):
    for variant in ("broken", "fixed"):
        path = tmp_path / f"{variant}.jsonl"
        write_jsonl(path, probes(variant))
        report = scan(path, True)
        codes = {f["code"] for f in report["findings"]}
        if variant == "broken":
            assert {
                "positive_reward_cycle",
                "goal_reward_mismatch",
                "possible_hidden_state",
                "history_association",
            } <= codes
            assert report["status"] == "FAIL"
        else:
            assert not codes and report["status"] == "PASS"
        assert report["coverage"]["total_state_coverage_percent"] is None
        assert report["reachability"]["global_reachability"] == "unknown"
        report["environment"] = '<script>alert("x")</script>'
        html = tmp_path / f"{variant}.html"
        render(report, html)
        content = html.read_text()
        assert "&lt;script&gt;" in content and '<script>alert("x")</script>' not in content
        assert "https://" not in content and "<svg" in content


def test_hodge_self_loop_and_gradient():
    graph = nx.MultiDiGraph()
    graph.add_edge("a", "a", reward=0.2, action="read")
    assert hodge(graph)["residual_energy_ratio"] == pytest.approx(1)
    graph = nx.MultiDiGraph()
    graph.add_edge("a", "b", reward=0.2, action="progress")
    result = hodge(graph)
    assert result["residual_energy_ratio"] == pytest.approx(0, abs=1e-10)
    assert result["orthogonality_error"] < 1e-9


@pytest.mark.parametrize("variant,code", [("broken", 1), ("fixed", 0)])
def test_cli_gate(tmp_path, variant, code):
    path = tmp_path / "input.jsonl"
    write_jsonl(path, probes(variant))
    result = subprocess.run(
        [sys.executable, "-m", "xray", "scan", str(path), "--output", str(tmp_path / "report")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == code, result.stderr
    assert json.loads((tmp_path / "report.json").read_text())["status"] in result.stdout
