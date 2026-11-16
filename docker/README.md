# ELMS Docker Environment & Identity Architecture

Руководство по запуску локального окружения ELMS, настройке SSO через Keycloak и безопасному production-доставлению статических секретов через Vault.

---

## 1. Быстрый старт

### Предварительные требования

- Docker Engine 24+ и Docker Compose v2.
- Запись в локальном файле `/etc/hosts`:
  ```text
  127.0.0.1 elms.localhost
  ```

### Запуск окружения

### Пошаговый маршрут оператора (FR-007 Operator Runbook)

1. **Локальный конфигурационный файл**: Скопируйте `docker/.env.dev.example` в игнорируемый файл `docker/.env.dev`:
   ```bash
   cp docker/.env.dev.example docker/.env.dev
   ```
2. **Dev-only значения**: Используйте только synthetic значения из dev-контракта. Они не являются production credentials, не переносятся в `.env.prod` и не должны попадать в git.
3. **Запуск Compose**: Запустите сервисы и дождитесь выполнения `create-site` и импорта realm через `docker/keycloak/entrypoint.sh`:
   ```bash
   docker compose -f docker/compose.dev.yaml --env-file docker/.env.dev up -d
   ```
   При каждом старте dev-контейнера Keycloak выполняется идемпотентный seed
   `docker/keycloak/seed-demo-users.sh`. Он создаёт или обновляет локальные
   демонстрационные аккаунты из `KEYCLOAK_TEST_*_PASSWORD` и назначает им группы.
   Повторно запустить seed вручную можно командой:
   ```bash
   make keycloak.seed
   ```
4. **Вход через Keycloak**: Откройте `http://elms.localhost:8082/login`. Используется стандартная форма Frappe: отдельная кнопка Keycloak не показывается, её submit связан с локальным password flow Keycloak через `login-keycloak.js`.
5. **Проверка идентичности и ролей**: После callback убедитесь, что пользователь авторизован в Frappe Desk (`/app`), идентичность связана по `sub`, а роли по умолчанию (`Desk User`, `ELMS Learner`) назначены автоматически.
6. **Обновление кэша при изменениях**: При изменении параметров Social Login Key или CSS-ассета выполните очистку кэша:
   ```bash
   docker compose -f docker/compose.dev.yaml exec backend bench --site elms.localhost clear-cache
   ```


1. Скопируйте конфигурацию переменных окружения:
   ```bash
   cp docker/.env.dev.example docker/.env.dev
   ```
2. Запустите сервисы с помощью скрипта-обертки:
   ```bash
   bash scripts/docker-up.sh
   ```
   *(или через Makefile: `make local.up`, или напрямую: `docker compose -f docker/compose.dev.yaml --env-file docker/.env.dev up -d`)*

3. Доступные сервисы и порты:
   - **ELMS / Frappe Desk**: [http://elms.localhost:8082](http://elms.localhost:8082) (порт публикации `8082`)
   - **Keycloak Admin Console**: [http://localhost:8480](http://localhost:8480) (порт публикации `8480`, учетные данные из `KEYCLOAK_ADMIN_PASSWORD`)
   - **MariaDB**: `localhost:3307`
   - **Keycloak PostgreSQL**: внутренний контур `keycloak-db:5432`

---

## 2. Архитектура аутентификации и SSO

### Архитектурный поток: Frappe → Keycloak

```text
+-----------------------+           +-----------------------+
|      Frappe / Desk    | --------> |       Keycloak        |
| (Authorization Plane) | <-------- |   (Identity Plane)    |
+-----------------------+   OIDC    +-----------------------+
```

1. **Разделение ответственности**:
   - **Keycloak** — каноническая плоскость идентичности (Identity Plane): управление локальными пользователями, учетными записями и сессиями.
   - **Frappe** — каноническая плоскость авторизации приложения (Application Authorization Plane): управление ролями, правами на DocType и доступом к Desk.
2. **Keycloak-only контракт**:
   - Frappe принимает только локальный OIDC/password flow доверенного realm `elms`.
   - Realm seed не содержит внешних identity providers или broker mappers.

### Сетевая топология и взаимодействие хостов (Host Networking 8000/8080)

Сетевая схема и сопоставление портов публикации на хосте и внутренних сервисов Docker:

| Узел / Контейнер | Хостовый порт / URL | Контейнерный порт | Описание и маршрутизация |
|---|---|---|---|
| **Frontend (Nginx)** | `8082` (`http://elms.localhost:8082`) | `8080` (`NGINX_LISTEN_PORT`) | Точка входа для браузера. Проксирует запросы на `backend:8000`. |
| **Backend (Frappe)** | — (внутренний) | `8000` (`BACKEND`) | Gunicorn web-сервер Frappe Desk и API `/api/method/...`. |
| **Keycloak IdP** | `8480` (`http://localhost:8480`) | `8080` (`KC_HTTP_PORT`) | SSO Identity Provider, консоль управления и OIDC эндпоинты. |
| **MariaDB** | `3307` | `3306` | СУБД Frappe (база `elms`). |

- **Маршрутизация браузера**:
  - Обращается к интерфейсу Frappe Desk по порту `8082` (`http://elms.localhost:8082`), проброшенному на порт `8080` Nginx (`HTTP_PUBLISH_PORT:-8082:8080`).
  - Перенаправляется на публичный порт Keycloak `8480` (`http://localhost:8480`), проброшенный на порт `8080` Keycloak (`KEYCLOAK_PUBLISH_PORT:-8480:8080`).
- **Межсервисное взаимодействие**:
  - Контейнер `backend` (Frappe) взаимодействует с Keycloak по внутренней Docker-сети `http://keycloak:8080` (валидация JWKS-ключей и userinfo).
  - Разрешение имени `elms.localhost` внутри контейнеров обеспечивается директивой `extra_hosts: ["${SITE_NAME:-elms.localhost}:host-gateway"]`.
- **OIDC callback**: ответ авторизации возвращается на Frappe endpoint `login_via_keycloak`.

#### Команды валидации сетевой доступности (cURL Commands)

- **Keycloak OpenID Discovery (хост -> keycloak:8480)**:
  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8480/realms/elms/.well-known/openid-configuration
  # Ожидаемый результат: 200 (валидный JSON с OIDC метаданными)
  ```
- **Frappe OAuth Redirect Initiator**:
  ```bash
  curl -s -I "http://elms.localhost:8082/api/method/frappe.integrations.oauth2_logins.login_via_keycloak"
  # Ожидаемый результат: 302 Found на realm elms
  ```
- **Frappe Desk Login Page (хост -> nginx:8082 -> backend:8000)**:
  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" http://elms.localhost:8082/login
  # Ожидаемый результат: 200 (страница входа ELMS со стандартной формой)
  ```
- **Frappe OAuth Redirect Initiator**:
  ```bash
  curl -s -I "http://elms.localhost:8082/api/method/frappe.integrations.oauth2_logins.login_via_keycloak"
  # Ожидаемый результат: 302 Found (Location: http://localhost:8480/realms/elms/protocol/openid-connect/auth...)
  ```
- **Межсервисный вызов из контейнера backend в keycloak:8080**:
  ```bash
  docker compose -f docker/compose.dev.yaml exec backend curl -s -o /dev/null -w "%{http_code}\n" http://keycloak:8080/realms/elms/.well-known/openid-configuration
  # Ожидаемый результат: 200
  ```

---

## 3. Синхронизация идентичности и JIT-провижининг (Identity Lifecycle & JIT Provisioning)

### Just-in-Time провижининг (FR-011, AC-9)

ELMS не использует тяжелые механизмы синхронизации директорий. Создание учетных
записей выполняется через локальный Keycloak password flow или через управляемый
invite из ELMS:
1. Пользователь получает приглашение и завершает настройку пароля в Keycloak.
2. При возврате в Frappe создается или находится локальный `User` на основе
   нормализованных OIDC-утверждений (`sub`, `email`, имя, фамилия).
4. Хук `User.after_insert` (`elms.sso.roles.maybe_assign_sso_roles`) проверяет наличие обязательных ролей в базе данных и назначает роли по умолчанию (`Desk User`, `ELMS Learner`) по принципу **fail-closed** (если роль отсутствует в системе — регистрация прерывается).

### Однонаправленная синхронизация (FR-014, AC+9, AC-7)

Синхронизация выполняется строго в одном направлении: **Keycloak → Frappe**.
Двунаправленная или обратная автоматическая перезапись ролей из Frappe в Keycloak **запрещена**.

### Правила сопоставления групп ролям (Group-to-Role Mappings)

При входе пользователя или плановой синхронизации группы Keycloak сопоставляются с утвержденным набором ролей Frappe:

| Группа Keycloak | Роль Frappe | Назначение |
|---|---|---|
| `Administrators` / `/Administrators` | `System Manager` | Полный административный доступ к Desk |
| `Employees` / `/Employees` | `Employee` | Базовый доступ сотрудника |
| `Instructors` / `/Instructors` | `Instructor` | Преподавательский состав LMS |
| `Students` / `/Students` | `Student` | Слушатели курсов |

- **Сохранение прав**: назначение ролей не переопределяет и не удаляет существующие Frappe DocType permissions.
- **Жизненный цикл (Lifecycle)**: при деактивации пользователя в Keycloak (`enabled: false`), в Frappe статус пользователя устанавливается в `enabled: 0`, блокируя доступ к системе.

---

## 4. Отказоустойчивость SSO при сбое Keycloak

### Поведение при недоступности Keycloak

1. При сбое Keycloak Frappe возвращает явную ошибку, редирект не завершается,
   сессия не создаётся.
2. Автоматическая генерация локальных паролей и обход Keycloak запрещены.
   - Административное восстановление выполняется только оператором через Vault/AppRole и проверку preflight; пользовательского login bypass нет.

### Чек-лист проверки веток отказа и конкретные исходы (Outage Branch Checklist Outcomes)

| Ветка проверки | Входные параметры | Выполняемое действие | Конкретный результат (Outcome) | Статус |
|---|---|---|---|---|
| **Штатный локальный вход** | Keycloak доступен, пароль настроен | Ввод учетных данных в стандартной форме | **Keycloak:** проверяет пароль. **Frappe:** создаёт User, назначает роли `Desk User` и `ELMS Learner`, открывает Desk-сессию. | PASS |
| **Сбой Keycloak (Fail-Closed)** | Keycloak недоступен или возвращает 5xx | Попытка входа | **Fail-Closed:** токен и сессия Frappe не создаются. | PASS |
| **Отсутствие роли по умолчанию** | Роль `ELMS Learner` отсутствует в БД Frappe | Прохождение OAuth-аутентификации | **Fail-Closed (BN-005):** Хук `maybe_assign_sso_roles` выбрасывает исключение `frappe.throw`. Создание пользователя отменяется, пользователь без роли не сохраняется. | PASS |

### Операторское восстановление

Прямой Desk login и пользовательский break-glass не входят в production-контур.
При проблеме с Vault остановите promotion, проверьте sealed/unavailable/
unauthorized/missing-render состояние и восстановите AppRole только через
защищённую операторскую сессию и runbook `docs/operations/elms-production.md`.

---

## 5. Почтовый шлюз Yandex SMTP (FR-016)

- Почтовые уведомления ELMS настроены на отправку через Yandex SMTP (`smtp.yandex.ru:465`, SSL).
- **Отказоустойчивость и обработка ошибок (Fail-Closed)**:
  - При недоступности почтового сервера или сетевом сбое отправка почты завершается явной ошибкой `YandexSMTPDeliveryError`.
  - Маскировка сбоев отправки под успешный результат (`|| true` или silent drop) категорически запрещена.

---

## 6. Управление окружениями и команды Makefile

### Цели Makefile

В корне репозитория настроен чистый `Makefile`, делегирующий выполнение в `scripts/docker-up.sh`:

- `make local.up` (или `make dev`) — сборка и запуск dev-стека в фоновом режиме с автоматической синхронизацией create-site.
- `make local.restart` (или `make docker.restart`) — быстрый перезапуск сервисов приложения Frappe (backend, frontend, websocket, scheduler, queues) + миграция сайта и очистка кэша.
- `make local.rebuild` (или `make docker.rebuild`) — пересборка образов и форсированное пересоздание контейнеров (`up -d --build --force-recreate`).
- `make local.build` (или `make docker.build`) — сборка образов без немедленного перезапуска контейнеров.
- `make local.down` — остановка контейнеров локального dev-стека.
- `make local.ps` — вывод статуса работающих контейнеров.
- `make local.logs` — просмотр последних логов сервисов.
- `make dev` — алиас для `local.up`.
- `make prod` / `make prod.up` — staged production-контур на localhost/high-port (build + Caddy `127.0.0.1:18080`).
- `make prod.down` / `make prod.ps` / `make prod.logs` — остановка / статус / логи staged-контура.
- `make prod.smoke` — безопасная проверка merged Compose и Vault contract без запуска контейнеров.
- `make prod.edge.up` — публичный edge на `80/443`; требует явного `ELMS_EDGE_APPROVED=1`.
- `make prod.edge.down` / `make prod.edge.ps` / `make prod.edge.logs` — операции с публичным edge.

### Конфигурация Production (`docker/compose.prod.yaml` + Caddy)

Канонический production-файл — image-only граф: Frappe, MariaDB, Redis, Keycloak,
Vault Agent и Caddy. В нём нет `build`, исходников и host-портов. Сборка разрешена
только в явном `docker/compose.prod.build.yaml` для local/CI или staged rehearsal;
production deploy потребляет готовые release images через `docker/compose.prod.yaml`.
`docker/compose.prod.staged.yaml` публикует только localhost/high-port, а
`docker/compose.prod.edge.yaml` используется только через owner-approved cutover.
MariaDB, Redis, Gunicorn, Nginx (frontend), Keycloak и Vault остаются внутри Docker-сетей.

Значения `docker/.env.dev` — synthetic dev-only contract (`ELMS_SSO_REQUIRE=0`,
локальный review URL и HTTP разрешён). Их нельзя переносить в `docker/.env.prod`:
production metadata остаётся non-secret, а пароли, client secrets и review handoff
рендерятся только Vault Agent.

| Снаружи (firewall) | Сервис | Куда проксирует Caddy |
|---|---|---|
| staged: `127.0.0.1:18080` | `caddy` | локальная rehearsal-проверка маршрутов |
| edge: `80` / `443` | `caddy` | `SITE_NAME` → `frontend:8080`, `AUTH_HOSTNAME` → `keycloak:8080` |
| — | `frontend` / `backend` / `db` / `keycloak` | без publish |

1. Подготовьте DNS: `A`/`AAAA` для `SITE_NAME` и `AUTH_HOSTNAME` на IP сервера.
2. Скопируйте только deployment metadata (секреты в этот файл не добавляются):
   ```bash
   cp docker/.env.prod.example docker/.env.prod
   # SITE_NAME, AUTH_HOSTNAME, SITE_HOST_NAME, KEYCLOAK_PUBLIC_URL,
   # FRAPPE_PUBLIC_URL, ACME_EMAIL и immutable image ref/tag
   ```
   AppRole `role-id`/`secret-id` создаются оператором и хранятся root-owned вне git.
   Заполните Vault path `elms/data/runtime`, затем проверьте его без вывода значений:
   ```bash
   bash scripts/infra/vault_preflight.sh --env-file docker/.env.prod --dry-run
   bash scripts/infra/vault_preflight.sh --env-file docker/.env.prod
   ```
3. Сначала выполните staged rehearsal:
   ```bash
   make prod
   # или: bash scripts/infra/compose_smoke.sh --env-file docker/.env.prod --dry-run
   ```
   Staged smoke использует отдельный Compose project и не должен делить volumes с live.
4. После backup/restore evidence, owner approval и проверки rollback откройте firewall **80/443**
   и отдельно выполните публичный cutover:
   ```bash
   ELMS_EDGE_APPROVED=1 \
   ELMS_EDGE_EVIDENCE=/var/lib/elms/evidence/edge-predecessor.json \
     make prod.edge.up
   ```
5. Проверка публичного маршрута:
   ```bash
   curl -fsS -o /dev/null -w "%{http_code}\n" "https://$SITE_NAME/login"
   curl -fsS -o /dev/null -w "%{http_code}\n" "https://$AUTH_HOSTNAME/realms/elms/.well-known/openid-configuration"
   ```
6. Keycloak OIDC discovery: `https://<AUTH_HOSTNAME>/realms/elms/.well-known/openid-configuration`.

Caddyfile: `docker/caddy/Caddyfile` (авто-TLS Let's Encrypt по `ACME_EMAIL`).  
Keycloak в prod: `start` (не `start-dev`) + `KC_PROXY_HEADERS=xforwarded` + `KC_HOSTNAME=<AUTH_HOSTNAME>`.

Проверки контрактов: `python scripts/infra/check_compose_policy.py`,
`python scripts/infra/check_secret_contract.py`,
`python scripts/infra/check_release_manifest.py`.

---

## 7. Устранение неполадок (Troubleshooting)

1. **Ошибка создания / миграции сайта (`create-site`)**:
   Контейнер `create-site` выполняется однократно при старте и завершается с кодом `0` при успехе. Если бэкенд не стартует из-за `create-site`, проверьте логи:
   ```bash
   docker compose -f docker/compose.dev.yaml logs create-site
   ```
2. **Очистка кэша Frappe**:
   При обновлении метаданных DocType или конфигураций очистите кэш сайта:
   ```bash
   docker compose -f docker/compose.dev.yaml exec backend bench --site elms.localhost clear-cache
   ```
3. **Полный перезапуск стека**:
   ```bash
   make local.down
   make local.up
   ```
4. **Проверка подключения к MariaDB в dev**:
   ```bash
   docker compose -f docker/compose.dev.yaml exec -it db mariadb -u root -p -e "SHOW DATABASES;"
   ```
