"""Export exactly one Taskset class for native V1 discovery."""

from support_preflight.taskset import SupportTaskset

__all__ = ["SupportTaskset"]


def load_environment(config=None):
    import verifiers.v1 as vf

    if config is None:
        config = vf.SingleAgentEnvConfig.model_validate(
            {
                "taskset": {"id": "support-preflight"},
                "agent": {"harness": {"id": "null"}, "runtime": {"type": "subprocess"}},
            }
        )
    return vf.load_environment(config)
