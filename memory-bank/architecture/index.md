# Architecture and workflow map — ELMS

Это навигационный индекс memory-bank. Полная as-built карта пополняется через
`BACK VAN`; текущий workflow wiring описан в
[`docs/process/gstack-vs-harness-workflow.md`](../../docs/process/gstack-vs-harness-workflow.md).

## Текущие источники

| Область | Источник |
|---|---|
| Product modules and roles | [`product/modules.md`](../product/modules.md) |
| Product vision | [`product/vision.md`](../product/vision.md) |
| UI direction | [`product/design.md`](../product/design.md) |
| Technical context | [`techContext.md`](../techContext.md) |
| System patterns | [`systemPatterns.md`](../systemPatterns.md) |
| Workflow state | [`activeContext.md`](../activeContext.md) |
| Внешние интеграции (канон) | [`integrations.md`](integrations.md) |

## Внешние интеграции и операционный контур (кратко)

**ELMS** — единый внутренний учёт, документооборот, заявки и автоподачи в госреестры. Ручные стыки as-is (Прометей ↔ Bitrix ↔ Минтруд, Bitrix→Минтруд вручную, подача ФРДО сбоку) в целевой модели **автоматизируются внутри ELMS**.

Внешний периметр: Bitrix24 (переходный sync), СДО «Прометей» (миграция), Минтруд, Олимпокс, ФИС ФРДО. **ОНАТО** — донор логики автоподачи в ФИС ФРДО; логика **переносится в ELMS**, внешний ОНАТО не остаётся sole runtime.

Детали, as-is→to-be, DENY — [`integrations.md`](integrations.md).

Правило: explanatory process docs остаются в `docs/process/`, а фактические
решения и stateful artifacts — в `memory-bank/`. Здесь не создаётся второй
независимый каталог планов.
