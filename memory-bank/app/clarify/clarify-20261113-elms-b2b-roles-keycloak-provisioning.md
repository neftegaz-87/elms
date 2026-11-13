# clarify — elms-b2b-roles-keycloak-provisioning

**plan_id:** T-A07 (proposed)  
**slug:** elms-b2b-roles-keycloak-provisioning  
**role:** app  
**date:** 2026-11-13  
**feature_description:** Смена ролевой модели B2B (учебный центр → компании → сотрудники), отказ от Yandex SSO (Keycloak-only), выдача аккаунтов из ELMS с синхронизацией в Keycloak для входа.  
**status:** in_progress

---

## Контекст и цель

- Вход чата: ролевая модель (мы админим компании, компании — сотрудников); Yandex снимаем; остаёмся на Keycloak; аккаунты выдаются из ELMS и сразу синхронизируются в Keycloak.
- As-built: Frappe → Keycloak Social Login; Yandex как brokered IdP; JIT User при первом входе; роли `ELMS Admin` / Operations / Learner / Instructor / Methodologist; `organization` на Batch — строка, отдельного DocType организации нет; `reconcile_keycloak_user` = KC→Frappe на callback, не провижининг Frappe→KC.
- Цель Phase 0: снять ambiguity до APP PLAN Phase 1 (контракт invite/provision, tenant scope, sunset Yandex).
- Архитектурный канон интеграций: `memory-bank/architecture/integrations.md` (ELMS = учёт/ДО; Keycloak без Yandex).
- Round 1 (2026-11-13): нужен **B2B (Q1=B) и B2C** — формы заявок юрлиц (сотрудничество по курсам) и физлиц (запись на курс); invite=email set-password; Yandex sunset+миграция (Q4=C); кабинет компании с прогрессом/отчётами (Q5=B); Q3 — нужна расшифровка квоты перед выбором.

---

## Grill pass (Phase 0 — mandatory)

| Поле | Значение |
|------|----------|
| **Reframe** | Учебный центр из ELMS выдаёт компаниям и людям доступ так, что пользователь сразу может войти через Keycloak; Yandex уходит; изоляция данных компании — часть той же модели. |
| **Premises** | (1) Keycloak — единственный IdP — `accepted` (чат). (2) Нужна роль представителя компании — `accepted` (чат). (3) Создание User в ELMS без записи в Keycloak = нельзя войти — `accepted`. (4) Org-scope обязателен, иначе Company Admin видит чужих — `accepted`. (5) Wedge = invite+sync+роль+Yandex purge, без полного B2B-портала аналитики — `challenged` до Q. |
| **Weakest link** | Провижининг ELMS→Keycloak без идемпотентности/отката оставит «User в Frappe есть, войти нельзя» или дубликаты `sub`/email. |
| **Anti-scope (черновик)** | Корпоративный SSO заказчика; Bitrix→Минтруд; ОНАТО/ФРДО; миграция Прометея; полный кабинет аналитики компании; смена пароля коллеги без Keycloak account lifecycle. |
| **Verdict** | `needs_user_Q` |
| **Design tree (sketch)** | Who invites → Credential delivery → Org entity/scope → Yandex sunset & legacy users → Wedge vs portal UI → Fail/retry sync |

---

## Product probe (черновик до ответов)

- **Demand reality:** B2B-школа; админ учебного центра и кадровик компании должны заводить людей без раздачи паролей «в мессенджер» и без Yandex.
- **Status quo:** вход через Keycloak(+Yandex); пользователи появляются JIT при первом SSO; массовой выдачи из ELMS в Keycloak нет; org — строка на Batch.
- **Desperate specificity:** человек заведён «где-то», но не может войти, пока вручную не создадут учётку в Keycloak / не зайдут через Yandex.
- **Narrowest wedge (гипотеза):** ELMS Admin (+ опционально Company Admin) создаёт/приглашает User → sync в Keycloak → email set-password → вход Keycloak→Frappe с ролью и org User Permission.
- **Observation:** as-built reconcile идёт KC→Frappe; нужен обратный sole path provision.
- **Future-fit:** позже IdP компании в Keycloak не должен ломать модель invite/org.

---

## Таксономия сканирования

| Категория | Status | Notes |
|-----------|--------|-------|
| scope | Partial | Роли и Keycloak-only ясны; граница Company Admin / wedge UI — нет |
| data | Partial | Нужен ли DocType Organization; ключ личности (email); lifecycle disabled |
| UX-API | Missing | Desk form invite vs whitelist API; что видит Company Admin |
| NFR | Partial | Идемпотентность sync, секреты Keycloak Admin API, audit |
| integrations | Partial | Keycloak Admin API; Yandex purge; не Bitrix в этом эпике? |
| edge | Missing | Sync fail mid-way; повторный invite; email уже в KC |
| constraints | Clear | Keycloak-only; fail-closed; Frappe не хранит продуктовые пароли слушателей |
| terminology | Partial | `ELMS Company Admin` vs «кадровик»; Organization |
| design_skills | Clear | Desk product_ui (формы Desk / Workspace), не marketing landing |

---

## Design skills pack

```yaml
surface: product_ui
dialect: none
image_pack: []
groups: [D0]
pin_v1: false
resolved_paths:
  - .agents/skills/frontend-design/SKILL.md
status: draft
note: "Desk Form/Workspace для выдачи аккаунтов и org-scope; login остаётся stock Frappe+/login + Keycloak."
```

---

## Frontier rounds

### Round 1 — 2026-11-13 — answered

| Q | Answer |
|---|--------|
| Q1 | **B** + расширение: нужен также **B2C** — формы заявлений юрлиц (сотрудничество по курсам) и физлиц (прохождение курса) |
| Q2 | **A** — invite email, ссылка задать пароль в Keycloak |
| Q3 | **не выбран** — запрошено пояснение «Organization + Subscription/квота» |
| Q4 | **C** — purge Yandex + миграция существующих Yandex-пользователей на локальный пароль Keycloak |
| Q5 | **B** — роли/org/invite/Yandex sunset **и** кабинет компании (прогресс сотрудников, отчёты) |

### Round 2 — 2026-11-13 — answered

| Q | Answer |
|---|--------|
| Q3 / Q6 | **Без договорного лимита** → **Q6=A**: `ELMS Organization` + User Permission; квоту Subscription при invite **не** проверяем |
| Q7 | **B → пересмотрен в Round 3:** см. Q10 (формы в ELMS + sync Bitrix) |
| Q8 | **A**: три APP-эпика |
| Q9 | **A**: кабинет = список сотрудников + статус зачисления + % прогресса + простой отчёт |

### Round 3 — 2026-11-13

| Q | Answer |
|---|--------|
| Q10 | Владелец уточнил: **формы делаем в ELMS**, связываем с Bitrix, синхронизация **хуками**. Это отменяет «ELMS не владеет заявкой» (старый Q7=B). |
| Q11 | **B**: SoT статуса заявки = **Bitrix**; форма ELMS создаёт лид и читает статус обратно |

---

## Q→A log

| ID | Decision |
|----|----------|
| Q1 | B2B: Admin → Company Admin → сотрудники своей org. Нужны заявления физлиц (курс) и юрлиц (сотрудничество по курсам). |
| Q2 | Invite-only: email → Keycloak set-password; пароль не светить в Desk. |
| Q3/Q6 | Organization + User Permission; **без** договорного лимита Subscription на invite. |
| Q4 | Yandex IdP purge + миграция существующих Yandex-пользователей на локальный Keycloak credential. |
| Q5/Q9 | Кабинет компании: сотрудники, статусы зачисления, % прогресса, простой отчёт. |
| Q7/Q10 | Формы заявок **в ELMS** + синхронизация с Bitrix хуками. |
| Q8 | Три APP-эпика: (1) доступ/Keycloak/org/invite; (2) формы + Bitrix; (3) кабинет компании. |
| Q11 | **Bitrix = SoT статуса** заявки; ELMS form создаёт лид и отображает/подтягивает статус из Bitrix. |

---

## Glossary

**`ELMS Organization`** — карточка компании-заказчика (ИНН/ОГРН, название) для изоляции и Company Admin.

**`ELMS Subscription` (квота)** — договорной лимит мест; в срезе доступа на invite **не** используем.

**Заявка** — UI/запись-ссылка в ELMS + сущность лида/сделки в **Bitrix (SoT статуса)**. ELMS не объявляет локальный статус главнее Bitrix.

---

## Epic cut (locked)

| Epic | Outcome |
|------|---------|
| T-A07-elms-b2b-org-keycloak-provisioning | Keycloak-only, Yandex sunset+migrate, Organization, Company Admin, invite→Keycloak sync |
| T-A08-elms-application-forms-bitrix-status | Формы физ/юр в ELMS → create lead Bitrix; status SoT Bitrix; read-back в ELMS |
| T-A09-elms-company-admin-cabinet | Кабинет: сотрудники, зачисления, % прогресса, простой отчёт |

**deps:** T-A09 depends T-A07; T-A08 depends T-A07 (org/invite path after CRM approve is operational handoff).

---

## Completion Report

**status:** done  
**Grill:** Round 1–3 complete; Q1–Q11 resolved  
**design_pack:** Desk product_ui / D0 (кабинет+invite); web forms for applications  
**CRITICAL open:** none (Bitrix stage field mapping — PLAN detail, not blocker)  
**Ready for Phase 1:** yes  
**Next:** APP PLAN Phase 1 multi-epic T-A07 → T-A08 → T-A09
