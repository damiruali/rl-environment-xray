"""Native, current Verifiers v1 plugin (Taskset → Task → MCP Toolset)."""

from __future__ import annotations

from typing import Literal

import verifiers.v1 as vf
from pydantic import Field

from support_preflight.environment import Scenario, Snapshot, SupportEnvironment, scenarios

SYSTEM_PROMPT = (
    "You are a support agent in a synthetic simulation. Handle the duplicate subscription "
    "payment: investigate, verify eligibility, refund, notify and resolve. Use the tools. "
    "Call one tool at a time. If approval is required, escalate then continue. "
    "Do not claim success before tools confirm it. Do not repeat unchanged reads."
)


class SupportData(vf.TaskData):
    scenario: Scenario
    variant: Literal["broken", "fixed"] = "fixed"
    max_turns: int = 16


class SupportState(vf.State):
    snapshot: Snapshot | None = None
    transitions: list[dict] = Field(default_factory=list)


class SupportToolsConfig(vf.ToolsetConfig):
    pass


class SupportToolset(vf.Toolset[SupportToolsConfig, SupportState]):
    TOOL_PREFIX = None

    async def setup_task(self, task: SupportData) -> None:
        self.data = task

    def act(self, name: str, args: dict | None = None) -> dict:
        env = SupportEnvironment(
            self.data.scenario, self.data.variant, self.data.max_turns, self.state.snapshot
        )
        if env.state.terminal:
            return {"ok": False, "error": "episode_terminal", "done": True}
        row = env.step(name, args)
        self.state.snapshot = env.state
        self.state.transitions.append(row)
        return {
            **row["tool_result"],
            "state": row["next_observable_state"],
            "reward": row["reward"],
            "done": row["done"],
        }

    @vf.tool
    async def get_ticket(self) -> dict:
        """Read the customer's duplicate-payment ticket."""
        return self.act("get_ticket")

    @vf.tool
    async def get_customer(self) -> dict:
        """Read the synthetic customer's subscription information."""
        return self.act("get_customer")

    @vf.tool
    async def get_billing_history(self) -> dict:
        """Inspect transactions and identify a duplicate charge."""
        return self.act("get_billing_history")

    @vf.tool
    async def search_knowledge_base(self) -> dict:
        """Read the duplicate-payment procedure."""
        return self.act("search_knowledge_base")

    @vf.tool
    async def check_refund_policy(self) -> dict:
        """Verify refund eligibility after inspecting billing history."""
        return self.act("check_refund_policy")

    @vf.tool
    async def issue_refund(self) -> dict:
        """Refund the duplicate after eligibility and any required approval."""
        return self.act("issue_refund")

    @vf.tool
    async def add_internal_note(self, message: str = "Investigation in progress") -> dict:
        """Record an internal note, at most 1000 characters."""
        return self.act("add_internal_note", {"message": message})

    @vf.tool
    async def send_customer_reply(
        self, message: str = "The duplicate payment was refunded."
    ) -> dict:
        """Notify the customer after a completed refund."""
        return self.act("send_customer_reply", {"message": message})

    @vf.tool
    async def escalate_ticket(self) -> dict:
        """Request approval from a deterministic simulated review service."""
        return self.act("escalate_ticket")

    @vf.tool
    async def resolve_ticket(self) -> dict:
        """Close the ticket after refund and notification."""
        return self.act("resolve_ticket")


class SupportTaskConfig(vf.TaskConfig):
    tools: SupportToolsConfig = SupportToolsConfig()


class SupportTask(vf.Task[SupportData, SupportState, SupportTaskConfig]):
    @classmethod
    def toolsets(cls, config: SupportTaskConfig) -> list[vf.Toolset]:
        return [SupportToolset(config.tools)]

    @vf.stop
    async def done(self, trace: vf.Trace) -> bool:
        return bool(trace.state.snapshot and trace.state.snapshot.terminal) or (
            trace.num_turns >= self.data.max_turns
        )

    async def finalize(self, trace: vf.Trace) -> None:
        trace.info["xray_transitions"] = trace.state.transitions

    @vf.reward
    async def environment_reward(self, trace: vf.Trace) -> float:
        if self.data.variant == "fixed":
            # Shaping feedback is not the training objective. Stopping before closure
            # must not tie a policy that finishes the entire business task.
            return await self.business_success(trace)
        return trace.state.snapshot.accumulated_reward if trace.state.snapshot else 0.0

    @vf.metric
    async def progress_feedback(self, trace: vf.Trace) -> float:
        return trace.state.snapshot.accumulated_reward if trace.state.snapshot else 0.0

    @vf.metric
    async def business_success(self, trace: vf.Trace) -> float:
        rows = trace.state.transitions
        return float(bool(rows) and rows[-1]["verifier"]["business_success"])


class SupportConfig(vf.TasksetConfig):
    variant: Literal["broken", "fixed"] = "fixed"
    num_tasks: int = Field(6, ge=1, le=20)
    max_turns: int = Field(16, ge=1, le=40)
    task: SupportTaskConfig = SupportTaskConfig()


class SupportTaskset(vf.Taskset[SupportTask, SupportConfig]):
    def load(self) -> list[SupportTask]:
        return [
            SupportTask(
                SupportData(
                    idx=i,
                    name=s.task_id,
                    scenario=s,
                    variant=self.config.variant,
                    max_turns=self.config.max_turns,
                    system_prompt=SYSTEM_PROMPT,
                    prompt="I was charged twice. Please refund the extra payment.",
                ),
                self.config.task,
            )
            for i, s in enumerate(scenarios(self.config.num_tasks))
        ]


if __name__ == "__main__":
    SupportToolset.run()
