## Epic

### Outcome
Разработчик одной командой поднимает локальный ELMS site на Frappe: MariaDB с User/Administrator, Redis, backend/workers/nginx и пустой custom app `elms` — без ERPNext и без чужих LMS/CRM apps.

### In
- Monorepo layout: `frappe/` (v15) + app `elms/`
- Docker compose.dev: db, redis, configurator, create-site, backend, workers, frontend, keycloak(+db)
- Скелет app: hooks, modules Core/ERP/LMS, install hooks-заглушки
- Site с Administrator из env

### Out
- Роли и DocType permissions (следующая ось)
- Настройка Social Login Key / OAuth callbacks (следующая ось)
- Desk Workspaces UI (FRONT)
- Доменные сущности ERP/LMS

### Done when
1. `docker compose … up -d --build` завершает create-site без silent fallback
2. `/login` отвечает 200; Administrator входит с паролем из env
3. `bench list-apps` содержит только `frappe` и `elms`

### Forbidden after
ставить ERPNext/LMS/Education/CRM в image · игнорировать падение create-site · второй framework рядом с Frappe

### Chat decisions
- Frappe только как framework + образец организации кода
- Keycloak контейнер закладываем в compose уже здесь (конфиг клиента — в SSO-эпике)
- App path: `elms/elms/` в корне репо (как `lms/lms/` в эталоне)

---

## Covering

### Outcome
ELMS получает воспроизводимый foundation: один Frappe site в Docker с custom app, БД User, тремя ролями-разделами и базовым SSO Keycloak+Яндекс — без vendor ERP/LMS apps и без доменной логики.

### Axes
- Docker + site + скелет app `elms`
- Ролевая модель на три роли и placeholder DocTypes секций
- Social Login Key для Keycloak и Яндекс

### Invariants
- Runtime = Frappe Framework; SoT продукта = app `elms`
- Секреты только env/site_config, не в git
- Ошибки явные; silent fallback FORBIDDEN
- Эталон `frappe-erp-crm` — read-only паттерны

### Out
- Доменные DocTypes ERP/LMS (курсы, склады, документы)
- Отдельный Vue SPA
- Prod TLS / MFA
- Forge / 1С контур

### Done when
1. Site поднимается из compose с Administrator
2. Три роли ограничивают доступ к секциям на уровне permissions
3. На `/login` доступны Keycloak и Яндекс при корректных env

### Forbidden after
склеить оси в один mega-plan · ставить vendor apps «чтобы быстрее» · dual-path auth в обход Social Login Key

### Chat decisions
- SSO = Keycloak + Яндекс
- Роли = ELMS Admin / ELMS ERP User / ELMS LMS User
- Разделы = Desk Workspaces ERP / LMS / Settings

---

## Board

title: Запуск рабочей среды ELMS в Docker

summary: |
  Что делаем
  Собираем и запускаем систему ELMS так, чтобы любой разработчик одной командой поднял рабочий сайт: база данных, вход администратора, пустое приложение ELMS и сервис Keycloak рядом.

  Зачем
  Без этого нельзя стабильно проверять роли, вход через SSO и разделы Desk. Нужна общая «коробка», в которой дальше появляются права и обучение/ERP-скелет.

  Стадии
  1) Положить в проект платформу Frappe и каркас приложения ELMS.
  2) Описать Docker: база MariaDB, Redis, сайт, веб-сервер.
  3) При первом запуске автоматически создать сайт и пользователя Administrator.
  4) Добавить контейнер Keycloak (пока просто работает в стеке; настройка входа — в следующей задаче).
  5) Проверить: открывается страница входа, администратор входит, в системе видно приложение ELMS.

  Результат для наблюдателя
  По адресу локального сайта открывается вход ELMS, логин администратора работает, окружение готово к настройке ролей и SSO.
