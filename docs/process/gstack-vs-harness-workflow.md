# GSTACK и harness в ELMS

ELMS использует два связанных, но не взаимозаменяемых контура. GSTACK —
короткий слой product/engineering review. Harness из `dev-hub` — рабочий цикл
с памятью, ownership и проверяемыми артефактами.

## Коротко

| | GSTACK | dev-hub harness |
|---|---|---|
| Назначение | Think → Plan → Review → Test → Ship | VAN → PLAN → DECOMPOSE → IMPLEMENT → QA → DONE |
| Где живёт | Обычно `~/.claude/skills/gstack`; в ELMS не копируется | `harness/` → `dev-hub/harness`, rules/agents/commands |
| Артефакты | review/design/ship evidence в `docs/` | `memory-bank/`, queue и YAML plan/step/QA |
| Основные вызовы | `/office-hours`, `/plan-eng-review`, `/review`, `/qa`, `/ship` | `BACK …`, `FRONT …`, `APP …` |
| SoT | Внешний skill-pack, если установлен | `rules/` + `memory-bank/` ELMS и hub workflow |

Это гибрид: GSTACK не заменяет harness, а harness не требует полного GSTACK
спринта перед каждой маленькой задачей. Внешние slash-skills — опциональный
review-gate; продуктовый цикл и завершение задачи остаются под управлением hub.

## Рабочий цикл

```text
Идея / спорная постановка
  ├─ GSTACK /office-hours (если skill установлен)
  └─ BACK|FRONT|APP CLARIFY
           ↓
      PLAN: WHAT, scope, non-goals, ownership, QA charter
           ↓
      DECOMPOSE → IMPLEMENT sNN → QA → DONE
```

GSTACK-ревью можно запускать перед PLAN или между PLAN и IMPLEMENT для крупного
изменения. Его вывод нужно сохранить в `docs/` без секретов и персональных
данных, а принятое решение и исполняемые обязательства перенести в соответствующий
артефакт `memory-bank/`.

## Артефакты harness

| Команда | Основной артефакт | Смысл |
|---|---|---|
| `BACK VAN` | `memory-bank/architecture/` + `back/van/van-YYYYMMDD.md` | as-built карта |
| `BACK` / `FRONT` / `APP PLAN` | `*/plan/<epic>/` + `roadmap/queue.yaml` | WHAT/HOW и QA contract |
| `… DECOMPOSE` | `yaml/decompose-index.yaml` + `steps/sNN-*.yaml` | исполняемые шаги |
| `… IMPLEMENT` | `*/implement/<epic>/sNN-*.yaml` | TDD, verify, finish |
| `… QA` | `*/qa/<epic>/qa-*.yaml` | приёмка и evidence |
| `… ARCHIVE NOW` | `memory-bank/archive/` | явное архивирование |

Для ELMS продуктовые правила и домен берутся из `rules/` и `memory-bank/product/`.
Роли и технические workflow-gates берутся из hub; CRM/ERP-секции hub для ELMS
не являются каноном.

## Что уже подключено в ELMS

- `.dev-hub` указывает на `../../dev-hub`;
- `harness/`, `.agents/skills/` и `.cursor/rules` подключены к hub;
- `.cursor/rules.d/` содержит project rules ELMS и router harness;
- `Makefile` подключает общий `dev-hub/make/product.mk`;
- `AGENTS.override.md` задаёт порядок: `rules/` → hub AGENTS → workflow artifacts.

Проверка подключения:

```bash
cat .dev-hub
readlink -f harness
readlink -f .agents/skills
```

## Где лежит документация

Документация действительно находится в обоих слоях:

1. GSTACK-facing описание и review-навигация — `docs/process/` (этот каталог).
2. Состояние ELMS, решения и traceability исполнения — `memory-bank/`;
   входная точка: [`memory-bank/README.md`](../../memory-bank/README.md).
3. Внешняя справка GSTACK — в его установленном каталоге
   `~/.claude/skills/gstack` (если он установлен), а не в репозитории ELMS.
4. `.gstack/` — только локальные receipts/screens. Это не место канонической
   документации и не место для product decisions.

Изменение процесса сначала описывается здесь, затем его конкретные последствия
фиксируются в `memory-bank/`. Дублировать полный план между этими каталогами не
нужно.

## Git Flow и ветвление при работе с GSTACK

В проекте ELMS действует строгое правило ветвления для предотвращения бесконтрольного создания веток:

1. **Единая рабочая ветка для GSTACK — `sokol`:**
   - Все агенты и разработчики, использующие скиллы GSTACK (`/autoplan`, `/ship`, `/qa`, `/review` и т.д.), **всегда работают в ветке `sokol`**.
   - **Запрещено** создавать отдельные ветки под каждую задачу или фичу через GSTACK (никаких `feature/...`, `gstack-...`, временных worktree-веток).
2. **Классический Git Flow проекта:**
   ```text
   sokol (рабочая ветка для задач / GSTACK)
     ↓ (pull request / merge после проверки)
   dev (интеграционная ветка / стейджинг)
     ↓ (релиз / стабильная версия)
   main (production-ready)
   ```
   - Любые доработки накапливаются и тестируются в `sokol`.
   - После завершения задачи и прохождения проверок изменения мерджатся в `dev`.
   - Из `dev` после комплексной проверки изменения мерджатся в `main`.
3. **Защита от автосоздания веток в gstack-командах:**
   - При вызове GSTACK-инструментов, которые предлагают создать новую ветку (например, `ship` или `autoplan`), необходимо явно оставаться на `sokol` (`git branch --show-current` должен возвращать `sokol`).

## Управление контейнерами Docker

Для работы со стеком ELMS используются следующие основные команды:

| Действие | Команда через Make | Команда через скрипт / Compose | Что делает |
|---|---|---|---|
| **Запуск** | `make local.up` (или `make dev`) | `bash scripts/docker-up.sh dev up -d` | Поднимает dev-стек в фоне, выполняет миграцию (`create-site`) |
| **Перезапуск приложения** | `make local.restart` | `bash scripts/docker-up.sh dev restart backend websocket queue-short queue-long scheduler frontend` | Перезапускает сервисы Frappe + миграция сайта + clear-cache |
| **Полный перезапуск всех контейнеров** | — | `bash scripts/docker-up.sh dev restart` | Перезапускает все контейнеры (включая DB, Redis, Keycloak) |
| **Ребилд (пересборка и запуск)** | `make local.rebuild` | `bash scripts/docker-up.sh dev up -d --build --force-recreate` | Пересобирает Docker-образы и перезапускает контейнеры |
| **Сборка образов** | `make local.build` | `bash scripts/docker-up.sh dev build` | Пересобирает образы без немедленного перезапуска |
| **Остановка** | `make local.down` | `bash scripts/docker-up.sh dev down` | Останавливает и удаляет контейнеры dev-стека (данные в томах сохраняются) |
| **Статус контейнеров** | `make local.ps` | `bash scripts/docker-up.sh dev ps` | Показывает текущий статус всех контейнеров стека |
| **Логи** | `make local.logs` | `bash scripts/docker-up.sh dev logs -f [service]` | Просмотр логов (можно передать имя конкретного контейнера) |

## Практический выбор

- Нужно быстро проверить, стоит ли строить решение, — GSTACK `/office-hours`
  или `BACK|FRONT|APP CLARIFY`.
- Нужен архитектурный/product/engineering gate — GSTACK review и запись
  результата в `docs/`, затем продолжение через PLAN.
- Нужна трассируемая реализация — harness: PLAN → DECOMPOSE → IMPLEMENT → QA.
- Нужна UI-приёмка ELMS — `FRONT`/`APP` workflow; visual canon берётся из
  `rules/elms-design.mdc`, а не из CRM Desk.

Не устанавливать GSTACK и не добавлять его исходники в ELMS автоматически.
Если skill недоступен, тот же product/engineering intent закрывается ролями
hub и фиксируется в `memory-bank/`.

## Источники

- [`rules/README.md`](../../rules/README.md) — project rules ELMS;
- [`AGENTS.override.md`](../../AGENTS.override.md) — Codex wiring;
- [`memory-bank/README.md`](../../memory-bank/README.md) — durable state;
- `$(cat .dev-hub)/AGENTS.md` — общий router и workflow;
- [upstream GSTACK](https://github.com/garrytan/gstack) — внешний skill-pack.
