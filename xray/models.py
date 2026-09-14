"""Versioned, model-neutral transition contract with explicit provenance."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Transition(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: Literal["1.0"] = "1.0"
    episode_id: str
    task_id: str
    environment: str
    source: Literal["model", "scripted_probe", "test"]
    model: str | None = None
    step: int = Field(ge=1)
    state_id: str
    observable_state_id: str
    observable_state: dict
    internal_state: dict
    action: str
    action_args: dict
    requested_action_args: dict | None = None
    next_state_id: str
    next_observable_state: dict
    next_internal_state: dict
    reward: float
    done: bool
    terminated: bool
    truncated: bool
    verifier: dict
    tool_result: dict

    @field_validator("verifier")
    @classmethod
    def verifier_contract(cls, value):
        if not isinstance(value.get("business_success"), bool):
            raise ValueError("verifier.business_success must be boolean")
        return value


class Finding(BaseModel):
    code: str
    severity: Literal["CRITICAL", "WARNING", "INFO"]
    title: str
    detail: str
    evidence: dict = Field(default_factory=dict)
    suggestion: str
