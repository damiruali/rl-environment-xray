from collections import defaultdict

from xray.analyzers.reward_consistency import outcome, signature
from xray.graph_builder import episodes
from xray.models import Finding


def analyze(rows):
    grouped = defaultdict(lambda: defaultdict(set))
    for group in episodes(rows).values():
        history = []
        for row in group:
            if not row.truncated:
                grouped[signature(row)][tuple(history)].add(outcome(row))
            history.append(row.action)
    candidates = [
        paths
        for paths in grouped.values()
        if len(paths) > 1 and len({tuple(sorted(v)) for v in paths.values()}) > 1
    ]
    if not candidates:
        return []
    return [
        Finding(
            code="history_association",
            severity="WARNING",
            title="Outcome differs across observed histories",
            detail="Different action histories precede the same visible state/action but different observed outcomes. Small observational samples establish association only, not causation.",
            evidence={
                "groups": len(candidates),
                "history_paths": [list(k) for k in candidates[0]][:5],
            },
            suggestion="Replay matched histories while controlling hidden fields; expand observation if needed.",
        )
    ]
