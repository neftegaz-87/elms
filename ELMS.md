# ELMS

**`rules/`** — SoT настроек этого проекта для агентов.

| Runtime | Проводка |
|---------|----------|
| Cursor | `.cursor/rules.d/*.mdc` → `rules/*.mdc` |
| Codex | `AGENTS.override.md` → Read `rules/` (вместо hub `AGENTS.md`) |

Подробности: `rules/README.md`.

## Быстрый старт и команды

- **Ветка для работы:** `sokol` (merge в `dev`, затем в `main`; никаких отдельных веток под каждую задачу).
- **Запуск стека:** `make local.up` (или `make dev`)
- **Перезапуск приложения:** `make local.restart`
- **Ребилд контейнеров:** `make local.rebuild`
- **Остановка стека:** `make local.down`
- **Статус / логи:** `make local.ps` / `make local.logs`

Подробности процесса и интеграции с GSTACK: `docs/process/gstack-vs-harness-workflow.md`.
