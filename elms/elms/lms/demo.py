"""Idempotent Russian oil-and-gas LMS demo catalogue seed."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict

import frappe


def _upsert(doctype: str, filters: Dict[str, Any], values: Dict[str, Any]) -> str:
    name = frappe.db.get_value(doctype, filters, "name")
    if name:
        doc = frappe.get_doc(doctype, name)
        doc.update(values)
        doc.flags.ignore_permissions = True
        doc.save()
        return name

    doc = frappe.get_doc({"doctype": doctype, **values})
    doc.flags.ignore_permissions = True
    doc.insert()
    return doc.name


def _active_dates() -> tuple[str, str]:
    start = date.fromisoformat(frappe.utils.today()) - timedelta(days=5)
    return start.isoformat(), (start + timedelta(days=365)).isoformat()


def seed_demo_data() -> Dict[str, Any]:
    """Create or update a complete demo catalogue without creating users."""
    start_date, end_date = _active_dates()
    courses = [
        {
            "course_code": "DEMO-OIL-OT-STR-2026",
            "course_name": "Безопасные методы работ: стропальные операции",
            "category": "Охрана труда (ПП РФ № 2464)",
            "academic_hours": 16,
            "passing_percentage": 80,
            "short_description": "Практический вводный курс для стропальщиков на объектах добычи, подготовки и транспортировки нефти и газа.",
            "description": "<p>Демонстрационная программа для отработки учебного пути ELMS. Материалы не заменяют утверждённую работодателем программу обучения и проверку знаний.</p><p><b>Результат:</b> слушатель понимает назначение строп, порядок осмотра, сигналы и безопасную организацию зоны подъёма.</p>",
        },
        {
            "course_code": "DEMO-OIL-PB-2026",
            "course_name": "Промышленная безопасность на объектах нефтегазового комплекса",
            "category": "Промышленная безопасность (Ростехнадзор)",
            "academic_hours": 24,
            "passing_percentage": 80,
            "short_description": "Основы управления рисками при эксплуатации промысловых, трубопроводных и резервуарных объектов.",
            "description": "<p>Демонстрационный курс по культуре безопасности и распознаванию опасностей в нефтегазовых операциях.</p><p>Для реального обучения необходимо заменить материалы на утверждённые локальные документы организации.</p>",
        },
        {
            "course_code": "DEMO-OIL-PIPE-2026",
            "course_name": "Оператор технологических трубопроводов: безопасная эксплуатация",
            "category": "Повышение квалификации (ДПО)",
            "academic_hours": 24,
            "passing_percentage": 80,
            "short_description": "Базовая программа для операторов: маршрут обхода, запорная арматура, утечки и действия по наряду.",
            "description": "<p>Демонстрационный курс для проверки полного цикла: каталог, запись, уроки, активное время и расчёт прогресса.</p>",
        },
    ]

    course_names = {}
    for course in courses:
        values = {**course, "is_published": 1}
        course_names[course["course_code"]] = _upsert(
            "ELMS Course", {"course_code": course["course_code"]}, values
        )

    curriculum = {
        "DEMO-OIL-OT-STR-2026": [
            {
                "chapter_name": "1. Основы безопасной строповки",
                "description": "Назначение грузозахватных приспособлений и границы безопасной работы.",
                "lessons": [
                    ("Роли стропальщика и сигнальщика", "Профессии и зоны ответственности.", 5),
                    ("Осмотр строп и маркировка", "Проверьте бирку, целостность ветвей, крюков и замков. Не используйте строп с повреждениями или без читаемой маркировки.", 6),
                ],
            },
            {
                "chapter_name": "2. Организация подъёма груза",
                "description": "Сигналы, опасная зона и действия при нештатной ситуации.",
                "lessons": [
                    ("Сигналы машинисту крана", "До начала подъёма согласуйте единый порядок сигналов, убедитесь в видимости сигнальщика и остановите операцию при потере связи.", 6),
                    ("Контрольная памятка перед подъёмом", "Перед подъёмом проверьте массу и центр тяжести груза, состояние тары, свободный путь и отсутствие людей в опасной зоне.", 5),
                ],
            },
        ],
        "DEMO-OIL-PB-2026": [
            {
                "chapter_name": "1. Опасности нефтегазового объекта",
                "description": "Идентификация источников энергии, давления и воспламенения.",
                "lessons": [
                    ("Опасные и вредные производственные факторы", "Разберите риск загазованности, давления, движущихся механизмов, повышенной температуры и ограниченных пространств.", 7),
                    ("Наряд-допуск и газоопасные работы", "До начала работ проверьте допуск, состав бригады, результаты контроля воздушной среды и готовность средств связи.", 8),
                ],
            },
            {
                "chapter_name": "2. Барьеры и реагирование",
                "description": "Предотвращение инцидентов и первичные действия при отклонениях.",
                "lessons": [
                    ("Пять уровней защиты", "Разделяйте технические, организационные и индивидуальные барьеры. Отказ одного барьера не должен приводить к потере контроля.", 7),
                    ("Аварийная остановка и сообщение", "При запахе газа, срабатывании сигнализации или потере герметичности остановите работу по процедуре и сообщите ответственному.", 6),
                ],
            },
        ],
        "DEMO-OIL-PIPE-2026": [
            {
                "chapter_name": "1. Технологическая схема",
                "description": "Оборудование, арматура и маршрут безопасного обхода.",
                "lessons": [
                    ("Запорная арматура и обозначения", "Научитесь читать условные обозначения и сверять положение арматуры с оперативной схемой.", 7),
                    ("Маршрут обхода оборудования", "Проводите обход по утверждённому маршруту, фиксируйте отклонения и не открывайте оборудование без разрешения.", 7),
                ],
            },
            {
                "chapter_name": "2. Отклонения и передача смены",
                "description": "Наблюдение, фиксация и коммуникация между сменами.",
                "lessons": [
                    ("Признаки утечки и отклонения параметров", "Сопоставляйте показания приборов с визуальными признаками и немедленно сообщайте о несоответствиях.", 6),
                    ("Чек-лист передачи смены", "Передайте статус оборудования, действующие наряды, временные схемы, ограничения и незавершённые действия.", 5),
                ],
            },
        ],
    }

    lesson_count = 0
    for code, chapters in curriculum.items():
        course = course_names[code]
        for chapter_index, chapter in enumerate(chapters, start=1):
            chapter_name = _upsert(
                "ELMS Course Chapter",
                {"course": course, "chapter_name": chapter["chapter_name"]},
                {
                    "chapter_name": chapter["chapter_name"],
                    "course": course,
                    "sequence_id": chapter_index,
                    "description": chapter["description"],
                },
            )
            for lesson_index, (lesson_name, body, duration) in enumerate(chapter["lessons"], start=1):
                _upsert(
                    "ELMS Course Lesson",
                    {"course": course, "lesson_name": lesson_name},
                    {
                        "lesson_name": lesson_name,
                        "course": course,
                        "chapter": chapter_name,
                        "sequence_id": lesson_index,
                        "content_type": "Article",
                        "duration_minutes": duration,
                        "minimum_time_seconds": 60,
                        "is_mandatory": 1,
                        "body": f"<p>{body}</p><p><b>Мини-задание:</b> назовите три условия, при которых работу нужно остановить и доложить ответственному.</p>",
                    },
                )
                lesson_count += 1

    batch_names = {}
    for code, suffix in (
        ("DEMO-OIL-OT-STR-2026", "Стропальные работы"),
        ("DEMO-OIL-PB-2026", "Промышленная безопасность"),
        ("DEMO-OIL-PIPE-2026", "Технологические трубопроводы"),
    ):
        course = course_names[code]
        batch_names[code] = _upsert(
            "ELMS Batch",
            {"batch_name": f"Демо-поток 2026 · {suffix}"},
            {
                "batch_name": f"Демо-поток 2026 · {suffix}",
                "course": course,
                "start_date": start_date,
                "end_date": end_date,
                "organization": "Демонстрационный контур НефтеГаз",
                "order_number": "DEMO-2026",
                "status": "Active",
            },
        )
        _upsert(
            "ELMS Subscription",
            {"contract_number": f"DEMO-{code}"},
            {
                "company_name": "Демонстрационный контур НефтеГаз",
                "inn": "0000000000",
                "course": course,
                "contract_number": f"DEMO-{code}",
                "total_seats": 100,
                "seats_used": 0,
                "valid_from": start_date,
                "valid_to": end_date,
                "status": "Active",
            },
        )

    return {
        "courses": len(course_names),
        "batches": len(batch_names),
        "lessons": lesson_count,
        "message": "Demo LMS catalogue seeded",
    }
