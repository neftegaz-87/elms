# Процесс разработки ELMS

Это навигация по гибридному циклу ELMS: GSTACK помогает уточнить решение и
провести независимый pre-code review, а dev-hub harness ведёт исполняемый цикл
и его долговременную память.

## Где искать документацию

| Слой | Путь | Назначение |
|---|---|---|
| GSTACK-facing | `docs/process/` | Объяснение review-команд, границ и выбора контура |
| GSTACK runtime | `.gstack/` | Локальные screenshots/receipts; не SoT и не git-артефакт |
| Harness state | `memory-bank/` | Product context, решения, queue и PLAN/IMPLEMENT/QA artifacts |
| Product rules | `rules/` | Канон ELMS для агентов |
| Shared workflow | `.dev-hub` + `harness/` | Указатель и ссылки на общие роли, gates и loop из dev-hub |

## Ключевые правила

- **Ветвление (Git Flow):** работа с GSTACK ведётся строго в ветке `sokol`. Создание отдельных веток под каждую задачу/фичу запрещено. Порядок слияния: `sokol` → `dev` → `main`.
- **Управление контейнерами:** запуск — `make local.up`, перезапуск приложения — `make local.restart`, ребилд — `make local.rebuild`, остановка — `make local.down`.

Главный документ с подробным описанием: [GSTACK и harness](gstack-vs-harness-workflow.md).

Правило синхронизации: `docs/process/` объясняет процесс, а `memory-bank/`
фиксирует фактическое состояние конкретной задачи. Не создавать второй
независимый план в `.gstack/` или в документации процесса.
