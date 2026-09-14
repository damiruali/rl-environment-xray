# Experimental graph gradient / residual diagnostic

Written before implementation. This does not invoke the Hodge conjecture.

Each observed directed transition is an oriented edge. Let B have one row per edge:
-1 at its source and +1 at its destination (self-loop row = 0).
Let r contain observed rewards. Solve `min_phi ||B phi - r||²` with sparse LSQR.
The fitted component `B phi` is a graph gradient; `r - B phi` is orthogonal to
the incidence image up to numerical tolerance. Report the residual energy fraction
`||residual||² / ||r||²` (0 if all rewards are 0), solver status and orthogonality error.

Assumptions: finite observed multigraph, unit observation weights (frequently observed
edges therefore have more influence), fixed canonical state projection. Disconnected
components have arbitrary additive potential constants. We do not interpret their absolute values.

The gradient is NOT necessarily business progress. On directed graphs, an algebraic
cycle-space residual is NOT necessarily an executable directed positive-reward cycle.
Parallel observations and inconsistent rewards also produce residual. Finite-horizon
turn and accumulated reward are intentionally absent from business-state node identity;
they remain in raw records. Projection choice materially affects this signal.

No faces / 2-complex were supplied: no defensible separate curl and harmonic components
are claimed. This diagnostic never changes PASS/FAIL. Enable with `--experimental-hodge`.
Neither a zero residual nor a clean sampled graph proves absence of reward hacking.

Reference: Jiang, Lim, Yao, Ye, [Statistical ranking and combinatorial Hodge theory](https://arxiv.org/abs/0811.1067).
Our code uses only the graph incidence least-squares portion, not the complete ranking model.
