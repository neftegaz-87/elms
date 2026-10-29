# clarify — bitrix-rest

**plan_id:** n/a
**slug:** bitrix-rest
**role:** back
**date:** 2026-10-28
**feature_description:** Отдельные Python-скрипты, которые по входящему вебхуку Bitrix24 вызывают REST и показывают, что портал отдаёт. Инструкция, как создать вебхук и положить URL в настройки.
**status:** done

---

## Контекст и цель

- Вход: `BACK PLAN` — полная интеграция с API Битрикс, документация вебхука, URL в настройках, вызов отдельными Python-скриптами во время интеграций.
- Цель сессии CLARIFY: снять ambiguity до Phase 1 (Phase 0 внутри `BACK PLAN`).
- Факты из репозитория (не спрашиваем):
  - Продукт ELMS — Frappe Operations+LMS (`memory-bank/product/vision.md`). Доменные сущности — следующий горизонт после foundation. Готового Python-клиента Bitrix REST в коде нет.
  - Доска разработки уже ходит в Bitrix24 через `BITRIX_WEBHOOK_URL` в `.env` (`LOOP_BOARD_PROVIDER=bitrix24`). Это секрет доски, не клиент интеграций. Значение URL в этот артефакт не копируется.
  - Официальный канон вызова: входящий вебхук, POST JSON на `https://<портал>/rest/<user_id>/<code>/<method>.json`. Список прав текущего вебхука — метод `scope`. Полный набор модулей портала — `scope` с `full=true`.
  - Документация: [входящие и исходящие вебхуки](https://apidocs.bitrix24.ru/local-integrations/local-webhooks.html), [как вызывать REST](https://apidocs.bitrix24.ru/settings/how-to-call-rest-api/index.html), [авторизация](https://apidocs.bitrix24.ru/settings/how-to-call-rest-api/authorization.html), [scope](https://apidocs.bitrix24.ru/api-reference/common/system/scope.html), [права](https://apidocs.bitrix24.ru/api-reference/scopes/permissions.html).
- Ограничение платформы: вебхук видит только отмеченные scope и права сотрудника, который его создал. Методы контекста приложения (`placement.bind` и часть телефонии/чатов) через вебхук недоступны (`WRONG_AUTH_TYPE`). «Видеть вообще всё» без галочек прав и без OAuth-приложения платформа не отдаёт.

---

## Grill pass (Phase 0 — mandatory)

| Поле | Значение |
|------|----------|
| **Reframe** | Нужен не синк портала в ELMS и не второй клиент доски, а транспорт: скрипты читают URL вебхука из настроек, вызывают метод REST и печатают ответ. «Всё видеть» = узнать scope вебхука и вызвать любой метод, который этот scope разрешает. |
| **Premises** | 1. Потребитель — человек или шаг интеграции, который запускает скрипт. Статус: `accepted`. 2. Авторизация — входящий вебхук, URL в настройках. Статус: `accepted`. 3. Форма клиента — универсальный вызов плюс просмотр scope, без зеркала в DocType. Статус: `accepted` (Q1 = A). 4. Отдельная настройка, не вебхук доски. Статус: `accepted` (Q2 = A). 5. OAuth, события и placement не входят. Статус: `accepted`. |
| **Weakest link** | Вебхук с широкими правами выполняет изменения от имени сотрудника. Транспорт имя метода не фильтрует: это следствие Q1 = A, риск описан в инструкции. |
| **Anti-scope** | Не Desk UI, не DocType-синк ELMS, не замена доски, не OAuth и не исходящие вебхуки Bitrix→ELMS. |
| **Verdict** | `needs_user_Q` → закрыт ответами Round 1 |
| **Design tree (sketch)** | 1) Форма клиента: универсальный вызов / каталог модулей / синк в ELMS. 2) Идентичность вебхука: новая настройка или секрет доски. 3) После (1): политика записи (метод как есть / только чтение). 4) После (1–2): какие scope перечислить в инструкции. 5) Где лежат скрипты (`scripts/bitrix/`). 6) Ошибки `insufficient_scope` и `WRONG_AUTH_TYPE` без подмены другим каналом авторизации. |

---

## Product probe (office-hours lite, optional)

| # | Вопрос | Контекст / Ответ |
|---|--------|------------------|
| 1 | **Demand reality** | Запрос в этой сессии: дергать API Битрикс из интеграций и видеть ответы. Инцидент в коде не найден — клиента нет. |
| 2 | **Status quo** | Доска ходит своим вебхуком. Общего вызова REST нет: каждый будущий интеграционный шаг писал бы свой HTTP. |
| 3 | **Desperate specificity** | Нет одного места, куда кладётся вебхук интеграций, и нет команды «вызови метод и покажи JSON». |
| 4 | **Narrowest wedge** | Скрипт `scope` + скрипт вызова произвольного метода + инструкция создания входящего вебхука. Каталог всех методов руками и синк в Frappe — шире клина. |
| 5 | **Observation & surprise** | Вебхук не равен «весь портал»: права задаются галочками, часть методов требует приложение. |
| 6 | **Future-fit** | Если позже появится локальное приложение OAuth или синк CRM в ELMS, транспорт скриптов остаётся годным; зеркало DocType этот клин не обещает. |

- **Reframe:** транспорт и инструкция, не продукт «ELMS зеркалит Битрикс».
- **Premises (3–5 falsifiable):** см. Grill pass.
- **Recommended wedge:** универсальный вызов + `scope` + отдельная настройка вебхука.

---

## Таксономия сканирования

| Категория | Status | Notes |
|-----------|--------|-------|
| scope | Clear | Q1 = A: универсальный вызов и просмотр scope. Синк и каталог обёрток вне эпика. |
| data | Clear | Локальных сущностей нет. Тело запроса и ответа — JSON портала как есть. |
| UX-API | Clear | Два скрипта: вызов метода и просмотр scope. Ошибка Битрикс — ненулевой выход. |
| NFR | Clear | Секрет только в `BITRIX_REST_WEBHOOK_URL`. Повтор запроса при лимите не делаем. |
| integrations | Clear | Q2 = A: новый входящий вебхук. Доска и OAuth не используются. |
| edge | Clear | Пустой URL, чужой секрет доски, `insufficient_scope`, `WRONG_AUTH_TYPE`, лимит batch — в плане как fail-closed. |
| constraints | Clear | Python-скрипты, не Frappe whitelist. Ошибки без fallback на другой канал авторизации. |
| terminology | Clear | «Хук» = входящий вебхук REST в отдельной настройке. |
| design_skills (FRONT UI) | n/a | BACK, UI нет. |

---

## Design skills pack (FRONT — при UI-scope)

n/a

---

## Frontier rounds

### Round 1
- Q1 форма клиента → A · resolution: resolved
- Q2 идентичность вебхука → A · resolution: resolved

### Round 2
- Не задавался. Политика записи вытекает из Q1 = A: тот же вызов выполняет любое имя метода, включая изменение данных. Список scope в коде не фиксируется: его задают галочками вебхука, скрипт `scope` показывает факт.

### Round 3
- —

---

## Q→A log

### Q1
- **Question:** Что в этой итерации значит «полная интеграция» и «всё видеть»?
- **Why it matters:** От этого зависит, пишем один транспорт или каталог модулей, или синк в ELMS.
- **Recommended / Suggested:** A — универсальный вызов любого метода и команда `scope`, чтобы видеть права вебхука и ответы методов.
- **Options:** A универсальный REST-вызов + просмотр scope | B отдельные обёртки по модулям (CRM, задачи, пользователи, диск, календарь) | C выгрузка сущностей Битрикс в DocType ELMS
- **Answer:** A
- **resolution:** resolved
- **round:** 1

### Q2
- **Question:** Какой вебхук кладём в настройки?
- **Why it matters:** Вебхук доски уже живёт в `BITRIX_WEBHOOK_URL`. Широкие права интеграций на том же секрете смешивают канбан и доступ к порталу.
- **Recommended / Suggested:** A — новый входящий вебхук и отдельная переменная настроек. Доску не трогаем.
- **Options:** A новая настройка только для этих скриптов | B тот же `BITRIX_WEBHOOK_URL`, что у доски | C не вебхук, а локальное OAuth-приложение
- **Answer:** A
- **resolution:** resolved
- **round:** 1

---

## Deferred / [НУЖНО УТОЧНИТЬ] items

| Item | Severity | Why deferred | Next |
|------|----------|--------------|------|
| Политика записи | IMPORTANT | Закрыто следствием Q1 = A: один entrypoint, имя метода не фильтруется | resolved |
| Список scope в инструкции | IMPORTANT | Не enum в коде. Инструкция объясняет галочки; `scope` показывает выданное | resolved |

Открытых CRITICAL нет.

---

## Completion Report

- **Grill:** done · verdict=needs_user_Q · rounds=1 · grill_Q=2 · mode=frontier
- **Asked:** 2/20
- **Resolved:** Q1 = A универсальный вызов + scope; Q2 = A отдельная настройка вебхука
- **Deferred:** нет
- **Coverage:** scope=Clear · data=Clear · UX-API=Clear · NFR=Clear · integrations=Clear · edge=Clear · constraints=Clear · terminology=Clear · design_pack=n/a
- **Next action:** Phase 1 `BACK PLAN` в этой сессии
