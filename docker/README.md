# ELMS Docker Environment & Identity Architecture

Руководство по запуску локального окружения ELMS, настройке SSO через Keycloak, процедурам аварийного входа (break-glass) и резервной аутентификации при сбоях внешних провайдеров.

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

1. **Копирование окружения**: Скопируйте `docker/.env.dev.example` в игнорируемый файл `docker/.env.dev`:
   ```bash
   cp docker/.env.dev.example docker/.env.dev
   ```
2. **Конфигурация секретов**: Задайте `KEYCLOAK_CLIENT_SECRET` (секрет клиента Keycloak `elms-frappe`) и при необходимости `YANDEX_CLIENT_ID` / `YANDEX_CLIENT_SECRET` (OAuth-приложение Yandex 360). Секреты хранятся только в `.env.dev` и не передаются в git.
3. **Регистрация Redirect URI в Yandex**: Укажите redirect URI брокера Keycloak: `http://localhost:8480/realms/elms/broker/yandex/endpoint` (в dev) или `https://<auth-host>/realms/elms/broker/yandex/endpoint` (в prod).
4. **Запуск Compose**: Запустите сервисы и дождитесь выполнения `create-site` и импорта realm через `docker/keycloak/entrypoint.sh`:
   ```bash
   docker compose -f docker/compose.dev.yaml --env-file docker/.env.dev up -d
   ```
5. **Вход через Keycloak**: Откройте `http://elms.localhost:8082/login`. На странице отображается единственная кнопка входа через Keycloak со стилями Neftegaz (`login.css`). Нажмите кнопку, перейдите в Keycloak, выберите Yandex 360 (или локального пользователя) и завершите first-broker-login.
6. **Проверка идентичности и ролей**: После callback убедитесь, что пользователь авторизован в Frappe Desk (`/app`), идентичность связана по `sub`, а роли по умолчанию (`Desk User`, `ELMS LMS User`) назначены автоматически.
7. **Проверка локального резервного пользователя**: Проверьте резервный вход с локальными учетными данными `fallback.user` в Keycloak при недоступности Yandex.
8. **Обновление кэша при изменениях**: При изменении параметров Social Login Key или CSS-ассета выполните очистку кэша:
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

### Архитектурный поток: Frappe → Keycloak → Yandex 360

```text
+-----------------------+           +-----------------------+           +-----------------------+
|      Frappe / Desk    | --------> |       Keycloak        | --------> |      Yandex 360       |
| (Authorization Plane) | <-------- |   (Identity Plane)    | <-------- |    (External IdP)     |
+-----------------------+   OIDC    +-----------------------+   OIDC    +-----------------------+
```

1. **Разделение ответственности**:
   - **Keycloak** — каноническая плоскость идентичности (Identity Plane): управление пользователями, группами, учетными записями, сессиями и брокеринг внешних провайдеров.
   - **Frappe** — каноническая плоскость авторизации приложения (Application Authorization Plane): управление ролями, правами на DocType и доступом к Desk.
   - **Yandex 360** — внешний корпоративный Identity Provider для штатного входа сотрудников и SMTP-шлюз.
2. **Запрет прямого входа Frappe → Yandex (FR-012, AC-4)**:
   - Прямой вход `Frappe → Yandex 360` исключен из архитектуры и не является production path.
   - Frappe принимает federated SSO исключительно от доверенного Keycloak realm `elms`.

### Настройка брокера Yandex в Keycloak (Manual Broker Onboarding)

1. Зарегистрируйте OAuth-приложение в кабинете разработчика Yandex:
   - Redirect URI приложения: `http://localhost:8480/realms/elms/broker/yandex/endpoint` (или внешний HTTPS адрес Keycloak).
   - Запрашиваемые права: доступ к адресу электронной почты и базовой информации профиля.
2. Передайте `YANDEX_CLIENT_ID` и `YANDEX_CLIENT_SECRET` в конфигурацию окружения `docker/.env.dev`.
3. В Keycloak realm `elms` брокер сконфигурирован как OIDC Identity Provider с алиасом `yandex` и сценарием первого входа `first broker login`.

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
- **Keycloak Broker Callback**: входящий ответ авторизации от Yandex поступает на публичный эндпоинт брокера `http://localhost:8480/realms/elms/broker/yandex/endpoint`.

#### Команды валидации сетевой доступности (cURL Commands)

- **Keycloak OpenID Discovery (хост -> keycloak:8480)**:
  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8480/realms/elms/.well-known/openid-configuration
  # Ожидаемый результат: 200 (валидный JSON с OIDC метаданными)
  ```
- **Keycloak Broker Endpoint**:
  ```bash
  curl -s -I http://localhost:8480/realms/elms/broker/yandex/endpoint
  # Ожидаемый результат: 200 OK или 302 Found
  ```
- **Frappe Desk Login Page (хост -> nginx:8082 -> backend:8000)**:
  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" http://elms.localhost:8082/login
  # Ожидаемый результат: 200 (страница входа Frappe с кнопкой Keycloak)
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

ELMS не использует тяжелые механизмы синхронизации директорий (SCIM или периодический фоновый импорт пользователей из Yandex). Создание учетных записей происходит строго **Just-in-Time (JIT)** при первом успешном входе:
1. Пользователь проходит аутентификацию в Yandex через брокер Keycloak.
2. Keycloak создает локальную запись пользователя в realm `elms` и привязывает federated identity Yandex (`first broker login`).
3. При возврате в Frappe создается локальный `User` на основе нормализованных OIDC-утверждений (`sub`, `email`, имя, фамилия).
4. Хук `User.after_insert` (`elms.sso.roles.maybe_assign_sso_roles`) проверяет наличие обязательных ролей в базе данных и назначает роли по умолчанию (`Desk User`, `ELMS LMS User`) по принципу **fail-closed** (если роль отсутствует в системе — регистрация прерывается).

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

## 4. Резервный вход и аварийные процедуры при сбое Yandex 360

### Поведение при недоступности внешнего IdP Yandex (FR-005a, FR-015, AC-8, BN-007, BN-008)

1. **Brokered-only пользователи**:
   - Пользователи, у которых нет локальных учетных данных в Keycloak и авторизующиеся исключительно через федерацию Yandex 360, при сбое Yandex получают явную ошибку аутентификации от Keycloak.
   - Ложный успех или offline-вход без подтверждения личности **запрещены (Fail-Closed, BN-007, TM-009)**.
2. **Пользователи с локальными Keycloak credentials (Local Fallback Path, AC-8, BN-008)**:
   - Автоматическая генерация паролей для всех brokered-пользователей запрещена.
   - Для критических ролей и администраторов в Keycloak realm вручную задаются локальные учетные записи/пароли:
     - `admin@elms.local` (роль `admin`, группа `/Administrators`)
     - `fallback.user@elms.local` (роль `employee`, группа `/Employees`)
   - При сбое Yandex такие пользователи могут авторизоваться на странице входа Keycloak, используя форму ввода имени пользователя и пароля Keycloak в обход кнопки Yandex IdP, через тот же клиент `elms-frappe`.

### Чек-лист проверки веток отказа и конкретные исходы (Outage Branch Checklist Outcomes)

| Ветка проверки | Входные параметры | Выполняемое действие | Конкретный результат (Outcome) | Статус |
|---|---|---|---|---|
| **Штатный JIT-вход (Happy Path)** | Yandex 360 активен | Вход через Keycloak -> выбор Yandex -> авторизация | **Keycloak:** создана учетная запись с привязкой identityProvider=yandex.<br>**Frappe:** создан User, назначены роли `Desk User` и `ELMS LMS User`. Открыта сессия Desk (`sid`, HTTP 200). | PASS |
| **Сбой Yandex без локального пароля (Fail-Closed)** | Yandex 360 недоступен (5xx/timeout), нет пароля в Keycloak | Клик по кнопке Yandex на форме входа Keycloak | **Fail-Closed (BN-007):** Keycloak отображает ошибку внешнего провайдера. Редирект в Frappe не выполняется. Сессия в Frappe не создается. Доступ закрыт. | PASS |
| **Сбой Yandex с локальным паролем (Local Fallback)** | Yandex 360 недоступен, задан пароль для `fallback.user@elms.local` | Ввод логина и пароля напрямую в форму Keycloak | **Local Fallback (BN-008):** Keycloak валидирует пароль локально, выпускает токен OIDC для `elms-frappe`. Редирект на `login_via_keycloak` успешен, Frappe открывает сессию для существующего пользователя. | PASS |
| **Отсутствие роли по умолчанию** | Роль `ELMS LMS User` отсутствует в БД Frappe | Прохождение OAuth-аутентификации | **Fail-Closed (BN-005):** Хук `maybe_assign_sso_roles` выбрасывает исключение `frappe.throw`. Создание пользователя отменяется, пользователь без роли не сохраняется. | PASS |

### Процедура Break-Glass для системного администратора

В случае полной недоступности внешних каналов аутентификации предусмотрено два уровня аварийного доступа:

1. **Уровень 1: Локальный вход через Keycloak**:
   - Перейдите на страницу авторизации Keycloak `http://localhost:8480`.
   - Введите имя пользователя `admin` и пароль, заданный переменной `KEYCLOAK_ADMIN_PASSWORD`.
2. **Уровень 2: Прямой Desk Break-Glass (обход SSO)**:
   - Перейдите на URL прямого входа Frappe: `http://elms.localhost:8082/login`.
   - Выполните вход под локальным пользователем `Administrator` с системным паролем из `ADMIN_PASSWORD` (по умолчанию `admin`).

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

- `make local.up` — сборка и запуск dev-стека в фоновом режиме с автоматической синхронизацией create-site.
- `make local.down` — остановка контейнеров локального dev-стека.
- `make local.ps` — вывод статуса работающих контейнеров.
- `make local.logs` — просмотр последних логов сервисов.
- `make dev` — алиас для `local.up`.
- `make prod` / `make prod.up` — сборка и запуск prod (Caddy :80/:443).
- `make prod.down` / `make prod.ps` / `make prod.logs` — остановка / статус / логи prod.

### Конфигурация Production (`docker/compose.prod.yaml` + Caddy)

Prod = immutable image + named volumes + **Caddy как единственный edge**.
На хост публикуются только **80** и **443**. MariaDB, Redis, Gunicorn, Nginx (frontend), Keycloak — только во внутренней Docker-сети.

| Снаружи (firewall) | Сервис | Куда проксирует Caddy |
|---|---|---|
| `80` / `443` | `caddy` | `SITE_NAME` → `frontend:8080`, `AUTH_HOSTNAME` → `keycloak:8080` |
| — | `frontend` / `backend` / `db` / `keycloak` | без publish |

1. DNS: `A`/`AAAA` для `SITE_NAME` и `AUTH_HOSTNAME` на IP сервера.
2. Скопируйте и заполните секреты (пустые и placeholder `*.example.com` — fail-closed):
   ```bash
   cp docker/.env.prod.example docker/.env.prod
   # SITE_NAME, AUTH_HOSTNAME, SITE_HOST_NAME, KEYCLOAK_PUBLIC_URL, FRAPPE_PUBLIC_URL,
   # ACME_EMAIL, DB_PASSWORD, ADMIN_PASSWORD, KEYCLOAK_*_PASSWORD, KEYCLOAK_CLIENT_SECRET
   ```
3. Откройте на хосте/firewall порты **80** и **443** (нужны и для Let's Encrypt HTTP-01).
4. Запуск:
   ```bash
   make prod
   # или: bash scripts/docker-up.sh prod up -d --build
   ```
5. Проверка:
   ```bash
   curl -fsS -o /dev/null -w "%{http_code}\n" "https://$SITE_NAME/login"
   curl -fsS -o /dev/null -w "%{http_code}\n" "https://$AUTH_HOSTNAME/realms/elms/.well-known/openid-configuration"
   ```
6. Yandex OAuth redirect URI: `https://<AUTH_HOSTNAME>/realms/elms/broker/yandex/endpoint`.

Caddyfile: `docker/caddy/Caddyfile` (авто-TLS Let's Encrypt по `ACME_EMAIL`).  
Keycloak в prod: `start` (не `start-dev`) + `KC_PROXY_HEADERS=xforwarded` + `KC_HOSTNAME=<AUTH_HOSTNAME>`.

Команды: `make prod` / `make prod.down` / `make prod.ps` / `make prod.logs`.

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
4. **Проверка подключения к MariaDB**:
   ```bash
   docker compose -f docker/compose.dev.yaml exec db mariadb -u root -p123 -e "SHOW DATABASES;"
   ```
