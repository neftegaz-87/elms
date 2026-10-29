## Epic

### Outcome
Пользователь ELMS входит через единственную кнопку Keycloak на стандартной `/login`; Keycloak брокерит Yandex 360, создаёт realm-пользователя при первом brokered login и возвращает OIDC-сессию во Frappe. Для выбранных пользователей локальный пароль Keycloak является резервным способом входа при недоступности Yandex. Секреты только из env/site_config, новый SSO-user в dev получает default роль `ELMS LMS User` (или явный throw если роли нет) — без самописного OAuth-стека.

### In
- Keycloak realm/client import + Social Login Key provider Keycloak
- Yandex OIDC Identity Provider внутри Keycloak + first-broker-login provisioning
- site_config/env credential injection
- Optional explicit local Keycloak credential for approved fallback users
- Default role on SSO signup fail-closed
- Smoke/unit на brokered flow, one Frappe provider, fallback path, and secret hygiene

### Out
- Docker bootstrap базовый (уже есть контейнер Keycloak)
- Матрица DocPerm секций (уже есть)
- Кастомный login SPA / редизайн Desk
- Prod IdP hardening, MFA, account linking UX beyond Frappe defaults

### Done when
1. При валидных KEYCLOAK_* на `/login` видна только кнопка Keycloak; callback path `login_via_keycloak`
2. При валидных YANDEX_* Keycloak показывает Yandex как upstream IdP; Yandex callback указывает на Keycloak broker endpoint
3. Первый вход через Yandex создаёт/связывает Keycloak realm user и затем Frappe User; полный импорт каталога не обещается
4. Для пользователя с явно установленным локальным паролем Keycloak вход работает при недоступном Yandex
5. Secrets не в git; missing secret → провайдер/брокер не «тихо успешен» с пустым client
6. Новый signup (dev Allow) получает `ELMS LMS User` + `Desk User` или throw

### Forbidden after
хардкод client_secret · прямой Frappe→Yandex OAuth router · второй Yandex Social Login Key · silent empty roles on signup · dual auth framework

### Chat decisions
- Frappe-facing provider: только Keycloak; Yandex — upstream Identity Provider внутри Keycloak
- Default SSO role в dev: ELMS LMS User
- Local Keycloak password fallback — только для явно выбранных пользователей

---

## Covering

### Outcome
ELMS получает воспроизводимый foundation: один Frappe site в Docker с custom app, БД User, тремя ролями-разделами и базовым brokered SSO Keycloak→Yandex с локальным Keycloak fallback — без vendor Operations/LMS apps и без доменной логики.

### Axes
- Docker + site + скелет app `elms`
- Ролевая модель на три роли и placeholder DocTypes секций
- Social Login Key для Keycloak; Yandex broker configuration in Keycloak

### Invariants
- Runtime = Frappe Framework; SoT продукта = app `elms`
- Секреты только env/site_config, не в git
- Ошибки явные; silent fallback FORBIDDEN
- Эталон `frappe-erp-crm` — read-only паттерны

### Out
- Доменные DocTypes Operations/LMS (курсы, склады, документы)
- Отдельный Vue SPA
- Prod TLS / MFA
- Forge / 1С контур

### Done when
1. Site поднимается из compose с Administrator
2. Три роли ограничивают доступ к секциям на уровне permissions
3. На `/login` доступен только Keycloak; внутри Keycloak доступны Yandex и, для разрешённых пользователей, локальная форма пароля

### Forbidden after
склеить оси в один mega-plan · ставить vendor apps «чтобы быстрее» · dual-path auth в обход Social Login Key

### Chat decisions
- SSO = Keycloak + Яндекс
- Роли = ELMS Admin / ELMS Operations User / ELMS LMS User
- Разделы = Desk Workspaces Operations / LMS / Settings

---

## Board

title: Вход в ELMS через Keycloak с Yandex broker и локальным fallback

summary: |
  Что делаем
  Подключаем единый вход через Keycloak. На странице Keycloak пользователь обычно выбирает Yandex, а для заранее подготовленных пользователей доступен локальный пароль Keycloak при сбое Yandex. Во Frappe остаётся одна кнопка.

  Зачем
  Людям проще войти привычным аккаунтом. Администратору проще контролировать доступ. Секреты приложений не хранятся в коде проекта.

  Важно для безопасности
  Пароли и ключи приложений лежат только в защищённых настройках окружения. Если ключ не задан — кнопка входа этим способом не включается «тихо наполовину». Новому пользователю при первом входе в тестовом режиме выдаётся узкая роль учебного контура (или система явно сообщает об ошибке, если роль не настроена).

  Стадии
  1) Довести Keycloak: realm, клиент приложения, адреса возврата после входа.
  2) Настроить в Keycloak Yandex Identity Provider и broker callback.
  3) Настроить в ELMS единственный Social Login Key Keycloak.
  4) При первом brokered входе создать realm user, federated link и Frappe User со стартовой ролью учебного контура.
  5) Для выбранного fallback-пользователя установить локальный пароль Keycloak и проверить вход при недоступном Yandex.
  6) Проверить отсутствие прямого Yandex provider и секретов в git.

  Результат для наблюдателя
На странице входа виден «Keycloak». После выбора Yandex внутри Keycloak человек попадает в ELMS с понятной стартовой ролью; при аварии одобренный fallback-пользователь входит локальным паролем Keycloak.
