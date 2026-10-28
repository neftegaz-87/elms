# Публикация задач на доску после PLAN

**Дата:** 2026-10-28  
**Канон хаба:** `harness/templates/board/board-publish.md` · rules `workflow-board-after-plan.mdc`  
(`make hub-link` сеет шаблоны `.loop/*`, `scripts/board-sync.sh`, этот файл)

## Правило

После завершения **BACK PLAN** и/или **FRONT PLAN** (есть `plan.md` + `prompt.md` с секцией `## Board`) нужно **сразу опубликовать карточки на Bitrix**, не дожидаясь DECOMPOSE/IMPLEMENT.

## Кто на карточке (постановщик = исполнитель)

Смотри [`.loop/board-actors.yaml`](../../.loop/board-actors.yaml):

- `sokolov` (240) — Евгений Соколов  
- `erokhin` (274) — Андрей Ерохин  

В `epics:` укажи актёра для каждого эпика. Менять можно до `board-sync`.

## Команда

```bash
cd /home/aero/PyProject/elms
./scripts/board-sync.sh --all
# или точечно:
./scripts/board-sync.sh T-B01-elms-docker-bootstrap T-B02-elms-roles-rbac
```

Текст карточки берётся из `## Board` в `prompt.md` (title + summary для нетехнических читателей: что / зачем / стадии).

## Описание в prompt

В `## Board` писать простым языком:

1. Что делаем  
2. Зачем  
3. Стадии реализации  
4. Результат для наблюдателя  

Без внутренних ID эпиков в title/summary (их подставит loop).

## Не путать

- `board-sync` — создать/перенести карточку задачи  
- `board-docs` — приложить файлы plan/prompt к карточке (отдельно, по необходимости)  
- авто `loop finish` пока использует только `.env` `BITRIX_RESPONSIBLE_ID`; для нужного актёра после PLAN всегда зови `scripts/board-sync.sh`
