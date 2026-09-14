from xray.graph_builder import episodes


def analyze(rows, graph):
    actions = {row.action for row in rows}
    # Generic scanner has no authoritative catalogue. Demo adds its known tool catalogue separately.
    return {
        "label": "Observed trajectory coverage",
        "states": graph.number_of_nodes(),
        "transitions": len(rows),
        "unique_transitions": len(
            {
                (r.state_id, r.action, str(sorted(r.action_args.items())), r.next_state_id)
                for r in rows
            }
        ),
        "episodes": len(episodes(rows)),
        "terminal_states": len({r.next_state_id for r in rows if r.done}),
        "actions_observed": sorted(actions),
        "total_state_coverage_percent": None,
        "unvisited_branches": "unknown: no exhaustive reference graph",
    }
