# T-A06 runtime evidence — 2026-11-13

## Migration

```text
docker compose -f docker/compose.dev.yaml exec -T backend bench --site elms.localhost migrate
EXIT:0
```

Live Single exists:

```text
ELMS Integration Settings — enabled=0, default_model=cx/gpt-5.6-luna-high
```

## Backend / assets

```text
./bin/pytest -q --tb=line
174 passed, 9 skipped

node --check elms/elms/public/js/desk-learning.js → EXIT:0
python3 -m py_compile elms/elms/ai/{omniroute,context,api}.py → EXIT:0
```

## leftover_sot / behavior

- `compose.prod.yaml` has no OmniRoute hard-dep.
- AI modules have no `site_config` / `get_site_config` dual-path.
- No floating FAB (`elms-assistant-fab` absent; negative asserts green).

## Authenticated live API

Administrator session against `http://elms.localhost:8082`:

```text
elms.ai.api.get_models → 417 ValidationError disabled + correlation_id
elms.ai.api.ask → 417 ValidationError disabled + correlation_id
elms.lms.api.get_learning_relationships → 200 (LMS unaffected)
GET /api/resource/ELMS Integration Settings → 200 (Password key not returned)
```

Generic `scripts/live_smoke.sh` remains red on unrelated Yandex login markup (same pre-existing finding as T-A05); T-A06 live lane uses the authenticated assistant/LMS smoke above.

## Authenticated browser wire

Playwright `/app/elms-learning` with Administrator cookies:

- route 200
- `[data-elms-assistant]` present and opens panel
- `elms.ai.api.get_models` → 417 disabled fail-closed shown in UI with correlation_id
- LMS APIs (`get_learning_admin_data`, `get_course_catalog`, `get_learner_dashboard`, `get_program_catalog`, `get_learning_relationships`) → 200
- screenshot: `browser-artifacts/elms-assistant-qa-20261113.png`
