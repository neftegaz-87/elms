# Tasks

| ID | Задача | Статус | Plan |
|----|--------|--------|------|
| T-000 | Vision + modules + techContext старт | done | — |
| T-B01 | elms-docker-bootstrap | done | [plan](back/plan/T-B01-elms-docker-bootstrap/md/plan.md) |
| T-B02 | elms-roles-rbac | done | [plan](back/plan/T-B02-elms-roles-rbac/md/plan.md) |
| T-B03 | elms-sso-keycloak-yandex | done | [plan](back/plan/T-B03-elms-sso-keycloak-yandex/md/plan.md) |
| T-A01 | elms-keycloak-login-ui | planned | [plan](app/plan/T-A01-elms-keycloak-login-ui/md/plan.md) |
| T-F01 | elms-desk-sections-roles | planned | [plan](front/plan/T-F01-elms-desk-sections-roles/md/plan.md) |
| T-B04 | bitrix-rest-client | done | [plan](back/plan/T-B04-bitrix-rest-client/md/plan.md) |

## Queues

- BACK: [back/roadmap/queue.yaml](back/roadmap/queue.yaml) batch `elms-foundation`, batch `bitrix-rest`
- FRONT: [front/roadmap/queue.yaml](front/roadmap/queue.yaml) batch `elms-desk-shell`
- APP: [app/roadmap/queue.yaml](app/roadmap/queue.yaml) batch `elms-auth-surface`

## Порядок IMPLEMENT

1. T-B01 → 2. T-B02 → 3. T-B03 → 4. T-A01 → 5. T-F01 (Workspaces only; login affordance covered by T-A01)

## last

| Дата | Событие |
|------|---------|
| 2026-10-29 | BACK CONTEXT SYNC T-B04: Bitrix REST клиент, call.py/scope.py CLI, docs, 37 тестов (всего 81) |
| 2026-10-29 | BACK CONTEXT SYNC T-B03 re-QA: BF-010/BF-011 закрыты, 51 тест, create-site и live HTTP evidence подтверждены |
| 2026-10-29 | BACK CONTEXT SYNC T-B03: Keycloak SSO + Yandex broker, JIT-провижининг, fail-closed роли, 44 теста |
| 2026-10-29 | BACK CONTEXT SYNC T-B02: роли ELMS Admin / Operations / LMS User, Single DocTypes якорей, fail-closed perms |
| 2026-10-28 | BACK PLAN T-B04 bitrix-rest-client: скрипты REST, отдельный вебхук, инструкция |
| 2026-10-28 | Пересозданы карточки с понятными описаниями: T-B01=35034 (Соколов), T-B02=35035 (Ерохин), T-B03=35036 (Ерохин), T-F01=35037 (Соколов) |
| 2026-10-28 | Правило: после BACK/FRONT PLAN → `scripts/board-sync.sh` (`board-publish.md` + cursor rule) |
| 2026-10-28 | Board actors config: `.loop/board-actors.yaml` + `scripts/board-sync.sh` (Соколов 240 / Ерохин 274) |
| 2026-10-28 | BACK+FRONT PLAN foundation: Docker, RBAC×3, SSO Keycloak+Yandex, Desk workspaces |
| 2026-10-28 | Старт: свой Operations+LMS на Frappe; vendor apps только как примеры |
