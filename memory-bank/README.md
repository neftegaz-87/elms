# Memory-bank ELMS

`memory-bank/` — долговременная память продукта и исполняемый журнал работы:
контекст, решения, очереди и артефакты PLAN / DECOMPOSE / IMPLEMENT / QA.

Документация workflow находится в двух местах:

- процесс и GSTACK-facing обзор — [`docs/process/`](../docs/process/),
  особенно [gstack-vs-harness-workflow.md](../docs/process/gstack-vs-harness-workflow.md);
- фактическое состояние конкретной задачи — здесь, в `memory-bank/`.

`docs/process/` не заменяет memory-bank и не является вторым task ledger.
Решение из GSTACK review после принятия переносится в plan/decision artifact
этого каталога. Локальный `.gstack/` предназначен только для временных
receipts/screens и не является источником истины.

## Основные разделы

- `product/` — vision, modules и design ELMS;
- `decisions/` — принятые архитектурные решения;
- `compliance/` — нормативные и privacy-ограничения;
- `back/`, `front/`, `app/` — role-specific workflow artifacts;
- `activeContext.md` — текущий handoff loop/kernel.
