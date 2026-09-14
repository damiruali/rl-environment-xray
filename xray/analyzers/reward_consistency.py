import json
from collections import defaultdict

from xray.models import Finding


def signature(row):
    return (row.observable_state_id, row.action, json.dumps(row.action_args, sort_keys=True))


def outcome(row):
    # Compare observable outcome, not hidden internal IDs or runtime accounting.
    return json.dumps([row.reward, row.next_observable_state, row.tool_result], sort_keys=True)


def analyze(rows):
    findings = []
    mismatch = [
        r for r in rows if r.verifier.get("rubric_success") and not r.verifier["business_success"]
    ]
    if mismatch:
        findings.append(
            Finding(
                code="goal_reward_mismatch",
                severity="CRITICAL",
                title="Reward rubric accepts a failed business task",
                detail="The independent business verifier disagrees with the environment success rubric.",
                evidence={
                    "occurrences": len(mismatch),
                    "examples": [
                        {
                            "episode_id": r.episode_id,
                            "step": r.step,
                            "reward": r.reward,
                            "source": r.source,
                            "verifier": r.verifier,
                        }
                        for r in mismatch[:5]
                    ],
                },
                suggestion="Require completed refund, customer notification and correct closure together.",
            )
        )
    groups = defaultdict(list)
    for row in rows:
        if row.truncated:
            continue  # Known horizon boundary is not evidence of hidden business state.
        groups[signature(row)].append(row)
    conflicts = [group for group in groups.values() if len({outcome(r) for r in group}) > 1]
    if conflicts:
        findings.append(
            Finding(
                code="possible_hidden_state",
                severity="WARNING",
                title="Possible hidden-state dependency",
                detail="Same observable snapshot and action arguments produced different outcomes. Partial observability, stochasticity or an incomplete projection may explain this; it does not prove non-Markov dynamics.",
                evidence={
                    "conflicting_groups": len(conflicts),
                    "examples": [
                        [
                            {
                                "episode_id": r.episode_id,
                                "step": r.step,
                                "action": r.action,
                                "reward": r.reward,
                                "tool_result": r.tool_result,
                                "source": r.source,
                            }
                            for r in group[:6]
                        ]
                        for group in conflicts[:5]
                    ],
                },
                suggestion="Expose approval requirements, or explicitly model and test the belief/history state.",
            )
        )
    return findings
