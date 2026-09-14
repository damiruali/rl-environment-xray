# Как читать проект

Начните с результата: `artifacts/xray/broken_report.html`, затем `fixed_report.html`.
Далее следуйте одному возврату денег по цепочке файлов.

| Файл | Что делает | Кто вызывает / вход | Куда отдаёт результат |
|---|---|---|---|
| `environments/support_preflight/support_preflight/environment.py` | Создаёт synthetic state и исполняет десять действий. `verify()` отделён от reward | Toolset или scripted probe → scenario, variant, action, args | Transition dictionary: before/after, reward, verifier |
| `environments/support_preflight/support_preflight/taskset.py` | Native V1 Taskset/Task/Toolset; `@tool`, `@reward`, `@metric`, `@stop` | Prime `eval` → конфигурация и scenario rows | MCP results агенту, typed rollout state хосту, trace.info экспортёру |
| `environments/support_preflight/support_preflight/__init__.py` | Экспортирует Taskset; convenience loader вызывает настоящий vf loader | Verifiers plugin discovery / load test | SingleAgentEnv с local null harness |
| `xray/provider_proxy.py` | Локальный relay с ограниченным backoff при 429; сохраняет только числовую usage | Native eval → HTTP completion request | Ответ Groq обратно в тот же model call; без смены модели |
| `xray/demo.py` | Проводит smoke и paired eval; экспортирует trajectories; исполняет отдельные probes | `python -m xray demo [--live]` | baseline/fixed summaries, JSONL, сравнение |
| `xray/models.py` | Контракт Transition/Finding | JSONL reader и collector | Проверенные типизированные записи |
| `xray/collector.py` | Читает/пишет JSONL, записывает JSON | Exporter или scanner → records / path | Файлы без chain-of-thought |
| `xray/graph_builder.py` | Проверяет последовательность; сохраняет параллельные рёбра | Scanner → transitions | NetworkX MultiDiGraph |
| `xray/analyzers/reward_cycles.py` | SCC + непрерывный witnessed positive cycle | Graph + episodes | Critical finding с states/actions/reward/occurrences/provenance |
| `xray/analyzers/reward_consistency.py` | Сравнивает reward/goal; одинаковые наблюдения и действия | Transitions | Critical mismatch / possible hidden-state warning |
| `xray/analyzers/history_dependency.py` | Сопоставляет истории до одинакового наблюдения | Episodes | Warning об ассоциации, не причинное доказательство |
| `xray/analyzers/reachability.py` | Различает witnessed, unknown, reference-unreachable | Sampled rows либо явно exhaustive graph | Scoped statistics / warning |
| `xray/analyzers/coverage.py` | Считает только наблюдённое | Graph + rows | Counts; denominator unknown |
| `xray/analyzers/hodge.py` | Решает sparse least squares для incidence matrix | Graph, только с feature flag | Experimental residual energy и numerical diagnostics |
| `xray/scoring.py` | Применяет прозрачные штрафы за типы findings | Findings | Heuristic health + FAIL/REVIEW/PASS |
| `xray/report.py` | Собирает scan, граф примера, summaries, provenance и hash входа | CLI → JSONL | JSON и HTML |
| `xray/templates/report.html` | Рендерит standalone dashboard и экранирует текст | Jinja → report dict | Открываемый offline HTML без CDN |
| `xray/__main__.py` | CLI, пути, exit codes, вывод ошибок | Пользователь или CI | Artifacts + машинно-проверяемый gate |
| `tests/` | Проверяет business logic, V1 load, serialization, graph, scope, HTML и CLI | pytest | Regression confidence, не safety certification |

## Одна строка trajectory

Дополнительные точки входа: `xray/assets.py` получает measured reports и summaries,
генерирует overview, RESULTS.md и RU/EN drafts; `scripts/capture_screenshots.py`
открывает реальные HTML в Chromium и сохраняет шесть изображений;
`scripts/regrade.py` пересчитывает итоговую rubric по сохранённым состояниям без модели;
`scripts/check_artifacts.py` проверяет matched tasks, provenance, hashes, screenshots
и отсутствие известных API-key/token значений. `scripts/sanitize_attempts.py`
удаляет reasoning из заранее перечисленных ранних неудачных прогонов, сохраняя их статус.

В финальной fixed rubric `@vf.reward` — binary business success, а промежуточный
milestone feedback остаётся отдельной метрикой. Guard добавлен после live eval;
offline regrading подтвердил, что оценки всех 12 model episodes остались прежними.
Подробности — `artifacts/regrading.json`.

`episode_id + step` идентифицируют действие. `state_id → action(args) → next_state_id`
задаёт ребро. `reward` — обратная связь среды; `verifier.business_success` — реальная
цель. `source` сообщает, выбрала действие модель или это заранее заданная проверка.
`terminated` отличается от `truncated`: завершение бизнес-эпизода не равно исчерпанию
лимита шагов. Internal и observable snapshots нужны для двух разных диагностик.

## Пример дефекта

Broken `check_refund_policy()` без нового знания: business state тот же, reward +0.2.
Шесть повторов дают +1.2, возврат не сделан. Награда больше, чем за просто закрытый
тикет (+1), но это свидетельство плохого стимула, а не доказательство будущей RL-policy.

Fixed повторное чтение даёт 0. Первый корректный переход к проверенной eligibility
после анализа billing даёт +0.2, затем повторно не оплачивается. `milestones` входит
в internal identity, поэтому первая выплата не ошибочно считается циклом.
