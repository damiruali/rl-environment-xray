Most RL demos start with training. I tried starting one step earlier: testing the environment itself.

I built RL Environment X-Ray, a small engineering prototype using native Prime Verifiers v1.
The task: a support agent must refund a duplicate subscription charge, notify the customer, and resolve the ticket. Synthetic data, ten MCP tools.

I intentionally introduced three defects:
— +0.2 for repeatedly reading the refund policy;
— +1 for closing a ticket without actually refunding it;
— an approval requirement hidden from the observation.

{% if summaries %}After a one-task, two-rollout smoke test, I ran {{ summaries.broken.episodes }} real Qwen3.8-27B rollouts per variant on matched tasks and settings.
Business success: {{ summaries.broken.business_successes }}/{{ summaries.broken.episodes }} in broken{% if summaries.fixed is defined %}, {{ summaries.fixed.business_successes }}/{{ summaries.fixed.episodes }} in fixed{% endif %}. A high success rate alone does not validate the reward function.
{% else %}This artifact set currently contains scripted probes only, without a model baseline.
{% endif %}
The adversarial probes are labelled separately. They test repeatable reward without business progress. I am not presenting scripted actions as model-discovered exploits, or claiming that reward hacking was learned through RL.

X-Ray builds a transition graph, detects witnessed positive-reward cycles, checks the reward rubric against independent business success, and flags possible hidden-state dependency.

After fixing rewards, closure conditions, and the observation:
broken: {{ reports.broken.health }}/100, {{ reports.broken.status }};
fixed: {{ reports.fixed.health }}/100, {{ reports.fixed.status }} within the tested scope.

That score is a heuristic, not a safety probability. Total state-space coverage is unknown. An experimental graph gradient/residual diagnostic does not affect the gate.

No RL training was performed. The point is to catch defects in the world before spending compute to train an agent in it.

Test the environment before you train the agent.

#AIAgents #ReinforcementLearning #Evaluation #MCP

---
Suggested assets: screenshots 03-positive-loop, 04-xray-fail, 05-fixed-environment, 06-xray-pass; alternatively use the experiment overview. Nothing was posted automatically.
