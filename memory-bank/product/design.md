# ELMS — дизайн

**Path:** `memory-bank/product/design.md`  
**Дата:** 2026-10-30  
**Правило:** `rules/elms-design.mdc` (Cursor: symlink `.cursor/rules.d/elms-design.mdc`)

## Идея

Визуальный язык берём из **neftegaz-ai-layer** (служебный светлый UI, cobalt action, компактные контролы) и **смешиваем** с родным учебным LMS UI (структура обучения, курсы, прогресс) — не с CRM/ERP Desk.

## Эталоны

| Источник | Что брать |
|----------|-----------|
| `/home/aero/PyProject/neftegaz-ai-layer/DESIGN.md` | направление, палитра, типографика, spacing |
| `/home/aero/PyProject/neftegaz-ai-layer/frontend/src/index.css` | CSS-токены |
| `/home/aero/PyProject/neftegaz-ai-layer/frontend/src/ui.jsx` | геометрия кнопок/состояний |
| app `elms` LMS / website surfaces | учебная IA, контентные экраны |

## Не эталон дизайна

ERPNext Desk, Frappe CRM UI, копипаст CRM design-system как brand ELMS.

## Связь с foundation

Login Keycloak (`T-A01`) уже опирается на neftegaz tokens (cobalt `#0D4CD3`, высота 44px, radius 3px). Дальнейшие web/Desk поверхности — тот же язык + LMS-паттерны.
