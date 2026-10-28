# Tasks

| ID | Задача | Статус | Plan |
|----|--------|--------|------|
| T-000 | Vision + modules + techContext старт | done | — |
| T-B01 | elms-docker-bootstrap | planned | [plan](back/plan/T-B01-elms-docker-bootstrap/md/plan.md) |
| T-B02 | elms-roles-rbac | planned | [plan](back/plan/T-B02-elms-roles-rbac/md/plan.md) |
| T-B03 | elms-sso-keycloak-yandex | planned | [plan](back/plan/T-B03-elms-sso-keycloak-yandex/md/plan.md) |
| T-F01 | elms-desk-sections-roles | planned | [plan](front/plan/T-F01-elms-desk-sections-roles/md/plan.md) |

## Queues

- BACK: [back/roadmap/queue.yaml](back/roadmap/queue.yaml) batch `elms-foundation`
- FRONT: [front/roadmap/queue.yaml](front/roadmap/queue.yaml) batch `elms-desk-shell`

## Порядок IMPLEMENT

1. T-B01 → 2. T-B02 → 3. T-B03 → 4. T-F01

## last

| Дата | Событие |
|------|---------|
| 2026-10-28 | Пересозданы карточки с понятными описаниями: T-B01=35034 (Соколов), T-B02=35035 (Ерохин), T-B03=35036 (Ерохин), T-F01=35037 (Соколов) |
| 2026-10-28 | Правило: после BACK/FRONT PLAN → `scripts/board-sync.sh` (`board-publish.md` + cursor rule) |
| 2026-10-28 | Board actors config: `.loop/board-actors.yaml` + `scripts/board-sync.sh` (Соколов 240 / Ерохин 274) |
| 2026-10-28 | BACK+FRONT PLAN foundation: Docker, RBAC×3, SSO Keycloak+Yandex, Desk workspaces |
| 2026-10-28 | Старт: свой ERP+LMS на Frappe; vendor apps только как примеры |
