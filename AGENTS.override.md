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
Путь: содержимое `.dev-hub` (сейчас `../dev-hub`) + `/AGENTS.md`, т.е. обычно `../dev-hub/AGENTS.md`.

Прочитай hub AGENTS **после** `rules/`.  
Секции hub про ERPNext / CRM / CRM Playwright для ELMS **не применять** — см. `rules/agents-overlay.md`.

## Cursor vs Codex

| Runtime | Как подхватывает `rules/` |
|---------|---------------------------|
| **Cursor** | `.cursor/rules.d/*.mdc` → symlink на `rules/*.mdc` (`alwaysApply`) |
| **Codex** | этот `AGENTS.override.md` → обязан Read `rules/` |
