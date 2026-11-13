# PLAN — T-B11 ELMS host-local logs / read-from-ops

**Epic ID:** `T-B11-elms-host-local-logs-read-contract`  
**Роль:** BACK  
**Дата:** 2026-11-12  
**Уровень:** L2 (контракт + compose policy + docs; без нового продуктового UI)  
**Decision SoT:** `memory-bank/decisions/observability-stack.md` (пересмотр 2026-11-12)  
**Центр:** репозиторий `observability` / эпик `T-OBS-001-ops-console-pull-logs`

## Context consumed

- `memory-bank/decisions/observability-stack.md`
- `memory-bank/systemPatterns.md` §11
- `memory-bank/techContext.md` (observability bullet + item 23)
- `memory-bank/back/roadmap/queue.yaml` batch `elms-production`
- Внешний канон центра: `/home/aero/PyProject/observability/memory-bank/plan/T-OBS-001-ops-console-pull-logs/md/plan.md`
- As-built sunset: прежний текст «ship to central Loki» в decision/systemPatterns/techContext (уже переписан в этом же изменении канона)

## Technology axiom

| Выбор | Machine boundary | FORBIDDEN |
|-------|------------------|-----------|
| Логи = stdout/stderr контейнеров | docker logging driver / journald | remote Vector/Alloy sink на центральный Loki |
| Ротация json-file | `max-size` + `max-file` в compose | безлимитные логи на диске хоста |
| Чтение с ops | SSH / SSH `-L` к localhost Dozzle | публичный bind UI логов; постоянный push |
| Health для алертов | существующие healthchecks сервисов | подмена «алерт = есть логи на центре» |

## WHY

Оператор лезет в логи при проблеме. Постоянная пересылка на ops-машину:

- занимает диск и RAM центра без ежедневной пользы;
- увеличивает сетевую поверхность;
- дублирует то, что уже есть в `docker logs` на хосте.

Нужен единственный контракт: **хранить здесь, читать оттуда**.

## WHAT

### FR-001 — Local log SoT

Все сервисы ELMS compose пишут в stdout/stderr. Штатное хранилище — logging driver хоста с ротацией. Нет второго склада (Loki volume) в ELMS SoT.

### FR-002 — No remote ship

В canonical `docker/compose.prod.yaml`, `compose.dev.yaml` и overlays **нет** сервисов/конфигов Vector/Alloy/Fluent Bit с endpoint центрального Loki. Policy/check падает, если такой sink появляется.

### FR-003 — Optional localhost log UI

Допускается overlay с Dozzle (или эквивалент), bind только `127.0.0.1:<port>`. Публичный `0.0.0.0` — FAIL. Документируется чтение через SSH-туннель с ops-машины из inventory observability.

### FR-004 — Structured JSON where already required

Сервисы, которые уже обязаны писать JSON (по существующим app-контрактам), сохраняют JSON. Этот эпик **не** вводит новый schema logger для всего Frappe Desk prose; минимум — не ломать существующие structured emitters и зафиксировать ротацию для всех контейнеров графа.

### FR-005 — Handoff to observability

В ELMS docs (techContext / decision / короткий runbook pointer) указано:

- хост ELMS = target в inventory центра;
- как открыть логи (`docker logs` / туннель Dozzle);
- что алерты и uptime живут в `observability`, не в ELMS.

### FR-006 — Sunset ship-to-central instructions

Все instruction surfaces ELMS (decision, systemPatterns, techContext, tasks index) не требуют push на Loki. Устаревшие формулировки удалены/переписаны (часть уже в каноне на дату плана).

## AC+

1. Compose policy / test: появление `loki` / remote Vector sink в ELMS SoT → FAIL.
2. У каждого mandatory service в prod compose заданы bounded logging options (или наследуемый default с явным enforce).
3. Если Dozzle overlay есть — только localhost; тест/policy это ловит.
4. Operator runbook pointer: «логи на хосте; читать с ops» без шагов ship.
5. Decision AC− из `observability-stack.md` выполнены для ELMS tree.

## AC−

1. Нет dual path ship + local после эпика.
2. Нет центрального Loki «внутри ELMS вместо observability».
3. Нет «модуль агента есть, но optional ship default off» как done.
4. Нет публичного log UI.
5. Нет требования Tempo/ELK.

## Target layout

```text
docker/compose.prod.yaml          # logging opts; NO loki/vector remote
docker/compose.dev.yaml           # same contract
docker/compose.*.yaml overlays    # optional dozzle localhost only
scripts/… policy/tests            # deny remote sink / public dozzle
memory-bank/decisions/…           # already SoT
docs/runbooks/… (если принят path) pointer to observability
```

## HOW (границы, не as-built wrap)

1. Inventory текущих logging секций compose (sunset: любой намёк на ship).
2. Enforce ротации и deny-list образов/сервисов remote log pipeline в policy.
3. Опциональный overlay Dozzle localhost + документ туннеля.
4. Сверка docs с decision; obsolete ship text — purge.
5. QA: policy tests + ручной check «с ops-хоста читаются логи без копирования».

## Skills (IMPLEMENT)

- `.agents/skills/docker-compose/SKILL.md`
- `.agents/skills/docker-management/SKILL.md`
- `.agents/skills/firewall-config/SKILL.md` (если открываются порты — deny public log UI)
- `.agents/skills/python-observability/SKILL.md` (только если трогаем structured emitters; иначе skip)

## Cut / later

- Центральный Loki revisit — только отдельным решением в `observability`.
- Метрики node_exporter на ELMS — владение центра (`T-OBS-001`), не этот эпик.
- Полная унификация JSON schema всех Frappe логов — out of appetite.

## Dependencies

- Decision observability-stack 2026-11-12 (уже принят).
- Параллельно / после: `observability` `T-OBS-001` (inventory + read path).
- Soft: T-B05 compose graph (done) как база.

## Verification (targeted на IMPLEMENT)

- Policy/unit: deny remote sink / public dozzle.
- Compose config validate.
- Manual: SSH from ops inventory host → `docker logs` or tunneled Dozzle.

## Board

См. `md/prompt.md` §Board. Sync: `./scripts/board-sync.sh T-B11-elms-host-local-logs-read-contract` после появления `.env` доски.
