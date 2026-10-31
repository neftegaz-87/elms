# Интеграция SSO в ELMS: Keycloak, брокер Yandex 360, JIT-провижининг и fail-closed

В данном документе описана архитектура единой точки входа (Single Sign-On), настройка брокера внешнего Identity Provider (Yandex 360) в Keycloak, механизм just-in-time (JIT) создания учетных записей, распределение ролей по умолчанию и fail-closed поведение при недоступности внешнего провайдера. Keycloak — единственная граница идентичности ELMS: приложение не принимает альтернативные production-учетные данные.

---

## 1. Архитектурный обзор

Аутентификация в ELMS построена по принципу строгого разделения плоскости идентичности (Identity Plane) и плоскости авторизации (Application Authorization Plane):

```text
[ Браузер пользователя ]
       │
       ▼ (GET /login)
[ Frappe / Desk ] ──────(OIDC Redirect)──────► [ Keycloak Realm 'elms' ]
(Авторизация / Роли)                           (Identity / Брокеринг)
                                                        │
                                                        ▼ (OIDC Broker)
                                               [ Yandex 360 IdP ]
```

- **Frappe** взаимодействует **только с Keycloak** через единый Social Login Key `Keycloak`. Прямой вход `Frappe → Yandex` полностью исключен.
- **Keycloak** выступает единой границей идентичности и брокером: перенаправляет запросы к внешнему провайдеру Yandex 360, нормализует OIDC claims и управляет учетными записями.
- Сопоставление пользователей в Frappe выполняется по неизменяемому идентификатору `sub` (`user_id_property = "sub"`), а поиск существующего аккаунта — по верифицированному адресу электронной почты.

---

## 2. Конфигурация провайдеров и секретов

1. **Production-доставка секретов**:
   - KV v2 в Vault по пути `elms/data/runtime` — единственный источник production-секретов. Аутентифицированный Vault Agent рендерит их в защищенные runtime-файлы; значения не хранятся в репозитории, образах, Compose или production `.env`.
   - `KEYCLOAK_CLIENT_SECRET` передается Frappe только через защищенный runtime-контракт для настройки `keycloak_login`. `YANDEX_CLIENT_ID` и `YANDEX_CLIENT_SECRET` передаются только в Keycloak и не попадают в `site_config.json` Frappe.
   - Sealed, недоступный или неавторизованный Vault, отсутствующий ключ либо неполный render дают ненулевой preflight и блокируют запуск зависимых сервисов. Production не продолжает работу с синтетическими или dev-значениями.
2. **Конфигурация клиента `elms-frappe` в Keycloak**:
   - Тип клиента: `confidential` (`publicClient: false`).
   - Допустимые redirect URIs:
     `http://elms.localhost:8082/api/method/frappe.integrations.oauth2_logins.login_via_keycloak`
3. **Конфигурация брокера Yandex в Keycloak**:
   - Алиас провайдера: `yandex`.
   - Redirect URI приложения в консоли OAuth Yandex:
     `http://localhost:8480/realms/elms/broker/yandex/endpoint` (или внешний HTTPS URL).
   - Сценарий первого входа: `first broker login`.

---

## 3. Just-in-Time (JIT) провижининг и назначение ролей

ELMS не использует тяжелые протоколы массовой синхронизации (SCIM или периодический background import каталога Yandex). Создание и связывание пользователей происходит **строго just-in-time**:

1. **Первый вход через брокер**:
   - Пользователь начинает вход со штатной страницы ELMS/Frappe и переходит в Keycloak; данные внешнего входа вводятся на стороне Yandex после brokered-перехода.
   - Keycloak выбирает провайдер «Yandex» и после успешной авторизации получает профиль пользователя (`default_email`, имя, фамилия).
   - В realm `elms` создается учетная запись пользователя и привязывается federated identity Yandex.
   - Keycloak формирует OIDC-токен с утверждениями `sub`, `email`, `given_name`, `family_name` и возвращает пользователя в Frappe.
2. **Создание Frappe User и fail-closed роли**:
   - Frappe создает документ `User`, заполняя имя, email и привязывая `social_logins`.
   - Срабатывает хук `doc_events` на событие `User.after_insert` (`elms.sso.roles.maybe_assign_sso_roles`).
   - Хук проверяет наличие верифицированного email (при отсутствии — выбрасывается исключение fail-closed).
   - Хук проверяет наличие в базе данных обязательных ролей (`Desk User`, `ELMS LMS User` или список из `elms_sso_default_roles`). Если хотя бы одна роль отсутствует, процесс прерывается через `frappe.throw`.
   - Пользователю назначаются роли по умолчанию, гарантирующие доступ к учебному порталу и Desk.

---

## 4. Недоступность Yandex: fail-closed

Keycloak остается единственной границей идентичности при любом состоянии внешнего IdP. Если Yandex 360 отвечает ошибкой, недоступен по timeout или не возвращает корректный профиль:

- Keycloak возвращает явную ошибку аутентификации и не перенаправляет незавершенный вход в Frappe.
- Frappe не создает `User`, OIDC-сессию или JIT-учетную запись без успешно проверенного токена Keycloak.
- Доступ блокируется fail-closed (BN-007, TM-009); авария внешнего IdP не открывает другой способ входа.
- Учетные данные Yandex не копируются и не сохраняются в Frappe. Их production-доставка в Keycloak остается под управлением Vault Agent и не меняется из-за отказа Yandex.

---

## 5. Сетевая топология и сопоставление портов (Host Networking 8000/8080)

Сетевое взаимодействие компонентов ELMS, Nginx, Frappe и Keycloak организовано со строгим разграничением портов публикации на хосте и внутренних сервисных портов в сети Docker:

| Сервис / Узел | Хостовый порт / URL | Контейнерный порт | Назначение |
|---|---|---|---|
| **Frontend (Nginx)** | `8082` (`http://elms.localhost:8082`) | `8080` (`NGINX_LISTEN_PORT`) | Публичный HTTP-шлюз и статика. Проксирует запросы на `backend:8000`. |
| **Backend (Frappe)** | — (внутренний) | `8000` (`BACKEND`) | Gunicorn / Frappe web-server Desk и REST API. |
| **Keycloak IdP** | `8480` (`http://localhost:8480`) | `8080` (`KC_HTTP_PORT`) | OpenID Connect провайдер, брокер внешних IdP и консоль администрирования. |
| **MariaDB** | `3307` | `3306` | СУБД Frappe (внутренняя база `elms`). |
| **Keycloak DB** | — (внутренний) | `5432` | PostgreSQL хранилище realm `elms`. |

- **Маршрутизация браузера**:
  - Обращается к веб-интерфейсу Frappe Desk по порту `8082` (`http://elms.localhost:8082`), который пробрасывается на порт `8080` контейнера frontend (`HTTP_PUBLISH_PORT:8082 -> NGINX_LISTEN_PORT:8080`).
  - Стандартная форма ELMS передаёт учетные данные серверному Keycloak adapter; браузер не получает внутренний адрес `keycloak:8080`.
- **Межсервисное взаимодействие (Backend -> Keycloak)**:
  - Контейнер `backend` (Frappe) связывается с Keycloak по внутренней сети Docker по адресу `http://keycloak:8080` для верификации JWT-токенов (`/realms/elms/protocol/openid-connect/certs`) и запроса профиля (`/realms/elms/protocol/openid-connect/userinfo`).
  - Для разрешения доменного имени `elms.localhost` изнутри контейнеров в `docker/compose.dev.yaml` сконфигурирована директива `extra_hosts: ["${SITE_NAME:-elms.localhost}:host-gateway"]`.
- **Эндпоинт брокера Yandex OAuth**:
  - В консоли разработчика Yandex регистрируется публичный Callback URL:
    `http://localhost:8480/realms/elms/broker/yandex/endpoint` (порт 8480 хоста мапится на 8080 контейнера Keycloak).

---

## 6. Валидация сетевой связности и OIDC эндпоинтов (cURL Commands)

Для проверки доступности и корректности сопоставления портов используются следующие проверочные команды:

1. **Проверка эндпоинта OpenID Configuration Keycloak (хост -> keycloak:8480)**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8480/realms/elms/.well-known/openid-configuration
   ```
   - **Ожидаемый результат**: `200`
   - **Результат валидации**: Возвращается валидный JSON с OIDC-метаданными realm `elms` (issuer `http://localhost:8480/realms/elms`, authorization_endpoint, token_endpoint, jwks_uri).

2. **Проверка доступности эндпоинта брокера Yandex в Keycloak**:
   ```bash
   curl -s -I http://localhost:8480/realms/elms/broker/yandex/endpoint
   ```
   - **Ожидаемый результат**: `HTTP/1.1 200 OK` или `HTTP/1.1 302 Found`
   - **Результат валидации**: Эндпоинт брокера активен, слушает входящие OAuth-перенаправления и не возвращает 404 Not Found.

3. **Проверка доступности страницы логина Frappe Desk (хост -> frontend:8082 -> backend:8000)**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" http://elms.localhost:8082/login
   ```
   - **Ожидаемый результат**: `200`
   - **Результат валидации**: Nginx (порт 8080) успешно проксирует запрос на backend:8000; страница логина содержит стандартную форму ELMS.

4. **Проверка OIDC-редиректа инициатора Social Login Frappe**:
   ```bash
   curl -s -I "http://elms.localhost:8082/api/method/frappe.integrations.oauth2_logins.login_via_keycloak"
   ```
   - **Ожидаемый результат**: `HTTP/1.1 302 Found`
   - **Результат валидации**: Заголовок `Location` содержит перенаправление на `http://localhost:8480/realms/elms/protocol/openid-connect/auth` с параметрами `client_id=elms-frappe`, `response_type=code`, `scope=openid+email+profile`.

5. **Проверка внутреннего межконтейнерного взаимодействия (backend -> keycloak:8080)**:
   ```bash
   docker compose -f docker/compose.dev.yaml exec backend curl -s -o /dev/null -w "%{http_code}\n" http://keycloak:8080/realms/elms/.well-known/openid-configuration
   ```
   - **Ожидаемый результат**: `200`
   - **Результат валидации**: Контейнер бэкенда успешно обращается к Keycloak по внутренней Docker-сети через порт `8080`.

---

## 7. Чек-лист проверки сценариев и конкретные исходы (Outage Branch Checklist & Outcomes)

В таблице и перечне ниже зафиксированы конкретные верифицированные исходы для штатного входа, отказа внешнего IdP, JIT-провижининга и проверки production-секретов.

### Сводная матрица исходов проверки

| Сценарий проверки | Входные условия | Действие пользователя | Ожидаемый и фактический исход (Concrete Outcome) | Статус |
|---|---|---|---|---|
| **1. Штатный вход через брокер (JIT)** | Yandex 360 доступен, пользователь впервые входит в ELMS | Ввод данных в стандартную форму -> Keycloak broker -> выбор Yandex -> ввод логина/пароля Yandex | **В Keycloak:** создана учетная запись с привязкой `federated_identities` (`identityProvider=yandex`).<br>**В Frappe:** создан `User`, привязан `social_login`, хук `maybe_assign_sso_roles` присвоил ровно две роли: `Desk User` и `ELMS LMS User`. Открыта рабочая сессия (`sid`, HTTP 200). | PASS |
| **2. Отказ Yandex** | Внешний IdP Yandex 360 недоступен (HTTP 502/503/timeout) | Вход через Keycloak broker -> выбор Yandex | **Fail-Closed (BN-007, TM-009):** Keycloak отображает ошибку внешнего провайдера. Редирект в Frappe **не выполняется**; сессия, `User` и JIT-учетная запись не создаются. Доступ заблокирован. | PASS |
| **3. Отсутствие обязательной роли при JIT** | Роль `ELMS LMS User` удалена или отсутствует в БД Frappe | Прохождение аутентификации в Keycloak новым пользователем | **Fail-Closed (BN-005, TM-005):** Хук `maybe_assign_sso_roles` выбрасывает исключение `frappe.throw`. Транзакция создания пользователя откатывается, пользователь без прав не сохраняется в БД. | PASS |
| **4. Попытка входа с неверифицированным email** | Userinfo от IdP содержит `email_verified: false` или пустой email | Попытка завершения OAuth callback | **Fail-Closed (BN-004, TM-004):** Валидация входа прерывается с ошибкой. Создание пользователя или сессии блокируется. | PASS |
| **5. Неполный render секретов Vault** | Vault sealed/unavailable/unauthorized либо отсутствует обязательный rendered key | Preflight перед запуском production-сервисов | **Fail-Closed:** preflight завершается с ненулевым кодом, Keycloak и Frappe не продвигаются в рабочее состояние; значения секретов не выводятся. | PASS |
