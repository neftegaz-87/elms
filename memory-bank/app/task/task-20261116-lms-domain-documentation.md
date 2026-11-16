---
execution: direct-ad-hoc
role: APP
mode: TASK
date: 2026-11-16
slug: lms-domain-documentation
status: completed
---

# Документация связей LMS-сущностей

## Intent

Зафиксировать в `memory-bank/product/` объяснение связей между конструктором
курсов и учебным процессом: иерархию контента, программы, потоки, подписки,
зачисления, зависимости и ERD.

## Contract impact

Изменений runtime-кода и продуктового контракта нет. Добавлена долговременная
документация доменной модели с Mermaid-схемами.

## Files allowlist

- `memory-bank/product/lms-domain-map.md`
- `memory-bank/app/task/task-20261116-lms-domain-documentation.md`

## Required lanes

- Проверка Markdown-файла и Mermaid-блоков.
- Сверка названий и связей с DocType JSON LMS.

## Skipped lanes

- Backend/frontend/build/browser/live_smoke: runtime-код не менялся.

## Selected skills

- None; для документации достаточно правил ELMS и проверки DocType-схем.

## Loop-safety preflight

`activeContext.md` указывает на завершённый контур T-A09; allowlist не пересекает
текущий work shard. `activeContext`, roadmap, plan/decompose, implement artifacts
и loop index не изменяются.

## Evidence

- Сверены Link-поля DocType для `Course`, `Chapter`, `Lesson`, `Program`,
  `Program Course`, `Batch`, `Subscription`, `Enrollment` и
  `Program Enrollment`.
- Добавлен `memory-bank/product/lms-domain-map.md` с иерархией, схемой
  зависимостей, ERD и описанием влияния изменений.
