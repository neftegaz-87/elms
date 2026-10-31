# Контекст продукта (productContext)

**Дата:** 2026-10-29  
**Обновлено:** 2026-10-31 (после T-B06 QA PASS & context sync, T-B05 QA PASS, T-A01 APP QA PASS, T-B03 re-QA PASS и T-B04 QA PASS)

## Текущий срез (Current Wedge & Delivery Status)

- **Статус фундамента:**
  - **Docker Bootstrap (`T-B01`):** завершён и прошёл верификацию QA. Развёрнута топология с Frappe v15, MariaDB, Redis, Keycloak.
  - **Roles RBAC (`T-B02`):** завершён и прошёл верификацию QA:
    - Зафиксированы три целевые роли: `ELMS Admin`, `ELMS Operations User`, `ELMS LMS User` (Operations заменяет ERP).
    - Созданы три Single DocTypes в качестве RBAC-якорей секций: `ELMS Operations Section` (Operations), `ELMS LMS Section` (LMS), `ELMS Settings Section` (ELMS Core). Модули выровнены: `ELMS Core`, `Operations`, `LMS`.
    - Настроена матрица прав `DocPerm`: Admin имеет полный доступ (RWCD), Operations User — RW в Operations Section, LMS User — RW в LMS Section; гостевой и межролевой доступ закрыты (fail-closed).
    - Жизненный цикл ролей и прав автоматизирован через хуки `after_install` и `after_migrate` без скрытых подавлений ошибок (все выявленные QA дефекты BF-001, BF-002, BF-003 устранены с fail-closed поведением, 13 unit-тестов RBAC green).
  - **SSO Keycloak + Yandex 360 Broker (`T-B03`):** завершён и прошёл верификацию QA:
    - Развёрнут централизованный контур SSO: Keycloak 24 (realm `elms`, клиент `elms-frappe`), брокер внешнего Identity Provider Yandex 360 с точкой терминации `/realms/elms/broker/yandex/endpoint`.
    - В Frappe зарегистрирован ровно один Social Login Key (`Keycloak`) с каноническим redirect `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak`. Прямой Social Login Key Yandex или параллельные OAuth-модули в Frappe полностью исключены.
    - Инициализация Social Login Key идемпотентна (`ensure_social_login_keys` в `after_install` и `after_migrate`), флаг активности контролируется наличием учетных данных в конфигурации (`site_config.keycloak_login`).
    - Реализован Just-in-Time (JIT) провижининг пользователей при первом входе через брокер (`first broker login`) со связыванием по `sub` и верифицированному адресу электронной почты.
    - Реализован fail-closed хук назначения ролей `User.after_insert` (`maybe_assign_sso_roles`), автоматически присваивающий новому пользователю роли `Desk User` и `ELMS LMS User`. При отсутствии целевой роли операция прерывается с `frappe.throw`, блокируя создание непривилегированного пользователя.
    - Документирован и верифицирован регламент работы при сбоях внешнего IdP: fail-closed поведение без создания фиктивных сессий, поддержка резервного входа по локальным паролям Keycloak и Break-Glass доступ администратора Frappe.
    - Повторная QA-проверка подтвердила 51 passed в ELMS/Frappe suite, реальный `create-site` с установленными `frappe` и `elms`, а также live HTTP smoke с exit code 0 и typed evidence в `docs/reports/sso-browser-api-trace.json`.
    - Интерактивный Yandex login не заявляется: он `not_run` без реальных credentials и зарегистрированного callback; broker route проверен на ожидаемый fail-closed ответ `502` при отсутствии state.
  - **Keycloak Login UI (`T-A01`):** завершён и принят APP QA как единый vertical slice на штатной странице Frappe `/login`:
    - Штатная страница Frappe `/login` сохранена как единственный UI-владелец входа; на ней рендерится стандартная форма логина, делегирующая аутентификацию в Keycloak через `login-keycloak.js`, и ровно одна кнопка `.btn-keycloak`, ведущая на публичный URL Keycloak (`KEYCLOAK_PUBLIC_URL/realms/elms`). Прямой Yandex-контрол и template fork отсутствуют.
    - Ассет `login.css` подключается через `web_include_css` и гарантирует токены Neftegaz с повышенной специфичностью и `!important`, предотвращая переопределение со стороны `login.bundle.css`.
    - Live browser evidence (`browser-artifacts/browser-evidence.json`, `login-page.png`) подтвердил computed styles: высота контролов `44px`, radius `3px`, cobalt action `rgb(13, 76, 211)` (`#0d4cd3`); `bench build --app elms` завершился успешно (`Application Assets Linked`).
    - Устранены все выявленные QA дефекты (BF-001..BF-004 в `bugfix-queue.yaml` закрыты со статусом `done`).
    - APP QA подтвердил 65 passed (`bin/pytest -q --tb=line`), live browser exit code 0 и live HTTP trace (`docs/reports/sso-browser-api-trace.json`) с успешными journeys `JRN-SSO-001`, `JRN-SSO-001A`, `JRN-SSO-001B`; интерактивный Yandex остаётся `not_run`, а broker endpoint без state — ожидаемый fail-closed `502`.
  - **LMS as-built:** в `elms/elms/lms/` пока только Single DocType `ELMS LMS Section` как RBAC-якорь (`ELMS Admin` RWCD, `ELMS LMS User` RW). Course/Program/Enrollment/Progress/Lesson/Certificate, LMS Settings, API и учебный UI ещё не реализованы. `/app/setup-wizard/0` — мастер платформы Frappe, не конфигурация LMS.
  - **Bitrix REST Client & CLI (`T-B04`):** завершён и прошёл верификацию QA:
    - Развёрнут изолированный REST-клиент Bitrix24 (`scripts/bitrix/rest_client.py`) и утилиты CLI `call.py` (вызов произвольных методов API) и `scope.py` (проверка прав вебхука с флагом `--full`).
    - Реализована строгая изоляция конфигурации: использование исключительно переменной окружения `BITRIX_REST_WEBHOOK_URL` формата `https://<domain>/rest/<user_id>/<webhook_code>/` без тихого отката к ключу доски `BITRIX_WEBHOOK_URL` (fail-closed exit code 2 без сетевого вызова).
    - Зафиксирован строгий контракт кодов завершения: `0` — успешный JSON-ответ в stdout, `1` — ошибка Bitrix API (`error`, `error_description`) или сетевой сбой HTTP в stderr, `2` — ошибка аргументов, валидации формата URL, некорректного JSON или превышения лимитов batch (stderr, без сетевого вызова).
    - Обеспечена защита от утечек секретов: маскирование секретного токена вебхука (`***`) во всех сообщениях об ошибках, исключениях и логах.
    - Реализован batch guard (максимум 50 команд, запрет рекурсивных вложенных вызовов).
    - Разработана эксплуатационная документация `docs/bitrix-incoming-webhook.md` и обновлён шаблон `.env.example`.
    - Тестовый набор T-B04 расширен на 37 тестов `tests/bitrix/test_rest_client.py` с детерминированным urllib Opener mock.
  - **Production Container Stack (`T-B05`):** завершён и принят BACK QA как воспроизводимый production boundary ELMS:
    - Канонический `docker/compose.prod.yaml` стал image-only SoT без checkout build, source mounts и host-портов внутренних сервисов; local/CI build, staged localhost/high-port rehearsal и owner-approved edge публикация разделены явными overlays.
    - Production graph включает Frappe web/frontend/websocket/workers/scheduler, MariaDB, Redis cache/queue, Keycloak/Keycloak PostgreSQL, Vault/Vault Agent и staged Caddy с health/readiness, restart, security и bounded-resource policy.
    - Секреты проходят Vault Agent rendered-file contract с fail-closed preflight, release identity требует tag+digest, а `ELMS_REVIEW_URL` и signed one-time handoff сохраняют отдельную внешнюю review boundary без phantom Compose service.
    - QA подтвердил `87 passed, 2 skipped`, `tests/infra` — `15 passed`, и typed canonical live smoke без environment override (`live_evidence=true`, `exit_code=0`, `2026-10-31T14:56:33Z`). BF-001 (T-B05 `behavior_smoke`) закрыт со статусом `done`; интерактивный staged Vault bootstrap и public edge cutover в эпик не входили.
  - **Vault Secrets (`T-B06`):** завершён и принят BACK QA как production static-secret boundary:
    - Pinned integrated-Raft Vault работает на private Compose-only listener; KV v2 и read-only `elms-agent` AppRole policy доставляют секреты только через authenticated Vault Agent render. MariaDB/Keycloak DB используют password files, Frappe/Keycloak/review/Yandex — защищённые rendered files.
    - Production не имеет direct `.env`/local-secret fallback, root-token runtime, Vault dev mode или public `8200`; sealed/unavailable/unauthorized/incomplete render блокирует promotion с non-zero. OAuth/session state остаётся writable application-owned state.
    - Synthetic bootstrap/rotation/snapshot/restore/revoke и redaction evidence, а также fail-closed negative fixtures приняты; legacy fallback tests и SSO documentation reconciled with the current contract.
    - QA подтвердил `87 passed, 2 skipped`, `tests/infra` — `27 passed`, Compose/policy/preflight/legacy scans — PASS и canonical live smoke `live_evidence=true`, `exit_code=0` (`2026-10-31T18:08:24Z`). Реальное production initialization/unseal, KV population, AppRole files и custody остаются operator gates.
- **Следующие шаги (Next Foundation Wedges):**
  - `T-F01` (Desk workspaces / role navigation): as-built закрыт — LMS/Operations/Settings workspaces, role filter, platform workspaces скрыты; login affordance закрыт в T-A01.
  - Прикладная синхронизация Bitrix24 (LMS / Operations интеграционные сценарии) на базе стабилизированного REST-транспорта `T-B04`.
  - Follow-up boundaries: `T-B07` — external backup repository, freshness/capacity gate и restore rehearsal; `T-B08` — registry push, protected deploy approval, release/rollback execution и drill; `T-B09` — public edge cutover, DNS/firewall/ACME, host-Caddy ownership и maintenance-window rollback. T-B06 завершён как контракт и evidence gate; реальные production custody/bootstrap actions остаются операторскими gates.
  - **Канон агента (2026-10-30):** SoT в `rules/` (`elms-approach.mdc`, `elms-design.mdc`, `agents-overlay.md`); Cursor подключает через `.cursor/rules.d/elms-*.mdc` → symlink. Роли/атрибуты/домен — LMS/`elms`; ERP/CRM — вторичный read-only источник framework-паттернов Frappe, без ERP/CRM-брендинга; UI — neftegaz + LMS. Hub CRM-секции не канон.
