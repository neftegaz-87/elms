# SSO ELMS: Keycloak-only

ELMS использует Keycloak как единственную границу идентичности. Вход выполняется
через штатную форму Frappe и локальные учётные данные Keycloak; внешние IdP,
broker hints и прямые OAuth-маршруты в production-контур не входят.

## Архитектурный поток

```text
[Браузер] → [Frappe /login] → [Keycloak realm elms] → [OIDC callback Frappe]
```

Frappe хранит только Social Login Key `Keycloak`, использует immutable `sub` как
идентификатор и сопоставляет существующего пользователя по верифицированному
email. Пароли в Frappe не сохраняются.

## Runtime и секреты

- `KEYCLOAK_CLIENT_SECRET` и пароль администратора Keycloak поставляются через
  Vault Agent; Yandex OAuth-секреты для ELMS не требуются.
- Realm seed: `docker/keycloak/realm-elms.json`; в нём нет identity providers
  или mappers внешнего брокера.
- Production healthcheck проверяет только обязательные Keycloak, Frappe и DB
  секреты.
- Для browser-facing URL используется `KEYCLOAK_PUBLIC_URL`, для server-side
  запросов — `KEYCLOAK_INTERNAL_URL`.

## Login contract

1. `/login` отдаёт стандартную форму пароля и `login-keycloak.js`.
2. Submit формы вызывает серверный Keycloak password flow.
3. После успешной проверки Frappe создаёт или находит пользователя по OIDC
   claims, назначает канонические роли и открывает Desk-сессию.
4. Неверный пароль, недоступный Keycloak или неверифицированный email завершают
   вход ошибкой; Frappe-only success не допускается.

## Legacy migration

Для пользователей, у которых осталась legacy identity link, администратор
запускает `elms.access.api.migrate_yandex_users` сначала с `dry_run=True`, затем
с `dry_run=False`. Операция идемпотентно создаёт/обновляет локального
пользователя Keycloak, добавляет `UPDATE_PASSWORD`, и только после успешного
действия провайдера заменяет старую ссылку. Пароли и секреты не выводятся.

Подробная процедура: `docs/runbooks/keycloak-yandex-user-migration.md`.

## Проверка

```bash
python3 -m json.tool docker/keycloak/realm-elms.json >/dev/null
bash -n docker/keycloak/entrypoint.sh scripts/live_smoke.sh
timeout -k 10s 300s bash scripts/live_smoke.sh
```

Live smoke проверяет OIDC discovery, страницу входа, callback и отсутствие
Yandex-маршрутов или `kc_idp_hint`.
