## Epic

### Outcome
Пользователь ELMS входит через Keycloak или Яндекс OAuth на стандартной `/login`: Social Login Key настроены, секреты только из env/site_config, новый SSO-user в dev получает default роль `ELMS LMS User` (или явный throw если роли нет) — без самописного OAuth-стека.

### In
- Keycloak realm/client import + Social Login Key provider Keycloak
- Yandex Social Login Key provider Custom + endpoints
- site_config/env credential injection
- Default role on SSO signup fail-closed
- Smoke/unit на fixtures и наличие кнопок провайдеров

### Out
- Docker bootstrap базовый (уже есть контейнер Keycloak)
- Матрица DocPerm секций (уже есть)
- Кастомный login SPA / редизайн Desk
- Prod IdP hardening, MFA, account linking UX beyond Frappe defaults

### Done when
1. При валидных KEYCLOAK_* на `/login` видна кнопка Keycloak; callback path `login_via_keycloak`
2. При валидных YANDEX_* видна кнопка Яндекс; callback `oauth2_logins.custom/yandex`
3. Secrets не в git; missing secret → провайдер не «тихо успешен» с пустым client
4. Новый signup (dev Allow) получает `ELMS LMS User` + `Desk User` или throw

### Forbidden after
хардкод client_secret · свой OAuth router в обход Social Login Key · silent empty roles on signup · dual auth framework

### Chat decisions
- Провайдеры: Keycloak + Яндекс
- Default SSO role в dev: ELMS LMS User

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

title: Вход в ELMS через Keycloak и Яндекс

summary: |
  Что делаем
  Подключаем удобный вход без отдельного пароля ELMS: корпоративный Keycloak и вход через Яндекс. Кнопки появляются на обычной странице входа системы.

  Зачем
  Людям проще войти привычным аккаунтом. Администратору проще контролировать доступ. Секреты приложений не хранятся в коде проекта.

  Важно для безопасности
  Пароли и ключи приложений лежат только в защищённых настройках окружения. Если ключ не задан — кнопка входа этим способом не включается «тихо наполовину». Новому пользователю при первом входе в тестовом режиме выдаётся узкая роль учебного контура (или система явно сообщает об ошибке, если роль не настроена).

  Стадии
  1) Довести Keycloak: realm, клиент приложения, адреса возврата после входа.
  2) Настроить в ELMS вход через Keycloak.
  3) Настроить в ELMS вход через Яндекс (приложение на стороне Яндекса + кнопки на /login).
  4) При первом входе нового человека назначить стартовую роль учебного контура + доступ в рабочий стол.
  5) Проверить вручную оба сценария входа и отсутствие секретов в git.

  Результат для наблюдателя
  На странице входа видны «Keycloak» и «Яндекс». После успешного входа человек попадает в ELMS с понятной стартовой ролью.
