"""Exercise multi-state and misleading projected cycles, not just the support self-loop."""

from xray.analyzers.reward_cycles import analyze
from xray.demo import probes
from xray.graph_builder import build_graph


def edge(episode, step, source, target, reward):
    prototype = probes("fixed")[0]
    return prototype.model_copy(
        update={
            "episode_id": episode,
            "step": step,
            "state_id": source,
            "next_state_id": target,
            "reward": reward,
            "action": f"{source}_to_{target}",
            "source": "test",
        }
    )


def test_witnessed_two_state_positive_cycle():
    rows = [edge("one", 1, "a", "b", 0.3), edge("one", 2, "b", "a", -0.1)]
    findings = analyze(rows, build_graph(rows))
    assert findings[0].evidence["cycles"][0]["total_reward"] == 0.2
    assert findings[0].evidence["cycles"][0]["actions"] == ["a_to_b", "b_to_a"]


def test_stitched_cycle_is_not_reported_as_witnessed():
    rows = [edge("one", 1, "a", "b", 0.3), edge("two", 1, "b", "a", -0.1)]
    assert analyze(rows, build_graph(rows)) == []


def test_nonpositive_cycle_not_reported():
    rows = [edge("one", 1, "a", "b", 0.2), edge("one", 2, "b", "a", -0.2)]
    assert analyze(rows, build_graph(rows)) == []
