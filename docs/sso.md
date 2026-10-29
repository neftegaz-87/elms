# Интеграция SSO в ELMS: Keycloak, брокер Yandex 360, JIT-провижининг и аварийный fallback

В данном документе описана архитектура единой точки входа (Single Sign-On), настройка брокера внешнего Identity Provider (Yandex 360) в Keycloak, механизм just-in-time (JIT) создания учетных записей, распределение ролей по умолчанию и регламент резервного входа при недоступности внешних провайдеров.

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
- **Keycloak** выступает единым брокером идентичности: перенаправляет запросы к внешнему провайдеру Yandex 360, нормализует OIDC claims и управляет учетными записями.
- Сопоставление пользователей в Frappe выполняется по неизменяемому идентификатору `sub` (`user_id_property = "sub"`), а поиск существующего аккаунта — по верифицированному адресу электронной почты.

---

## 2. Конфигурация провайдеров и секретов

1. **Конфигурация Frappe (`site_config.json`)**:
   - Ключ `keycloak_login` генерируется из переменных окружения `KEYCLOAK_CLIENT_ID` и `KEYCLOAK_CLIENT_SECRET`.
   - Секреты внешнего IdP Yandex (`YANDEX_CLIENT_ID`, `YANDEX_CLIENT_SECRET`) передаются исключительно в контейнер Keycloak и никогда не попадают в `site_config.json` Frappe.
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
   - Пользователь на странице логина Frappe нажимает «Войти через Keycloak».
   - На странице входа Keycloak выбирает провайдер «Yandex».
   - После успешной авторизации в Yandex брокер Keycloak получает профиль пользователя (`default_email`, имя, фамилия).
   - В realm `elms` создается учетная запись пользователя и привязывается federated identity Yandex.
   - Keycloak формирует OIDC-токен с утверждениями `sub`, `email`, `given_name`, `family_name` и возвращает пользователя в Frappe.
2. **Создание Frappe User и fail-closed роли**:
   - Frappe создает документ `User`, заполняя имя, email и привязывая `social_logins`.
   - Срабатывает хук `doc_events` на событие `User.after_insert` (`elms.sso.roles.maybe_assign_sso_roles`).
   - Хук проверяет наличие верифицированного email (при отсутствии — выбрасывается исключение fail-closed).
   - Хук проверяет наличие в базе данных обязательных ролей (`Desk User`, `ELMS LMS User` или список из `elms_sso_default_roles`). Если хотя бы одна роль отсутствует, процесс прерывается через `frappe.throw`.
   - Пользователю назначаются роли по умолчанию, гарантирующие доступ к учебному порталу и Desk.

---

## 4. Локальный Keycloak Fallback при сбое Yandex

Для обеспечения непрерывности образовательного процесса при недоступности внешнего сервиса Yandex 360 предусмотрен регламент резервного входа (local fallback):

1. **Политика назначения паролей**:
   - Локальные учетные данные Keycloak **не генерируются автоматически** для всех пользователей (запрещен auto-provisioning паролей).
   - Администратор системы заблаговременно задает локальный пароль в Keycloak Admin Console для ключевых пользователей (администраторы, дежурные преподаватели) — например, для сервисного пользователя `fallback.user`.
   - Пароли Yandex никогда не копируются и не сохраняются в Keycloak или Frappe.
2. **Ветка отказа при сбое Yandex (outage without local credential)**:
   - Пользователь, аутентифицирующийся исключительно через брокер Yandex и не имеющий локального пароля в Keycloak, получает явную ошибку аутентификации от Keycloak при сбое внешнего IdP.
   - Создание фиктивной сессии исключено (Fail-Closed, BN-007, TM-009).
3. **Ветка резервного входа (outage with local credential)**:
   - Пользователь с предварительно настроенным локальным паролем Keycloak переходит по ссылке SSO, но на форме Keycloak вводит имя пользователя и пароль Keycloak (минуя кнопку Yandex).
   - Аутентификация проходит через тот же клиент `elms-frappe` и возвращает OIDC-токен с тем же `sub` / `email`.
   - Frappe сопоставляет пользователя с уже существующим `User` и открывает рабочую сессию (BN-008, TM-010).

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
  - При клике «Войти через Keycloak» перенаправляется на публичный порт Keycloak `8480` (`http://localhost:8480`), проброшенный на порт `8080` контейнера keycloak (`KEYCLOAK_PUBLISH_PORT:8480 -> KC_HTTP_PORT:8080`).
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
   - **Результат валидации**: Nginx (порт 8080) успешно проксирует запрос на backend:8000; страница логина содержит форму входа и кнопку «Войти через Keycloak».

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

В таблице и перечне ниже зафиксированы конкретные верифицированные исходы для всех веток аутентификации, включая штатный вход, аварии внешнего IdP и аварийный fallback.

### Сводная матрица исходов проверки

| Сценарий проверки | Входные условия | Действие пользователя | Ожидаемый и фактический исход (Concrete Outcome) | Статус |
|---|---|---|---|---|
| **1. Штатный вход через брокер (JIT)** | Yandex 360 доступен, пользователь впервые входит в ELMS | Клик «Войти через Keycloak» -> выбор Yandex -> ввод логина/пароля Yandex | **В Keycloak:** создана учетная запись с привязкой `federated_identities` (`identityProvider=yandex`).<br>**В Frappe:** создан `User`, привязан `social_login`, хук `maybe_assign_sso_roles` присвоил ровно две роли: `Desk User` и `ELMS LMS User`. Открыта рабочая сессия (`sid`, HTTP 200). | PASS |
| **2. Ветка сбоя Yandex: пользователь без локального пароля** | Внешний IdP Yandex 360 недоступен (HTTP 502/503/timeout), локального пароля в Keycloak нет | Клик «Войти через Keycloak» -> выбор Yandex на форме входа | **Fail-Closed (BN-007, TM-009):** Keycloak отображает экран ошибки аутентификации внешнего провайдера. Редирект в Frappe **не выполняется**. В Frappe **не создается** сессия и не создается User. Доступ полностью заблокирован. | PASS |
| **3. Ветка сбоя Yandex: пользователь с локальным паролем (Fallback)** | Внешний IdP Yandex 360 недоступен, для `fallback.user@elms.local` предварительно задан локальный пароль Keycloak | Клик «Войти через Keycloak» -> ввод логина и локального пароля в форму Keycloak (в обход Yandex) | **Local Fallback (BN-008, TM-010):** Keycloak локально валидирует пароль, выдает OIDC-токен через тот же клиент `elms-frappe`. Браузер редиректится на `login_via_keycloak`. Frappe связывает токен с существующим `User`, сессия открывается (`sid`, HTTP 200). | PASS |
| **4. Отсутствие обязательной роли при JIT** | Роль `ELMS LMS User` удалена или отсутствует в БД Frappe | Прохождение аутентификации в Keycloak новым пользователем | **Fail-Closed (BN-005, TM-005):** Хук `maybe_assign_sso_roles` выбрасывает исключение `frappe.throw`. Транзакция создания пользователя откатывается, пользователь без прав не сохраняется в БД. | PASS |
| **5. Попытка входа с неверифицированным email** | Userinfo от IdP содержит `email_verified: false` или пустой email | Попытка завершения OAuth callback | **Fail-Closed (BN-004, TM-004):** Валидация входа прерывается с ошибкой. Создание пользователя или сессии блокируется. | PASS |
| **6. Прямой обходной Desk Break-Glass** | Полный сбой Keycloak и внешней сети | Переход на `http://elms.localhost:8082/login`, вход под `Administrator` | **Break-Glass Level 2:** Локальная аутентификация платформы Frappe предоставляет полный доступ системного администратора. | PASS |
