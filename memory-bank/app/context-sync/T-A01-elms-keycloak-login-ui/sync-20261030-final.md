# Context sync — T-A01-elms-keycloak-login-ui

**Дата:** 2026-10-30  
**Роль:** APP  
**Worker:** `agent_type=context-sync` (запускается parent после QA PASS)  
**Epic:** T-A01-elms-keycloak-login-ui  
**QA artifact:** `memory-bank/app/qa/T-A01-elms-keycloak-login-ui/qa-20261029-login-ui.yaml`  
**Session ID:** `session-4ccd0e96b16c`  
**Status:** PASS / final  
**Force:** no

## Evidence used

| Source | Path / jump |
|--------|-------------|
| QA artifact | `memory-bank/app/qa/T-A01-elms-keycloak-login-ui/qa-20261029-login-ui.yaml` |
| Bugfix queue | `memory-bank/app/bugfix/T-A01-elms-keycloak-login-ui/bugfix-queue.yaml` |
| Browser trace | `browser-artifacts/browser-evidence.json` |
| Browser screenshot | `browser-artifacts/login-page.png` |
| Live HTTP trace | `docs/reports/sso-browser-api-trace.json` |
| Technology axiom | `memory-bank/app/plan/T-A01-elms-keycloak-login-ui/md/plan.md` §Решение (`pydantic-settings` on env read boundary, `frappe.conf["keycloak_login"]` runtime SoT) |
| Context consumed | `memory-bank/app/plan/T-A01-elms-keycloak-login-ui/md/plan.md` §Context consumed |
| decompose-index | `memory-bank/app/plan/T-A01-elms-keycloak-login-ui/yaml/decompose-index.yaml` |
| Root canon | `techContext.md` / `productContext.md` / `systemPatterns.md` |

## Bugfix resolution

| Item | Class | Summary | Evidence |
|------|-------|---------|----------|
| BF-001 | lane:browser | `.btn-keycloak` background color переопределялся правилами `login.bundle.css` из-за порядка подключения CSS-ассетов | Добавлены `!important` и повышенная специфичность в `elms/elms/public/css/login.css`; `scripts/run_browser_qa.py` подтвердил `backgroundColor: rgb(13, 76, 211)`, `height: 44px`, `borderRadius: 3px`. |
| BF-002 | lane:live_smoke | AC+4 поток Yandex через брокер Keycloak без прямого вызова Frappe | `scripts/live_smoke.sh` расширен проверками делегирования (`/realms/elms/broker/yandex/login`, IdentityBrokerService endpoint `/realms/elms/broker/yandex/endpoint`, 0 прямых Yandex-вызовов); подтверждено в `docs/reports/sso-browser-api-trace.json`. |
| BF-003 | lane:browser | AC+1 ровно один контрол `.btn-keycloak` с публичным `KEYCLOAK_PUBLIC_URL/realms/elms` | `scripts/run_browser_qa.py` подтвердил ровно один `.btn-keycloak`, отсутствие внутренних хостов (`keycloak:8080`), 0 прямых Yandex-кнопок. |
| BF-004 | ac_gap | AC+6 / AC−3 отсутствие секретов в репозитории с наблюдаемым выводом zero-match | Выполнен bounded secret scan `! rg -i '(client_secret|password)\s*[:=]\s*["0-9a-zA-Z]{16,}' docker/ elms/ .env.example` (0 совпадений, exit 0); вывод прикреплён к артефакту QA. |

## QA retro

| Вопрос | Ответ |
|--------|-------|
| Какой дефект пропустили предыдущие gates? | CSS stylesheet ordering in Frappe: `login.bundle.css` is included via `head_include` block after `head.html`, overriding equal-specificity selectors from `web_include_css` |
| Какой gate/check оказался лишним? | none |
| Какой тест флапает или был хрупким? | none |
| Что изменить в следующем цикле? | Always test computed styles in actual browser via Playwright rather than relying solely on static CSS token text assertions |

## Changes

| File | Action | Summary |
|------|--------|---------|
| `memory-bank/techContext.md` | updated | Синхронизировано решение 18 (Login UI surface T-A01): сохранение штатной `/login`, ровно один контрол `.btn-keycloak` с публичным Keycloak URL, отсутствие direct Yandex, делегирование стандартной формы через `login-keycloak.js`, специфичность `login.css` против `login.bundle.css`, подтверждение computed styles 44px/3px/#0d4cd3; добавлен `T-A01` в таблицу планов foundation; зафиксированы результаты тестов (65 passed, asset build done, browser QA exit 0, live smoke exit 0, закрытие BF-001..BF-004). |
| `memory-bank/productContext.md` | updated | Уточнено описание среза `T-A01`: штатная `/login` как единственная поверхность входа, стандартная форма с делегированием в Keycloak через `login-keycloak.js`, ровно одна кнопка `.btn-keycloak` с публичным Keycloak URL, отсутствие direct Yandex-контролов, защита специфичности `login.css`, подтверждение computed styles (44px, 3px, #0d4cd3), закрытие всех дефектов очереди bugfix (BF-001..BF-004), 65 passed тестов. |
| `memory-bank/systemPatterns.md` | updated | Актуализирован паттерн 7 (`Stock Frappe Login Surface & Computed-Style Gate`): точное описание сосуществования стандартной формы логина и единой кнопки `.btn-keycloak`, исключение прямых Yandex-контролов, каскадная граница специфичности `login.css` над `login.bundle.css` с `!important`, обязательность live computed style проверки через Playwright. |
| `projectbrief.md` | no-op | Файл отсутствует в репозитории; изменений не требуется. |
| `constitution.md` | no-op | Вне скоупа задачи. |
| `style-guide.md` | no-op | Вне скоупа задачи. |

## Rationale

- Корневой канон приведен в строгое соответствие с фактическими результатами APP QA PASS эпика `T-A01-elms-keycloak-login-ui`.
- Все зафиксированные изменения основаны на первичных артефактах верификации: `memory-bank/app/qa/T-A01-elms-keycloak-login-ui/qa-20261029-login-ui.yaml`, `memory-bank/app/bugfix/T-A01-elms-keycloak-login-ui/bugfix-queue.yaml`, `browser-artifacts/browser-evidence.json`, `docs/reports/sso-browser-api-trace.json`.
- Исправлена неточность предыдущего чернового синка: зафиксировано корректное наличие ровно одной кнопки `.btn-keycloak` наряду со стандартной формой логина.
- Вся ретроспектива и результаты устранения блокеров BF-001..BF-004 перенесены без искажений.

## Forbidden check

- [x] Не трогали `product/vision|phases|roadmap`
- [x] Не трогали plan/decompose/implement/code

## Return

- `status: done` → `sync_path: memory-bank/app/context-sync/T-A01-elms-keycloak-login-ui/sync-20261030-final.md`
