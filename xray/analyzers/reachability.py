"""Sampled absence is unknown. Unreachable requires a caller-supplied exhaustive model."""

import networkx as nx

from xray.graph_builder import episodes
from xray.models import Finding


def reference_reachability(graph, initial_states, targets, *, exhaustive=False):
    reached = set()
    for start in initial_states:
        if start not in graph:
            raise ValueError("initial state absent from reference graph")
        reached |= {start} | nx.descendants(graph, start)
    if reached.intersection(targets):
        return "reachable"
    return "unreachable" if exhaustive else "unknown"


def analyze_reference(graph, initial_states, targets, *, exhaustive=False):
    status = reference_reachability(graph, initial_states, targets, exhaustive=exhaustive)
    if status != "unreachable":
        return status, []
    return status, [
        Finding(
            code="reference_target_unreachable",
            severity="CRITICAL",
            title="Target unreachable in supplied exhaustive reference model",
            detail="No directed path reaches any required target from the supplied initial states. This conclusion is scoped to the reference model, whose exhaustiveness is a caller assertion.",
            evidence={
                "initial_states": list(initial_states),
                "targets": list(targets),
                "exhaustive_reference": True,
            },
            suggestion="Repair the target predicate or add the missing transition; validate reference-model fidelity.",
        )
    ]


def analyze(rows):
    groups = episodes(rows)
    successes = [key for key, group in groups.items() if group[-1].verifier["business_success"]]
    stats = {
        "scope": "observed rollouts only",
        "successful_episodes": len(successes),
        "observed_success_path": bool(successes),
        "global_reachability": "unknown",
        "exhaustive_reference_provided": False,
    }
    findings = []
    if not successes:
        findings.append(
            Finding(
                code="success_not_observed",
                severity="WARNING",
                title="No successful path observed",
                detail="Finite rollouts cannot establish global unreachability.",
                evidence=stats,
                suggestion="Add a known-good control trajectory and targeted branch probes.",
            )
        )
    return stats, findings
