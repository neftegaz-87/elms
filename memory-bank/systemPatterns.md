# Архитектурные паттерны системы (systemPatterns)

**Дата:** 2026-10-31
**Статус:** Базовые системные паттерны подтверждены по результатам T-B06 QA PASS, T-B05 QA PASS, T-A01 APP QA PASS, T-B04 QA PASS и T-B03 re-QA PASS

## 1. Slim Single-App Frappe Architecture

- **Принцип:** Репозиторий содержит платформу `elms` поверх чистого фреймворка `frappe` (v15). Сторонние тяжелые приложения (`erpnext`, `crm`, `hrms`, `education`) исключены из `apps.json`, `sites/apps.txt` и Docker-образов.
- **Структура приложения:** `elms` с модулями `ELMS Core`, `Operations`, `LMS`; namespace `Core` Frappe не переопределяется.
- **Правило расширения:** Новая бизнес-логика реализуется строго внутри `elms/` через стандартные Frappe DocTypes, Document Controller hooks и whitelist API, без создания параллельных web-фреймворков.

## 2. Fail-Closed Bootstrap Pattern

- **Принцип:** Автоматическое развёртывание сайта и приложений должно завершаться с ненулевым кодом выхода при любой ошибке (никаких `|| true`, проигнорированных ошибок миграции или скрытых fallback-логик).
- **Реализация:** Сервис `create-site` в `docker/compose.dev.yaml` выполняет `bench new-site` и `bench --site ... install-app elms`. Другие сервисы топологии зависят от успешного завершения `create-site` (`condition: service_completed_successfully`).
- **Runtime evidence:** T-B03 re-QA подтвердил `create-site` с exit code 0 и установленными приложениями `frappe`/`elms`; live HTTP smoke обязан сохранять typed evidence и не может подменяться synthetic trace.

## 3. Central Identity Broker Pattern (SSO & RBAC)

- **Принцип:** Строгое разделение плоскости аутентификации/идентичности (Identity Plane) и плоскости авторизации/прав (Application Authorization Plane):
  - **Keycloak (Identity Broker):** центральный брокер идентичности, управляющий жизненным циклом пользователей и федерацией внешних провайдеров. Внешний Identity Provider Yandex 360 регистрируется как brokered OIDC IdP внутри Keycloak с точкой терминации `/realms/elms/broker/yandex/endpoint`.
  - **Frappe (Application Plane):** доверяет аутентификации Keycloak через единственный Social Login Key `Keycloak` с каноническим redirect `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak`. Прямой Social Login Key Yandex или параллельные OAuth-модули в Frappe строго запрещены.
  - **Конфигурация и секреты:** Frappe `site_config` содержит только `keycloak_login` (`client_id`, `client_secret`). Секреты внешнего IdP Yandex передаются только в контейнер Keycloak. Git tracking свободен от открытых секретов.
  - **Conf Gating:** Включение Social Login Key (`enable_social_login = 1`) происходит только при наличии действительных учетных данных в `site_config`.
  - **Just-in-Time (JIT) Provisioning:** Пользователи создаются в Frappe строго в момент первого успешного входа через Keycloak брокер (`first broker login`), сопоставляясь по неизменяемому `sub` и верифицированному email. Массовый импорт каталога запрещён.
  - **Fail-Closed Role Assignment Hook:** Хук `User.after_insert` (`elms.sso.roles.maybe_assign_sso_roles`) гарантированно присваивает новому SSO-пользователю роли `Desk User` и `ELMS LMS User`. Если хотя бы одна из ролей отсутствует в базе данных, операция выбрасывает `frappe.throw`, откатывая транзакцию и предотвращая появление учетных записей без прав.
  - **Outage Branching & Local Fallback:** Сбой внешнего IdP Yandex завершается fail-closed (никаких фиктивных сессий). Для утверждённых пользователей поддерживается резервный вход по локальным паролям Keycloak (`fallback.user@elms.local`), а для аварийного восстановления — локальный логин Administrator в Desk UI (Break-Glass Level 2).
  - **Live Boundary Evidence:** `scripts/live_smoke.sh` проверяет Frappe login, Keycloak authorization и Yandex broker route, пишет `docs/reports/sso-browser-api-trace.json`; отсутствие реальных Yandex credentials/callback фиксируется как `not_run`, а не как fabricated success.

## 4. Multi-Service Container Topology

- **Локальный контур (`docker/compose.dev.yaml`):**
  - `backend` — HTTP Gunicorn сервер Frappe.
  - `websocket` — real-time Node.js socket.io сервер Frappe.
  - `queues` — Celery / Redis фоновые очереди (`default`, `short`, `long`).
  - `scheduler` — планировщик периодических задач Frappe.
  - `configurator` — инициализация общих настроек `common_site_config.json`.
  - `create-site` — разовый раннер инициализации базы данных и установки приложения.
  - `db` — MariaDB 11.
  - `redis` — in-memory хранилище кэша и очередей.
  - `keycloak` + `keycloak-db` — сервис единого входа (Keycloak 24) и база данных PostgreSQL.
- **Производственный контур (`docker/compose.prod.yaml`):** аналогичный стек с production-настройками и политиками перезапуска.

## 5. Section Anchor Pattern for DocPerm & Workspace Segregation

- **Принцип:** До реализации разветвлённых предметных DocTypes границы доступа между разделами системы (Operations, LMS, ELMS Core/Settings) фиксируются с помощью легковесных Single DocTypes (`ELMS Operations Section`, `ELMS LMS Section`, `ELMS Settings Section`).
- **Свойства якорей:** Якорные сущности не содержат доменных полей и бизнес-логики, служа точками привязки прав `DocPerm` и будущих рабочих пространств Desk (Workspace JSON).
- **Жизненный цикл прав (Lifecycle Hooks):** Идемпотентная инициализация ролей (`ensure_roles`) и распределение прав (`ensure_section_perms`) выполняются при `after_install` и `after_migrate` (`elms/elms/install.py`).
- **Fail-Closed & No-Silent-Fallback:** Любой сбой создания роли или назначения прав генерирует исключение (`frappe.throw`), предотвращая запуск системы в полунастроенном состоянии. Использование `try/except: pass`, тихий возврат при отсутствии подключения к БД или пропуск при отсутствии DocType / Custom DocPerm запрещены и контролируются fail-closed исключениями.
- **Сохранение платформенных ролей:** Системные роли Frappe (`Administrator`, `System Manager`) не блокируются и сохраняют административный доступ.

## 6. Isolated External REST Integration Pattern (Bitrix24 REST Client)

- **Single Dedicated Transport:** Единственная точка входа и транспортный модуль `scripts/bitrix/rest_client.py` (`post_json`, `WebhookEndpoint`, `CallArgs`, `RestEnvelope`, `BitrixRestError`), выполняющий валидацию конечных точек и вызовы JSON POST без дублирования HTTP-клиентов и внешних тяжелых зависимостей (стандартная библиотека `urllib.request` + Pydantic-границы).
- **Credential Isolation & No Silent Fallback:** Строгое разделение прав доступа. Ключ доски задач (`BITRIX_WEBHOOK_URL`) и ключ REST API (`BITRIX_REST_WEBHOOK_URL`) изолированы. Отсутствие или пустое значение `BITRIX_REST_WEBHOOK_URL` приводит к немедленному выходу с кодом 2 без попытки использовать ключ доски или выполнять сетевые запросы (fail-closed, AC-3, BN-001, BN-002).
- **Fail-Closed Argument & Payload Validation:** Все входные параметры (формат URL `https://.../rest/<id>/<code>/`, синтаксис имени метода `[a-z0-9_]+(\.[a-z0-9_]+)+`, структура параметров `--params` как JSON-объект) валидируются до отправки сетевого запроса. Ошибки не маскируются и возвращают код 2 (AC--3, BN-003, BN-004).
- **Batch Protection Guard:** Предотвращение исчерпания квот портала и отказов Bitrix API за счет локальной проверки ограничений пакетных вызовов (`batch`): не более 50 вложенных команд, запрет рекурсивных/вложенных `batch` вызовов (AC-6, BN-005).
- **Deterministic Exit Code Contract:** Чёткая семантика возврата CLI-утилит (`call.py`, `scope.py`):
  - `0`: Успешное выполнение, тело ответа Bitrix JSON выводится в stdout.
  - `1`: Ошибка API Bitrix24 (`error`, `error_description`) или сбой HTTP-транспорта; детали ошибки выводятся в stderr, stdout остаётся пустым (AC-2, BN-006, BN-007).
  - `2`: Ошибка конфигурации окружения, аргументов CLI или нарушение защитных ограничений; ошибка выводится в stderr, stdout пуст, HTTP-запрос не отправляется (AC-3, BN-001..BN-005).
- **Fail-Closed Secret Masking:** Гарантированное маскирование секретной части токена вебхука во всех сообщениях исключений, логах stderr, строковых представлениях (`str`/`repr`) моделей и объектов конфигурации (`***`).

## 7. Stock Frappe Login Surface & Computed-Style Gate

- **Surface ownership:** Login остаётся на штатном Frappe `/login`; вертикальный срез подключает scoped `login.css` через `web_include_css` и `login-keycloak.js` через `web_include_js`, не создавая custom SPA или template fork. Рендерится стандартная форма и ровно одна кнопка `.btn-keycloak` с публичным Keycloak URL (`KEYCLOAK_PUBLIC_URL/realms/elms`). Прямые Yandex-кнопки исключены.
- **Cascade boundary:** `login.bundle.css` подключается через `head_include` после `head.html` и переопределяет equal-specificity selectors из `web_include_css`. Для гарантии применения дизайна Neftegaz (`#0d4cd3`, `44px`, `3px`) в `login.css` используются селекторы повышенной специфичности и правило `!important` для состояний кнопки action (устранён дефект BF-001).
- **Runtime acceptance:** Статические CSS-токены не заменяют browser evidence: acceptance проверяет live computed style и asset delivery в реальном браузере через Playwright. T-A01 подтвердил `44px` control height, `3px` radius, cobalt action `rgb(13, 76, 211)` (`#0d4cd3`), single `.btn-keycloak` button и отсутствие direct Yandex control.
- **Identity boundary:** Browser login и live HTTP trace проходят через Keycloak authorization/broker route; Frappe не вызывает Yandex напрямую, а interactive Yandex остаётся `not_run` без реальных credentials и callback.

## 8. Immutable Production Compose & Vault Gate Pattern

- **Canonical ownership:** `docker/compose.prod.yaml` — единственный production Compose SoT: он image-only, не содержит checkout `build`, source-code mounts или host-публикаций внутренних DB/Redis/Frappe/Keycloak/Vault сервисов. Local/CI build, staged localhost/high-port rehearsal и public edge switch принадлежат отдельным явным overlays.
- **Dependency promotion gate:** Mandatory services имеют health/readiness, restart policy, `security_opt: no-new-privileges:true` и bounded resources. `configurator` и `create-site` — one-shot boundaries; backend не promoted при неуспешном one-shot или unhealthy dependency.
- **Secret and release gate:** Vault Agent рендерит runtime/database credentials в защищённые files с `error_on_missing_key`; production env и Compose не принимают прямые секретные значения. Release manifest связывает image tag+digest с commit/Compose hash и отклоняет `latest`, `dev`, `prod-local` и secret-like values.
- **Rehearsal and external boundary:** Staged smoke работает в изолированном Compose project на localhost/high port, сохраняет typed live evidence и удаляет только staged project. Внешний review service не становится Compose-сервисом: ELMS владеет только HTTPS URL validation и signed one-time handoff.
- **Vault source of truth:** KV v2 через authenticated AppRole/Vault Agent render — единственный production static-secret source. Pinned integrated-Raft Vault слушает только внутри Compose; dev mode, root-token runtime, public `8200`, direct `.env`/local fallback и secret-bearing diagnostics запрещены. Development synthetic secrets изолированы от production delivery.
- **Promotion and state boundary:** `vault_preflight.sh` и service dependencies fail closed для sealed, unavailable, unauthorized и incomplete render states; MariaDB/Keycloak DB получают `*_PASSWORD_FILE`, а OAuth/session state остаётся writable application-owned state вне read-only Vault render boundary.
- **Recovery evidence:** bootstrap, rotation, snapshot, restore, revoke и preflight runbooks возвращают status-only diagnostics; synthetic fixtures подтверждают redaction и disposable restore без публикации secret values. Root-owned AppRole files находятся вне repository и не читаются в stdout/logs.
