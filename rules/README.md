# `rules/` — настройки проекта для агентов

## Что это

Папка **продуктовых инструкций этого репозитория** для агентов.  
SoT правим **только здесь**. Подключение к runtime — через тонкие ссылки/оверлеи (не копии текста в hub).

| Путь | Что это |
|------|---------|
| `rules/` | **SoT настроек ЭТОГО проекта** |
| `.cursor/rules/` | общий harness / dev-hub (symlink) |
| `.cursor/rules.d/` | **Cursor:** симлинки → `rules/*.mdc` |
| `AGENTS.md` | symlink на hub (workflow); Codex его **не** берёт, если есть override |
| `AGENTS.override.md` | **Codex:** project override → обязан читать `rules/` |

## Правило для всех проектов

В **каждом** продуктовом репо своя `rules/`:

```text
<project>/
  rules/                             ← SoT инструкций проекта
    README.md
    <project>-approach.mdc
    <project>-design.mdc             ← по необходимости
    agents-overlay.md
  .cursor/rules.d/
    *.mdc → ../../rules/...          ← Cursor
  AGENTS.override.md                 ← Codex (указывает на rules/)
  AGENTS.md → ../dev-hub/AGENTS.md   ← hub workflow (symlink ок)
```

**Открыт проект X → агент берёт `X/rules/`, не чужой CRM и не hub CRM-секции.**

## Cursor

1. Правим файлы в `rules/`.
2. Симлинки:

```bash
ln -sfn ../../rules/elms-approach.mdc .cursor/rules.d/elms-approach.mdc
ln -sfn ../../rules/elms-design.mdc   .cursor/rules.d/elms-design.mdc
```

3. Frontmatter `.mdc`: `alwaysApply: true`.

Не копировать текст в `.cursor/rules.d/` и не править harness `.cursor/rules`.

## Codex

Codex **не** читает `.cursor/rules.d/*.mdc`.  
Он собирает инструкции из `AGENTS.md` / `AGENTS.override.md` (в одном каталоге — **один** файл; `AGENTS.override.md` побеждает).

Поэтому в корне продукта:

1. Оставляем `AGENTS.md` → symlink на hub (для Cursor/Claude entrypoint и людей).
2. Кладём **`AGENTS.override.md`**: «сначала `rules/`, потом hub AGENTS для workflow; CRM-секции hub не канон».
3. SoT по-прежнему в `rules/` — override только проводка, не дублировать длинный канон.

Проверка: `codex` в корне elms должен видеть override и следовать `rules/README.md`.

Не полагаться на то, что Codex сам откроет `.mdc` без явного Read из override.

## Файлы ELMS (этот репо)

| Файл | Назначение |
|------|------------|
| `elms-approach.mdc` | продукт Operations+LMS; роли из LMS/`elms`; ERP/CRM только паттерны Frappe |
| `elms-design.mdc` | UI: neftegaz-ai-layer + родной LMS |
| `agents-overlay.md` | что из hub `AGENTS.md` не канон; стиль кода/тестов |

Продуктовый SoT рядом: `memory-bank/product/` (`modules.md`, `vision.md`, `design.md`).

## Чеклист нового проекта на том же hub

1. Создать `<project>/rules/` с README и своими `.mdc` / `agents-overlay.md`.
2. В каждом файле: «мы в репо X → берём эти rules».
3. **Cursor:** симлинки `.cursor/rules.d/` → `rules/`.
4. **Codex:** корневой `AGENTS.override.md` → Read `rules/` + hub AGENTS для workflow.
5. Не писать продукт в hub `AGENTS.md` / harness `.cursor/rules`.
6. `hub-link` не трогает `AGENTS.override.md` и `rules/` — их держит продукт.
