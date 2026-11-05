# [T-A02 | elms-learning-core-flows] PLAN

**Дата:** 2026-11-05  
**Режим:** APP PLAN  
**Уровень:** L1  
**Статус:** planned  
**Prompt:** [md/prompt.md](prompt.md)  
**Queue:** `memory-bank/app/roadmap/queue.yaml` → `T-A02` / `T-A02-elms-learning-core-flows`  
**Batch:** `elms-learning-core`  
**Deps:** `T-B02-elms-roles-rbac`, `T-F01-elms-desk-sections-roles`  
**Related:** `memory-bank/product/lms-best-practices.md`, `memory-bank/product/modules.md`  
**SUSPENSION GUARD:** active — plan output unlimited (§0.0)

---

## Решение

Внедряем базовый учебный контур (Core Learning Flows) приложения `elms` на базе чистого Frappe Framework v15 без установки сторонних монолитов (ERPNext/vendor LMS). Контур объединяет лучшие практики современных систем дистанционного обучения (когортные потоки, корпоративные подписки, трекинг фактического времени освоения) с жесткими требованиями законодательства РФ (152-ФЗ, ФИС ФРДО, Постановление Правительства № 2464 по охране труда, Приказ Минобрнауки № 816, Реестр отечественного ПО Минцифры № 1236).

Архитектурный срез охватывает:
1. **Доменные сущности (DocTypes) в модуле `LMS`:**
   - `ELMS Batch` — Поток обучения / учебная группа с привязкой к датам, куратору и приказу.
   - `ELMS Subscription` — Корпоративная подписка / договорная квота мест для B2B клиентов.
   - `ELMS Enrollment` — Зачисление слушателя на курс / в поток.
   - `ELMS Course Progress` — Сводный прогресс по курсу, статус контрольных рубежей и допуск к экзамену.
   - `ELMS Lesson Progress` — Детальный прогресс по каждому уроку с учетом затраченного времени.
   - `ELMS User Activity` — Журнал телеметрии сессий (входы, сдача заданий, античит-события).
   - `ELMS Video Watch Log` — Журнал подтвержденного просмотра видео с защитой от ускоренной перемотки.
2. **Рабочее пространство Workspace «LMS» в Desk:**
   - Обновление `elms/desk/workspaces.py` с разбивкой на карточки «Управление обучением», «Успеваемость и прогресс», «Аттестация и документы».
3. **Whitelist API и сервисный уровень:**
   - Зачисление слушателя с валидацией квоты подписки.
   - Фиксация прогресса и контрольных импульсов (heartbeat) активности.
   - Расчет прогресса и автоматическое открытие допуска к аттестации.
4. **Ролевой доступ и Fail-Closed безопасность:**
   - Изоляция данных на уровне DocPerm (слушатель видит только свои записи, представитель заказчика — только своих сотрудников).

---

## Context consumed

| Path | Что вошло в решение |
|---|---|
| `memory-bank/product/modules.md` | Канонический реестр модулей, ролей и зарегистрированных DocTypes контура LMS |
| `memory-bank/product/lms-best-practices.md` | Сравнительный анализ мировых практик LMS и адаптация к требованиям регуляторов РФ |
| `memory-bank/compliance/fis-frdo-export.md` | Требования Рособрнадзора к полям документов (ДПО 40 колонок, ПО 35 колонок, СНИЛС) |
| `memory-bank/compliance/ot-exam-attempts.md` | Требования Минтруда (ПП № 2464): разделение тренировок и экзаменов, пересдача 30 дней |
| `memory-bank/compliance/152-fz-privacy.md` | Требования Роскомнадзора: базы в РФ, изоляция ПДн, разделение вечных реестров и телеметрии |
| `memory-bank/compliance/reestr-po-certification.md` | Требования Минцифры РФ № 1236: автономность, отказ от зарубежных CDN/шрифтов |
| `docs/vendor/learning/` | Зеркало официальной документации Frappe Learning (LMS): паттерны batches, progress, courses |
| `docs/vendor/frappe-marketplace-free/` | Выжимка по 289 бесплатным приложениям сообщества Frappe |
| `elms/elms/desk/workspaces.py` | Текущая конфигурация Workspace «LMS» — точка расширения навигации Desk |
| `rules/elms-approach.mdc` | HARD канон: пишем своё в `elms`, vendor apps не форкаем, ERP/CRM только framework-паттерны |
| `rules/elms-design.mdc` | Визуальный канон: служебный светлый UI neftegaz-ai-layer + учебные паттерны LMS |

---

## Product outcome (WHAT)

Администратор учебного центра, куратор и слушатель получают целостный и юридически легитимный процесс дистанционного обучения в интерфейсе Desk:
- Администратор/методист создает потоки обучения (`ELMS Batch`), привязывает корпоративные договоры и квоты мест (`ELMS Subscription`).
- Слушатели зачисляются в потоки (`ELMS Enrollment`) вручную или по заявке предприятия; система автоматически списывает свободные места квоты.
- При изучении материалов уроков клиентский трекер регулярно отправляет контрольные сигналы активности (`heartbeat`), фиксируя реальное время освоения (согласно Приказу Минобрнауки № 816).
- Прогресс рассчитывается автоматически (`ELMS Course Progress`); после успешного прохождения всех обязательных рубежей слушатель получает допуск к итоговой аттестации (`exam_eligible=1`).
- Все действия протоколируются в соответствии со 152-ФЗ, а собранные метаданные подготавливаются для последующей выгрузки в ФИС ФРДО и ЕИСОТ Минтруда РФ.

---

## Delivery closure

| Capability / outcome | Classification | Production entrypoint and caller | Success enforcement | Failure enforcement | Independent outcome test |
|---|---|---|---|---|---|
| LMS DocTypes Registration | `vertical_slice` | Frappe bench migrate / `after_install` | Все 7 DocTypes установлены, имеют корректный JSON schema и валидные DocPerm | Синтаксическая ошибка или невалидный DocPerm прерывает миграцию | Автотест проверяет наличие DocTypes в базе данных и их поля |
| Desk Workspace LMS Updates | `vertical_slice` | Frappe Desk `/app/lms` → `workspaces.py` | В Desk отображаются новые карточки: Управление обучением, Успеваемость, Документы | Отсутствие DocType в схеме вызывает явную ошибку | Тест runtime workspace проверяет состав ссылок и карточек |
| Enrollment & Subscription Quota | `vertical_slice` | `elms.lms.api.enroll_learner` | Зачисление создано, статус `Active`, квота подписки уменьшена на 1, `Course Progress` инициализирован | Превышение квоты (`seats_used >= total_seats`) вызывает `frappe.ValidationError` | Тест зачисления проверяет блокировку при исчерпании лимита мест |
| Time-on-Task & Activity Telemetry | `vertical_slice` | `elms.lms.api.record_lesson_progress` | Прогресс урока обновлен, секунды добавлены, лог активности записан | Отрицательное время или неподтвержденный просмотр отклоняются | Тест фиксирует корректное накопление секунд изучения |
| Course Progress & Exam Eligibility | `vertical_slice` | `elms.lms.api.calculate_course_progress` | Процент пересчитан; при 100% обязательных рубежей выставляется `exam_eligible=1` | Несданный обязательный рубеж блокирует допуск (`exam_eligible=0`) | Тест рубежного контроля проверяет блокировку допуска |
| Role Isolation & DocPerm | `vertical_slice` | Frappe Permission Engine | Слушатель читает только свои зачисления; Гость получает PermissionError 403 | Попытка чтения чужих данных возвращает пустой список или 403 | Тест ролевой изоляции под учетной записью слушателя |

---

## User stories

| ID | Story | Priority | Independent Test |
|---|---|---:|---|
| US-LMS-001 | Как администратор ЦДО, я могу создать учебный поток (`ELMS Batch`) с указанием дат, куратора и номера приказа. | P0 | Создание документа `ELMS Batch` через API или Desk с валидацией обязательных полей |
| US-LMS-002 | Как менеджер корпоративных программ, я могу завести подписку компании (`ELMS Subscription`) с лимитом мест. | P0 | Создание подписки, зачисление N сотрудников, проверка счетчика `seats_used` |
| US-LMS-003 | Как администратор, я не могу зачислить слушателя сверх оплаченной квоты подписки. | P0 | Попытка зачисления N+1 слушателя вызывает отказ с понятным сообщением об исчерпании мест |
| US-LMS-004 | Как слушатель, войдя в Desk, я вижу только свои зачисления и программы в Workspace LMS. | P0 | Вход под ролью `ELMS LMS User`, запрос списка `ELMS Enrollment` возвращает только свои записи |
| US-LMS-005 | Как слушатель, при изучении урока моё фактическое время фиксируется в системе. | P0 | Вызов `record_lesson_progress` обновляет затраченные секунды и статус освоения |
| US-LMS-006 | Как методист, я вижу, что допуск к экзамену открывается только при прохождении всех обязательных материалов курса. | P0 | Допуск `exam_eligible` становится `1` строго после завершения 100% обязательных уроков |
| US-LMS-007 | Как специалист по ИБ, я вижу, что действия слушателей и сетевые параметры логируются согласно 152-ФЗ. | P1 | Каждое ключевое событие порождает запись в `ELMS User Activity` с IP и временной меткой |

---

## Functional requirements

### FR-001 — Domain Schema & DocTypes (Module LMS)
1. **ELMS Batch (Поток / Группа):**
   - `batch_name` (Data, Mandatory)
   - `course` (Link `ELMS Course` или Data, Mandatory)
   - `start_date` (Date, Mandatory)
   - `end_date` (Date, Mandatory)
   - `instructor` (Link `User`)
   - `organization` (Data / B2B клиент)
   - `order_number` (Data — приказ о зачислении)
   - `status` (Select: `Planning`, `Active`, `Completed`, `Cancelled`)
2. **ELMS Subscription (Корпоративная подписка / Квота):**
   - `company_name` (Data, Mandatory)
   - `inn` (Data, 10 или 12 цифр)
   - `contract_number` (Data)
   - `total_seats` (Int, Mandatory)
   - `seats_used` (Int, Read-only, default 0)
   - `valid_from` (Date), `valid_to` (Date)
   - `status` (Select: `Active`, `Expired`, `Exhausted`)
3. **ELMS Enrollment (Зачисление слушателя):**
   - `user` (Link `User`, Mandatory)
   - `batch` (Link `ELMS Batch`, Mandatory)
   - `subscription` (Link `ELMS Subscription`, Optional)
   - `enrollment_date` (Date, default Today)
   - `status` (Select: `Active`, `Completed`, `Suspended`, `Cancelled`)
4. **ELMS Course Progress (Сводный прогресс курса):**
   - `enrollment` (Link `ELMS Enrollment`, Unique, Mandatory)
   - `user` (Link `User`, Read-only)
   - `progress_percentage` (Percent, default 0)
   - `total_lessons` (Int, default 0)
   - `completed_lessons` (Int, default 0)
   - `total_time_spent_seconds` (Int, default 0)
   - `exam_eligible` (Check, default 0)
   - `completion_date` (Datetime)
5. **ELMS Lesson Progress (Прогресс урока):**
   - `course_progress` (Link `ELMS Course Progress`, Mandatory)
   - `lesson_id` (Data, Mandatory)
   - `is_completed` (Check, default 0)
   - `time_spent_seconds` (Int, default 0)
   - `last_heartbeat_at` (Datetime)
6. **ELMS User Activity (Лог телеметрии):**
   - `user` (Link `User`, Mandatory)
   - `activity_type` (Select: `Login`, `Lesson View`, `Quiz Submit`, `Heartbeat`, `Tab Blur`)
   - `reference_doctype` (Data), `reference_name` (Data)
   - `ip_address` (Data)
   - `timestamp` (Datetime, default Now)
7. **ELMS Video Watch Log (Лог просмотра видео):**
   - `user` (Link `User`, Mandatory)
   - `lesson_id` (Data, Mandatory)
   - `watched_seconds` (Int, default 0)
   - `playback_speed` (Float, default 1.0)
   - `verified` (Check, default 1)

### FR-002 — Whitelist API Endpoints
- **`elms.lms.api.enroll_learner(user, batch, subscription=None)`**:
  - Валидирует наличие свободных мест при указании `subscription`.
  - Создает `ELMS Enrollment`.
  - Увеличивает `seats_used` в подписке.
  - Инициализирует `ELMS Course Progress`.
- **`elms.lms.api.record_lesson_progress(enrollment, lesson_id, time_spent_delta=0, mark_completed=False)`**:
  - Обновляет или создает запись в `ELMS Lesson Progress`.
  - Добавляет время в секундах, валидируя максимальный шаг (не более 300 сек за один heartbeat).
  - При `mark_completed=True` выставляет статус освоения.
  - Триггерит пересчет сводного прогресса курса.
- **`elms.lms.api.calculate_course_progress(course_progress_name)`**:
  - Считает процент завершенных обязательных уроков.
  - При 100% освоения ставит `exam_eligible = 1`.
  - Записывает обновленные значения в базу.
- **`elms.lms.api.get_learner_dashboard()`**:
  - Возвращает список активных курсов, процентов завершения и недавнюю активность текущего сессионного пользователя.

### FR-003 — Workspace Navigation Update
- Обновить `elms/elms/desk/workspaces.py`:
  - Расширить определение `ELMS_WORKSPACE_DEFINITIONS` для секции `LMS`:
    - Карточка «Управление обучением»: ссылки на `ELMS Batch`, `ELMS Subscription`, `ELMS Enrollment`.
    - Карточка «Успеваемость и активность»: ссылки на `ELMS Course Progress`, `ELMS User Activity`.
    - Карточка «Аттестация»: ссылки на `ELMS LMS Section`.

---

## Contract & API Specifications

### 1. `POST /api/method/elms.lms.api.enroll_learner`
- **Input:**
  ```json
  {
    "user": "student@example.ru",
    "batch": "BATCH-2026-001",
    "subscription": "SUB-GAZPROM-01"
  }
  ```
- **Output Success (200):**
  ```json
  {
    "message": {
      "enrollment": "ENR-2026-0001",
      "status": "Active",
      "course_progress": "PROG-2026-0001"
    }
  }
  ```
- **Typed Errors:**
  - `ValidationError`: «Лимит мест по корпоративной подписке SUB-GAZPROM-01 исчерпан (10/10)»
  - `DoesNotExistError`: «Учебный поток не найден»
  - `PermissionError`: «Недостаточно прав для зачисления слушателя»

### 2. `POST /api/method/elms.lms.api.record_lesson_progress`
- **Input:**
  ```json
  {
    "enrollment": "ENR-2026-0001",
    "lesson_id": "lesson-ot-intro-01",
    "time_spent_delta": 60,
    "mark_completed": true
  }
  ```
- **Output Success (200):**
  ```json
  {
    "message": {
      "lesson_id": "lesson-ot-intro-01",
      "is_completed": 1,
      "total_time_spent_seconds": 180,
      "course_progress_percentage": 25.0,
      "exam_eligible": 0
    }
  }
  ```

---

## Ownership Matrix (Mixed vertical slice)

| Lane | Component / Artifact | Owner / Responsibility |
|---|---|---|
| **Backend Lane** | DocTypes JSON & Python controllers (`elms/elms/lms/doctype/*`) | Создание схем данных, хуков валидации, расчетных триггеров |
| **Backend Lane** | Whitelist API (`elms/elms/lms/api.py`) | Реализация безопасных эндпоинтов зачисления, трекинга и прогресса |
| **Frontend/Desk Lane** | Workspace Desk definition (`elms/elms/desk/workspaces.py`) | Навигационные карточки, шорткаты и права в панели Desk |
| **Frontend/Desk Lane** | Scoped UI & List Views | Настройка читаемых списков зачислений и индикаторов прогресса (CSS/JS) |
| **Compliance Lane** | Нормативная валидация | Проверка соответствия 152-ФЗ, 816 приказу, 2464 ПП РФ и ФИС ФРДО |
| **QA Lane** | Test Suite (`elms/elms/tests/test_lms_*.py`) | 100% покрытие сценариев зачисления, превышения квот, трекинга и изоляции прав |

---

## Test & QA Charter

1. **Test DocTypes & Schema Integrity:**
   - Проверка успешной миграции и создания таблиц в MariaDB.
   - Проверка значений по умолчанию и валидаторов.
2. **Test Subscriptions & Quota Guard:**
   - Создание подписки на 2 места.
   - Успешное зачисление 2 слушателей.
   - Проверка, что 3-е зачисление блокируется с понятным `frappe.ValidationError`.
3. **Test Time Telemetry & Heartbeat:**
   - Отправка корректных дельт времени.
   - Отклонение подозрительных интервалов (более 300 секунд за один вызов).
   - Фиксация записей в `ELMS User Activity`.
4. **Test Course Progress & Exam Eligibility:**
   - Добавление уроков.
   - Пошаговое закрытие уроков.
   - Проверка, что `exam_eligible` становится `1` только при 100% завершении плана.
5. **Test Fail-Closed Security & DocPerm:**
   - Попытка гостя вызвать методы API -> 403 Forbidden.
   - Слушатель может просматривать только свой прогресс.

