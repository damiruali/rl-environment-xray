# RL Environment X-Ray — implementation plan

Promise: **Test the environment before you train the agent.**

This is a reproducible engineering prototype, not a trainer or a safety proof.
All support data are synthetic. No training or public publication without the
requested authorization. Report measured results, never desired numbers.

## Phases

- [x] Phase 1 — Prime research: inspect the live Hub, current Verifiers source and
  CLI help, and at least three relevant environment implementations. Record
  versions, architecture, links and limitations in research/ENVIRONMENT_RESEARCH.md.
- [x] Phase 2 — Support environment: implement deterministic synthetic support
  tasks, ten tools, independent business success, broken V1 and fixed V2, and a
  genuine Verifiers v1 adapter/package.
- [x] Phase 3 — Baseline rollouts: verify an available inexpensive/local model,
  run a 1-task × 2-rollout smoke test, then a small paired baseline. Supplement
  with explicitly labelled scripted diagnostic probes, not fabricated model runs.
- [x] Phase 4 — Trajectory capture: versioned JSONL, stable business-state IDs,
  distinct observations/internal state, provenance, usage and verifier outcomes.
- [x] Phase 5 — X-Ray: graph/SCC/cycle checks, scoped reachability, measured
  coverage, reward-goal mismatch, consistency and possible history dependence;
  optional clearly specified graph-gradient projection.
- [x] Phase 6 — Comparison: run identical task/probe schedules on broken/fixed,
  generate JSON/standalone HTML reports and meaningful regression tests.
- [x] Phase 7 — Prime packaging: build/install/load and smoke-test the v1 package;
  validate current publication commands. Prepare for publication; do not push
  publicly without confirmation.
- [x] Phase 8 — LinkedIn assets: six real screenshots, Mermaid pipeline, plain
  language walkthrough, RU/EN posts reflecting actual observations.

## Acceptance criteria

Local one-command demo; real model evidence separately labelled from scripted
probes; broken defects found and fixed critical defects removed; no fabricated
total coverage/unreachability or mathematical guarantees; installed environment
load test; serialization, graph, reward-cycle, reachability and report tests;
exact runnable commands and candid remaining blockers.

## Execution log

- 2026-09-11: Read full user brief. Workspace is empty apart from Git metadata.
  System Python is 3.10; uv and Prime CLI are not on PATH. Ollama is installed.
  Live Prime docs include changing v0/v1 examples: actual package source and
  installed CLI help will determine the adapter, not copied legacy snippets.
- 2026-09-11: Read Tau2, Enterprise Ops, BFCL native V1 sources and a published
  TauLong README from the Hub. Implemented independent synthetic engine and
  native MCP Taskset/Task/Toolset. Published Verifiers 0.3.2.dev80 Task/MCP source
  matches inspected commit; exact release locked.
- 2026-09-11: Early GPT-OSS attempts failed on provider limits / tool format.
  Qwen3.8-27B chosen for final comparison, reasoning disabled, no model switching
  within baseline/fixed. macOS hidden .pth flags broke editable imports; switched
  to non-editable wheel install. Early attempts retained in redacted audit files.
- 2026-09-11: Native Qwen smoke 1 task × 2 rollouts succeeded (2/2 business success).
  Main six-task paired eval running. Twenty regression tests pass, including
  1,296 short fixed-environment action sequences. Wheel/sdist build succeeds.
  Probe-only diagnostics: broken 24/100 FAIL, fixed 100/100 scoped PASS.
- 2026-09-11: Completed native paired eval: 6/6 business success for both versions;
  broken 42 model transitions, fixed 39. Model-only checks do not reveal the seeded
  defects; seven labelled probes per side produce broken FAIL (24) vs fixed PASS (100).
  Twenty-four tests pass. Fixed final training score was additionally gated on full
  business success; offline regrading all 12 model episodes leaves their scores unchanged.
  Six actual browser screenshots captured; source/trajectory/provenance/secret audit PASS.
  Mermaid and SVG, RU/EN posts and walkthrough complete. No RL training or Hub push.
