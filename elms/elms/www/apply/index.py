"""Context for the individual course application page."""

import frappe


def _list_published_courses() -> list[dict]:
    return list(
        frappe.get_all(
            "ELMS Course",
            filters={"is_published": 1},
            fields=["name", "course_name", "course_code"],
            order_by="course_name asc",
            limit_page_length=100,
        )
        or []
    )


def get_context(context: dict) -> dict:
    context.no_cache = 1
    context.courses = _list_published_courses()
    return context
