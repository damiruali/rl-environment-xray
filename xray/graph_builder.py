"""Preserve every observed edge, including repetitions, in a directed multigraph."""

from collections import defaultdict

import networkx as nx

from xray.models import Transition


def episodes(rows: list[Transition]) -> dict[str, list[Transition]]:
    groups = defaultdict(list)
    for row in rows:
        groups[row.episode_id].append(row)
    for group in groups.values():
        group.sort(key=lambda row: row.step)
        if [r.step for r in group] != list(range(1, len(group) + 1)):
            raise ValueError("episode must contain contiguous unique steps starting at 1")
        for a, b in zip(group, group[1:]):
            if a.done or a.next_state_id != b.state_id:
                raise ValueError("discontinuous or post-terminal episode")
    return dict(groups)


def build_graph(rows: list[Transition]) -> nx.MultiDiGraph:
    episodes(rows)  # validate before constructing claims
    graph = nx.MultiDiGraph()
    for row in rows:
        graph.add_node(row.state_id, state=row.internal_state, observable=row.observable_state)
        graph.add_node(
            row.next_state_id, state=row.next_internal_state, observable=row.next_observable_state
        )
        graph.add_edge(
            row.state_id,
            row.next_state_id,
            key=f"{row.episode_id}:{row.step}",
            action=row.action,
            reward=row.reward,
            episode=row.episode_id,
            step=row.step,
            source=row.source,
        )
    return graph
