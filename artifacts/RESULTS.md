# Measured experiment results

No RL training. No Hub publication.

| Variant | Model episodes | Business success | Mean reward | X-Ray | Health |
|---|---:|---:|---:|---|---:|
| broken | 6 | 6 | 1.2 | FAIL | 24 |
| fixed | 6 | 6 | 1.0 | PASS | 100 |

X-Ray here includes seven explicitly labelled scripted probes per variant.
Health is a heuristic, not safety probability. Total state coverage and global reachability unknown.
The final fixed training rubric is gated on full business success; milestone feedback remains a separate diagnostic signal.
[Offline regrading](regrading.json) checks the final rubric on the 12 saved model trajectories: all scores unchanged, no new model calls.

## broken model evaluation

Model: `qwen/qwen3.8-27b`.
Usage: `{'prompt_tokens': 80800, 'completion_tokens': 1304, 'reasoning_tokens': 0}`.
Dated list-price estimate: $0.069856. Provider invoice cost remains unavailable (`null`).
[Pricing snapshot: Groq Qwen3.8-27B, 2026-09-11](https://console.groq.com/docs/model/qwen/qwen3.8-27b). Excludes early failed attempts and account-specific pricing.

## fixed model evaluation

Model: `qwen/qwen3.8-27b`.
Usage: `{'prompt_tokens': 72331, 'completion_tokens': 1490, 'reasoning_tokens': 0}`.
Dated list-price estimate: $0.063825. Provider invoice cost remains unavailable (`null`).
[Pricing snapshot: Groq Qwen3.8-27B, 2026-09-11](https://console.groq.com/docs/model/qwen/qwen3.8-27b). Excludes early failed attempts and account-specific pricing.
