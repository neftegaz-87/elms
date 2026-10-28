# [T-B01 | elms-docker-bootstrap] PLAN

**Дата:** 2026-10-28  
**Режим:** BACK PLAN  
**Уровень:** L3  
**Статус:** active  
**Clarify:** Phase 0 skipped — taxonomy clear (чат 2026-10-28: skeleton + Docker + SSO later; Frappe-only)  
**Prompt:** [md/prompt.md](prompt.md)  
**Queue:** `memory-bank/back/roadmap/queue.yaml` → `T-B01` / `T-B01-elms-docker-bootstrap`  
**Batch:** `elms-foundation`  
**Deps:** []  
**Unlocks:** `T-B02-elms-roles-rbac`, `T-B03-elms-sso-keycloak-yandex`  
**Skills (Phase 1):** writing-plans · docker/frappe_docker patterns from etalon  
**SUSPENSION GUARD:** active — plan output unlimited (§0.0)

---

## MULTI-EPIC PLAN — 3 эпика (batch `elms-foundation`)

| Queue id | epic_id | Ось | Deps | Appetite hint |
|----------|---------|-----|------|---------------|
| T-B01 | T-B01-elms-docker-bootstrap | Docker + site + скелет app | — | 2–4d |
| T-B02 | T-B02-elms-roles-rbac | Admin + Operations + LMS роли и placeholder DocTypes | T-B01 | 1–2d |
| T-B03 | T-B03-elms-sso-keycloak-yandex | Keycloak + Yandex Social Login | T-B01, T-B02 | 3–5d |

**Chat lock:** Frappe Framework only; custom app `elms`; Keycloak in compose as the canonical IdP/broker; Yandex 360 as external IdP and corporate mail; Frappe as the authorization source of truth; roles Admin/Operations/LMS; Desk sections via Workspaces (FRONT T-F01).

---

## Context consumed

| Path | Что вошло в axiom / Deps / FR |
|------|-------------------------------|
| `memory-bank/product/vision.md` | Своя платформа Operations+LMS; vendor apps не ставим; эталон только паттерны |
| `memory-bank/product/modules.md` | Runtime frappe + elms; модули Core/Operations/LMS planned |
| `memory-bank/techContext.md` | Frappe v15; bench/Docker open; layered patterns из эталона |
| `memory-bank/activeContext.md` | Старт; bootstrap next |
| Эталон `frappe-erp-crm/docker/compose.dev.yaml` | Services pattern: db, redis, configurator, create-site, backend, frontend |
| Эталон `frappe-erp-crm/docker/Dockerfile` | Image build; **урезать** до frappe+elms |
| Эталон `frappe-erp-crm/apps.json` | Формат apps list — у нас только frappe, elms |
| `.cursor/rules/elms-approach.mdc` | AlwaysApply: no vendor ERP/LMS as product apps |

---

## Delivery closure

| Capability / outcome | Classification | Production entrypoint and caller | Success / failure enforcement | Independent outcome test | Foundation approval / follow-up |
|---|---|---|---|---|---|
| Dev Docker stack + Frappe site + app elms | `vertical_slice` | `scripts/docker-up.sh` / `docker compose -f docker/compose.dev.yaml --env-file docker/.env.dev up -d --build` → browser `/login` | create-site non-zero exit → stack unhealthy; no fake «OK» if site missing | Given clean volumes; When up --build; Then `/login` 200 and Administrator login works; `bench --site $SITE list-apps` shows frappe+elms only | Chat 2026-10-28; follow-up T-B02/T-B03 |

---

## Technology axiom (replace-not-wrap)

| Выбор | Machine input | FORBIDDEN после эпика |
|-------|---------------|------------------------|
| Frappe Framework v15 как единственный framework | дерево `frappe/` в monorepo (vendor copy или git submodule с version-15) | Django/FastAPI/второй HTTP-сервер рядом |
| Custom app `elms` path `elms/elms/` | `apps.json` + `sites/apps.txt` = `frappe\nelms` | Добавление erpnext/crm/lms/education/hrms в apps.txt/image |
| Compose из эталона, slim | `docker/compose.dev.yaml` services listed in HOW | Копировать полный suite apps mounts из frappe-erp-crm |
| Fail-closed create-site | entrypoint exit code propagates; depends_on condition completed_successfully | `\|\| true` / ignore install errors / sleep-and-pretend |
| Keycloak service present | containers `keycloak` + `keycloak-db` up (realm seed may be stub) | Откладывать контейнер «на T-B03» без сервиса в compose |
| Identity boundary | Frappe trusts only Keycloak; Keycloak brokers Yandex; Frappe owns app roles | Прямой Frappe → Yandex как второй неуправляемый login path |
| User/role sync | Keycloak owns identity lifecycle; Frappe owns effective permissions; mapping is explicit and idempotent | Дублирование пользователей или двунаправленный конфликт ролей |

As-built Makefile (neftegaz leftovers) и пустой repo — **sunset inventory**, не шаблон runtime.

---

## Продуктовая спека (WHAT)

Команда разработки получает локальный ELMS: открывает URL site, видит стандартный Frappe login, входит как Administrator. В Desk ещё нет бизнес-разделов с данными (роли/workspaces — следующие эпики), но app `elms` установлен и модули Core/Operations/LMS объявлены. Keycloak контейнер уже в стеке и является единственной точкой SSO для Frappe; Yandex 360 подключается к Keycloak как внешний IdP и одновременно остаётся корпоративной почтой. Локальные пользователи Keycloak и break-glass Administrator позволяют сохранить вход при недоступности Yandex.

### Module naming decision

- **Operations / Бизнес-операции** заменяет `ERP` как название продуктового модуля.
- В Operations входят BPM/workflows, электронные документы, маршруты согласования, AI-автоматизация, задачи и интеграции.
- **LMS** отвечает за обучение, курсы, программы, зачисления и оценки.
- **Core** содержит общие настройки, пользователей и инфраструктурные сущности.
- Классический ERP-контур (финансы, склад, закупки и т.п.) пока не заявляется и не должен подразумеваться названием роли или модуля.
- В техническом skeleton `modules.txt` фиксируется как `Core`, `Operations`, `LMS`; внутренний Python package для Operations может быть `business_operations`.

### Identity architecture decision

- **Keycloak** — каноническая плоскость идентичности: пользователи, группы, статусы, сессии и внешний IdP broker.
- **Yandex 360** — внешний IdP для обычного входа сотрудников и SMTP-провайдер; Frappe не ходит в Yandex напрямую.
- **Frappe** — каноническая плоскость авторизации приложения: роли, DocType permissions и доступ к Desk.
- Синхронизация идёт направленно `Keycloak → Frappe`: lifecycle пользователя и согласованные group-to-role mappings. Двунаправленная запись ролей запрещена до отдельного решения о владельце данных.
- Для отказоустойчивости должны существовать локальные credentials в Keycloak для администраторов и тех пользователей, которым нужен вход без Yandex. Один только brokered Yandex account не даёт offline-аутентификацию.

---

## Product probe (office-hours lite)

| # | Question | Answer / Probe | Decision / Impact on PLAN |
|---|----------|----------------|---------------------------|
| 1 | Reframe | Боль = нет воспроизводимого site | Docker vertical slice first |
| 2 | Narrowest wedge | frappe+elms+db+redis+nginx+create-site | Без домена |
| 3 | Pre-mortem | «Скопировали весь frappe-erp-crm apps» | FR DENY vendor apps + verify list-apps |
| 4 | Distribution | README docker + .env.example | Документ в docker/README.md |
| 5 | Technical leverage | Эталон compose/Dockerfile | Slim fork, не wrap |
| 6 | Appetite | 2–4d; prod compose cut optional stub | prod compose minimal OK; TLS out |

---

### User Stories

| # | Story | Priority | Independent Test |
| :--- | :--- | :--- | :--- |
| US-001 | Как разработчик, я хочу поднять стек одной командой, чтобы не собирать bench вручную. | P0 | `docker compose … up -d --build` → healthy backend + frontend |
| US-002 | Как администратор, я хочу войти Administrator/пароль из env, чтобы проверить site. | P0 | Login form accepts credentials; redirected to Desk `/app` |
| US-003 | Как разработчик, я хочу пустой app `elms` с modules Core/Operations/LMS, чтобы наращивать DocTypes. | P0 | App on site; modules.txt contains three names |
| US-004 | Как разработчик, я хочу Keycloak в compose, чтобы SSO-эпик не добавлял инфраструктуру с нуля. | P1 | `docker compose ps` показывает keycloak running |

#### Acceptance Scenarios — US-001

- **Given:** склонированный репо, скопированный `docker/.env.dev` из example  
- **When:** `./scripts/docker-up.sh up -d --build` (или эквивалент compose)  
- **Then:** сервисы db, redis-*, backend, frontend, create-site completed; frontend публикует HTTP_PUBLISH_PORT

#### Acceptance Scenarios — US-002

- **Given:** стек up, SITE_NAME и ADMIN_PASSWORD в env  
- **When:** POST login Administrator  
- **Then:** session cookie; Desk доступен; wrong password → явная ошибка Frappe (не 500 без текста)

#### Acceptance Scenarios — US-003

- **Given:** create-site finished  
- **When:** `bench --site $SITE list-apps` и чтение `elms/elms/modules.txt`  
- **Then:** apps = frappe, elms; modules = Core, Operations, LMS

#### Acceptance Scenarios — US-004

- **Given:** compose up  
- **When:** inspect keycloak container  
- **Then:** listening на KEYCLOAK_PUBLISH_PORT; realm import path существует (полный client config — T-B03)

---

### Functional Requirements (FR-###)

- **FR-001:** Добавить `frappe/` version-15 в monorepo (git submodule на `frappe/frappe` branch `version-15` **или** vendor copy из эталона `/home/aero/PyProject/PersonalProject/frappe-erp-crm/frappe`). Зафиксировать способ в `docker/README.md` и `memory-bank/techContext.md`.
- **FR-002:** Создать app skeleton `elms/`:
  - `elms/pyproject.toml` (name `elms`)
  - `elms/elms/__init__.py`, `hooks.py`, `modules.txt` (`Core\nOperations\nLMS`), `patches.txt`, `install.py` (пустые/минимальные after_install stubs без ролей — роли в T-B02)
  - `elms/elms/public/`, `elms/elms/templates/` как пустые деревья при необходимости bench
- **FR-003:** Корневой `apps.json`:
  ```json
  [
    {"name": "frappe", "path": "frappe"},
    {"name": "elms", "path": "elms"}
  ]
  ```
- **FR-004:** `docker/Dockerfile`: multi-stage/base по эталону, но `bench get-app`/`COPY` только frappe+elms; `sites/apps.txt` только эти два.
- **FR-005:** `docker/compose.dev.yaml` services:
  - `db` MariaDB 11.8 utf8mb4
  - `redis-cache`, `redis-queue`
  - `configurator` — пишет apps.txt, db_host, redis URLs
  - `create-site` — `bench new-site` + `bench --site install-app elms`; fail-closed
  - `backend`, `websocket`, `queue-short`, `queue-long`, `scheduler`
  - `frontend` nginx
  - `keycloak-db` (Postgres), `keycloak` (image quay.io/keycloak/keycloak, start-dev или import)
  - volumes: bind-mount `../frappe`, `../elms` для editable develop
- **FR-006:** `docker/.env.dev.example` с ключами: `COMPOSE_PROJECT_NAME`, `SITE_NAME` (default `elms.localhost`), `ADMIN_PASSWORD`, `DB_PASSWORD`, `HTTP_PUBLISH_PORT` (default 8082), `DB_PUBLISH_PORT`, `KEYCLOAK_PUBLISH_PORT`, `KEYCLOAK_ADMIN`, `KEYCLOAK_ADMIN_PASSWORD`, placeholders `KEYCLOAK_CLIENT_ID/SECRET`, `YANDEX_CLIENT_ID/SECRET` (используются Keycloak для brokered Yandex login в T-B03).
- **FR-007:** `scripts/docker-up.sh` — wrapper как в эталоне (dev default).
- **FR-008:** `docker/README.md` — быстрый старт, hosts entry `elms.localhost`, порты, login.
- **FR-009:** Убрать/заменить neftegaz-specific targets в корневом `Makefile` так, чтобы `make` не ссылался на чужой проект; минимальные targets `local.up` / `local.down` на elms compose **или** документировать только `scripts/docker-up.sh` как SoT и оставить Makefile без ложных remote-dev (явный delete устаревших phony).
- **FR-010:** Keycloak: volume/import dir `docker/keycloak/` с минимальным `realm-elms.json` stub (realm name `elms`) — детальный client `elms-frappe` донастраивается в T-B03, но файл и сервис обязательны.
- **FR-011:** Health: backend/frontend зависят от successful create-site; при ошибке install-app контейнер create-site = exited non-zero и backend не стартует как healthy path.
- **FR-012:** Frappe принимает внешний SSO только от Keycloak (OIDC/SAML по поддержанному адаптеру); прямой Frappe → Yandex login не является production path.
- **FR-013:** Keycloak подключает Yandex 360 как внешний IdP и сохраняет стабильный внешний subject, verified email/domain и display name; связывание аккаунтов только по email запрещено.
- **FR-014:** User lifecycle и согласованный group-to-role mapping синхронизируются из Keycloak в Frappe идемпотентно: `enabled`/`disabled`, создание пользователя и назначение явно разрешённых ролей. Эффективные DocType permissions остаются в Frappe.
- **FR-015:** В Keycloak предусмотрены локальные credentials для break-glass Administrator и выбранных fallback-пользователей; при недоступности Yandex они могут войти через Keycloak, а brokered-only пользователи получают явную ошибку без ложного success.
- **FR-016:** Почтовые уведомления ELMS идут через Yandex SMTP независимо от SSO; недоступность Yandex SMTP не должна маскироваться под успешную отправку.

### Non-Functional Requirements (NFR-###)

- **NFR-001:** Первая сборка image может быть долгой; документировать.
- **NFR-002:** Секреты только в `.env.dev` (gitignore); example без реальных secret.
- **NFR-003:** Логи create-site читаемы (`docker compose logs create-site`).
- **NFR-004:** Ошибки bench/MariaDB не глотать; exit code ≠ 0.
- **NFR-005:** Keycloak/Yandex secrets и локальные fallback credentials не попадают в git-tracked files.
- **NFR-006:** Синхронизация пользователей и ролей повторяема, наблюдаема в логах и не удаляет локальные Frappe-права молча.

### Success Criteria

| ID | Результат | Проверка |
| :--- | :--- | :--- |
| SC-001 | Stack up | compose ps + curl `/login` |
| SC-002 | Admin login | manual/scripted login |
| SC-003 | Apps only frappe+elms | `bench list-apps` |
| SC-004 | Keycloak up | compose ps keycloak |
| SC-005 | modules.txt | Core, Operations, LMS |
| SC-006 | Frappe trusts Keycloak only | issuer/audience check and login through Keycloak |
| SC-007 | Yandex outage fallback | local Keycloak user reaches Frappe while Yandex IdP is unavailable |
| SC-008 | Identity/role reconciliation | repeat sync converges; effective permissions remain Frappe-owned |

### Assumptions

- Host Docker available; ports 8082/3307/KEYCLOAK free or overridden via env.
- Frappe v15 совместим с MariaDB 11.8 как в эталоне.
- Пользователь добавит `127.0.0.1 elms.localhost` в hosts при необходимости.

### Clarifications

- App layout locked: `elms/elms/hooks.py` (чат/plan).
- Keycloak in T-B01 compose; Frappe trusts Keycloak; Yandex is configured in Keycloak as the external IdP and OAuth/OIDC wiring is T-B03.
- Keycloak is the user administration plane; Frappe remains the application authorization plane. Initial sync is one-way and explicit: Keycloak → Frappe.
- Prod compose: допустим stub `compose.prod.yaml` копией dev без bind-mounts **или** отложить файл — если откладываем, явная строка Out в AC− «prod compose not claimed done». **Решение:** добавить minimal `compose.prod.yaml` без TLS (TLS out).

## AC

1. Compose up создаёт site и ставит `elms`.
2. Administrator login работает с env password.
3. `list-apps` = frappe, elms only.
4. modules.txt = Core, Operations, LMS.
5. Keycloak (+ db) running.
6. README описывает старт.
7. AC− vendor apps 0.
8. SSO path is Frappe → Keycloak → Yandex 360; a local Keycloak fallback path is documented and tested for an enabled user.
9. Keycloak identity lifecycle and approved role mappings reconcile into Frappe without replacing Frappe permission rules.

### AC−

1. Нет erpnext/crm/lms/education/hrms/payments/insights/raven/wiki/drive в `apps.txt` / Dockerfile COPY apps.
2. Нет `\|\| true` на create-site / install-app.
3. Нет client_secret в git-tracked files.
4. Нет претензии «прямой Frappe → Yandex login работает»: SSO идёт через Keycloak.
5. Нет доменных DocTypes Course/Item/etc.
6. Нет обещания offline-входа для brokered-only Yandex users без локальных Keycloak credentials.
7. Нет двунаправленной автоматической перезаписи ролей между Keycloak и Frappe.

## Boundary / negative cases

| ID | Class | Input / condition | Expected | Maps TM |
|----|-------|-------------------|----------|---------|
| BN-001 | misconfig | пустой ADMIN_PASSWORD | create-site FAIL явная ошибка | TM-001 |
| BN-002 | infra | MariaDB not ready | wait-for-it/retry затем fail, не silent empty site | TM-002 |
| BN-003 | deny vendor | случайный COPY erpnext в Dockerfile | review FAIL; list-apps test FAIL | TM-003 |
| BN-004 | authz | wrong admin password | login reject | TM-004 |
| BN-005 | duplicate | повторный up на существующих volumes | site не дублируется ломая данные; idempotent path documented | TM-005 |
| BN-006 | port conflict | HTTP_PUBLISH_PORT занят | compose error явный | TM-006 |
| BN-007 | dependency outage | Yandex IdP unavailable | enabled local Keycloak fallback user can login; brokered-only user gets explicit auth error | TM-008 |
| BN-008 | drift | Keycloak user/group state differs from Frappe | idempotent sync reconciles only declared fields and logs result | TM-009 |
| BN-009 | authz | Keycloak group has no approved Frappe mapping | user authenticates but receives no implicit elevated role | TM-010 |

Checklist: empty password BN-001; infra BN-002; deny BN-003; authz BN-004; duplicate BN-005; misconfig ports BN-006; IdP outage BN-007; sync drift BN-008; unmapped group BN-009.

## Техника / архитектура (HOW)

### Target tree

```text
/home/aero/PyProject/elms/
├── frappe/                    # framework v15
├── elms/
│   ├── pyproject.toml
│   └── elms/
│       ├── hooks.py
│       ├── modules.txt
│       ├── patches.txt
│       ├── install.py
│       └── __init__.py
├── apps.json
├── docker/
│   ├── Dockerfile
│   ├── compose.dev.yaml
│   ├── compose.prod.yaml
│   ├── .env.dev.example
│   ├── README.md
│   └── keycloak/
│       └── realm-elms.json
├── scripts/
│   └── docker-up.sh
└── memory-bank/
```

### Compose topology

```text
browser -> frontend:8080(nginx) -> backend:8000
backend -> db:3306
backend -> redis-cache, redis-queue
create-site -> db (bench new-site + install-app elms)
keycloak -> keycloak-db:5432
browser -> keycloak:KEYCLOAK_PUBLISH_PORT (admin + later OIDC)
```

### hooks.py minimal fields

- `app_name = "elms"`
- `app_title = "ELMS"`
- `app_publisher` / `app_description` / `app_license`
- `required_apps = []`
- modules via `modules.txt` only

### create-site command sketch (fail-closed)

```bash
bench new-site "$SITE_NAME" --mariadb-root-password "$DB_PASSWORD" \
  --admin-password "$ADMIN_PASSWORD" --no-mariadb-socket
bench --site "$SITE_NAME" install-app elms
bench --site "$SITE_NAME" set-config developer_mode 1
```

Любой non-zero → container exit ≠ 0.

## Eng review spine

### Data flow

```text
[docker-up] -> [build image frappe+elms] -> [db/redis healthy]
  -> [configurator apps.txt+redis] -> [create-site User Administrator in MariaDB]
  -> [backend gunicorn] -> [nginx /login]
```

### Failure matrix

| Component | Failure | Detection | Response | Test ID |
|-----------|---------|-----------|----------|---------|
| env | missing ADMIN_PASSWORD | create-site | exit ≠0 | TM-001 |
| db | down | healthcheck | backend not start | TM-002 |
| Dockerfile | vendor app copied | list-apps / rg | FAIL gate | TM-003 |
| login | bad password | Frappe auth | deny | TM-004 |
| volumes | re-up | site exists branch | documented idempotent | TM-005 |
| bind | port in use | docker error | fail | TM-006 |

### Eng spine self-check

| Dimension | Score | Gap |
|-----------|-------|-----|
| Data flow | 5 | — |
| Failure | 5 | — |
| Testability | 4 | e2e login script optional |

## Replacement / sunset

### A. Code / modules

| Устаревает | Замена | Policy |
|------------|--------|--------|
| Makefile neftegaz remote-dev / loki targets | elms docker-up SoT | delete or gut misleading targets in-epic |
| Пустой git-only repo без runtime | docker+apps tree | add |

### B. Docs

| Устаревает | Замена |
|------------|--------|
| techContext «bench vs docker open» | Docker = default SoT after T-B01 |

### Replacement cleanup

Greenfield runtime — `deletes`: neftegaz Makefile noise. Verify: `rg -n neftegaz Makefile` → 0 after epic.

## Test map (TM)

| ID | Type | Setup | Assert |
|----|------|-------|--------|
| TM-001 | manual/script | empty ADMIN_PASSWORD | create-site fails |
| TM-002 | compose | stop db | depends_on/health prevents false ready |
| TM-003 | static | rg Dockerfile/apps.json | no vendor app names |
| TM-004 | manual | wrong password | login fail |
| TM-005 | manual | second up | site intact |
| TM-006 | manual | port busy | compose error |
| TM-007 | smoke | happy path | /login 200 + list-apps |
| TM-008 | integration | Yandex unavailable | local Keycloak fallback user reaches Frappe; brokered-only path fails explicitly |
| TM-009 | integration | repeat user/group sync | Frappe state converges and approved roles do not duplicate |
| TM-010 | integration | unmapped Keycloak group | no elevated Frappe role is granted implicitly |

## Implementation stages (advisory for DECOMPOSE)

| Stage | Delta |
|-------|-------|
| s01 | Vendor frappe + apps.json + app skeleton |
| s02 | Dockerfile slim |
| s03 | compose.dev + env example + docker-up |
| s04 | create-site fail-closed + verify login |
| s05 | keycloak(+db) + realm/client + Yandex external-IdP configuration |
| s06 | Frappe↔Keycloak SSO + identity lifecycle/approved role mapping + Yandex outage fallback |
| s07 | README + Makefile cleanup + compose.prod minimal |

## Out of scope

- Role fixtures / DocType permissions (T-B02)
- Direct Frappe → Yandex Social Login; Yandex is brokered through Keycloak in T-B03
- Desk Workspace JSON (FRONT T-F01)
- Domain DocTypes
- TLS, MFA, production IdP hardening
- Full SCIM/HR bidirectional provisioning and arbitrary bidirectional role sync (separate follow-up after the one-way contract is proven)

## Risks

| Risk | Mitigation |
|------|------------|
| Frappe submodule size / clone time | document; optional vendor copy from etalon path |
| Keycloak image ARM | use official multi-arch; note in README |
| Site name cookie/host | SITE_NAME=elms.localhost + hosts |
| Yandex broker protocol | validate Yandex OAuth/OIDC/SAML compatibility with Keycloak before locking the adapter; if a custom provider is required, keep it explicit and tested |
| Identity/role drift | one-way idempotent sync with audit log; Frappe remains the final permission gate |

## Open questions → resolved

| Q | Resolution |
|---|------------|
| App path apps/elms vs elms/elms | **elms/elms/** |
| Include Keycloak now? | **Yes**, service in T-B01 |
| Prod TLS? | **Out** |
