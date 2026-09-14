Большинство RL demo начинается с обучения. Я попробовал начать на шаг раньше: проверить саму среду.

Собрал RL Environment X-Ray — небольшой инженерный prototype на Prime Verifiers v1.
Сценарий простой: support-агент должен вернуть двойное списание, уведомить клиента и закрыть обращение. Всё синтетическое, десять инструментов доступны через MCP.

В первую версию намеренно добавил три дефекта:
— +0.2 за повторное чтение refund policy;
— +1 за закрытие обращения даже без возврата;
— скрытое требование ручного approval.

{% if summaries %}Сначала — smoke 1 задача × 2 rollout. Затем — по {{ summaries.broken.episodes }} реальных rollout на Qwen3.8-27B для broken и fixed, на одинаковых задачах и настройках.
Business success: {{ summaries.broken.business_successes }}/{{ summaries.broken.episodes }} в broken{% if summaries.fixed is defined %} и {{ summaries.fixed.business_successes }}/{{ summaries.fixed.episodes }} в fixed{% endif %}. Высокий success rate сам по себе не доказывает корректность reward.
{% else %}В этом наборе артефактов пока только scripted probes, model baseline ещё не приложен.
{% endif %}
Важно: заранее заданные adversarial probes учтены отдельно. Именно они проверяют повторяемый доход без бизнес-прогресса. Я не выдаю их за самостоятельно найденный моделью exploit и не утверждаю, что наблюдал обучение reward hacking.

X-Ray строит граф переходов, находит фактически наблюдённые положительные циклы, сравнивает reward с независимым business-success verifier и отмечает possible hidden-state dependency.

После исправления наград, условия закрытия и наблюдаемости — повторный прогон:
broken: {{ reports.broken.health }}/100, {{ reports.broken.status }};
fixed: {{ reports.fixed.health }}/100, {{ reports.fixed.status }} в рамках этой выборки.

Это heuristic health score, не вероятность безопасности. Полное покрытие пространства состояний неизвестно. Экспериментальный graph gradient/residual модуль не влияет на gate.

RL training не запускал. Смысл — поймать дефект мира ДО того, как потратить бюджет на обучение агента в этом мире.

Test the environment before you train the agent.

#AIAgents #ReinforcementLearning #Evaluation #MCP

---
Материалы к посту: screenshots 03-positive-loop, 04-xray-fail, 05-fixed-environment, 06-xray-pass. Можно приложить overview вместо всей карусели. Не опубликовано автоматически.
