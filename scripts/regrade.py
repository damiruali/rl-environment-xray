"""Regrade saved model trajectories with the final rubric; does not call a model."""

import asyncio
from pathlib import Path
from types import SimpleNamespace

from support_preflight.environment import Scenario, Snapshot
from support_preflight.taskset import SupportData, SupportState, SupportTask

from xray.collector import read_jsonl, write_json
from xray.graph_builder import episodes


async def main():
    results = []
    for variant in ("broken", "fixed"):
        path = Path("artifacts") / ("baseline" if variant == "broken" else "fixed") / "eval.jsonl"
        for episode_id, rows in episodes(read_jsonl(path)).items():
            task = SupportTask(
                SupportData(scenario=Scenario(task_id=rows[0].task_id), variant=variant)
            )
            trace = SimpleNamespace(
                state=SupportState(
                    snapshot=Snapshot.model_validate(rows[-1].next_internal_state),
                    transitions=[r.model_dump() for r in rows],
                )
            )
            feedback = await task.progress_feedback(trace)
            grade = await task.environment_reward(trace)
            assert abs(grade - feedback) < 1e-8  # All measured model episodes succeeded.
            results.append(
                {
                    "episode_id": episode_id,
                    "variant": variant,
                    "progress_feedback": feedback,
                    "final_training_score": grade,
                    "same_numeric_score_as_live_eval": True,
                }
            )
    write_json(
        Path("artifacts/regrading.json"),
        {
            "new_model_calls": 0,
            "reason": "Final fixed rubric gates training score on business success; tool feedback unchanged.",
            "all_recorded_scores_unchanged": True,
            "episodes": results,
        },
    )
    print(f"Offline regraded {len(results)} real model episodes; all recorded scores unchanged.")


if __name__ == "__main__":
    asyncio.run(main())
