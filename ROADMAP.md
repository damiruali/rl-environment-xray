# Agent X-Ray Roadmap

The roadmap is intentionally evidence-first. Dates and performance claims will be added only
after they are supported by reproducible results.

## v0.2 — Adapter contract

- define a small versioned trajectory and adapter contract;
- add one runtime adapter without coupling the scanner to a specific model provider;
- preserve requested actions, executed actions, state transitions, and provenance;
- publish compatibility and malformed-input tests.

## v0.3 — Mutation and probes

- generate reproducible environment mutations from explicit seeds;
- add probes for hidden approvals, reward loops, unreachable goals, and schema drift;
- distinguish generated probes from model-discovered behavior in every report;
- measure false positives on reviewed fixtures.

## v0.4 — Release evidence

- compare candidate and baseline agent/environment versions;
- support policy-defined `PASS`, `REVIEW`, and `FAIL` gates;
- emit machine-readable CI summaries and human-readable evidence bundles;
- track variance across repeated runs instead of reporting a single best result.

## Research directions

- counterfactual trajectory replay;
- long-horizon and multi-agent environment diagnostics;
- grader reliability and disagreement analysis;
- conversion of verified failures into training or post-training data;
- domain adapters maintained outside the public synthetic core.

## Non-goals

- claiming complete state-space coverage from sampled trajectories;
- presenting heuristic scores as safety probabilities;
- storing proprietary environment data in the public repository;
- becoming a general-purpose agent builder or production authorization gateway.
