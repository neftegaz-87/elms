# Контекст продукта (productContext)

**Дата:** 2026-10-29  
**Обновлено:** 2026-10-29 (после T-B03 re-QA PASS и T-B04 QA PASS)

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
  - **Bitrix REST Client & CLI (`T-B04`):** завершён и прошёл верификацию QA:
    - Развёрнут изолированный REST-клиент Bitrix24 (`scripts/bitrix/rest_client.py`) и утилиты CLI `call.py` (вызов произвольных методов API) и `scope.py` (проверка прав вебхука с флагом `--full`).
    - Реализована строгая изоляция конфигурации: использование исключительно переменной окружения `BITRIX_REST_WEBHOOK_URL` формата `https://<domain>/rest/<user_id>/<webhook_code>/` без тихого отката к ключу доски `BITRIX_WEBHOOK_URL` (fail-closed exit code 2 без сетевого вызова).
    - Зафиксирован строгий контракт кодов завершения: `0` — успешный JSON-ответ в stdout, `1` — ошибка Bitrix API (`error`, `error_description`) или сетевой сбой HTTP в stderr, `2` — ошибка аргументов, валидации формата URL, некорректного JSON или превышения лимитов batch (stderr, без сетевого вызова).
    - Обеспечена защита от утечек секретов: маскирование секретного токена вебхука (`***`) во всех сообщениях об ошибках, исключениях и логах.
    - Реализован batch guard (максимум 50 команд, запрет рекурсивных вложенных вызовов).
    - Разработана эксплуатационная документация `docs/bitrix-incoming-webhook.md` и обновлён шаблон `.env.example`.
    - Тестовый набор T-B04 расширен на 37 тестов `tests/bitrix/test_rest_client.py` с детерминированным urllib Opener mock.
- **Следующие шаги (Next Foundation Wedges):**
  - `T-F01`: Настройка рабочих пространств и разделов Desk UI под целевые роли (`ELMS Admin`, `ELMS Operations User`, `ELMS LMS User`).
  - Прикладная синхронизация Bitrix24 (CRM / LMS интеграционные сценарии) на базе стабилизированного REST-транспорта `T-B04`.
