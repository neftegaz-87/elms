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
   - **Keycloak Admin Console**: [http://localhost:8480](http://localhost:8480) (порт публикации `8480`, admin / admin)
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

---

## 3. Синхронизация идентичности (Identity Lifecycle & Reconciliation)

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

### Поведение при недоступности внешнего IdP Yandex (FR-015, AC+8, BN-008)

1. **Brokered-only пользователи**:
   - Пользователи, у которых нет локальных учетных данных в Keycloak и авторизующиеся исключительно через федерацию Yandex 360, при сбое Yandex получают явную ошибку аутентификации от Keycloak.
   - Ложный успех или offline-вход без подтверждения личности **запрещены (AC-6)**.
2. **Пользователи с локальными Keycloak credentials (Local Fallback Path)**:
   - Для критических ролей и администраторов в Keycloak realm создаются локальные учетные записи:
     - `admin@elms.local` (роль `admin`, группа `/Administrators`)
     - `fallback.user@elms.local` (роль `employee`, группа `/Employees`)
   - При сбое Yandex такие пользователи могут авторизоваться на странице входа Keycloak, используя форму ввода имени пользователя и пароля Keycloak в обход кнопки Yandex IdP.

### Процедура Break-Glass для системного администратора

В случае полной недоступности внешних каналов аутентификации предусмотрено два уровня аварийного доступа:

1. **Уровень 1: Локальный вход через Keycloak**:
   - Перейдите на страницу авторизации Keycloak `http://localhost:8480`.
   - Введите имя пользователя `admin` и пароль `KEYCLOAK_ADMIN_PASSWORD` (по умолчанию `admin` в dev).
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
- `make prod` — запуск продакшн-конфигурации через `compose.prod.yaml`.

### Конфигурация Production (`docker/compose.prod.yaml`)

Для развертывания в автономном / production режиме подготовлен файл `docker/compose.prod.yaml`:
- **Без bind-mounts кода**: исходный код приложений `frappe` и `elms` упакован непосредственно в базовый Docker-образ (`apps/frappe` и `apps/elms`), что гарантирует неизменяемость рантайма и изоляцию от хостовой файловой системы.
- **Именованные тома**: персистентные данные (`sites`, `logs`, `db-data`, `redis-queue-data`, `keycloak-db-data`) хранятся исключительно в именованных docker volumes.
- Запуск prod-окружения:
  ```bash
  bash scripts/docker-up.sh prod up -d
  # или через make:
  make prod
  ```

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
