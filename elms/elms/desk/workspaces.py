"""ELMS Desk workspaces and their role boundaries."""

import json
from typing import Any

import frappe


ELMS_WORKSPACE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "name": "LMS",
        "module": "LMS",
        "icon": "education",
        "sequence_id": 1,
        "roles": ("ELMS Admin", "ELMS LMS User"),
        "content": "Учебный контур ELMS СДО: курсы, слушатели и учебные группы.",
        "links": (
            ("Учебный контур", "ELMS LMS Section", "Состояние LMS"),
            ("Пользователи и группы", "User Group", "Учебные группы"),
            ("Пользователи и группы", "User", "Слушатели и пользователи"),
        ),
    },
    {
        "name": "Operations",
        "module": "Operations",
        "icon": "organization",
        "sequence_id": 2,
        "roles": ("ELMS Admin", "ELMS Operations User"),
        "content": "Операционный контур ELMS: процессы и рабочие задачи.",
        "links": (("Операционный контур", "ELMS Operations Section", "Состояние Operations"),),
        "shortcuts": (
            {
                "type": "URL",
                "url": "/app/elms-review",
                "label": "Сверка заявки",
                "icon": "check-circle",
            },
        ),
    },
    {
        "name": "Settings",
        "module": "ELMS Core",
        "icon": "setting",
        "sequence_id": 3,
        "roles": ("ELMS Admin",),
        "content": "Настройки ELMS: роли, профили доступа и группы пользователей.",
        "links": (
            ("Настройки ELMS", "ELMS Settings Section", "Состояние настроек"),
            ("Доступ и роли", "Role", "Роли"),
            ("Доступ и роли", "Role Profile", "Профили ролей"),
            ("Доступ и роли", "User Group", "Группы пользователей"),
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


def _workspace_content(description: str, links: tuple[tuple[str, str, str], ...]) -> str:
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
                "data": {"text": "<span class=\"h3\"><b>ELMS СДО</b></span>", "col": 12},
            },
            {"type": "paragraph", "data": {"text": description, "col": 12}},
            {"type": "spacer", "data": {"col": 12}},
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
                "link_type": "DocType",
                "link_to": link_to,
                "hidden": 0,
                "onboard": 0,
            }
        )
    return links


def _workspace_shortcuts(definition: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in definition.get("shortcuts", ())]


def _ensure_workspace(definition: dict[str, Any]) -> None:
    name = definition["name"]
    if frappe.db.exists("Workspace", name):
        workspace = frappe.get_doc("Workspace", name)
    else:
        workspace = frappe.new_doc("Workspace")
        workspace.label = name

    workspace.update(
        {
            "label": name,
            "title": name,
            "module": definition["module"],
            "icon": definition["icon"],
            "sequence_id": definition["sequence_id"],
            "public": 1,
            "is_hidden": 0,
            "for_user": "",
            "parent_page": "",
            "hide_custom": 1,
            "content": _workspace_content(definition["content"], definition["links"]),
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


def ensure_workspaces() -> None:
    """Create the ELMS navigation and remove platform workspaces from the UI."""
    for definition in ELMS_WORKSPACE_DEFINITIONS:
        _ensure_workspace(definition)
    _hide_platform_workspaces()
