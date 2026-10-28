# Архитектурные паттерны системы (systemPatterns)

**Дата:** 2026-10-28  
**Статус:** Базовые системные паттерны зафиксированы по результатам T-B01

## 1. Slim Single-App Frappe Architecture

- **Принцип:** Репозиторий содержит платформу `elms` поверх чистого фреймворка `frappe` (v15). Сторонние тяжелые приложения (`erpnext`, `crm`, `hrms`, `education`) исключены из `apps.json`, `sites/apps.txt` и Docker-образов.
- **Структура приложения:** `elms` с модулями `Core`, `Operations`, `LMS`.
- **Правило расширения:** Новая бизнес-логика реализуется строго внутри `elms/` через стандартные Frappe DocTypes, Document Controller hooks и whitelist API, без создания параллельных web-фреймворков.

## 2. Fail-Closed Bootstrap Pattern

- **Принцип:** Автоматическое развёртывание сайта и приложений должно завершаться с ненулевым кодом выхода при любой ошибке (никаких `|| true`, проигнорированных ошибок миграции или скрытых fallback-логик).
- **Реализация:** Сервис `create-site` в `docker/compose.dev.yaml` выполняет `bench new-site` и `bench --site ... install-app elms`. Другие сервисы топологии зависят от успешного завершения `create-site` (`condition: service_completed_successfully`).

## 3. Central Identity Broker Pattern (SSO & RBAC)

- **Принцип:** Разделение контуров аутентификации и авторизации:
  - **Keycloak:** центральный брокер идентичности (IdP broker), управляющий жизненным циклом пользователей и федерацией внешних провайдеров (Yandex ID и др.).
  - **Frappe:** доверяет аутентификации Keycloak (через Social Login Key OpenID Connect), синхронизирует профиль через хук `on_login`, но монопольно владеет локальными ролями и правами доступа (DocPerm/RBAC).
- **Запрет:** Прямая интеграция Frappe с внешними провайдерами в обход Keycloak как второго неуправляемого пути входа запрещена.

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
  - `keycloak` + `keycloak-db` — сервис единого входа и база данных PostgreSQL.
- **Производственный контур (`docker/compose.prod.yaml`):** аналогичный стек с production-настройками и политиками перезапуска.
