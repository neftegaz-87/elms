# [T-B10-elms-offline-registry-bundle] PLAN

**Дата:** 2026-11-11  
**Режим:** BACK PLAN (+ devops skills: docker-compose / docker-management)  
**Уровень:** L2  
**Статус:** ready for DECOMPOSE  
**Clarify:** `memory-bank/back/clarify/clarify-20261111-offline-registry-bundle.md`  
**Prompt:** `md/prompt.md`  
**Route recommendation:** `BACK DECOMPOSE`, затем `BACK IMPLEMENT sNN` (не TASK: multi-surface delivery + compliance gates)

---

## Context consumed

| Path | Что вошло в axiom / Deps / FR |
|------|-------------------------------|
| `memory-bank/techContext.md` | image-only `compose.prod.yaml`; overlays build/staged/edge; digests/manifest T-B08; Vault Agent как prod secrets SoT |
| `memory-bank/systemPatterns.md` | §8 Compose+Vault gate; §10 immutable CI release; fail-closed; no silent fallback |
| `memory-bank/projectbrief.md` | n/a — файла нет |
| `memory-bank/architecture/index.md` | навигация; SoT = product/techContext/systemPatterns |
| `memory-bank/product/vision.md` | свой `elms` на Frappe; vendor LMS/ERP не ставим |
| `memory-bank/product/modules.md` | DENY зарубежных CDN/шрифтов (реестр №1236) |
| `memory-bank/product/design.md` | n/a для этого эпика (нет UI-scope) |
| `memory-bank/product/lms-best-practices.md` | автономность / локальные ассеты как compliance-ориентир |
| `memory-bank/product/board-publish.md` | после PLAN — board-sync |
| `memory-bank/compliance/reestr-po-certification.md` | air-gap, запрет CDN/runtime pull, лицензии, Debian/Ubuntu base, сборка у резидента |
| `docker/compose.prod.yaml` | сервисный граф; `pull_policy: always`; Vault services; `ELMS_VAULT_REQUIRED=1` |

---

## Clarifications

Session: `clarify-20261111-offline-registry-bundle` · status `done` · Grill closed.

| Решение | Итог |
|---------|------|
| Primary outcome | Технический air-gap бандл + SBOM; юр. подача в Минцифры **out** |
| Vault | **Вне** состава продукта и offline-бандла |
| Host OS proof | Ubuntu LTS / Debian; Astra/РЕД — follow-up |
| Secrets | **Offline secrets profile** (files); online Vault остаётся для connected prod |
| Bundle services | Полный prod-граф **минус** `vault` / `vault-agent` |

Deferred: РФ-зеркало исходников, Astra/РЕД протокол, юр. подача, замена Vault движком.

---

## Product decision / WHAT

Сделать **доказуемую офлайн-поставку ELMS**: комплект pin'нутых Docker-образов + compose overlay без registry pull + явный offline secrets profile + `install.sh` + air-gap verification + SBOM/license inventory.

Это слой **delivery/compliance** поверх T-B05/T-B08, не LMS-домен и не заявка в реестр.

**Success signal:** на хосте без egress выполняется `docker load` → `compose up` полного графа без Vault → health/smoke; в evidence нет обращений к внешним registry/CDN/PyPI/npm; SBOM приложен; Vault-образы отсутствуют в бандле.

---

## PLAN review passes

| Pass | Status | Evidence |
|------|--------|----------|
| Product | done | Clarify Q1–Q5 = A; wedge = air-gap capability |
| Design | skip | Нет UI / Desk surface |
| DX | done | Operator CLI: pack/install/air-gap-check; ошибки fail-closed (нет сети, digest mismatch, нет secrets file) |
| Eng | done | Dual explicit profiles (online Vault vs offline files); overlay `pull_policy: never`; next = DECOMPOSE |

### Ownership matrix

| Surface / outcome | BACK | FRONT | Infra | QA | Contract / evidence | Rollback | Independent check |
|-------------------|------|-------|-------|-----|---------------------|----------|-------------------|
| Offline compose overlay (no Vault, never pull) | accountable | n/a | BACK | BACK | compose file + digest refs | revert overlay; online prod untouched | compose config validate + policy tests |
| Offline secrets profile (rendered files) | accountable | n/a | BACK | BACK | file paths + `ELMS_VAULT_REQUIRED` policy for profile | delete profile; prod Vault path intact | unit/contract tests fail-closed |
| Bundle pack (`docker save` + manifest) | accountable | n/a | BACK | BACK | bundle layout + checksums | discard artifact | pack dry-run + load on clean host |
| Air-gap gate | accountable | n/a | BACK | BACK | no-egress evidence JSON | n/a | scripted deny-egress rehearsal |
| SBOM / license inventory | accountable | n/a | BACK | BACK | SPDX/CycloneDX + deny GPL/AGPL in app layer | n/a | scanner gate non-zero on forbidden licenses |
| Install docs (RU) | accountable | n/a | BACK | BACK | install/admin guide | n/a | docs present in bundle; no CDN instructions |

---

## Technology axiom

1. **Два явных профиля поставки, без silent fallback:**
   - **Connected prod** (канон T-B05/T-B06/T-B08): `compose.prod.yaml` + Vault Agent + registry digests + `pull_policy` по online-политике.
   - **Offline registry bundle:** отдельный overlay/compose profile: **нет** сервисов Vault; `pull_policy: never`; секреты только из **offline secrets profile** (заранее подготовленные protected files того же контракта путей, что Agent render, но без Vault runtime).
2. Выбор профиля — **явный** (флаг/`COMPOSE_FILE`/install entrypoint). Запрещено: «Vault недоступен → тихо читаем `.env`» на connected prod.
3. App/Keycloak images **immutable** и содержат все runtime deps/assets/fonts (build-time bake). На площадке **запрещены** `pip`/`npm`/`bench get-app`/CDN.
4. Базовые OS-слои образов — Debian/Ubuntu family; RHEL-клоны FORBIDDEN в дистрибутиве.
5. Vault **не** входит в состав регистрируемого продукта и **не** кладётся в offline-бандл (clarify Q2=A).

---

## Functional requirements

- **FR-001:** Offline overlay описывает полный prod-граф минус `vault`/`vault-agent` (db, redis-*, configurator, create-site, backend, websocket, queue-*, scheduler, frontend, keycloak-db, keycloak, caddy).
- **FR-002:** Все `image:` в offline-профиле — digest-pinned; `pull_policy: never`.
- **FR-003:** Скрипт упаковки собирает `docker save` набор образов + compose + checksums + SBOM + docs в версионированный бандл.
- **FR-004:** `install.sh` (или эквивалент): `docker load` → validate digests/checksums → `compose up` offline-профиля **без** сети.
- **FR-005:** Offline secrets profile: обязательные secret files на известных путях; отсутствие файла → non-zero до promotion app; `ELMS_VAULT_REQUIRED` для offline-профиля = выкл Vault-gate, но **вкл** file-secrets gate.
- **FR-006:** Air-gap gate: контролируемый прогон с запретом egress; evidence JSON (pass/fail); обращение к внешнему registry/CDN/pypi = fail.
- **FR-007:** SBOM (SPDX или CycloneDX) для app+keycloak images и inventory runtime images; gate fail на GPL/AGPL в **прикладном** слое ELMS/Frappe app deps (MariaDB server как среда — отдельно документируется).
- **FR-008:** RU краткая инструкция развёртывания offline-бандла (админ): шаги load/up, secrets layout, проверка здоровья, явный запрет «докачать из интернета».
- **FR-009:** CI/release hook (поверх T-B08): опциональный/отдельный job или script target, который публикует offline-bundle artifact по digests релиза (не ломая online deploy path).

---

## Out of scope (этот эпик)

- Подача заявления в Реестр Минцифры / пакет правообладателя.
- Протокол совместимости Astra Linux / РЕД ОС / Альт.
- РФ-зеркало git/CI как отдельный deliverable.
- Замена Vault другим секреты-движком.
- All-in-one monolith container.
- LMS/APP функциональность, миграция с Прометея.
- Изменение online prod SoT (Vault остаётся для connected).

---

## Appetite / cut_list

**Timebox:** один L2 эпик, hint **2** implement steps (cap L2→2).

**Cut (если не влезает):**
1. Полный CI publish бандла → оставить local/script pack + ручной artifact; CI wire — follow-up.
2. Расширенный SBOM всех transitive OS packages → минимум app Python/JS + documented runtime image digests.
3. Автоматический network-namespace air-gap в CI → допустим documented local gate + scripted check с mock/deny list, если CI runner ограничен.

**Не резать:** overlay without Vault, `pull_policy: never`, offline secrets fail-closed, install load path, evidence что бандл не содержит Vault images.

---

## Target layout (files)

| Path | Role |
|------|------|
| `docker/compose.prod.offline.yaml` (имя уточнит DECOMPOSE) | overlay/profile: no vault, never pull, digest refs |
| `docker/offline/` или `ops/offline/` | secrets profile templates (non-secret), install.sh, pack.sh |
| `scripts/infra/pack_offline_bundle.py` (или `.sh`) | assemble tar + checksums |
| `scripts/infra/check_offline_airgap.py` (или `.sh`) | air-gap / no-pull / no-vault-in-bundle gates |
| `scripts/infra/check_offline_secrets_contract.py` | file-secrets contract |
| `docs/operations/elms-offline-bundle.md` | RU install guide |
| `tests/infra/test_offline_bundle_*.py` | contract tests |
| CI workflow fragment / make target | optional publish of offline artifact |
| Bundle artifact layout (generated, not in git) | `images/*.tar` или multi-save, compose, sbom, checksums, docs |

---

## Implementation slices (outline → DECOMPOSE)

**Hint s01 — Offline profile + secrets contract**  
Compose offline overlay (full-minus-vault), digest-only images, file secrets profile + fail-closed checks; unit/contract tests; DENY vault services in profile.

**Hint s02 — Pack / install / air-gap / SBOM**  
Pack script, install.sh, air-gap evidence gate, SBOM+license deny list, RU docs, wire to release digests; obsolete «must pull online» instructions for offline path purged.

---

## Replacement / sunset

### A — surfaces

| Legacy surface | Replacement | Sunset/control |
|---|---|---|
| Единственный способ поставить ELMS на площадке = `pull` из registry при наличии сети | Offline bundle load + compose offline profile | Air-gap gate FAIL если install требует pull |
| Vault images как обязательная часть «поставки ELMS» для реестрового/offline контура | Vault вне бандла; offline secrets files | Bundle inventory MUST NOT contain vault image refs |

### B — entrypoints

| Legacy entrypoint | Replacement | Sunset/control |
|---|---|---|
| `compose.prod.yaml` + `ELMS_VAULT_REQUIRED=1` как единственный install entry | Явный offline entry (`install.sh` / compose file list) | Online entry не менять; offline не вызывает Vault |
| `PULL_POLICY=always` на offline install | `pull_policy: never` в offline profile | Contract test |

### C — fallbacks

| Old fallback | Replacement | Policy |
|---|---|---|
| Vault down → читать `.env` на prod | Forbidden | Fail-closed; offline = отдельный профиль |
| Нет образа → docker pull во время offline install | Forbidden | Fail with digest/missing image error |
| Нет SBOM → «потом» | Gate non-zero / missing artifact = FAIL pack | |

### I — instructions

| Old instruction | Replacement | Sunset/control |
|---|---|---|
| «Скачайте зависимости / подтяните images при старте» для изолированного контура | Offline bundle guide | Purge CDN/pull steps from offline docs |
| «Vault обязателен в любом дистрибутиве ELMS» | Vault = connected platform; offline = file secrets | Clarify in docs |

---

## Boundary / negative cases

| ID | Case | Expected |
|----|------|----------|
| BN-001 | Offline install при запрещённом egress и отсутствии локальных images | Non-zero; no successful pull attempt required for pass path |
| BN-002 | В бандле/compose offline есть `vault` / `vault-agent` image | Pack/check FAIL |
| BN-003 | Отсутствует обязательный secrets file offline profile | Non-zero before app promotion |
| BN-004 | Digest в compose не совпадает с loaded image | Non-zero |
| BN-005 | Connected prod profile без Vault «тихо» переключён на `.env` | Forbidden; tests must catch / policy deny |
| BN-006 | SBOM/scan находит GPL/AGPL в прикладном ELMS/Frappe-app dependency set | Gate FAIL |
| BN-007 | Install docs требуют fonts.googleapis / docker hub login mid-install | Docs/contract FAIL |

---

## #qa-consumes

| TM | Consumes | Assert |
|----|----------|--------|
| TM-001 | FR-001, FR-002, BN-002 | Offline compose: no vault services; pull_policy never; digest refs |
| TM-002 | FR-005, BN-003, BN-005 | Offline secrets gate fail-closed; no silent prod `.env` fallback |
| TM-003 | FR-003, FR-004, BN-001, BN-004 | Pack→load→up path; checksum/digest mismatch fails |
| TM-004 | FR-006 | Air-gap evidence artifact; egress/registry access ⇒ fail |
| TM-005 | FR-007, BN-006 | SBOM present; forbidden license in app layer ⇒ fail |
| TM-006 | FR-008, BN-007, sunset I | Offline docs without CDN/pull mid-install; RU present |

Independent tests = **behavior** (compose policy, pack/load, gate exit codes, evidence files) — не «файл существует».

---

## Eng review spine

| Topic | Decision |
|-------|----------|
| Architecture | Overlay/profile beside canonical `compose.prod.yaml`; не fork всего prod SoT |
| Patterns | Explicit dual profile; fail-closed; digest-pinned; Vault out of offline product boundary |
| Code surface | `scripts/infra/*`, `docker/*` overlay, `tests/infra/*`, ops docs; minimal touch to app Python |
| Failure | Missing image/secret/digest/SBOM → non-zero; no partial “up without secrets” |
| Rollback | Offline artifact disposable; online Vault prod unchanged |
| Route | DECOMPOSE → IMPLEMENT s01/s02 → QA |

**CREATIVE need:** нет (нет UI/contract design ambiguity beyond clarify).

---

## Verification strategy

```bash
# contract (targeted)
bin/pytest tests/infra/test_offline_bundle_*.py -q --tb=line
python3 scripts/infra/check_offline_secrets_contract.py --compose docker/compose.prod.offline.yaml
python3 scripts/infra/check_offline_airgap.py --bundle /path/to/bundle --dry-run

# pack (when images available)
python3 scripts/infra/pack_offline_bundle.py --release-manifest <manifest.json> --out dist/offline

# install rehearsal (operator / gated)
bash ops/offline/install.sh --bundle dist/offline --secrets /path/to/offline-secrets
```

QA handoff later: full `bin/pytest` + documented air-gap rehearsal evidence (не замена targeted IMPLEMENT checks).

---

## Acceptance criteria

### AC+

1. Offline profile поднимает полный граф без Vault на Ubuntu/Debian host из бандла без сети.
2. Bundle inventory не содержит Vault images; compose offline не объявляет vault services.
3. Отсутствие secrets file → install/promotion FAIL.
4. Air-gap evidence JSON = pass при deny-egress rehearsal.
5. SBOM + checksums в бандле; RU offline install doc в бандле.
6. Connected prod Vault path не ослаблен и не получил silent `.env` fallback.

### AC−

1. Нет dual machine path «Vault or .env» внутри **одного** профиля.
2. Нет `pull_policy: always` / registry pull в offline install happy path.
3. Нет инструкций offline, требующих интернет mid-install.
4. Нет тестов, требующих старый контракт «offline только через Vault-in-bundle».

---

## Review readiness

| Item | Status | Notes |
|------|--------|-------|
| Clarify Completion Report | Required / done | Q1–Q5 closed |
| Context Pack + Context consumed | Required / done | projectbrief n/a |
| Technology axiom | Required / done | dual explicit profiles |
| Replacement A+B+C+I | Required / done | brownfield delivery |
| Boundary BN (≥3) | Required / done | BN-001..007 |
| QA consumes (≥3 TM, BN→TM) | Required / done | TM-001..006 |
| Review passes Product/DX/Eng | Required / done | Design skip |
| Ownership matrix | Required / done | |
| prompt.md Epic+Covering+Board | Required / done | md/prompt.md |
| Queue row T-B10 | Required / done | roadmap/queue.yaml |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Размер бандла (full-minus-vault) | multi-tar + checksums; document capacity |
| Drift digests vs release manifest | pack читает T-B08 manifest only |
| Путаница online/offline профилей | явные имена файлов + install entry + tests |
| License false positive на MariaDB GPL | document DBMS as environment, not app layer; scan policy scoped |

---

## Dependencies

- **T-B05** — prod service graph / image-only compose  
- **T-B08** — digest/release manifest (источник pin для pack)  
- **T-B06** — контракт путей secrets (переиспользуем shape files; Vault runtime out of bundle)  
- Soft: T-B09 edge не блокирует offline bundle
