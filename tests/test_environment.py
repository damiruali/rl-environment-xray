from types import SimpleNamespace

import pytest
from support_preflight import load_environment
from support_preflight.environment import Scenario, SupportEnvironment, business_state, canonical_id
from support_preflight.taskset import (
    SupportData,
    SupportState,
    SupportTask,
    SupportToolsConfig,
    SupportToolset,
)


def finish(env):
    return [
        env.step(a)
        for a in [
            "get_billing_history",
            "check_refund_policy",
            "escalate_ticket",
            "issue_refund",
            "send_customer_reply",
            "resolve_ticket",
        ]
    ]


def test_native_environment_loads():
    env = load_environment()
    assert type(env).__name__ == "SingleAgentEnv"
    tasks = list(env.taskset)
    assert len(tasks) == 6
    assert len({t.key for t in tasks}) == 6
    assert env.config.agent.runtime.type == "subprocess"


@pytest.mark.parametrize("manual", [False, True])
def test_success_and_reward(manual):
    env = SupportEnvironment(Scenario(manual_approval=manual))
    rows = finish(env)
    assert rows[-1]["verifier"]["business_success"]
    assert env.state.accumulated_reward == 1.0
    assert rows[-1]["terminated"] and not rows[-1]["truncated"]
    with pytest.raises(ValueError, match="terminal"):
        env.step("resolve_ticket")


def test_broken_close_mismatch_and_fixed_guard():
    broken = SupportEnvironment(Scenario(), "broken").step("resolve_ticket")
    assert broken["reward"] == 1 and broken["verifier"]["rubric_success"]
    assert not broken["verifier"]["business_success"]
    fixed = SupportEnvironment(Scenario()).step("resolve_ticket")
    assert not fixed["done"] and fixed["reward"] == 0
    assert fixed["tool_result"]["error"] == "refund_and_notification_required"


def test_hidden_is_not_observable_until_fixed():
    a = SupportEnvironment(Scenario(manual_approval=False), "broken")
    b = SupportEnvironment(Scenario(manual_approval=True), "broken")
    assert a.observe() == b.observe()
    assert canonical_id(business_state(a.state)) != canonical_id(business_state(b.state))
    a.variant = b.variant = "fixed"
    assert a.observe() != b.observe()


def test_idempotency_and_validation():
    env = SupportEnvironment(Scenario())
    assert env.step("get_billing_history")["reward"] == 0.2
    assert env.step("get_billing_history")["reward"] == 0
    assert env.step("issue_refund")["tool_result"]["error"] == "verify_eligibility_first"
    assert not env.step("issue_refund", {"amount": 999999})["tool_result"]["ok"]
    assert not env.step("shell", {"command": "delete"})["tool_result"]["ok"]


def test_horizon_is_truncation_not_business_success():
    env = SupportEnvironment(Scenario(), max_turns=1)
    row = env.step("get_ticket")
    assert row["truncated"] and row["done"] and not row["terminated"]
    assert not row["verifier"]["business_success"]


async def test_native_toolset_same_engine_and_isolation():
    one = SupportToolset(SupportToolsConfig())
    two = SupportToolset(SupportToolsConfig())
    for tools in (one, two):
        await tools.setup_task(SupportData(scenario=Scenario()))
    result = await one.get_billing_history()
    assert result["reward"] == 0.2
    assert len(one.state.transitions) == 1
    assert two.state.snapshot is None


async def test_fixed_training_score_requires_closure_not_just_full_feedback():
    env = SupportEnvironment(Scenario())
    rows = [
        env.step(action)
        for action in [
            "get_billing_history",
            "check_refund_policy",
            "issue_refund",
            "send_customer_reply",
        ]
    ]
    task = SupportTask(SupportData(scenario=Scenario(), variant="fixed"))
    trace = SimpleNamespace(state=SupportState(snapshot=env.state, transitions=rows))
    assert await task.progress_feedback(trace) == 1
    assert await task.environment_reward(trace) == 0
    rows.append(env.step("resolve_ticket"))
    trace.state = SupportState(snapshot=env.state, transitions=rows)
    assert await task.environment_reward(trace) == 1
