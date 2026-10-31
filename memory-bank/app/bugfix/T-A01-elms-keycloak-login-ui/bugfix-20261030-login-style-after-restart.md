# BF-003 — Login visual language and asset delivery after container restart

## Symptom

После перезапуска dev-контейнеров `/login` иногда отдаёт страницу без Frappe CSS. Визуальная тема ELMS также должна покрывать весь стандартный экран входа, а не только кнопку Keycloak.

## Root cause

`assets/assets.json` и сохранённый named volume `frappe-dist` жили в разных состояниях: manifest ссылался на новые хэшированные Frappe CSS-файлы, а volume содержал старые имена. Runtime не запускал `bench build --force` при старте, поэтому nginx отвечал `404` на `website.bundle.css` и `login.bundle.css`.

## Scope

- собрать Frappe assets при старте dev backend до запуска Gunicorn;
- проверять в browser/live smoke, что все stylesheet links реально отвечают `200`;
- оформить login surface токенами и состояниями из `neftegaz-ai-layer` (`paper`, `surface`, `graphite`, `muted`, `line`, `action`, Source Sans fallback, тонкие контуры и cobalt action);
- сохранить стандартный Frappe login flow и fail-closed поведение SSO.

## Acceptance

- после `docker compose ... up` и перезапуска контейнера все CSS из `/login` доступны с HTTP `200`;
- экран `/login` визуально использует Neftegaz palette, control height `44px`, radius `3px`, focus/hover/active/disabled и reduced-motion;
- при заданном `KEYCLOAK_CLIENT_SECRET` отображается единственная кнопка Keycloak;
- при пустом секрете SSO остаётся отключённым без фиктивной кнопки или секрета.

## Verification

- targeted unit contract for the complete login surface;
- `bench build --force` during dev container startup;
- headless Chromium browser QA with stylesheet status checks;
- live HTTP smoke with stylesheet delivery checks.
