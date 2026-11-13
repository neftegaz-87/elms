# clarify — offline-registry-bundle

**plan_id:** T-B10-elms-offline-registry-bundle (pending Phase 1)
**slug:** offline-registry-bundle
**role:** back
**date:** 2026-11-11
**feature_description:** Офлайн-поставка ELMS (image-only бандл + install без интернета + air-gap gate + SBOM) как слой delivery поверх T-B05/T-B08 для соответствия требованиям Реестра отечественного ПО (air-gapped runtime, без pull/CDN/PyPI на площадке).
**status:** done

---

## Контекст и цель

- Вход: `BACK PLAN` — offline registry bundle после обсуждения рисков реестра Минцифры и модели поставки (не один monolith-контейнер, а бандл pin'нутых образов).
- Цель Phase 0: снять ambiguity по составу продукта vs среды, секретам air-gap и глубине OS/реестрового пакета до Phase 1 plan.
- Факты из репозитория (не спрашиваем):
  - Канон prod: `docker/compose.prod.yaml` image-only; `pull_policy` по умолчанию `always`; build/staged/edge — overlays.
  - Delivery-линейка: T-B05 (stack) → T-B06 (Vault) → T-B07 (backup) → T-B08 (CI digest/manifest) → T-B09 (edge).
  - Compliance: `memory-bank/compliance/reestr-po-certification.md` — air-gap, запрет CDN/зарубежных runtime-сервисов, запрет GPL/AGPL в прикладном коде, сборка у резидента РФ, отечественные ОС в разрешённом списке.
  - Frappe Framework — MIT; ERPNext/Frappe LMS в продукт не ставятся (GPL/AGPL).
  - Vault в текущем prod-графе обязателен (`ELMS_VAULT_REQUIRED=1`); лицензия Vault — отдельный риск для «состава регистрируемого ПО».

---

## Grill pass (Phase 0 — mandatory)

| Поле | Значение |
|------|----------|
| **Reframe** | Нужен не «один Docker со всем миром» и не вся заявка в Минцифры целиком, а **доказуемая офлайн-поставка** ELMS: immutable app/keycloak images + pin'нутые runtime images в бандле, install без сети, gate без egress, SBOM/лицензии и явная граница «продукт vs среда». |
| **Premises** | 1. Epic = delivery/compliance packaging поверх существующего image-only compose, не новый LMS-домен. Статус: `accepted`. 2. Один monolith-контейнер — anti-pattern; бандл нескольких digest-образов. Статус: `accepted`. 3. Vault **вне** состава регистрируемого ПО / offline-бандла продукта (Q2=A). Статус: `accepted`. 4. Успех эпика = техническая air-gap способность + SBOM, не юридическая подача в Минцифры (Q1=A). Статус: `accepted`. 5. Air-gap proof на Ubuntu LTS/Debian host; Astra/РЕД — follow-up (Q3=A). Статус: `accepted`. 6. База образов — Debian/Ubuntu-семейство, не RHEL-клон. Статус: `accepted`. |
| **Weakest link** | Смешать online Vault-prod и offline file-secrets в один silent fallback — запрещено; только явный профиль. |
| **Anti-scope** | Не APP LMS/UI; не подача заявления в Минцифры; не протокол Astra/РЕД; не РФ-зеркало исходников; не замена Frappe/Прометей; не all-in-one; не замена Vault движком; не rewrite всего CI. |
| **Verdict** | `auto_resolved` после Round 2 (Q4=A, Q5=A) |
| **Design tree (sketch)** | 1) Outcome=A ✓ 2) Vault out ✓ 3) Host OS=A ✓ 4) Secrets model offline ← Round 2 5) Какие сервисы в первом бандле ← Round 2 6) Формат tar+install.sh (default) 7) РФ-зеркало — out (след. из Q1=A) |

---

## Product probe (office-hours lite)

| # | Вопрос | Контекст / Ответ |
|---|--------|------------------|
| 1 | **Demand reality** | Запрос из сессии: риски не войти в реестр → нужен air-gapped дистрибутив. Регуляторный канон уже в `reestr-po-certification.md`. |
| 2 | **Status quo** | Prod deploy тянет images (`pull_policy: always`) из registry; офлайн-бандла/`docker save` комплекта нет. |
| 3 | **Desperate specificity** | На площадке без интернета нельзя воспроизвести поставку; экспертиза может отказать за runtime-зависимости. |
| 4 | **Narrowest wedge** | Offline bundle (images.tar + compose overlay `pull_policy: never` + install.sh) + air-gap CI/local gate + SBOM + граница Vault. |
| 5 | **Observation & surprise** | `BITRIX_STAGE_UAT` и blocked совпадают по id — не относится к эпику. Vault license ≠ классический OSS — относится. |
| 6 | **Future-fit** | Полная заявка в реестр (правообладатель, Astra-протокол, юристы) может сделать «только бандл» недостаточным — поэтому нужен Q про primary outcome. |

- **Recommended wedge:** runtime offline bundle + air-gap proof + SBOM; юридическую подачу и полную ОС-сертификацию — явно in/out по ответам Q.

---

## Таксономия сканирования

| Категория | Status | Notes |
|-----------|--------|-------|
| scope | Clear | Q1=A: tech air-gap+SBOM; legal filing / Astra out |
| data | Clear | Нет новых доменных DocType; артефакты бандла/SBOM/manifest |
| UX-API | Clear | CLI/install.sh operator surface, не Desk UI |
| NFR | Clear | Air-gap; offline secrets profile (Q4=A); digests; SBOM |
| integrations | Clear | Vault out; full prod graph minus vault/vault-agent (Q5=A) |
| edge | Clear | Нет сети / битый tar / digest mismatch / missing secrets file → fail-closed (plan BN) |
| constraints | Clear | Ubuntu/Debian host proof; RHEL FORBIDDEN; GPL/AGPL app FORBIDDEN |
| terminology | Clear | продукт ELMS = app(+keycloak custom); среда = db/redis/postgres/caddy; бандл = offline delivery; offline secrets profile ≠ Vault |
| design_skills (FRONT UI) | n/a | BACK infra |

---

## Design skills pack (FRONT — при UI-scope)

n/a

---

## Frontier rounds

### Round 1
- Q1 primary outcome → **A** · resolved
- Q2 Vault composition → **A** · resolved
- Q3 host OS proof depth → **A** · resolved

### Round 2
- Q4 offline secrets model → **A** · resolved
- Q5 first-bundle service set → **A** · resolved

---

## Q→A log

| Q | Answer | Resolution |
|---|--------|------------|
| Q1 | A — tech air-gap + SBOM; юр. подача out | accepted |
| Q2 | A — Vault вне продукта/бандла | accepted |
| Q3 | A — Ubuntu/Debian host proof; Astra/РЕД follow-up | accepted |
| Q4 | A — offline secrets profile (files); online Vault остаётся для connected prod | accepted |
| Q5 | A — полный prod-граф минус vault/vault-agent | accepted |

---

## CRITICAL / defer

| Item | Status |
|------|--------|
| РФ-зеркало исходников/сборки | **deferred** follow-up (Q1=A) · owner: back · next: registry-filing epic |
| Astra/РЕД OS protocol | **deferred** follow-up (Q3=A) · owner: back · next: OS-cert epic |
| Юридическая подача в Минцифры | **deferred** follow-up (Q1=A) · owner: legal/ops |
| Замена Vault другим движком | **deferred** (Q2=A) · owner: back |

Открытых CRITICAL blocker нет.

---

## Completion Report

- **Grill:** pass done; Verdict closed after Round 2
- **Frontier:** empty
- **Resolved:** Q1–Q5 = A/A/A/A/A
- **Deferred:** legal filing, Astra/РЕД, RF source mirror, Vault replacement
- **Ready for Phase 1:** yes
- **status:** done
- **Wedge:** offline bundle (full-minus-vault) + offline secrets profile + air-gap gate + SBOM + install.sh; format tar+compose overlay `pull_policy: never`