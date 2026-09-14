import json

from support_preflight.environment import Scenario, SupportEnvironment

from xray.collector import read_jsonl
from xray.demo import export_prime


def test_v1_export_uses_call_usage_and_drops_reasoning(tmp_path):
    engine = SupportEnvironment(Scenario(), "broken")
    transition = engine.step("get_ticket")
    trace = {
        "id": "trace",
        "ok": True,
        "info": {"xray_transitions": [transition]},
        "nodes": [
            {
                "message": {
                    "role": "assistant",
                    "reasoning_content": "DO NOT RETAIN ME",
                    "tool_calls": [{"name": "get_ticket", "arguments": '{"ticket_id":"123"}'}],
                }
            }
        ],
        "calls": [
            {"model": "qwen/qwen3.8-27b", "usage": {"prompt_tokens": 20, "completion_tokens": 7}}
        ],
        "errors": [],
    }
    raw = tmp_path / "traces.jsonl"
    raw.write_text(json.dumps({"traces": [trace]}) + "\n")
    output = tmp_path / "neutral.jsonl"
    summary = export_prime(tmp_path, "broken", output, "test")
    assert summary["usage"]["prompt_tokens"] == 20
    assert summary["usage"]["completion_tokens"] == 7
    assert "DO NOT RETAIN ME" not in raw.read_text() + output.read_text()
    assert read_jsonl(output)[0].requested_action_args == {"ticket_id": "123"}
    assert read_jsonl(output)[0].action_args == {}
