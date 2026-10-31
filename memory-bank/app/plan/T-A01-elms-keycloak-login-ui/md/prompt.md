## Epic

### Outcome

Сделать на стандартной странице Frappe одну понятную кнопку входа через Keycloak в светлом служебном стиле проекта Neftegaz. Кнопка ведёт в публичный Keycloak; Yandex 360 и локальный fallback находятся внутри Keycloak, после callback пользователь возвращается в Frappe Desk с существующими ролями.

### In

- Scoped CSS кнопки и login surface по palette/geometry/state из `/home/aero/PyProject/neftegaz-ai-layer`
- Стандартный Frappe Social Login Key `Keycloak` и callback без template fork
- Env contract для Keycloak, Yandex broker, Frappe public URL и SSO policy
- Docker Compose propagation в create-site/backend/keycloak
- Typed Python env adapter через `pydantic-settings`/`SecretStr` на существующей `conf.py` boundary
- Keycloak realm `elms`, confidential client `elms-frappe`, Yandex OIDC broker и explicit local fallback
- Backend/frontend/wire tests, live smoke и manual/browser acceptance

### Out

- Прямой Frappe provider/callback для Yandex
- Новый FastAPI/Flask/whitelist auth endpoint или custom session
- Vue/React login SPA и fork `frappe/frappe/www/login.html`
- Workspaces Operations/LMS/Settings из T-F01
- Bulk Yandex import/SCIM и автоматические пароли для всех пользователей
- Глобальная дизайн-система, dark mode, мобильное приложение и копирование бренда Neftegaz

### Done when

1. `.env` → Docker → site config/Keycloak realm проходит без секретов в tracked files.
2. На `/login` ровно одна доступная кнопка Keycloak, в cobalt/white/graphite стиле Neftegaz; Yandex не является отдельной Frappe-кнопкой.
3. Local Keycloak fallback проходит настоящий callback и открывает `/app` с `sub` и default roles.
4. При наличии Yandex credentials brokered flow работает на странице Keycloak; при отсутствии конфигурация честно disabled/fail-fast.
5. Backend, frontend build, wire journey, live smoke и bounded SoT scans имеют evidence; visual automation или manual AC явно зафиксированы.

### Forbidden after

Две SSO-кнопки; direct Frappe→Yandex; `keycloak:8080` в browser URL; CSS-only authz; скрытый fallback на старый OAuth; секреты в realm/site config/fixtures; backend-only PASS без `/login` и callback evidence.

### Chat decisions

- Один APP vertical slice, `L1`, один mixed `s01`; INTEG child не создаём.
- Frappe standard login markup остаётся владельцем href/callback.
- `Keycloak` — единственный Frappe Social Login Key; Yandex — только Keycloak broker.
- `.env` — операторский input; Frappe runtime получает `keycloak_login`, Keycloak получает Yandex credentials.
- T-F01 продолжает Workspaces и больше не реализует login affordance.

## Covering

### Outcome

Рабочий человеко-понятный SSO-вход ELMS: визуально аккуратная кнопка в штатном Frappe login, публичный Keycloak с Yandex/local choices, реальный callback в Frappe и fail-closed конфигурация через Docker env.

### Axes

- Login UI surface и Neftegaz-derived visual states
- Frappe Social Login Key/Keycloak callback wire
- Keycloak realm + Yandex broker + local fallback
- Env/Docker/Pydantic settings boundary
- Mixed APP QA

### Invariants

- Frappe permissions и T-B03 identity/role behavior остаются authoritative.
- Никакого прямого Frappe→Yandex пути.
- Один provider, один callback, один пользовательский done-критерий.
- Secret values не попадают в git, realm JSON, Frappe site config или logs.
- CSS scoped to login surface и не меняет Desk/глобальный UI.

### Out

- Desk Workspaces и domain UI.
- Новый auth framework или отдельный API.
- Global Neftegaz design-system import.
- Production Yandex credential provisioning в репозитории.

### Done when

Один пользователь может открыть `/login`, увидеть единственную styled Keycloak action, пройти реальный Keycloak local/Yandex flow и открыть `/app`; missing env не создаёт broken link/session.

### Forbidden after

Optional/dual auth SoT; прямой Yandex provider; «готово» по одному CSS-файлу или JSON realm; второй login epic в T-F01.

## Board

title: Единый вход ELMS через Keycloak
summary: На стандартной странице ELMS появляется одна понятная кнопка входа через Keycloak. Пользователь проходит локальный или Yandex 360 вход и возвращается в Frappe Desk с действующими ролями.

Зачем это бизнесу: сотрудники получают единый и предсказуемый вход без дублирования провайдеров, а оператор может включать или отключать SSO через окружение без хранения секретов в коде.

Технически: реализованы scoped-стили login surface, типизированные настройки, Docker/Keycloak wiring, broker Yandex 360, fail-closed проверки, backend/frontend/browser QA и live HTTP smoke. Результат для наблюдателя — на /login видна одна styled Keycloak action, а после успешной авторизации открывается /app.
