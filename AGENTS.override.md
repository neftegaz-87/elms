# ELMS — Codex project override

Codex в **этом** каталоге читает `AGENTS.override.md` **вместо** корневого `AGENTS.md`  
(symlink на hub). См. [Codex AGENTS.md discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md): в одном directory — один файл, override побеждает.

## HARD — настройки проекта

Продуктовые инструкции лежат в **`rules/`** (SoT для агентов этого репо).

1. Прочитай и следуй: `rules/README.md`
2. Затем: `rules/elms-approach.mdc`, `rules/elms-design.mdc`, `rules/agents-overlay.md`
3. Модули/роли: `memory-bank/product/modules.md`

**Открыт elms → канон = `rules/`. Не копай CRM/ERP за ролями и доменом.**

## Workflow (общий hub)

Ролевые команды `BACK` / `FRONT` / `APP` / … и router — в hub AGENTS.  
Путь: содержимое `.dev-hub` (сейчас `../../dev-hub`) + `/AGENTS.md`.

Прочитай hub AGENTS **после** `rules/`.  
Секции hub про ERPNext / CRM / CRM Playwright для ELMS **не применять** — см. `rules/agents-overlay.md`.

Документация цикла собрана в двух слоях:

- `docs/process/` — объяснение гибридного GSTACK + harness workflow и ссылки на
  внешнюю GSTACK-документацию;
- `memory-bank/` — состояние ELMS, решения и исполняемые артефакты PLAN /
  DECOMPOSE / IMPLEMENT / QA.

`docs/process/gstack-vs-harness-workflow.md` — точка входа для выбора контура.
Локальные receipts/screens из GSTACK могут лежать в `.gstack/`, но это не SoT и
не должны попадать в git; долговременная память задачи остаётся в `memory-bank/`.
Внешний GSTACK не копируется в ELMS: если он установлен, его slash-skills
используются как точечный review-gate, а выполнение ведётся через hub roles.

### GSTACK routing

- product/engineering review: GSTACK `office-hours` / `plan-*` / `review` по
  необходимости, затем результат фиксируется в `docs/process/` и принятом
  артефакте `memory-bank/`;
- browser acceptance / ship: GSTACK `qa` / `ship` только при наличии внешнего
  skill и подходящего стенда;
- неизвестный запрос к набору GSTACK направляется в установленный GSTACK skill;
  если его нет, использовать соответствующий `BACK` / `FRONT` / `APP` route;
- исходники GSTACK и его slash-команды не добавлять в ELMS автоматически;
- **Правило ветвления (Git Flow):** любой агент или разработчик, работающий через GSTACK, **всегда работает строго в ветке `sokol`**. Запрещено создавать отдельные фиче-ветки под задачи. Изменения накапливаются в `sokol`, затем мерджатся в `dev` и только после проверки — в `main` (`sokol` → `dev` → `main`).

## Cursor vs Codex

| Runtime | Как подхватывает `rules/` |
|---------|---------------------------|
| **Cursor** | `.cursor/rules.d/*.mdc` → symlink на `rules/*.mdc` (`alwaysApply`) |
| **Codex** | этот `AGENTS.override.md` → обязан Read `rules/` |
