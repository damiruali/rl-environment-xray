"""Require a witnessed contiguous closed walk, not a stitched-together graph cycle."""

from collections import defaultdict

import networkx as nx

from xray.graph_builder import episodes
from xray.models import Finding


def analyze(rows, graph):
    cyclic_nodes = set()
    for component in nx.strongly_connected_components(graph):
        if len(component) > 1 or any(graph.has_edge(n, n) for n in component):
            cyclic_nodes.update(component)
    found = defaultdict(list)
    for episode, group in episodes(rows).items():
        for start, first in enumerate(group):
            if first.state_id not in cyclic_nodes:
                continue
            for end in range(start, len(group)):
                segment = group[start : end + 1]
                if group[end].next_state_id != first.state_id:
                    continue
                # Only elementary witnessed cycles: avoid quadratic duplicate windows.
                states = [r.state_id for r in segment]
                if len(set(states)) != len(states):
                    break
                total = sum(r.reward for r in segment)
                if total > 1e-8 and not any(r.verifier["business_success"] for r in segment):
                    signature = tuple((r.state_id, r.action, r.next_state_id) for r in segment)
                    signature = min(signature[i:] + signature[:i] for i in range(len(signature)))
                    found[signature].append(
                        {
                            "episode_id": episode,
                            "steps": [start + 1, end + 1],
                            "source": first.source,
                            "states": states + [first.state_id],
                            "actions": [r.action for r in segment],
                            "total_reward": round(total, 8),
                        }
                    )
                break
    if not found:
        return []
    samples = [{**samples[0], "occurrences": len(samples)} for samples in found.values()]
    return [
        Finding(
            code="positive_reward_cycle",
            severity="CRITICAL",
            title="Positive reward cycle witnessed",
            detail="A contiguous rollout returned to the same internal business state with positive reward and no success. Clock/accounting are excluded; the finite turn cap bounds exploitation.",
            evidence={
                "cycles": samples,
                "occurrences": sum(x["occurrences"] for x in samples),
                "sources": sorted({x["source"] for v in found.values() for x in v}),
            },
            suggestion="Pay once for verified progress, never for unchanged reads.",
        )
    ]
