"""Small bounded exhaustive regression over a documented action alphabet, not whole-state coverage."""

from itertools import product

import pytest
from support_preflight.environment import Scenario, SupportEnvironment


def test_all_short_sequences_cannot_close_without_goal_or_exceed_reward_budget():
    alphabet = [
        "get_billing_history",
        "check_refund_policy",
        "issue_refund",
        "send_customer_reply",
        "resolve_ticket",
        "search_knowledge_base",
    ]
    checked = 0
    for actions in product(alphabet, repeat=4):
        env = SupportEnvironment(Scenario(), "fixed")
        for action in actions:
            if env.state.terminal:
                break
            row = env.step(action)
            assert 0 <= env.state.accumulated_reward <= 1
            if env.state.ticket["status"] == "resolved":
                assert row["verifier"]["business_success"]
        checked += 1
    assert checked == 1296  # depth 4, six-action alphabet, auto-approval scenario only


def test_fixed_repeat_after_progress_is_zero():
    env = SupportEnvironment(Scenario(), "fixed", max_turns=30)
    total = 0
    for action in [
        "get_billing_history",
        "check_refund_policy",
        "issue_refund",
        "send_customer_reply",
    ]:
        total += env.step(action)["reward"]
        for _ in range(3):
            assert env.step(action)["reward"] == 0
    assert total == pytest.approx(1)
