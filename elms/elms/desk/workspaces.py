"""ELMS Desk workspaces and their role boundaries."""

import json
from typing import Any

import frappe


ELMS_WORKSPACE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "name": "LMS",
        "label": "elms",
        "module": "LMS",
        "icon": "education",
        "sequence_id": 1,
        "roles": (
            "ELMS Admin",
            "ELMS Operations User",
            "ELMS Learner",
            "ELMS Instructor",
            "ELMS Methodologist",
        ),
        "content": "Курсы, потоки, подписки, прогресс и аттестация.",
        "shortcuts": (
            {
                "type": "URL",
                "url": "/app/elms-learning",
                "label": "Кабинет обучения и плеер",
                "icon": "education",
            },
            {
                "type": "URL",
                "url": "/app/elms-course-studio",
                "label": "Конструктор курсов",
                "icon": "edit",
            },
        ),
        "links": (
            ("Конструктор курсов", "ELMS Course", "Курсы"),
            ("Конструктор курсов", "ELMS Program", "Программы обучения"),
            ("Конструктор курсов", "ELMS Program Course", "Состав программ"),
            ("Учебный процесс", "ELMS Batch", "Потоки и группы"),
            ("Учебный процесс", "ELMS Subscription", "Подписки и квоты"),
            ("Учебный процесс", "ELMS Enrollment", "Зачисления"),
            ("Учебный процесс", "ELMS Program Enrollment", "Зачисления на программы"),
            ("Тесты и экзамены", "ELMS Quiz", "Тесты и экзамены"),
            ("Тесты и экзамены", "ELMS Quiz Question", "Банк вопросов"),
            ("Тесты и экзамены", "ELMS Quiz Attempt", "Попытки прохождения"),
            ("Трекер обучения", "ELMS Course Progress", "Прогресс по курсам"),
            ("Трекер обучения", "ELMS Lesson Progress", "Прогресс по урокам"),
            ("Трекер обучения", "ELMS User Activity", "Активность слушателей"),
            ("Трекер обучения", "ELMS Video Watch Log", "Просмотр видео"),
        ),
    },
    {
        "name": "Предпросмотр курсов",
        "label": "Предпросмотр курсов",
        "module": "LMS",
        "icon": "preview",
        "sequence_id": 2,
        "roles": ("ELMS Admin", "ELMS Operations User", "ELMS Instructor", "ELMS Methodologist"),
        "content": "Проверьте курс глазами обычного слушателя до публикации.",
        "shortcuts": (
            {
                "type": "URL",
                "url": "/app/elms-course-preview",
                "label": "Открыть предпросмотр",
                "icon": "preview",
            },
        ),
        "links": (),
    },
    {
        "name": "Settings",
        "module": "ELMS Core",
        "icon": "setting",
        "sequence_id": 3,
        "roles": ("ELMS Admin", "System Manager"),
        "content": "Кто входит в систему, что разрешено ролям и какие записи доступны пользователю.",
        "links": (
            ("Настройки elms", "ELMS Settings Section", "Состояние настроек"),
            ("Пользователи и доступ", "User", "Пользователи"),
            ("Пользователи и доступ", "Role", "Роли"),
            ("Пользователи и доступ", "permission-manager", "Матрица прав ролей"),
            ("Доступ и роли", "Role Profile", "Профили ролей"),
            ("Доступ и роли", "User Group", "Группы пользователей"),
            ("Доступ и записи", "User Permission", "Ограничения пользователей"),
        ),
    },
)

HIDDEN_PLATFORM_WORKSPACES: tuple[str, ...] = (
    "Users",
    "Website",
    "Tools",
    "Integrations",
    "Build",
    "Welcome Workspace",
)

OBSOLETE_ELMS_WORKSPACES: tuple[str, ...] = ("Управление LMS", "Operations", "Review")

LMS_AUTHORING_LINKS = frozenset(
    {
        "ELMS Course",
        "ELMS Program",
        "ELMS Program Course",
    }
)
LMS_PROCESS_LINKS = frozenset(
    {
        "ELMS Batch",
        "ELMS Subscription",
        "ELMS Enrollment",
        "ELMS Program Enrollment",
    }
)
LMS_ASSESSMENT_LINKS = frozenset({"ELMS Quiz", "ELMS Quiz Question", "ELMS Quiz Attempt"})
LMS_TRACKER_LINKS = frozenset(
    {
        "ELMS Course Progress",
        "ELMS Lesson Progress",
        "ELMS User Activity",
        "ELMS Video Watch Log",
    }
)


def _workspace_content(
    description: str,
    links: tuple[tuple[str, str, str], ...],
    shortcuts: tuple[dict[str, Any], ...] = (),
) -> str:
    cards: list[dict[str, Any]] = []
    card_names: list[str] = []
    for card_name, _, _ in links:
        if card_name not in card_names:
            card_names.append(card_name)
            cards.append({"type": "card", "data": {"card_name": card_name, "col": 4}})

    return json.dumps(
        [
            {
                "type": "header",
                "data": {"text": "<span class=\"h3\"><b>elms</b></span>", "col": 12},
            },
            {"type": "paragraph", "data": {"text": description, "col": 12}},
            {"type": "spacer", "data": {"col": 12}},
            *[
                {
                    "type": "shortcut",
                    "data": {"shortcut_name": shortcut["label"], "col": 4},
                }
                for shortcut in shortcuts
            ],
            *cards,
        ],
        ensure_ascii=False,
    )


def _workspace_links(definition: dict[str, Any]) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    current_card = None
    for card, link_to, label in definition["links"]:
        if card != current_card:
            links.append(
                {
                    "type": "Card Break",
                    "label": card,
                    "icon": definition["icon"],
                    "hidden": 0,
                }
            )
            current_card = card
        links.append(
            {
                "type": "Link",
                "label": label,
                "link_type": "Page" if link_to == "permission-manager" else "DocType",
                "link_to": link_to,
                "hidden": 0,
                "onboard": 0,
            }
        )
    return links


def _workspace_shortcuts(definition: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in definition.get("shortcuts", ())]


def filter_workspace_for_user(page_data: dict[str, Any], page: str, user: str | None = None) -> dict[str, Any]:
    """Hide LMS management links from learner-only users while keeping one LMS workspace."""

    if page != "LMS":
        return page_data

    current_user = user or frappe.session.user
    roles = set(frappe.get_roles(current_user) or [])
    if roles.intersection({"ELMS Admin", "ELMS Operations User"}):
        return page_data

    can_open_studio = bool(roles.intersection({"ELMS Methodologist", "System Manager"}))
    if not can_open_studio:
        shortcuts = page_data.get("shortcuts")
        if isinstance(shortcuts, list):
            page_data["shortcuts"] = [
                shortcut
                for shortcut in shortcuts
                if shortcut.get("url") != "/app/elms-course-studio"
            ]
        content = page_data.get("content")
        if isinstance(content, str):
            try:
                blocks = json.loads(content)
            except (TypeError, ValueError):
                blocks = []
            if isinstance(blocks, list):
                page_data["content"] = json.dumps(
                    [
                        block
                        for block in blocks
                        if not (
                            block.get("type") == "shortcut"
                            and block.get("data", {}).get("shortcut_name") == "Конструктор курсов"
                        )
                    ],
                    ensure_ascii=False,
                )

    if "ELMS Methodologist" in roles:
        allowed = LMS_AUTHORING_LINKS | LMS_ASSESSMENT_LINKS | LMS_TRACKER_LINKS
    elif "ELMS Instructor" in roles:
        allowed = {"ELMS Course", "ELMS Program", "ELMS Program Course"} | LMS_TRACKER_LINKS
    else:
        allowed = frozenset()

    cards_data = page_data.get("cards")
    if isinstance(cards_data, dict) and isinstance(cards_data.get("items"), list):
        filtered_cards = []
        for card in cards_data["items"]:
            links = card.get("links", []) if isinstance(card, dict) else []
            visible_links = [link for link in links if link.get("link_to") in allowed]
            if visible_links:
                filtered_card = dict(card)
                filtered_card["links"] = visible_links
                filtered_cards.append(filtered_card)
        cards_data["items"] = filtered_cards
        return page_data

    links = page_data.get("links")
    if isinstance(links, list):
        card_by_link: dict[int, str] = {}
        current_card = ""
        for index, link in enumerate(links):
            if link.get("type") == "Card Break":
                current_card = str(link.get("label") or "")
            elif link.get("type") == "Link":
                card_by_link[index] = current_card
        visible_cards = {
            card
            for index, card in card_by_link.items()
            if links[index].get("link_to") in allowed
        }
        page_data["links"] = [
            link
            for index, link in enumerate(links)
            if (
                link.get("type") == "Card Break" and link.get("label") in visible_cards
            )
            or (link.get("type") == "Link" and links[index].get("link_to") in allowed)
        ]

    content = page_data.get("content")
    if isinstance(content, str):
        try:
            blocks = json.loads(content)
        except (TypeError, ValueError):
            blocks = []
        if isinstance(blocks, list):
            visible_cards = {link.get("label") for link in page_data.get("links", []) if link.get("type") == "Card Break"}
            page_data["content"] = json.dumps(
                [
                    block
                    for block in blocks
                    if block.get("type") != "card" or block.get("data", {}).get("card_name") in visible_cards
                ],
                ensure_ascii=False,
            )
    return page_data


def _ensure_workspace(definition: dict[str, Any]) -> None:
    name = definition["name"]
    if frappe.db.exists("Workspace", name):
        workspace = frappe.get_doc("Workspace", name)
    else:
        workspace = frappe.new_doc("Workspace")
        workspace.name = name
        workspace.label = name

    workspace.update(
        {
            "label": definition.get("label", name),
            "title": definition.get("title", name),
            "module": definition["module"],
            "icon": definition["icon"],
            "sequence_id": definition["sequence_id"],
            "public": 1,
            "is_hidden": 0,
            "for_user": "",
            "parent_page": "",
            "hide_custom": 1,
            "content": _workspace_content(
                definition["content"],
                definition["links"],
                definition.get("shortcuts", ()),
            ),
            "links": _workspace_links(definition),
            "shortcuts": _workspace_shortcuts(definition),
            "roles": [{"role": role} for role in definition["roles"]],
        }
    )
    workspace.flags.ignore_permissions = True
    if workspace.is_new():
        workspace.insert()
    else:
        workspace.save()


def _hide_platform_workspaces() -> None:
    missing = [name for name in HIDDEN_PLATFORM_WORKSPACES if not frappe.db.exists("Workspace", name)]
    if missing:
        frappe.throw("Required Frappe workspaces are missing: " + ", ".join(missing))

    for name in HIDDEN_PLATFORM_WORKSPACES:
        workspace = frappe.get_doc("Workspace", name)
        workspace.public = 0
        workspace.is_hidden = 1
        workspace.for_user = ""
        workspace.flags.ignore_permissions = True
        workspace.save()


def _hide_obsolete_workspaces() -> None:
    for name in OBSOLETE_ELMS_WORKSPACES:
        if not frappe.db.exists("Workspace", name):
            continue
        workspace = frappe.get_doc("Workspace", name)
        workspace.public = 0
        workspace.is_hidden = 1
        workspace.for_user = ""
        workspace.flags.ignore_permissions = True
        workspace.save()


def ensure_workspaces() -> None:
    """Create the ELMS navigation and remove platform workspaces from the UI."""
    for definition in ELMS_WORKSPACE_DEFINITIONS:
        _ensure_workspace(definition)
    _hide_platform_workspaces()
    _hide_obsolete_workspaces()
