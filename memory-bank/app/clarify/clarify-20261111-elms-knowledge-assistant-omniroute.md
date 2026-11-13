# clarify — elms-knowledge-assistant-omniroute

**plan_id:** T-A06  
**slug:** elms-knowledge-assistant-omniroute  
**role:** app  
**date:** 2026-11-11  
**feature_description:** Grounded Desk-ассистент по as-built ELMS через OmniRoute + отдельное окно настроек интеграций (Single DocType), entry у «Поиск по связям».  
**status:** done

---

## Контекст и цель

- Вход: doc-chat без RAG; OmniRoute как у Codex; CRM-паттерн Settings Single; ELMS сейчас имеет только RBAC-якорь `ELMS Settings Section` и скрытый platform Workspace `Integrations`.
- Цель Phase 0: снять ambiguity до APP PLAN Phase 1.
- Ограничения: реестр ПО — LLM optional/fail-closed; секрет не в браузер.

---

## Grill pass (Phase 0 — mandatory)

| Поле | Значение |
|------|----------|
| **Reframe** | Desk staff получает grounded ответы по API/DocType ELMS через OmniRoute; админ включает интеграцию в отдельном окне настроек, как Settings Single в CRM/ERP. |
| **Premises** | Все Q1–Q10 resolved ниже · `accepted`. |
| **Weakest link** | Утечка API key в UI/логи или dual-path config (site_config + DocType). |
| **Anti-scope** | Floating FAB; Learner; RAG; Chat DocType; OmniRoute hard-dep prod; OpenAPI primary SoT; platform Frappe Integrations workspace как SoT. |
| **Verdict** | `auto_resolved` после Round 3 |
| **Design tree** | Persona✓ Surface✓ Registry✓ Corpus✓ Config SoT✓ Model✓ History✓ Settings window✓ Fields✓ RBAC✓ |

---

## Product probe

- **Demand reality:** нет FastAPI docs; нужны чат + окно интеграций.
- **Status quo:** ручное чтение кода; ключ OmniRoute только у Codex; в ELMS Settings нет формы интеграций.
- **Narrowest wedge:** relationship-search entry + chat panel + `get_models`/`ask` + Single `ELMS Integration Settings` в Settings Workspace.
- **Recommended wedge:** тот же.

---

## Таксономия сканирования

| Категория | Status | Notes |
|-----------|--------|-------|
| scope | Clear | Desk staff; optional LLM; relationship-search entry |
| data | Clear | Corpus A; Integration Settings Single; no Chat DocType |
| UX-API | Clear | Chat panel + Settings Form window |
| NFR | Clear | Fail-closed; ephemeral history; Password field server-side |
| integrations | Clear | OmniRoute via Integration Settings Single |
| edge | Clear | disabled/missing/down/unknown model → explicit error |
| constraints | Clear | Optional + reestr |
| terminology | Clear | — |
| design_skills | Clear | Desk product_ui / D0 |

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
  - .agents/skills/impeccable/SKILL.md
  - .agents/skills/emil-design-eng/SKILL.md
status: locked
note: "Entry в .elms-relationship-search-controls; Settings → ELMS Integration Settings Form."
```

---

## Frontier rounds

### Round 1
- Q1 A · Q2 A+relationship search · Q3 A

### Round 2
- Q4 A · Q5 A (server-side; SoT уточнён Round 3 как Single DocType Form) · Q6 B · Q7 A
- Addendum: нужны настройки интеграций

### Round 3
- Q8 A · Q9 A · Q10 A
- Addendum: отдельное окно как в CRM/ERP; в ELMS такого нет — должно появиться

---

## Q→A log

### Q1–Q3
- A / A+search controls / A · resolved · round 1

### Q4
- A DocType JSON + whitelist + REST cheat · resolved · round 2

### Q5
- A server-side secrets · resolved · round 2
- **Chat lock:** runtime SoT = Single `ELMS Integration Settings` (Password), не dual-path site_config fallback

### Q6
- B get_models + picker, default `cx/gpt-5.6-luna-high` · resolved · round 2

### Q7
- A sessionStorage + bounded history · resolved · round 2

### Q8
- A новый Single `ELMS Integration Settings` · resolved · round 3

### Q9
- A enabled + base_url + api_key Password + default_model · resolved · round 3

### Q10
- A write: ELMS Admin + System Manager; chat для Desk staff без секретов · resolved · round 3

---

## Deferred / [НУЖНО УТОЧНИТЬ] items

| Item | Severity | Why deferred | Next |
|------|----------|--------------|------|
| — | — | none | — |

---

## Completion Report

- **Grill:** done · verdict=auto_resolved · rounds=3 · grill_Q=10 · mode=frontier · design_pack=product_ui/D0
- **Asked:** 10/20
- **Resolved:** persona; entry; registry; corpus; server secrets via Integration Settings Single; model picker; history; settings window/fields/RBAC
- **Deferred:** none
- **Coverage:** scope=Clear · data=Clear · UX-API=Clear · NFR=Clear · integrations=Clear · edge=Clear · constraints=Clear · terminology=Clear · design_pack=Clear
- **Next action:** `APP PLAN` Phase 1 → `T-A06-elms-knowledge-assistant-omniroute`
