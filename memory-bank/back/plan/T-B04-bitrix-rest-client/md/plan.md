# [T-B04-bitrix-rest-client] PLAN

**Дата:** 2026-10-28
**Режим:** BACK PLAN
**Уровень:** L3
**Статус:** active
**Clarify:** `memory-bank/back/clarify/clarify-20261028-bitrix-rest.md`
**Prompt:** [md/prompt.md](prompt.md)

**Skills:** writing-plans · python-testing-patterns · architecture-patterns (eng spine) · grill-me (Phase 0, уже на диске)

## Контекст

- req: отдельные Python-скрипты, которые по входящему вебхуку Bitrix24 вызывают любой REST-метод и показывают JSON. Рядом — инструкция, как создать вебхук и положить URL в настройки.
- deps: нет. Скрипты не входят в Frappe app `elms` и не ждут RBAC/SSO.
- refs: [входящий вебхук](https://apidocs.bitrix24.ru/local-integrations/local-webhooks.html), [вызов REST](https://apidocs.bitrix24.ru/settings/how-to-call-rest-api/index.html), [авторизация](https://apidocs.bitrix24.ru/settings/how-to-call-rest-api/authorization.html), [scope](https://apidocs.bitrix24.ru/api-reference/common/system/scope.html), [method.get](https://apidocs.bitrix24.ru/api-reference/common/system/method-get.html), [methods (deprecated)](https://apidocs.bitrix24.ru/api-reference/common/system/methods.html), [batch](https://apidocs.bitrix24.ru/settings/how-to-call-rest-api/batch.html), [права scope](https://apidocs.bitrix24.ru/api-reference/scopes/permissions.html)

## Context consumed

| Path | Что вошло в axiom / Deps / FR |
|------|-------------------------------|
| `memory-bank/techContext.md` | Runtime продукта — Frappe app `elms`. Секрет доски уже живёт в `BITRIX_WEBHOOK_URL`. Новый клиент не становится вторым путём доски и не читает этот ключ. |
| `memory-bank/systemPatterns.md` | Fail-closed и запрет параллельного web-фреймворка. Скрипты остаются CLI вне Desk, без FastAPI и без whitelist. |
| `memory-bank/projectbrief.md` | Файла в репозитории нет. Бриф не подменялся vision. |
| `memory-bank/architecture/index.md` | Каталога `memory-bank/architecture/` нет. As-built берётся из techContext. |
| `memory-bank/product/vision.md` | ELMS — свой Operations+LMS на Frappe. Доменные сущности ещё впереди. Зеркало Битрикс в DocType этому горизонту не принадлежит. |
| `memory-bank/product/modules.md` | Новый модуль app не заводится: это не DocType и не роль. Запись в modules не требуется. |
| `memory-bank/product/board-publish.md` | После плана карточка публикуется через `scripts/board-sync.sh`. Это канал доски, не REST-клиент эпика. |

## Delivery closure

| Capability / outcome | Classification | Production entrypoint and caller | Success / failure enforcement | Independent outcome test | Foundation approval / follow-up |
|---|---|---|---|---|---|
| Вызов любого метода REST и печать JSON | `vertical_slice` | `scripts/bitrix/call.py` запускает оператор | HTTP 200 без поля `error` → stdout = тело, exit 0. Поле `error` или не-JSON → stderr и exit 1. Кривой URL/JSON → exit 2, запрос не уходит | Given URL в `BITRIX_REST_WEBHOOK_URL` и подставленный HTTP, When процесс `call.py user.current`, Then POST на `{url}user.current.json` и stdout равен телу. Given только `BITRIX_WEBHOOK_URL`, When `call.py`, Then exit 2 и ноль запросов | `n/a` |
| Просмотр прав вебхука | `vertical_slice` | `scripts/bitrix/scope.py` | Тот же конверт, что у вызова. `--full` шлёт JSON `{"full": true}` | Given URL, When `scope.py --full`, Then POST `scope.json` с `{"full": true}` и stdout = тело | `n/a` |
| Инструкция входящего вебхука | `vertical_slice` | `docs/bitrix-incoming-webhook.md` читает оператор до первого запуска | В тексте есть меню создания, имя настройки `BITRIX_REST_WEBHOOK_URL` и запрет подставлять секрет доски | Given файл инструкции, When ищем имя настройки и шаги меню, Then оба есть, а `BITRIX_WEBHOOK_URL` упомянут только как чужой секрет, который эти скрипты не читают | `n/a` |

## Technology axiom (replace-not-wrap)

| Выбор | Machine input | FORBIDDEN после эпика |
|-------|---------------|------------------------|
| Pydantic v2 на границе | URL вебхука, JSON аргументов CLI, JSON-конверт ответа Битрикс | regex по HTML/прозе → строка «как будто разобрали ошибку»; второй сырой URL рядом с моделью |
| Один endpoint | Переменная `BITRIX_REST_WEBHOOK_URL` | чтение `BITRIX_WEBHOOK_URL`, пустая строка как повод взять другой ключ, soft default портала |
| Имя метода — одно поле | строчная точка-нотация, проверяется моделью до HTTP | параллельное поле «как ввёл пользователь» + отдельный normalize; enum всех методов портала |
| Ответ | модель конверта с `extra=allow`, наружу печатается исходный JSON | выкидывать неизвестные поля; считать список `methods` полным каталогом |

Клиента REST в репозитории нет. Доска ходит своим секретом и этим эпиком не заменяется. Greenfield для транспорта. Запрет читать секрет доски — enforce с первого шага, не «потом».

Имя метода не переводится в Enum: каталог портала открытый, `methods` официально неполный. Проверка конкретного имени с портала — вызов `method.get`, тем же `call.py`.

## Продуктовая спека (WHAT)

Оператор интеграции один раз кладёт URL входящего вебхука в настройку и дальше двумя командами смотрит, какие права у этого вебхука есть, и вызывает любой метод, который эти права разрешают. Ответ портала виден целиком. Ошибка портала и кривая настройка заканчиваются ненулевым кодом и текстом причины. Данные Битрикс в ELMS не сохраняются.

## Product probe (office-hours lite)

| # | Question | Answer / Probe | Decision / Impact on PLAN |
|---|----------|----------------|---------------------------|
| 1 | **Reframe:** Какую реальную проблему решаем (не фичу)? | Каждый интеграционный шаг сам собирал бы HTTP к порталу, а общего места для вебхука нет. | Один транспорт и одна настройка. |
| 2 | **Narrowest wedge:** Какой минимальный вариант проверит гипотезу? | Команда вызова метода и команда `scope` плюс инструкция вебхука. | Q1 = A. Нет обёрток по модулям и нет синка. |
| 3 | **Pre-mortem:** Почему этот план может провалиться через месяц? | Вебхук создали с узкими правами и ждут «весь портал». Либо секрет доски подставили в новую переменную и смешали контуры. | Инструкция прямо говорит про галочки. Код не читает секрет доски. `scope` показывает факт. |
| 4 | **Distribution/Adoption:** Как пользователи узнают/начнут использовать? | Инструкция в `docs/` и пример переменной в `.env.example`. Запуск — `python3` по пути скрипта. | FR на текст инструкции, не на устную договорённость. |
| 5 | **Technical leverage:** Какую тяжелую часть можно выкинуть или заменить? | Каталог методов руками и OAuth. Портал уже умеет `scope` и `method.get`. | Эти методы вызываются тем же транспортом. Отдельный генератор SDK вырезан. |
| 6 | **Appetite check:** Стоит ли задача заявленных ресурсов/timebox? | Два CLI, одна модель конверта, одна инструкция. Оценка — два дня. | `timebox_days: 2`. OpenAPI-дамп и ретраи — в cut list. |

### User Stories

| # | Story | Priority | Independent Test |
| :--- | :--- | :--- | :--- |
| US-001 | Как оператор интеграции, я хочу вызвать метод портала и увидеть JSON ответа, чтобы не писать HTTP в каждом шаге. | P0 | Процесс `call.py` с подставленным HTTP делает POST на URL метода и печатает тело. Поле `error` в теле даёт exit 1. |
| US-002 | Как оператор, я хочу увидеть права вебхука и полный список scope портала, чтобы понять, чего не хватает в галочках. | P0 | `scope.py` без флага шлёт `{}`. `scope.py --full` шлёт `{"full": true}`. Оба печатают тело ответа. |
| US-003 | Как оператор, я хочу по инструкции создать входящий вебхук и вписать URL в настройку, чтобы скрипты завелись без секрета доски. | P0 | Файл инструкции содержит шаги меню и имя `BITRIX_REST_WEBHOOK_URL`. Запуск без этой переменной, даже если задан только секрет доски, не делает HTTP и заканчивается exit 2. |

#### Acceptance Scenarios — US-001

- **Given:** `BITRIX_REST_WEBHOOK_URL` равен `https://portal.example/rest/1/secret/` и транспорт возвращает `{"result": {"ID": "1"}, "time": {}}`
- **When:** оператор запускает `python3 scripts/bitrix/call.py user.current`
- **Then:** уходит POST `https://portal.example/rest/1/secret/user.current.json` с телом `{}` и заголовком `Content-Type: application/json`; stdout — тот же JSON; код выхода 0; URL и секрет в stdout/stderr не появляются

#### Acceptance Scenarios — US-002

- **Given:** тот же URL и транспорт возвращает `{"result": ["crm", "user"]}`
- **When:** оператор запускает `python3 scripts/bitrix/scope.py --full`
- **Then:** POST `scope.json` с телом `{"full": true}`; stdout — тело ответа; код выхода 0

#### Acceptance Scenarios — US-003

- **Given:** в окружении есть только `BITRIX_WEBHOOK_URL`, а `BITRIX_REST_WEBHOOK_URL` нет
- **When:** оператор запускает `call.py` или `scope.py`
- **Then:** процесс завершается с кодом 2, текст говорит, что нет `BITRIX_REST_WEBHOOK_URL`, HTTP не вызывается

### Functional Requirements (FR-###)

- **FR-001:** `scripts/bitrix/call.py <method> [--params <json-object>]` читает только `BITRIX_REST_WEBHOOK_URL`, делает POST `{url}{method}.json` и при успехе печатает исходное JSON-тело в stdout.
- **FR-002:** Если в JSON есть непустое поле `error`, скрипт печатает `error` и `error_description` в stderr и завершается с кодом 1. Успешный stdout при этом пуст.
- **FR-003:** Нет переменной, пустое значение, не-https, путь не вида `/rest/<цифры>/<код>/` — код 2, HTTP нет. Переменная `BITRIX_WEBHOOK_URL` не читается.
- **FR-004:** `scripts/bitrix/scope.py` вызывает метод `scope`. Без флага тело `{}`. С `--full` тело `{"full": true}`.
- **FR-005:** `docs/bitrix-incoming-webhook.md` на русском объясняет, как создать входящий вебхук, какие права отметить и в какую переменную вставить URL.
- **FR-006:** Имя метода — строчные сегменты через точку (`user.current`, `crm.item.list`). Иное имя — код 2 до HTTP. Регистр сам не приводится.
- **FR-007:** `--params` — JSON-объект. Массив, строка, пустое или битый JSON — код 2 до HTTP. Без флага тело запроса `{}`.
- **FR-008:** Для метода `batch` локально отклоняются пакет больше 50 команд и команда, чьё значение начинается с `batch`. Код 2, текст с `ERROR_BATCH_LENGTH_EXCEEDED` или `ERROR_BATCH_METHOD_NOT_ALLOWED`. Остальные методы уходят на портал как есть, включая `*.add` и `*.delete`.
- **FR-009:** `.env.example` содержит пустой пример `BITRIX_REST_WEBHOOK_URL` и фразу, что это не ключ доски.

### Success Criteria (SC-###)

| ID | Измеримый результат | Проверка / источник | Type |
| :--- | :--- | :--- | :--- |
| SC-001 | Успешный вызов печатает тело портала и код 0 | unittest с подставленным HTTP, US-001 | outcome |
| SC-002 | Ошибка портала и кривая настройка не выглядят как успех | US-001 error path и US-003, коды 1 и 2 | outcome |
| SC-003 | Оператор может создать вебхук по файлу инструкции, не открывая план | наличие шагов меню и имени переменной в `docs/bitrix-incoming-webhook.md` | outcome |

### Assumptions

- Один портал, один входящий вебхук, запросы идут от сотрудника, который вебхук создал.
- Права шире галочек вебхук не даёт. «Видеть всё» значит видеть всё, что отмечено, и уметь запросить список scope.
- Изменения данных на портале разрешены: оператор передаёт имя метода сам.
- Pydantic v2 уже стоит в интерпретаторе, которым запускают скрипты (проверено: 2.13.4). Отдельный пакет HTTP не добавляем: POST делает `urllib.request`.
- `bin/pytest` в этом репозитории — проверка каркаса ELMS, не запуск этих тестов. Прогон эпика — `python3 -m unittest`.

### Clarifications

- Session: 2026-10-28, `memory-bank/back/clarify/clarify-20261028-bitrix-rest.md`.
- Q1 = A. Q2 = A. Запись любым методом оставлена на том же `call.py`. Список scope в коде не зашит.

### [НУЖНО УТОЧНИТЬ]

- Нет открытых пунктов.

## AC

1. `call.py user.current` с валидным URL печатает JSON портала и выходит с кодом 0.
2. Тело с `error` даёт код 1, stderr содержит код ошибки, stdout пуст.
3. Нет `BITRIX_REST_WEBHOOK_URL` — код 2, даже если `BITRIX_WEBHOOK_URL` задан, и HTTP не вызывается.
4. `scope.py --full` отправляет `{"full": true}`.
5. Инструкция и `.env.example` называют `BITRIX_REST_WEBHOOK_URL` и не учат читать ключ доски.
6. `batch` длиннее 50 или с вложенным `batch` не уходит в сеть.

### AC− (запрет соседнего секрета, клиента доски не удаляем)

1. Нет второго entrypoint на вызов REST интеграций.
2. Нет подстановки `BITRIX_WEBHOOK_URL`, если новая переменная пуста.
3. Кривой URL и битый JSON падают до запроса, без заглушки `{"result": []}`.
4. Доска остаётся на своём ключе. Этот эпик её код не меняет и не оборачивает.
5. Нет разбора ошибки регулярным выражением из HTML или текста страницы.

## Boundary / negative cases

| ID | Class | Input / condition | Expected (fail-closed) | Maps TM / AC |
|----|-------|-------------------|------------------------|--------------|
| BN-001 | empty / missing | переменной `BITRIX_REST_WEBHOOK_URL` нет | exit 2, HTTP нет, текст имени переменной | TM-003 / AC-3 |
| BN-002 | unknown / DENY old | задан только `BITRIX_WEBHOOK_URL` | exit 2, этот URL не читается и не логируется | TM-003 / AC−2 |
| BN-003 | authz / misconfig | URL без `https` или путь не `/rest/<id>/<code>/` | exit 2 до HTTP | TM-004 / AC-3 |
| BN-004 | misconfig | `--params` не JSON-объект; имя метода с заглавными или без точки | exit 2 до HTTP | TM-005 / FR-006, FR-007 |
| BN-005 | overflow | `batch` с 51 командой или командой `batch...` | exit 2, в тексте код ограничения, HTTP нет | TM-006 / FR-008 |
| BN-006 | authz | тело `{"error":"insufficient_scope","error_description":"...webhook token"}` | exit 1, stderr содержит `insufficient_scope`, stdout пуст | TM-002 / AC-2 |
| BN-007 | misconfig | HTTP не JSON или код не 200 | exit 1, stderr содержит статус, секрета в тексте нет | TM-007 / AC−5 |

Checklist:

| # | Class | Status |
|---|-------|--------|
| 1 | empty / missing required | done BN-001 |
| 2 | unknown key / DENY legacy SoT | done BN-002 |
| 3 | max / overflow / unicode | done BN-005; имя метода длиннее 128 символов тоже exit 2 |
| 4 | authz / unauthenticated | done BN-003, BN-006 |
| 5 | duplicate / idempotence | n/a: скрипт не хранит состояние и не дедуплицирует вызовы. Повторный запуск — новый POST |
| 6 | misconfig fail-closed (не stub) | done BN-001, BN-003, BN-004, BN-007 |

**Notes:** табличные кейсы URL и имён методов — в unittest параметрами, не один счастливый путь.

## Техника / архитектура (HOW)

Стек: Python 3.12, pydantic 2, `urllib.request`. Скрипты лежат в `scripts/bitrix/` и запускаются файлом, не через `bench` и не через Frappe whitelist.

Модуль `scripts/bitrix/rest_client.py` — единственное место HTTP.

- `WebhookEndpoint` — pydantic-модель. Поле `url` собирается только из `BITRIX_REST_WEBHOOK_URL`. Схема `https`. Путь ровно три сегмента после хоста: `rest`, цифры пользователя, код. Хвост с именем метода запрещён. Слэш на конце при хранении есть, в строке запроса не двоится.
- `CallArgs` — `method: str` с ограничением `^[a-z][a-z0-9_]{0,63}(\.[a-z][a-z0-9_]{0,63})+$` и длина всей строки не больше 128; `params: dict[str, Any]`.
- `RestEnvelope` — `error: str | None = None`, `error_description: str | None = None`, остальные поля через `extra=allow`. Непустое `error` поднимает `BitrixRestError` с этими двумя полями.
- `post_json(endpoint, method, params, opener) -> bytes` — POST, timeout 30 секунд, редиректы не следуют. Не-200 и не-JSON — `BitrixRestError`. Тело успеха возвращается байтами как пришло, после проверки конверта.

`call.py` и `scope.py` только разбирают argv, зовут `post_json` и печатают байты в stdout. Общего «ещё одного клиента» нет.

Коды выхода: `0` успех, `1` ответ портала или сеть, `2` локальная настройка и аргументы.

Секрет из URL в сообщения об ошибках не подставляется. В тексте остаётся хост и имя метода.

Инструкция (FR-005) — файл `docs/bitrix-incoming-webhook.md` с таким текстом:

```markdown
# Входящий вебхук Bitrix24 для скриптов интеграции

Скрипты `scripts/bitrix/call.py` и `scripts/bitrix/scope.py` ходят в один портал от имени сотрудника, который создал входящий вебхук. Канон: https://apidocs.bitrix24.ru/local-integrations/local-webhooks.html

## Создать вебхук

1. Войдите в портал тем сотрудником, чьи права должны быть у запросов. Метод не увидит сделку, которую этот сотрудник не видит в интерфейсе.
2. Откройте Приложения → Разработчикам. Если пункта «Входящий вебхук» нет, администратор должен разрешить этому сотруднику создавать вебхуки.
3. Готовые сценарии → Другое → Входящий вебхук.
4. В блоке назначения прав отметьте разделы, которые интеграции будут вызывать. Без галочки портал ответит `insufficient_scope`. Чтобы посмотреть, какие разделы вообще есть на портале, после сохранения запустите `python3 scripts/bitrix/scope.py --full`. Чтобы увидеть, что уже выдано этому вебхуку, запустите `python3 scripts/bitrix/scope.py`.
5. Сохраните вебхук и скопируйте URL вида `https://<портал>/rest/<user_id>/<код>/`. Код — секрет. Его не коммитят, не пишут в чат и не кладут в браузерный код.
6. Если администратор откроет чужой вебхук на редактирование, код сменится. Тогда в настройку вставляют новый URL.

Часть методов через вебхук не вызывается и отвечает `WRONG_AUTH_TYPE` (например `placement.bind` и часть телефонии). Для них нужно приложение, не этот URL. Скрипты сами на другой способ входа не переключаются.

## Куда вставить URL

В `.env` проекта (файл не коммитится):

```
BITRIX_REST_WEBHOOK_URL=https://<портал>/rest/<user_id>/<код>/
```

Это не `BITRIX_WEBHOOK_URL`. Тот ключ принадлежит доске. Скрипты интеграции его не читают. Пустая новая переменная не подменяется ключом доски.

## Как вызывать

Права текущего вебхука:

```
python3 scripts/bitrix/scope.py
python3 scripts/bitrix/scope.py --full
```

Любой метод, тело JSON-объектом. Имя метода — строчными буквами:

```
python3 scripts/bitrix/call.py user.current
python3 scripts/bitrix/call.py crm.item.list --params '{"entityTypeId": 2}'
```

Успех печатает JSON портала и код выхода 0. Ошибка портала — код 1 и текст `error` / `error_description` в stderr. Кривой URL, битый JSON или пустая настройка — код 2, запрос не отправляется.

Проверить, существует ли метод при текущих правах: `python3 scripts/bitrix/call.py method.get --params '{"name":"user.current"}'`. Список `methods` устарел и неполон (`tasks.task.list`, `crm.item.list` в него не входят). Его не использовать как каталог.

Пакет до 50 команд — тот же вызов метода `batch` (https://apidocs.bitrix24.ru/settings/how-to-call-rest-api/batch.html). Вложенный `batch` и пакет длиннее 50 скрипт отклоняет локально.

Вызов `*.add`, `*.update`, `*.delete` реально меняет данные портала от имени владельца вебхука. Отдельного режима «только чтение» нет.
```

`.env.example` дописывает блок:

```
# REST-скрипты интеграции. Не путать с BITRIX_WEBHOOK_URL доски.
BITRIX_REST_WEBHOOK_URL=
```

## Eng review spine

### Data flow (ASCII)

```text
[Оператор] -> [call.py | scope.py] -> [WebhookEndpoint + CallArgs]
            sync argv                 pydantic, до сети
         -> [post_json / urllib] -> [Bitrix REST POST *.json]
            sync, timeout 30s, без редиректа
         -> [RestEnvelope] -> stdout JSON | stderr + exit 1|2
            extra=allow
```

### Failure matrix

| Component / link | Failure | Detection | User/system response | Test ID |
|------------------|---------|-----------|----------------------|---------|
| Настройка | нет `BITRIX_REST_WEBHOOK_URL` | модель не строится | exit 2, HTTP нет | TM-003 |
| Настройка | в окружении только ключ доски | ключ не читается | exit 2 | TM-003 |
| URL | не https или чужой путь | pydantic | exit 2 | TM-004 |
| argv | битый JSON или плохое имя метода | pydantic до HTTP | exit 2 | TM-005 |
| batch | >50 или вложенный batch | локальная проверка | exit 2 с кодом ограничения | TM-006 |
| Портал | `error` в JSON, часто HTTP 200 | `RestEnvelope.error` | exit 1, stderr | TM-002 |
| Сеть | timeout, не-200, не JSON | `BitrixRestError` | exit 1, без секрета в тексте | TM-007 |
| Успех | JSON без `error` | конверт пустой error | stdout = байты тела, exit 0 | TM-001 |

### Eng spine self-check

| Dimension | Score 1–5 | Gap / action |
|-----------|-----------|--------------|
| Data flow complete | 5 | Четыре хопа: argv → модель → POST → конверт. Асинхронности нет. |
| Failure coverage | 5 | Настройка, соседний секрет, портал, сеть, batch. |
| Testability | 5 | `if __name__` вызывает `main(argv, env, opener)`. Тест пустого окружения запускает файл процессом. Остальные кейсы зовут тот же `main` с подставленным opener. Сети портала нет. |

Паттерн: один адаптер наружу (HTTP) и pydantic на границе. Слоя сущностей CRM нет — локальной предметной модели Битрикс этот эпик не вводит. Порты на каждый модуль были бы каталогом обёрток, от которого отказались в Q1.

## Replacement / sunset (brownfield)

Greenfield. Код доски не устаревает и не удаляется.

### A. Code / modules

| Устаревает (path / symbol) | Замена | Policy |
| :--- | :--- | :--- |
| n/a | — | greenfield |

### B. Entrypoints / deploy

| Устаревает (compose service / CMD / CLI) | Замена | Policy |
| :--- | :--- | :--- |
| n/a | — | greenfield |

### C. Fallbacks / soft-fail

| Устаревает (pattern / default / stub) | Замена (fail-closed) | Policy |
| :--- | :--- | :--- |
| n/a — клиента не было. Соседний ключ доски не является legacy-парсером этого эпика | не читать `BITRIX_WEBHOOK_URL` | keep у доски; для этих скриптов ключ запрещён |

### I. Instruction surfaces

| Устаревает (prompt / rule / finish-block / spawn text) | Замена (инструкция нового SoT) | Policy |
| :--- | :--- | :--- |
| n/a | `docs/bitrix-incoming-webhook.md` — новый SoT для оператора | greenfield |

<a id="qa-consumes"></a>
## QA consumes (test plan)

### Scope under test

- Epic / surfaces: `scripts/bitrix/call.py`, `scripts/bitrix/scope.py`, `scripts/bitrix/rest_client.py`, `docs/bitrix-incoming-webhook.md`, строка в `.env.example`
- Out of scope for QA: живой портал, доска, Frappe, OAuth

### Test matrix

| ID | Priority | Scenario | Command / fixture | Expected | Maps FR/AC |
|----|----------|----------|-------------------|----------|------------|
| TM-001 | P0 | Успешный `user.current` печатает тело | `timeout -k 10s 300s python3 -m unittest tests.bitrix.test_rest_client.CallSuccessTest` | POST на `user.current.json`, stdout = тело, exit 0 | AC-1 / US-001 |
| TM-002 | P0 | Конверт `insufficient_scope` | тот же модуль, `CallBitrixErrorTest` | exit 1, stderr содержит `insufficient_scope`, stdout пуст | AC-2 / BN-006 |
| TM-003 | P0 | Нет своего URL, есть только ключ доски | `MissingWebhookTest` | exit 2, opener не вызван | AC-3 / BN-001 / BN-002 |
| TM-004 | P0 | URL `http://` и URL с уже пришитым методом | `BadWebhookUrlTest` | exit 2 | BN-003 / AC-3 |
| TM-005 | P0 | `User.Current` и `--params []` | `BadArgsTest` | exit 2, HTTP нет | BN-004 / FR-006 / FR-007 |
| TM-006 | P0 | batch 51 и вложенный batch | `BatchGuardTest` | exit 2, HTTP нет | BN-005 / FR-008 |
| TM-007 | P0 | HTTP 500 и тело не JSON | `TransportFailureTest` | exit 1, секрета в stderr нет | BN-007 |
| TM-008 | P0 | `scope.py --full` | `ScopeFullTest` | тело `{"full": true}` | AC-4 / FR-004 |
| TM-009 | P0 | Инструкция и example | `InstructionTest` | файл содержит шаги «Входящий вебхук» и `BITRIX_REST_WEBHOOK_URL`; example содержит ту же переменную | AC-5 / FR-005 / FR-009 |

Прогон всего модуля:

```
timeout -k 10s 300s python3 -m unittest tests.bitrix.test_rest_client
```

Живой портал в этот прогон не входит. После того как оператор вставит URL, ручная проверка — `scope.py`, затем `call.py user.current`.

### Regression notes

- `bin/pytest` этот модуль не запускает. Зелёный `bin/pytest` не закрывает эпик.
- Тесты поднимают скрипт процессом и подменяют HTTP. Общий сокет и общий `.env` репозитория не читают: окружение теста задаёт только нужные ключи.

## Review readiness

| Gate | Required | Status | Evidence |
|------|----------|--------|----------|
| CLARIFY / Product probe | L3: one of done | done | clarify-20261028-bitrix-rest.md + §Product probe |
| Eng review spine | L2+ | done | §Eng review spine |
| §0.11 counterparts (draft) | if external refs in HOW | done | таблица ниже |
| Delivery closure | P0/P1 runtime capability | done | §Delivery closure, оба CLI — обещанный entrypoint |
| Boundary / negative cases | L2+ | done | BN-001…BN-007 |
| CREATIVE | if flagged | n/a | UI и развилки контракта нет |
| qa_consumes draft | L2+ | done | TM-001…TM-009, каждый BN имеет TM |
| Plan review batch | L2+ | done | лог ниже |

### §0.11 counterparts

| Внешняя ссылка в HOW | Парный контракт | Где проверяется |
|---|---|---|
| POST `{url}{method}.json` | страница вызова REST | TM-001 смотрит URL и `Content-Type` |
| `scope` и `full=true` в JSON, не form-data | страница `scope` | TM-008 |
| `error` + `error_description`, в том числе при HTTP 200 | страница авторизации и прав | TM-002 |
| batch ≤ 50 и запрет вложенности | страница batch | TM-006 |
| `methods` неполный | страница `methods` | инструкция запрещает каталог; отдельного скрипта `methods` нет |
| `method.get` | страница `method.get` | тот же `call.py`, отдельной обёртки нет |

## Plan review batch log

| Phase | Auto-resolved | Deferred (owner/next) | Taste / CRITICAL surfaced |
|-------|---------------|-------------------------|---------------------------|
| Product | Клин = транспорт + инструкция. Синк и SDK-модули вырезаны ответом Q1 = A. | нет | Широкий вебхук умеет менять данные. Это принято, не спрятано режимом только чтения. |
| Eng | Один модуль HTTP, pydantic на JSON, urllib, тесты процессом. Без портов на CRM/диск/задачи. | OpenAPI-дамп `rest.documentation.openapi` не входит (cut list) | `bin/pytest` легко принять за прогон этих тестов. В QA consumes это запрещено явно. |

## До DECOMPOSE (черновик нарезки)

Намёк, не контракт числа шагов. Исходы: настройка, вызов, scope, инструкция. Швов дробления нет. Полоса M, cap 5, цель 4.

1. `s01` — `WebhookEndpoint` и отказ читать ключ доски. Поведение: процесс без своей переменной выходит с кодом 2 и не зовёт сеть.
2. `s02` — `call.py`, конверт, коды 0/1/2, локальный отказ кривого `batch`.
3. `s03` — `scope.py` и `--full`.
4. `s04` — `docs/bitrix-incoming-webhook.md` и строка в `.env.example`.

Тесты лежат в шаге, который даёт поведение, а не отдельным шагом «покрыть потом».

## Appetite

| Поле | Значение | Описание |
| :--- | :--- | :--- |
| `timebox_days` | `2` | Календарный бюджет |
| `cut_list` | `['выгрузка OpenAPI rest.documentation.openapi', 'автоповтор при QUERY_LIMIT_EXCEEDED', 'обёртки модулей CRM и задач']` | Сначала вырезается это. Успех вызова, ошибка портала, отказ от ключа доски и инструкция остаются. |

## Следующий режим

→ BACK DECOMPOSE `T-B04-bitrix-rest-client`

CREATIVE не нужен.
