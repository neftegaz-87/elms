"""Whitelist API endpoints and domain services for the ELMS LMS module."""

import json
from datetime import timedelta
from typing import Any, Dict, List, Optional
import frappe

if not hasattr(frappe, "whitelist"):
    def _whitelist(*args, **kwargs):
        def decorator(f):
            return f
        if args and callable(args[0]):
            return args[0]
        return decorator
    frappe.whitelist = _whitelist

if not hasattr(frappe, "throw"):
    def _throw(message, exc=Exception, *args, **kwargs):
        raise exc(message)
    frappe.throw = _throw

try:
    from frappe import _
except (ImportError, AttributeError):
    def _(msg: str, *args, **kwargs) -> str:
        return msg


def _today() -> str:
    """Return current date string."""
    if hasattr(frappe, "utils") and hasattr(frappe.utils, "today"):
        return frappe.utils.today()
    from datetime import date
    return date.today().isoformat()


def _now_datetime():
    """Return current datetime string or object."""
    if hasattr(frappe, "utils") and hasattr(frappe.utils, "now_datetime"):
        return frappe.utils.now_datetime()
    from datetime import datetime
    return datetime.now().isoformat()


def _get_current_user() -> str:
    """Return the currently authenticated session user."""
    user = getattr(frappe.session, "user", None) or "Guest"
    return user


def _has_role(role: str, user: Optional[str] = None) -> bool:
    """Check if the user has a specific Frappe role."""
    check_user = user or _get_current_user()
    if check_user == "Administrator":
        return True
    roles = frappe.get_roles(check_user) if hasattr(frappe, "get_roles") else []
    return role in roles


def _is_learning_manager(user: Optional[str] = None) -> bool:
    """Return whether a user may manage the learning catalogue and cohorts."""
    check_user = user or _get_current_user()
    return (
        check_user == "Administrator"
        or _has_role("System Manager", check_user)
        or _has_role("ELMS Admin", check_user)
        or _has_role("ELMS Operations User", check_user)
        or _has_role("ELMS Methodologist", check_user)
    )


def _can_preview_courses(user: Optional[str] = None) -> bool:
    """Return whether a user may inspect learner-facing course material."""
    check_user = user or _get_current_user()
    return _is_learning_manager(check_user) or _has_role("ELMS Instructor", check_user)


def _require_authenticated() -> str:
    """Require a real Frappe session for learner and management APIs."""
    user = _get_current_user()
    if user == "Guest":
        frappe.throw(_("Authentication required"), frappe.PermissionError)
    return user


def _require_learning_manager() -> str:
    """Require an LMS management role; never trust a client-side role flag."""
    user = _require_authenticated()
    if not _is_learning_manager(user):
        frappe.throw(
            _("Learning management requires ELMS Admin or ELMS Operations User role"),
            frappe.PermissionError,
        )
    return user


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _doc_data(doc: Any, fields: List[str]) -> Dict[str, Any]:
    """Return a serialisable subset of a Frappe document for the desk UI."""
    if hasattr(doc, "get"):
        return {field: doc.get(field) for field in fields}
    return {field: getattr(doc, field, None) for field in fields}


def _save_doc(doctype: str, name: Optional[str], values: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update one managed LMS document after server-side role validation."""
    _require_learning_manager()
    if name:
        if not frappe.db.exists(doctype, name):
            frappe.throw(_("{0} {1} not found").format(doctype, name), frappe.DoesNotExistError)
        doc = frappe.get_doc(doctype, name)
    else:
        doc = frappe.new_doc(doctype)

    for field, value in values.items():
        if value is not None:
            setattr(doc, field, value)

    if name:
        doc.save()
    else:
        doc.insert()
    return doc.as_dict() if hasattr(doc, "as_dict") else dict(doc)


def _course_structure(course: str, enrollment: Optional[str] = None) -> Dict[str, Any]:
    """Build the learner-facing course structure from persisted chapters and lessons."""
    if not frappe.db.exists("ELMS Course", course):
        frappe.throw(_("Course {0} not found").format(course), frappe.DoesNotExistError)

    course_doc = frappe.get_doc("ELMS Course", course)
    chapters = frappe.get_all(
        "ELMS Course Chapter",
        filters={"course": course},
        fields=["name", "chapter_name", "sequence_id", "description"],
        order_by="sequence_id asc, modified asc",
    )
    lessons = frappe.get_all(
        "ELMS Course Lesson",
        filters={"course": course},
        fields=[
            "name", "lesson_name", "chapter", "sequence_id", "content_type",
            "duration_minutes", "minimum_time_seconds", "is_mandatory", "video_url", "body",
        ],
        order_by="sequence_id asc, modified asc",
    )

    progress_by_lesson: Dict[str, Dict[str, Any]] = {}
    if enrollment:
        progress_name = frappe.db.get_value(
            "ELMS Course Progress", {"enrollment": enrollment}, "name"
        )
        if progress_name:
            for row in frappe.get_all(
                "ELMS Lesson Progress",
                filters={"course_progress": progress_name},
                fields=["lesson_id", "is_completed", "time_spent_seconds", "last_heartbeat_at"],
            ):
                progress_by_lesson[row.get("lesson_id")] = row

    for lesson in lessons:
        lesson["progress"] = progress_by_lesson.get(
            lesson["name"],
            {"is_completed": 0, "time_spent_seconds": 0, "last_heartbeat_at": None},
        )

    chapter_data = []
    for chapter in chapters:
        chapter["lessons"] = [lesson for lesson in lessons if lesson.get("chapter") == chapter["name"]]
        chapter_data.append(chapter)
    ungrouped = [lesson for lesson in lessons if not lesson.get("chapter")]
    if ungrouped:
        chapter_data.insert(
            0,
            {"name": "__ungrouped__", "chapter_name": _("Без раздела"), "sequence_id": 0, "lessons": ungrouped},
        )

    return {
        "course": _doc_data(
            course_doc,
            [
                "name", "course_name", "course_code", "category", "academic_hours",
                "is_published", "passing_percentage", "short_description", "description",
            ],
        ),
        "chapters": chapter_data,
        "lesson_count": len(lessons),
    }


def _editor_course_fields() -> List[str]:
    return [
        "name", "course_name", "course_code", "category", "academic_hours",
        "is_published", "passing_percentage", "short_description", "description",
    ]


def _editor_payload(value: Any) -> Dict[str, Any]:
    payload = _json_value(value, {})
    if not isinstance(payload, dict):
        frappe.throw(_("Course draft must be an object"), frappe.ValidationError)
    return payload


def _assert_editor_child(doctype: str, name: Optional[str], course: str) -> None:
    if not name:
        return
    if not frappe.db.exists(doctype, name):
        frappe.throw(_("{0} {1} not found").format(doctype, name), frappe.DoesNotExistError)
    owner = frappe.db.get_value(doctype, name, "course")
    if owner != course:
        frappe.throw(_("{0} does not belong to this course").format(doctype), frappe.ValidationError)


def _delete_editor_child(doctype: str, name: str, course: str) -> None:
    _assert_editor_child(doctype, name, course)
    if doctype == "ELMS Course Lesson" and frappe.db.exists(
        "ELMS Lesson Progress", {"lesson_id": name}
    ):
        frappe.throw(
            _("A lesson with recorded progress cannot be removed"),
            frappe.ValidationError,
        )
    doc = frappe.get_doc(doctype, name)
    if hasattr(doc, "delete"):
        doc.delete()


@frappe.whitelist()
def get_course_editor_data(course: Optional[str] = None) -> Dict[str, Any]:
    """Return one course and its nested authoring outline for Course Studio."""
    _require_learning_manager()
    if not course:
        return {"course": None, "chapters": [], "quizzes": []}
    if not frappe.db.exists("ELMS Course", course):
        frappe.throw(_("Course {0} not found").format(course), frappe.DoesNotExistError)

    course_doc = frappe.get_doc("ELMS Course", course)
    chapters = frappe.get_all(
        "ELMS Course Chapter",
        filters={"course": course},
        fields=["name", "chapter_name", "sequence_id", "description"],
        order_by="sequence_id asc, modified asc",
    )
    lessons = frappe.get_all(
        "ELMS Course Lesson",
        filters={"course": course},
        fields=[
            "name", "lesson_name", "chapter", "sequence_id", "content_type",
            "duration_minutes", "minimum_time_seconds", "is_mandatory", "video_url", "body",
        ],
        order_by="sequence_id asc, modified asc",
    )
    quizzes = frappe.get_all(
        "ELMS Quiz",
        filters={"course": course},
        fields=["name", "quiz_name", "lesson", "quiz_type", "passing_percentage", "is_published"],
        order_by="modified desc, name asc",
    )
    quiz_by_lesson = {quiz.get("lesson"): quiz.get("name") for quiz in quizzes if quiz.get("lesson")}
    for lesson in lessons:
        lesson["quiz"] = quiz_by_lesson.get(lesson.get("name"))

    chapter_data = []
    for chapter in chapters:
        chapter["lessons"] = [
            lesson for lesson in lessons if lesson.get("chapter") == chapter.get("name")
        ]
        chapter_data.append(chapter)
    ungrouped = [lesson for lesson in lessons if not lesson.get("chapter")]
    if ungrouped:
        chapter_data.insert(
            0,
            {
                "name": "__ungrouped__",
                "chapter_name": _("Без раздела"),
                "sequence_id": 0,
                "description": "",
                "virtual": 1,
                "lessons": ungrouped,
            },
        )

    return {
        "course": _doc_data(course_doc, _editor_course_fields()),
        "chapters": chapter_data,
        "quizzes": quizzes,
    }


@frappe.whitelist()
def save_course_draft(payload: Any) -> Dict[str, Any]:
    """Persist the complete Course Studio outline in one management request."""
    _require_learning_manager()
    draft = _editor_payload(payload)
    course_values = draft.get("course")
    if not isinstance(course_values, dict) or not str(course_values.get("course_name") or "").strip():
        frappe.throw(_("Course name is required"), frappe.ValidationError)

    chapter_payload = draft.get("chapters") or []
    if not isinstance(chapter_payload, list):
        frappe.throw(_("Course chapters must be a list"), frappe.ValidationError)

    course_name = course_values.get("name")
    course_record = _save_doc(
        "ELMS Course",
        course_name,
        {
            "course_name": str(course_values.get("course_name")).strip(),
            "course_code": str(course_values.get("course_code") or "").strip(),
            "category": course_values.get("category") or "",
            "academic_hours": max(0, _as_int(course_values.get("academic_hours"))),
            "is_published": 1 if str(course_values.get("is_published")).lower() in ("1", "true", "yes", "on") else 0,
            "passing_percentage": max(0, min(100, _as_float(course_values.get("passing_percentage"), 80))),
            "short_description": course_values.get("short_description") or "",
            "description": course_values.get("description") or "",
        },
    )
    course_name = course_record.get("name")
    if not course_name:
        frappe.throw(_("Course could not be saved"), frappe.ValidationError)

    saved_lessons = 0
    for chapter_index, chapter_values in enumerate(chapter_payload, start=1):
        if not isinstance(chapter_values, dict):
            frappe.throw(_("Each chapter must be an object"), frappe.ValidationError)
        chapter_id = chapter_values.get("name")
        if chapter_id == "__ungrouped__":
            chapter_id = None
        _assert_editor_child("ELMS Course Chapter", chapter_id, course_name)
        chapter_record = _save_doc(
            "ELMS Course Chapter",
            chapter_id,
            {
                "chapter_name": str(chapter_values.get("chapter_name") or f"Раздел {chapter_index}").strip(),
                "course": course_name,
                "sequence_id": chapter_index,
                "description": chapter_values.get("description") or "",
            },
        )
        chapter_name = chapter_record.get("name")
        lessons = chapter_values.get("lessons") or []
        if not isinstance(lessons, list):
            frappe.throw(_("Chapter lessons must be a list"), frappe.ValidationError)
        for lesson_index, lesson_values in enumerate(lessons, start=1):
            if not isinstance(lesson_values, dict):
                frappe.throw(_("Each lesson must be an object"), frappe.ValidationError)
            lesson_id = lesson_values.get("name")
            _assert_editor_child("ELMS Course Lesson", lesson_id, course_name)
            lesson_record = _save_doc(
                "ELMS Course Lesson",
                lesson_id,
                {
                    "lesson_name": str(lesson_values.get("lesson_name") or f"Урок {lesson_index}").strip(),
                    "course": course_name,
                    "chapter": chapter_name,
                    "sequence_id": lesson_index,
                    "content_type": lesson_values.get("content_type") or "Article",
                    "duration_minutes": max(0, _as_int(lesson_values.get("duration_minutes"), 15)),
                    "minimum_time_seconds": max(0, _as_int(lesson_values.get("minimum_time_seconds"), 180)),
                    "is_mandatory": 1 if str(lesson_values.get("is_mandatory", 1)).lower() in ("1", "true", "yes", "on") else 0,
                    "video_url": lesson_values.get("video_url") or "",
                    "body": lesson_values.get("body") or "",
                },
            )
            saved_lessons += 1
            quiz_name = lesson_values.get("quiz")
            if quiz_name:
                if not frappe.db.exists("ELMS Quiz", quiz_name):
                    frappe.throw(_("Quiz {0} not found").format(quiz_name), frappe.DoesNotExistError)
                quiz_course = frappe.db.get_value("ELMS Quiz", quiz_name, "course")
                if quiz_course != course_name:
                    frappe.throw(_("Quiz does not belong to this course"), frappe.ValidationError)
                _save_doc("ELMS Quiz", quiz_name, {"course": course_name, "lesson": lesson_record.get("name")})

    if course_values.get("is_published") and saved_lessons == 0:
        frappe.throw(_("A published course must contain at least one lesson"), frappe.ValidationError)

    for lesson_id in draft.get("deleted_lessons") or []:
        _delete_editor_child("ELMS Course Lesson", lesson_id, course_name)
    for chapter_id in draft.get("deleted_chapters") or []:
        _delete_editor_child("ELMS Course Chapter", chapter_id, course_name)

    return get_course_editor_data(course_name)


def _record_user_activity(
    user: str,
    activity_type: str,
    reference_doctype: Optional[str] = None,
    reference_name: Optional[str] = None,
) -> None:
    """Record an immutable activity log entry adhering to 152-FZ audit requirements."""
    try:
        activity = frappe.new_doc("ELMS User Activity")
        activity.user = user
        activity.activity_type = activity_type
        activity.reference_doctype = reference_doctype or ""
        activity.reference_name = reference_name or ""
        activity.ip_address = getattr(frappe.local, "request_ip", "127.0.0.1") if hasattr(frappe, "local") else "127.0.0.1"
        activity.timestamp = _now_datetime()
        activity.flags.ignore_permissions = True
        activity.insert()
    except Exception:
        # Telemetry recording must never break primary transaction
        pass


@frappe.whitelist()
def enroll_learner(
    user: str,
    batch: str,
    subscription: Optional[str] = None,
    program_enrollment: Optional[str] = None,
) -> Dict[str, Any]:
    """Enroll a learner into an active batch with subscription quota enforcement."""
    session_user = _get_current_user()
    if session_user == "Guest":
        frappe.throw(_("Authentication required to enroll learners"), frappe.PermissionError)

    # Permission check: ELMS Admin or ELMS Operations User can enroll learners
    if not (_has_role("ELMS Admin") or _has_role("ELMS Operations User") or session_user == user):
        frappe.throw(_("Permission denied to enroll learner"), frappe.PermissionError)

    # Validate User exists
    if not frappe.db.exists("User", user):
        frappe.throw(_("User {0} does not exist").format(user), frappe.DoesNotExistError)

    # Validate Batch exists
    if not frappe.db.exists("ELMS Batch", batch):
        frappe.throw(_("Batch {0} does not exist").format(batch), frappe.DoesNotExistError)

    # Prevent duplicate active enrollment
    existing = frappe.db.get_value(
        "ELMS Enrollment",
        {"user": user, "batch": batch, "status": "Active"},
        "name",
    )
    if existing:
        frappe.throw(
            _("User {0} is already enrolled in batch {1}").format(user, batch),
            frappe.ValidationError,
        )

    # Quota validation if subscription is provided
    if subscription:
        if not frappe.db.exists("ELMS Subscription", subscription):
            frappe.throw(_("Subscription {0} does not exist").format(subscription), frappe.DoesNotExistError)

        sub_doc = frappe.get_doc("ELMS Subscription", subscription)
        if sub_doc.status != "Active":
            frappe.throw(_("Subscription {0} is not active ({1})").format(subscription, sub_doc.status), frappe.ValidationError)

        if sub_doc.seats_used >= sub_doc.total_seats:
            frappe.throw(
                _("Subscription {0} quota exhausted ({1}/{2} seats used)").format(
                    subscription, sub_doc.seats_used, sub_doc.total_seats
                ),
                frappe.ValidationError,
            )

        # Decrement available quota by incrementing seats_used
        sub_doc.seats_used += 1
        if sub_doc.seats_used >= sub_doc.total_seats:
            sub_doc.status = "Exhausted"
        sub_doc.flags.ignore_permissions = True
        sub_doc.save()

    # Create Enrollment
    batch_course = frappe.db.get_value("ELMS Batch", batch, "course")
    enrollment = frappe.new_doc("ELMS Enrollment")
    enrollment.user = user
    enrollment.batch = batch
    enrollment.course = batch_course or ""
    enrollment.program_enrollment = program_enrollment or ""
    enrollment.subscription = subscription or ""
    enrollment.enrollment_date = _today()
    enrollment.status = "Active"
    enrollment.flags.from_lms_api = True
    enrollment.flags.ignore_permissions = True
    enrollment.insert()

    # Initialize Course Progress
    progress = frappe.new_doc("ELMS Course Progress")
    progress.enrollment = enrollment.name
    progress.user = user
    progress.progress_percentage = 0.0
    progress.total_lessons = 0
    progress.completed_lessons = 0
    progress.total_time_spent_seconds = 0
    progress.exam_eligible = 0
    progress.flags.ignore_permissions = True
    progress.insert()

    # Record telemetry activity
    _record_user_activity(session_user, "Enrollment", "ELMS Enrollment", enrollment.name)

    return {
        "enrollment": enrollment.name,
        "status": enrollment.status,
        "course_progress": progress.name,
    }


@frappe.whitelist()
def save_course(
    name: Optional[str] = None,
    course_name: str = "",
    course_code: str = "",
    category: str = "",
    academic_hours: Any = 0,
    is_published: Any = 0,
    passing_percentage: Any = 80,
    short_description: str = "",
    description: str = "",
) -> Dict[str, Any]:
    """Create or update a course from the learning management surface."""
    if not str(course_name or "").strip():
        frappe.throw(_("Course name is required"), frappe.ValidationError)
    return _save_doc(
        "ELMS Course",
        name,
        {
            "course_name": str(course_name).strip(),
            "course_code": str(course_code or "").strip(),
            "category": category,
            "academic_hours": max(0, _as_int(academic_hours)),
            "is_published": 1 if str(is_published).lower() in ("1", "true", "yes", "on") else 0,
            "passing_percentage": max(0, min(100, _as_float(passing_percentage, 80))),
            "short_description": short_description,
            "description": description,
        },
    )


@frappe.whitelist()
def save_chapter(
    name: Optional[str] = None,
    chapter_name: str = "",
    course: str = "",
    sequence_id: Any = 1,
    description: str = "",
) -> Dict[str, Any]:
    """Create or update a course chapter."""
    if not str(chapter_name or "").strip() or not course:
        frappe.throw(_("Chapter name and course are required"), frappe.ValidationError)
    if not frappe.db.exists("ELMS Course", course):
        frappe.throw(_("Course {0} not found").format(course), frappe.DoesNotExistError)
    return _save_doc(
        "ELMS Course Chapter",
        name,
        {
            "chapter_name": str(chapter_name).strip(),
            "course": course,
            "sequence_id": max(1, _as_int(sequence_id, 1)),
            "description": description,
        },
    )


@frappe.whitelist()
def save_lesson(
    name: Optional[str] = None,
    lesson_name: str = "",
    course: str = "",
    chapter: str = "",
    sequence_id: Any = 1,
    content_type: str = "Article",
    duration_minutes: Any = 15,
    minimum_time_seconds: Any = 180,
    is_mandatory: Any = 1,
    video_url: str = "",
    body: str = "",
) -> Dict[str, Any]:
    """Create or update a lesson, including article/video material."""
    if not str(lesson_name or "").strip() or not course:
        frappe.throw(_("Lesson name and course are required"), frappe.ValidationError)
    if not frappe.db.exists("ELMS Course", course):
        frappe.throw(_("Course {0} not found").format(course), frappe.DoesNotExistError)
    if chapter and not frappe.db.exists("ELMS Course Chapter", chapter):
        frappe.throw(_("Chapter {0} not found").format(chapter), frappe.DoesNotExistError)
    if content_type not in ("Article", "Video", "Quiz"):
        frappe.throw(_("Unsupported lesson content type"), frappe.ValidationError)
    return _save_doc(
        "ELMS Course Lesson",
        name,
        {
            "lesson_name": str(lesson_name).strip(),
            "course": course,
            "chapter": chapter,
            "sequence_id": max(1, _as_int(sequence_id, 1)),
            "content_type": content_type,
            "duration_minutes": max(0, _as_int(duration_minutes, 15)),
            "minimum_time_seconds": max(0, _as_int(minimum_time_seconds, 180)),
            "is_mandatory": 1 if str(is_mandatory).lower() in ("1", "true", "yes", "on") else 0,
            "video_url": video_url,
            "body": body,
        },
    )


@frappe.whitelist()
def save_batch(
    name: Optional[str] = None,
    batch_name: str = "",
    course: str = "",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    instructor: Optional[str] = None,
    organization: str = "",
    order_number: str = "",
    status: str = "Planning",
) -> Dict[str, Any]:
    """Create or update a cohort with a real course and calendar."""
    if not str(batch_name or "").strip() or not course or not start_date or not end_date:
        frappe.throw(_("Batch, course, start date and end date are required"), frappe.ValidationError)
    if not frappe.db.exists("ELMS Course", course):
        frappe.throw(_("Course {0} not found").format(course), frappe.DoesNotExistError)
    if status not in ("Planning", "Active", "Completed", "Cancelled"):
        frappe.throw(_("Unsupported batch status"), frappe.ValidationError)
    return _save_doc(
        "ELMS Batch",
        name,
        {
            "batch_name": str(batch_name).strip(),
            "course": course,
            "start_date": start_date,
            "end_date": end_date,
            "instructor": instructor,
            "organization": organization,
            "order_number": order_number,
            "status": status,
        },
    )


@frappe.whitelist()
def save_subscription(
    name: Optional[str] = None,
    company_name: str = "",
    inn: str = "",
    course: Optional[str] = None,
    contract_number: str = "",
    total_seats: Any = 1,
    valid_from: Optional[str] = None,
    valid_to: Optional[str] = None,
    status: str = "Active",
) -> Dict[str, Any]:
    """Create or update a contractual subscription/quota."""
    seats = _as_int(total_seats, 1)
    if not str(company_name or "").strip() or not str(inn or "").strip() or seats < 1:
        frappe.throw(_("Company, INN and at least one seat are required"), frappe.ValidationError)
    if course and not frappe.db.exists("ELMS Course", course):
        frappe.throw(_("Course {0} not found").format(course), frappe.DoesNotExistError)
    if status not in ("Active", "Expired", "Exhausted"):
        frappe.throw(_("Unsupported subscription status"), frappe.ValidationError)
    return _save_doc(
        "ELMS Subscription",
        name,
        {
            "company_name": str(company_name).strip(),
            "inn": str(inn).strip(),
            "course": course,
            "contract_number": contract_number,
            "total_seats": seats,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "status": status,
        },
    )


@frappe.whitelist()
def get_course_structure(course: str, enrollment: Optional[str] = None) -> Dict[str, Any]:
    """Return persisted chapters, lessons and learner progress for the player."""
    user = _require_authenticated()
    if enrollment:
        enrollment_user = frappe.db.get_value("ELMS Enrollment", enrollment, "user")
        if enrollment_user != user and not _is_learning_manager(user):
            frappe.throw(_("Access denied"), frappe.PermissionError)
    elif not _can_preview_courses(user):
        published = frappe.db.get_value("ELMS Course", course, "is_published")
        if not published:
            frappe.throw(_("This course is not published"), frappe.PermissionError)
    _record_user_activity(user, "Course View", "ELMS Course", course)
    return _course_structure(course, enrollment)


@frappe.whitelist()
def get_learning_admin_data() -> Dict[str, Any]:
    """Return catalogue and operational queues for the manager tab."""
    user = _require_authenticated()
    manager = _is_learning_manager(user)
    result: Dict[str, Any] = {"authenticated": True, "user": user, "can_manage": manager}
    if not manager:
        return result

    result["courses"] = frappe.get_all(
        "ELMS Course",
        fields=["name", "course_name", "course_code", "category", "academic_hours", "is_published", "modified"],
        order_by="modified desc",
        limit_page_length=200,
    )
    result["batches"] = frappe.get_all(
        "ELMS Batch",
        fields=["name", "batch_name", "course", "course_name", "start_date", "end_date", "status", "instructor"],
        order_by="start_date desc",
        limit_page_length=200,
    )
    result["subscriptions"] = frappe.get_all(
        "ELMS Subscription",
        fields=["name", "company_name", "inn", "course", "contract_number", "total_seats", "seats_used", "valid_to", "status"],
        order_by="modified desc",
        limit_page_length=200,
    )
    result["enrollments"] = frappe.get_all(
        "ELMS Enrollment",
        fields=["name", "user", "batch", "course", "subscription", "enrollment_date", "status"],
        order_by="modified desc",
        limit_page_length=200,
    )
    result["quizzes"] = frappe.get_all(
        "ELMS Quiz",
        fields=["name", "quiz_name", "course", "quiz_type", "passing_percentage", "is_published"],
        order_by="modified desc",
        limit_page_length=200,
    )
    result["programs"] = frappe.get_all(
        "ELMS Program",
        fields=["name", "program_name", "program_code", "category", "total_hours", "is_published"],
        order_by="modified desc",
        limit_page_length=200,
    )
    result["users"] = frappe.get_all(
        "User",
        filters={"enabled": 1},
        fields=["name", "full_name", "email"],
        order_by="full_name asc",
        limit_page_length=500,
    )
    return result


def _relationship_text(value: Any) -> str:
    return str(value or "").casefold().strip()


def _relationship_matches(query: str, values: List[Any]) -> bool:
    needle = _relationship_text(query)
    return not needle or any(needle in _relationship_text(value) for value in values)


@frappe.whitelist()
def get_learning_relationships(
    search: str = "",
    entity_type: str = "",
    course: str = "",
    batch: str = "",
    user: str = "",
) -> Dict[str, Any]:
    """Return LMS records grouped by their course root and searchable by relationship labels."""
    _require_learning_manager()
    courses = frappe.get_all(
        "ELMS Course",
        fields=["name", "course_name", "course_code", "category", "academic_hours", "is_published"],
        order_by="modified desc",
        limit_page_length=500,
    )
    batches = frappe.get_all(
        "ELMS Batch",
        fields=["name", "batch_name", "course", "course_name", "start_date", "end_date", "status", "instructor"],
        order_by="start_date desc, modified desc",
        limit_page_length=500,
    )
    subscriptions = frappe.get_all(
        "ELMS Subscription",
        fields=["name", "company_name", "inn", "course", "contract_number", "total_seats", "seats_used", "valid_to", "status"],
        order_by="modified desc",
        limit_page_length=500,
    )
    enrollments = frappe.get_all(
        "ELMS Enrollment",
        fields=["name", "user", "batch", "course", "subscription", "enrollment_date", "status"],
        order_by="modified desc",
        limit_page_length=1000,
    )
    chapters = frappe.get_all(
        "ELMS Course Chapter",
        fields=["name", "chapter_name", "course", "sequence_id"],
        order_by="sequence_id asc, modified asc",
        limit_page_length=1000,
    )
    lessons = frappe.get_all(
        "ELMS Course Lesson",
        fields=["name", "lesson_name", "course", "chapter", "sequence_id", "content_type"],
        order_by="sequence_id asc, modified asc",
        limit_page_length=2000,
    )
    quizzes = frappe.get_all(
        "ELMS Quiz",
        fields=["name", "quiz_name", "course", "lesson", "quiz_type", "is_published"],
        order_by="modified desc",
        limit_page_length=1000,
    )
    program_courses = frappe.get_all(
        "ELMS Program Course",
        fields=["name", "program", "course", "sequence_id", "is_mandatory"],
        order_by="sequence_id asc, modified asc",
        limit_page_length=1000,
    )
    programs = frappe.get_all(
        "ELMS Program",
        fields=["name", "program_name", "program_code", "category", "is_published"],
        order_by="modified desc",
        limit_page_length=500,
    )
    users = frappe.get_all(
        "User",
        fields=["name", "full_name", "email"],
        limit_page_length=1000,
    )

    user_by_name = {row.get("name"): row for row in users}
    program_by_name = {row.get("name"): row for row in programs}
    allowed_types = {
        "course", "program", "batch", "subscription", "enrollment", "chapter", "lesson", "quiz", "user"
    }
    selected_type = _relationship_text(entity_type)
    if selected_type and selected_type not in allowed_types:
        frappe.throw(_("Unknown relationship entity type: {0}").format(entity_type), frappe.ValidationError)

    def entity(entity_kind: str, doctype: str, row: Dict[str, Any], title: Any, meta: Any) -> Dict[str, Any]:
        return {
            "type": entity_kind,
            "doctype": doctype,
            "name": row.get("name"),
            "title": title or row.get("name"),
            "meta": meta or "",
        }

    groups: List[Dict[str, Any]] = []
    for course_row in courses:
        course_name = course_row.get("name")
        related_batches = [row for row in batches if row.get("course") == course_name]
        related_subscriptions = [row for row in subscriptions if row.get("course") == course_name]
        related_enrollments = [row for row in enrollments if row.get("course") == course_name]
        related_chapters = [row for row in chapters if row.get("course") == course_name]
        related_lessons = [row for row in lessons if row.get("course") == course_name]
        related_quizzes = [row for row in quizzes if row.get("course") == course_name]
        related_program_courses = [row for row in program_courses if row.get("course") == course_name]
        if course and course not in {course_name, course_row.get("course_name"), course_row.get("course_code")}:
            continue
        if batch and not any(batch in {row.get("name"), row.get("batch_name")} for row in related_batches):
            continue
        if user and not any(user in {row.get("user"), (user_by_name.get(row.get("user"), {}) or {}).get("full_name")} for row in related_enrollments):
            continue

        course_entity = entity("course", "ELMS Course", course_row, course_row.get("course_name"), course_row.get("course_code"))
        batch_entities = [entity("batch", "ELMS Batch", row, row.get("batch_name"), row.get("status")) for row in related_batches]
        subscription_entities = [entity("subscription", "ELMS Subscription", row, row.get("company_name"), row.get("contract_number")) for row in related_subscriptions]
        enrollment_entities = [
            entity(
                "enrollment",
                "ELMS Enrollment",
                row,
                (user_by_name.get(row.get("user"), {}) or {}).get("full_name") or row.get("user"),
                row.get("status"),
            )
            for row in related_enrollments
        ]
        chapter_entities = [
            entity(
                "chapter",
                "ELMS Course Chapter",
                row,
                row.get("chapter_name"),
                f"Раздел {row.get('sequence_id')}",
            )
            for row in related_chapters
        ]
        chapter_title_by_name = {
            item.get("name"): item.get("title")
            for item in chapter_entities
            if item.get("name")
        }
        lesson_entities = []
        for row in related_lessons:
            chapter_name = row.get("chapter")
            chapter_title = chapter_title_by_name.get(chapter_name) or "Без раздела"
            lesson_entity = entity(
                "lesson",
                "ELMS Course Lesson",
                row,
                row.get("lesson_name"),
                f"{row.get('content_type') or 'Урок'} · {chapter_title}",
            )
            lesson_entity["chapter"] = chapter_name or "__ungrouped__"
            lesson_entity["chapter_name"] = chapter_title
            lesson_entities.append(lesson_entity)
        quiz_entities = [entity("quiz", "ELMS Quiz", row, row.get("quiz_name"), row.get("quiz_type")) for row in related_quizzes]
        program_entities = []
        seen_programs = set()
        for program_course in related_program_courses:
            program = program_by_name.get(program_course.get("program")) or {}
            program_name = program.get("name")
            if not program_name or program_name in seen_programs:
                continue
            seen_programs.add(program_name)
            program_entity = entity(
                "program",
                "ELMS Program",
                program,
                program.get("program_name"),
                "Курс {0} · {1}".format(
                    program_course.get("sequence_id") or "—",
                    "обязательный" if program_course.get("is_mandatory") else "дополнительный",
                ),
            )
            program_entity["course_sequence"] = program_course.get("sequence_id")
            program_entity["is_mandatory"] = bool(program_course.get("is_mandatory"))
            program_entity["course_name"] = course_row.get("course_name")
            program_entities.append(program_entity)

        outline = []
        for chapter_entity in chapter_entities:
            chapter_id = chapter_entity.get("name")
            outline.append(
                {
                    "chapter": chapter_entity,
                    "lessons": [
                        lesson
                        for lesson in lesson_entities
                        if lesson.get("chapter") == chapter_id
                    ],
                }
            )
        ungrouped_lessons = [
            lesson for lesson in lesson_entities if lesson.get("chapter") == "__ungrouped__"
        ]
        if ungrouped_lessons:
            outline.append(
                {
                    "chapter": {
                        "type": "chapter",
                        "doctype": "",
                        "name": "__ungrouped__",
                        "title": "Без раздела",
                        "meta": "Уроки без привязки",
                    },
                    "lessons": ungrouped_lessons,
                }
            )

        entity_groups = {
            "course": [course_entity],
            "program": program_entities,
            "batch": batch_entities,
            "subscription": subscription_entities,
            "enrollment": enrollment_entities,
            "chapter": chapter_entities,
            "lesson": lesson_entities,
            "quiz": quiz_entities,
        }
        matches = [
            item
            for kind, items in entity_groups.items()
            if not selected_type or kind == selected_type
            for item in items
            if _relationship_matches(search, [item.get("name"), item.get("title"), item.get("meta")])
        ]
        if selected_type == "user":
            matches = [
                entity("user", "User", user_by_name.get(row.get("user"), {"name": row.get("user")}),
                       (user_by_name.get(row.get("user"), {}) or {}).get("full_name") or row.get("user"), row.get("status"))
                for row in related_enrollments
                if _relationship_matches(search, [row.get("user"), (user_by_name.get(row.get("user"), {}) or {}).get("full_name"), (user_by_name.get(row.get("user"), {}) or {}).get("email")])
            ]
        if not selected_type and search and not matches:
            continue
        if selected_type and not matches:
            continue

        groups.append({
            "course": course_row,
            "matches": matches,
            "programs": program_entities,
            "batches": batch_entities,
            "subscriptions": subscription_entities,
            "enrollments": enrollment_entities,
            "chapters": chapter_entities,
            "lessons": lesson_entities,
            "outline": outline,
            "quizzes": quiz_entities,
            "counts": {kind: len(items) for kind, items in entity_groups.items()},
        })

    return {"search": search or "", "entity_type": selected_type, "groups": groups}


@frappe.whitelist()
def get_course_preview_catalog() -> Dict[str, Any]:
    """Return courses that an author may inspect in the learner preview."""
    user = _require_authenticated()
    if not _can_preview_courses(user):
        frappe.throw(_("Course preview requires an ELMS Instructor, ELMS Methodologist or ELMS Admin role"), frappe.PermissionError)
    filters = {} if _is_learning_manager(user) else {"is_published": 1}
    return {
        "user": user,
        "courses": frappe.get_all(
            "ELMS Course",
            filters=filters,
            fields=[
                "name", "course_name", "course_code", "category", "academic_hours",
                "is_published", "short_description", "description",
            ],
            order_by="modified desc",
            limit_page_length=200,
        ),
    }


def _json_value(value: Any, default: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value or "")
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def _quiz_questions(quiz: str) -> List[Dict[str, Any]]:
    questions = frappe.get_all(
        "ELMS Quiz Question",
        filters={"quiz": quiz},
        fields=["name", "question_text", "sequence_id", "question_type", "options_json", "points", "topic", "explanation"],
        order_by="sequence_id asc, name asc",
    )
    normalized = []
    for question in questions:
        options = _json_value(question.get("options_json"), [])
        if not isinstance(options, list) or not options:
            frappe.throw(_("Question {0} has invalid options").format(question.get("name")), frappe.ValidationError)
        normalized.append(
            {
                "name": question.get("name"),
                "question_text": question.get("question_text"),
                "sequence_id": question.get("sequence_id"),
                "question_type": question.get("question_type") or "Single Choice",
                "options": options,
                "points": max(1, _as_int(question.get("points"), 1)),
                "topic": question.get("topic") or "Общие вопросы",
                "explanation": question.get("explanation") or "",
            }
        )
    if not normalized:
        frappe.throw(_("Quiz has no questions"), frappe.ValidationError)
    return normalized


def _quiz_public_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "name": question["name"],
            "question_text": question["question_text"],
            "sequence_id": question["sequence_id"],
            "question_type": question["question_type"],
            "options": [
                {"id": option.get("id"), "text": option.get("text")}
                for option in question["options"]
            ],
            "points": question["points"],
            "topic": question["topic"],
        }
        for question in questions
    ]


def _require_enrollment_access(enrollment: str, user: str) -> Dict[str, Any]:
    enrollment_data = frappe.db.get_value(
        "ELMS Enrollment", enrollment, ["user", "course", "status"], as_dict=True
    ) or {}
    if not enrollment_data:
        frappe.throw(_("Enrollment {0} not found").format(enrollment), frappe.DoesNotExistError)
    if enrollment_data.get("user") != user and not _is_learning_manager(user):
        frappe.throw(_("Access denied"), frappe.PermissionError)
    if enrollment_data.get("status") != "Active" and not _is_learning_manager(user):
        frappe.throw(_("Enrollment is not active"), frappe.ValidationError)
    return enrollment_data


def _quiz_for_learner(quiz: str, enrollment: str, user: str) -> Dict[str, Any]:
    enrollment_data = _require_enrollment_access(enrollment, user)
    quiz_data = frappe.db.get_value(
        "ELMS Quiz",
        quiz,
        [
            "name", "quiz_name", "course", "lesson", "quiz_type", "passing_percentage",
            "time_limit_minutes", "max_attempts", "instructions", "is_published",
        ],
        as_dict=True,
    ) or {}
    if not quiz_data:
        frappe.throw(_("Quiz {0} not found").format(quiz), frappe.DoesNotExistError)
    if not quiz_data.get("is_published"):
        frappe.throw(_("This quiz is not published"), frappe.PermissionError)
    if quiz_data.get("course") != enrollment_data.get("course"):
        frappe.throw(_("Quiz does not belong to this enrollment"), frappe.ValidationError)
    return quiz_data


@frappe.whitelist()
def get_lesson_quiz(lesson_id: str, enrollment: str) -> Dict[str, Any]:
    """Return a learner-safe quiz payload without correct answers."""
    user = _require_authenticated()
    quiz = frappe.db.get_value(
        "ELMS Quiz", {"lesson": lesson_id, "is_published": 1}, "name"
    )
    if not quiz:
        frappe.throw(_("Published quiz for this lesson was not found"), frappe.DoesNotExistError)
    quiz_data = _quiz_for_learner(quiz, enrollment, user)
    questions = _quiz_questions(quiz)
    return {
        "quiz": {key: quiz_data.get(key) for key in (
            "name", "quiz_name", "quiz_type", "passing_percentage", "time_limit_minutes",
            "max_attempts", "instructions",
        )},
        "questions": _quiz_public_questions(questions),
    }


@frappe.whitelist()
def start_quiz(quiz: str, enrollment: str) -> Dict[str, Any]:
    """Create a server-side attempt and freeze its question snapshot."""
    user = _require_authenticated()
    quiz_data = _quiz_for_learner(quiz, enrollment, user)
    questions = _quiz_questions(quiz)
    active_attempt = frappe.db.get_value(
        "ELMS Quiz Attempt",
        {"quiz": quiz, "enrollment": enrollment, "status": "In Progress"},
        "name",
    )
    if active_attempt:
        frappe.throw(_("An attempt is already in progress"), frappe.ValidationError)

    statuses = ["In Progress", "Passed", "Failed"]
    used_attempts = len(
        frappe.get_all(
            "ELMS Quiz Attempt",
            filters={"quiz": quiz, "enrollment": enrollment, "status": ["in", statuses]},
            fields=["name"],
        )
    )
    max_attempts = _as_int(quiz_data.get("max_attempts"), 0)
    if max_attempts and used_attempts >= max_attempts:
        frappe.throw(_("No attempts remaining"), frappe.ValidationError)

    started_at = _now_datetime()
    time_limit = max(0, _as_int(quiz_data.get("time_limit_minutes"), 0))
    deadline_at = started_at + timedelta(minutes=time_limit) if time_limit else None
    attempt = frappe.new_doc("ELMS Quiz Attempt")
    attempt.quiz = quiz
    attempt.enrollment = enrollment
    attempt.user = user
    attempt.attempt_number = used_attempts + 1
    attempt.status = "In Progress"
    attempt.started_at = started_at
    attempt.deadline_at = deadline_at
    attempt.answers_json = "{}"
    attempt.snapshot_json = json.dumps(questions, ensure_ascii=False)
    attempt.flags.ignore_permissions = True
    attempt.insert()
    _record_user_activity(user, "Quiz Start", "ELMS Quiz Attempt", attempt.name)
    return {
        "attempt": attempt.name,
        "quiz": quiz_data.get("quiz_name"),
        "quiz_type": quiz_data.get("quiz_type"),
        "passing_percentage": quiz_data.get("passing_percentage"),
        "deadline_at": deadline_at,
        "questions": _quiz_public_questions(questions),
    }


def _complete_quiz_lesson(enrollment: str, lesson_id: str, user: str) -> Dict[str, Any]:
    course_progress_name = frappe.db.get_value(
        "ELMS Course Progress", {"enrollment": enrollment}, "name"
    )
    if not course_progress_name:
        cp = frappe.new_doc("ELMS Course Progress")
        cp.enrollment = enrollment
        cp.user = user
        cp.progress_percentage = 0.0
        cp.total_lessons = 0
        cp.completed_lessons = 0
        cp.total_time_spent_seconds = 0
        cp.exam_eligible = 0
        cp.flags.ignore_permissions = True
        cp.insert()
        course_progress_name = cp.name

    progress_name = frappe.db.get_value(
        "ELMS Lesson Progress",
        {"course_progress": course_progress_name, "lesson_id": lesson_id},
        "name",
    )
    progress = frappe.get_doc("ELMS Lesson Progress", progress_name) if progress_name else frappe.new_doc("ELMS Lesson Progress")
    progress.course_progress = course_progress_name
    progress.lesson_id = lesson_id
    progress.is_completed = 1
    progress.last_heartbeat_at = _now_datetime()
    progress.flags.ignore_permissions = True
    if progress.is_new():
        progress.insert()
    else:
        progress.save()
    return calculate_course_progress(course_progress_name)


@frappe.whitelist()
def submit_quiz(attempt: str, answers: Any) -> Dict[str, Any]:
    """Grade an attempt on the server and complete its lesson when passed."""
    user = _require_authenticated()
    attempt_doc = frappe.get_doc("ELMS Quiz Attempt", attempt)
    if attempt_doc.user != user and not _is_learning_manager(user):
        frappe.throw(_("Access denied"), frappe.PermissionError)
    if attempt_doc.status != "In Progress":
        frappe.throw(_("This attempt is already closed"), frappe.ValidationError)
    if attempt_doc.deadline_at and _now_datetime() > attempt_doc.deadline_at:
        attempt_doc.status = "Abandoned"
        attempt_doc.failure_reason = _("Time limit exceeded")
        attempt_doc.flags.ignore_permissions = True
        attempt_doc.save()
        frappe.throw(_("Quiz time limit exceeded"), frappe.ValidationError)

    questions = _json_value(attempt_doc.snapshot_json, [])
    submitted = _json_value(answers, {})
    if not isinstance(submitted, dict):
        frappe.throw(_("Answers must be a JSON object"), frappe.ValidationError)

    total_points = sum(max(1, _as_int(question.get("points"), 1)) for question in questions)
    earned_points = 0
    results = []
    for question in questions:
        expected = sorted(
            str(option.get("id"))
            for option in question.get("options", [])
            if option.get("correct")
        )
        answer = submitted.get(question.get("name"), [])
        provided = answer if isinstance(answer, list) else [answer]
        provided = sorted(str(value) for value in provided if value is not None and str(value) != "")
        correct = bool(expected) and provided == expected
        if correct:
            earned_points += max(1, _as_int(question.get("points"), 1))
        results.append({
            "question": question.get("name"),
            "topic": question.get("topic") or "Общие вопросы",
            "correct": correct,
            "answered": bool(provided),
        })

    score = round((earned_points / total_points) * 100, 2) if total_points else 0.0
    passing = _as_float(frappe.db.get_value("ELMS Quiz", attempt_doc.quiz, "passing_percentage"), 80)
    passed = score >= passing
    quiz_lesson = frappe.db.get_value("ELMS Quiz", attempt_doc.quiz, "lesson")
    attempt_doc.answers_json = json.dumps(submitted, ensure_ascii=False)
    attempt_doc.result_json = json.dumps(results, ensure_ascii=False)
    attempt_doc.score_percentage = score
    attempt_doc.passed = 1 if passed else 0
    attempt_doc.status = "Passed" if passed else "Failed"
    attempt_doc.submitted_at = _now_datetime()
    attempt_doc.flags.ignore_permissions = True
    attempt_doc.save()
    progress = None
    if passed and quiz_lesson:
        progress = _complete_quiz_lesson(attempt_doc.enrollment, quiz_lesson, user)
    _record_user_activity(user, "Quiz Submit", "ELMS Quiz Attempt", attempt_doc.name)
    quiz_type = frappe.db.get_value("ELMS Quiz", attempt_doc.quiz, "quiz_type")
    client_results = results
    if quiz_type == "Assessment":
        client_results = [{"topic": result["topic"]} for result in results if not result["correct"]]
    return {
        "attempt": attempt_doc.name,
        "status": attempt_doc.status,
        "score_percentage": score,
        "passing_percentage": passing,
        "passed": 1 if passed else 0,
        "results": client_results,
        "course_progress": progress,
    }


@frappe.whitelist()
def get_course_catalog() -> Dict[str, Any]:
    """Return published active batches available to the current learner."""
    user = _require_authenticated()
    batches = frappe.get_all(
        "ELMS Batch",
        filters={"status": "Active"},
        fields=["name", "batch_name", "course", "start_date", "end_date", "organization"],
        order_by="start_date asc, modified asc",
        limit_page_length=200,
    )
    catalog = []
    for batch in batches:
        course = frappe.db.get_value(
            "ELMS Course",
            batch.get("course"),
            [
                "course_name", "course_code", "category", "academic_hours",
                "short_description", "is_published",
            ],
            as_dict=True,
        ) or {}
        if not course.get("is_published"):
            continue
        enrollment = frappe.db.get_value(
            "ELMS Enrollment",
            {"user": user, "batch": batch.get("name"), "status": "Active"},
            "name",
        )
        catalog.append(
            {
                "batch": batch.get("name"),
                "batch_name": batch.get("batch_name"),
                "course": batch.get("course"),
                "course_name": course.get("course_name"),
                "course_code": course.get("course_code"),
                "category": course.get("category"),
                "academic_hours": course.get("academic_hours"),
                "short_description": course.get("short_description"),
                "start_date": batch.get("start_date"),
                "end_date": batch.get("end_date"),
                "organization": batch.get("organization"),
                "enrollment": enrollment,
            }
        )
    return {"user": user, "courses": catalog}


def _program_courses(program: str) -> List[Dict[str, Any]]:
    return frappe.get_all(
        "ELMS Program Course",
        filters={"program": program},
        fields=["name", "course", "sequence_id", "is_mandatory"],
        order_by="sequence_id asc, name asc",
    )


def _program_progress(program_enrollment: str) -> Dict[str, Any]:
    enrollment = frappe.get_doc("ELMS Program Enrollment", program_enrollment)
    memberships = _program_courses(enrollment.program)
    rows = []
    completed = 0
    percentages = []
    current_course = None
    for membership in memberships:
        course = membership.get("course")
        course_progress = frappe.db.get_value(
            "ELMS Enrollment",
            {"program_enrollment": program_enrollment, "course": course, "status": ["in", ["Active", "Completed"]]},
            "name",
        )
        percentage = 0.0
        course_progress_name = None
        if course_progress:
            course_progress_name = frappe.db.get_value(
                "ELMS Course Progress", {"enrollment": course_progress}, "name"
            )
            if course_progress_name:
                percentage = _as_float(
                    frappe.db.get_value("ELMS Course Progress", course_progress_name, "progress_percentage")
                )
        if percentage >= 100:
            completed += 1
        elif current_course is None and membership.get("is_mandatory"):
            current_course = course
        course_data = frappe.db.get_value(
            "ELMS Course", course, ["course_name", "course_code", "academic_hours"], as_dict=True
        ) or {}
        rows.append({
            "course": course,
            "course_name": course_data.get("course_name"),
            "course_code": course_data.get("course_code"),
            "academic_hours": course_data.get("academic_hours"),
            "sequence_id": membership.get("sequence_id"),
            "is_mandatory": membership.get("is_mandatory"),
            "enrollment": course_progress,
            "progress_percentage": percentage,
        })
        percentages.append(percentage)

    overall = round(sum(percentages) / len(percentages), 2) if percentages else 0.0
    enrollment.total_courses = len(memberships)
    enrollment.completed_courses = completed
    enrollment.progress_percentage = overall
    enrollment.current_course = current_course or (memberships[0].get("course") if memberships else None)
    if memberships and completed == len(memberships):
        enrollment.status = "Completed"
    enrollment.flags.ignore_permissions = True
    enrollment.save()
    return {
        "program_enrollment": enrollment.name,
        "program": enrollment.program,
        "status": enrollment.status,
        "total_courses": len(memberships),
        "completed_courses": completed,
        "progress_percentage": overall,
        "current_course": enrollment.current_course,
        "courses": rows,
    }


@frappe.whitelist()
def get_program_catalog() -> Dict[str, Any]:
    """Return published learning paths with their ordered course summaries."""
    user = _require_authenticated()
    programs = frappe.get_all(
        "ELMS Program",
        filters={"is_published": 1},
        fields=["name", "program_name", "program_code", "category", "total_hours", "description", "enforce_course_order"],
        order_by="modified desc",
        limit_page_length=100,
    )
    result = []
    for program in programs:
        program_enrollment = frappe.db.get_value(
            "ELMS Program Enrollment", {"program": program.get("name"), "user": user, "status": ["in", ["Active", "Completed"]]}, "name"
        )
        program["program_enrollment"] = program_enrollment
        program["course_count"] = len(_program_courses(program.get("name")))
        result.append(program)
    return {"user": user, "programs": result}


@frappe.whitelist()
def enroll_program(program: str) -> Dict[str, Any]:
    """Enroll the current learner into a published learning path."""
    user = _require_authenticated()
    program_data = frappe.db.get_value(
        "ELMS Program", program, ["name", "is_published"], as_dict=True
    ) or {}
    if not program_data:
        frappe.throw(_("Program {0} not found").format(program), frappe.DoesNotExistError)
    if not program_data.get("is_published"):
        frappe.throw(_("This program is not published"), frappe.PermissionError)
    existing = frappe.db.get_value(
        "ELMS Program Enrollment", {"program": program, "user": user, "status": "Active"}, "name"
    )
    if existing:
        return _program_progress(existing)

    memberships = _program_courses(program)
    if not memberships:
        frappe.throw(_("Program has no courses"), frappe.ValidationError)
    program_enrollment = frappe.new_doc("ELMS Program Enrollment")
    program_enrollment.program = program
    program_enrollment.user = user
    program_enrollment.enrollment_date = _today()
    program_enrollment.status = "Active"
    program_enrollment.total_courses = len(memberships)
    program_enrollment.completed_courses = 0
    program_enrollment.progress_percentage = 0.0
    program_enrollment.current_course = memberships[0].get("course")
    program_enrollment.flags.ignore_permissions = True
    program_enrollment.insert()
    first_course = _enroll_program_course(program_enrollment.name, memberships[0].get("course"), user)
    progress = _program_progress(program_enrollment.name)
    progress["course_enrollment"] = first_course.get("enrollment") if first_course else None
    _record_user_activity(user, "Program Enrollment", "ELMS Program Enrollment", program_enrollment.name)
    return progress


def _enroll_program_course(program_enrollment: str, course: str, user: str) -> Optional[Dict[str, Any]]:
    batch = frappe.db.get_value(
        "ELMS Batch", {"course": course, "status": "Active"}, "name"
    )
    if not batch:
        return None
    existing = frappe.db.get_value(
        "ELMS Enrollment", {"program_enrollment": program_enrollment, "course": course, "status": "Active"}, "name"
    )
    if existing:
        return {"enrollment": existing}
    existing = frappe.db.get_value(
        "ELMS Enrollment", {"user": user, "course": course, "status": "Active"}, "name"
    )
    if existing:
        enrollment_doc = frappe.get_doc("ELMS Enrollment", existing)
        enrollment_doc.program_enrollment = program_enrollment
        enrollment_doc.flags.ignore_permissions = True
        enrollment_doc.save()
        return {"enrollment": existing}
    return enroll_learner(user=user, batch=batch, program_enrollment=program_enrollment)


@frappe.whitelist()
def enroll_program_course(program_enrollment: str, course: str) -> Dict[str, Any]:
    """Open the next ordered course in a learner's program."""
    user = _require_authenticated()
    program_data = frappe.db.get_value(
        "ELMS Program Enrollment", program_enrollment, ["program", "user", "status"], as_dict=True
    ) or {}
    if not program_data:
        frappe.throw(_("Program enrollment not found"), frappe.DoesNotExistError)
    if program_data.get("user") != user and not _is_learning_manager(user):
        frappe.throw(_("Access denied"), frappe.PermissionError)
    if program_data.get("status") != "Active":
        frappe.throw(_("Program enrollment is not active"), frappe.ValidationError)
    memberships = _program_courses(program_data.get("program"))
    membership = next((item for item in memberships if item.get("course") == course), None)
    if not membership:
        frappe.throw(_("Course is not part of this program"), frappe.ValidationError)
    program = frappe.db.get_value("ELMS Program", program_data.get("program"), "enforce_course_order")
    if program:
        for item in memberships:
            if item.get("sequence_id") >= membership.get("sequence_id"):
                break
            previous_enrollment = frappe.db.get_value(
                "ELMS Enrollment", {"program_enrollment": program_enrollment, "course": item.get("course")}, "name"
            )
            if item.get("is_mandatory") and previous_enrollment:
                previous_progress = frappe.db.get_value(
                    "ELMS Course Progress", {"enrollment": previous_enrollment}, "progress_percentage"
                )
                if _as_float(previous_progress) < 100:
                    frappe.throw(_("Complete the previous course first"), frappe.ValidationError)
    result = _enroll_program_course(program_enrollment, course, user)
    if not result:
        frappe.throw(_("No active batch is available for this course"), frappe.ValidationError)
    return _program_progress(program_enrollment)


@frappe.whitelist()
def get_program_detail(program: str, program_enrollment: Optional[str] = None) -> Dict[str, Any]:
    """Return a learning path and its ordered course progress."""
    user = _require_authenticated()
    published = frappe.db.get_value("ELMS Program", program, "is_published")
    if not published and not _is_learning_manager(user):
        frappe.throw(_("This program is not published"), frappe.PermissionError)
    if not program_enrollment:
        program_enrollment = frappe.db.get_value(
            "ELMS Program Enrollment", {"program": program, "user": user, "status": ["in", ["Active", "Completed"]]}, "name"
        )
    else:
        program_user = frappe.db.get_value("ELMS Program Enrollment", program_enrollment, "user")
        if not program_user:
            frappe.throw(_("Program enrollment not found"), frappe.DoesNotExistError)
        if program_user != user and not _is_learning_manager(user):
            frappe.throw(_("Access denied"), frappe.PermissionError)
    program_data = frappe.db.get_value(
        "ELMS Program", program, ["name", "program_name", "program_code", "category", "total_hours", "description", "enforce_course_order"], as_dict=True
    ) or {}
    progress = _program_progress(program_enrollment) if program_enrollment else None
    return {"program": program_data, "progress": progress, "enrolled": bool(program_enrollment)}


@frappe.whitelist()
def enroll_self(batch: str) -> Dict[str, Any]:
    """Enroll the current learner into a published active batch."""
    user = _require_authenticated()
    if not frappe.db.exists("ELMS Batch", batch):
        frappe.throw(_("Batch {0} does not exist").format(batch), frappe.DoesNotExistError)

    batch_data = frappe.db.get_value(
        "ELMS Batch", batch, ["course", "status"], as_dict=True
    ) or {}
    if batch_data.get("status") != "Active":
        frappe.throw(_("This course is not open for enrollment"), frappe.ValidationError)
    if not frappe.db.get_value("ELMS Course", batch_data.get("course"), "is_published"):
        frappe.throw(_("This course is not published"), frappe.ValidationError)

    result = enroll_learner(user=user, batch=batch)
    _record_user_activity(user, "Self Enrollment", "ELMS Enrollment", result["enrollment"])
    return result


@frappe.whitelist()
def record_lesson_progress(
    enrollment: str,
    lesson_id: str,
    time_spent_delta: int = 0,
    mark_completed: bool = False,
) -> Dict[str, Any]:
    """Record heartbeat time-on-task telemetry and update lesson completion."""
    session_user = _get_current_user()
    if session_user == "Guest":
        frappe.throw(_("Authentication required"), frappe.PermissionError)

    if not frappe.db.exists("ELMS Enrollment", enrollment):
        frappe.throw(_("Enrollment {0} not found").format(enrollment), frappe.DoesNotExistError)

    enr_user = frappe.db.get_value("ELMS Enrollment", enrollment, "user")
    if session_user != enr_user and not _has_role("ELMS Admin"):
        frappe.throw(_("Access denied: cannot update progress for another user"), frappe.PermissionError)

    lesson_course = frappe.db.get_value("ELMS Course Lesson", lesson_id, "course")
    enrollment_course = frappe.db.get_value("ELMS Enrollment", enrollment, "course")
    if not enrollment_course:
        batch_name = frappe.db.get_value("ELMS Enrollment", enrollment, "batch")
        if batch_name:
            enrollment_course = frappe.db.get_value("ELMS Batch", batch_name, "course")
    # Legacy progress records may contain an external lesson identifier. Once a
    # persisted ELMS lesson exists, enforce the course boundary strictly.
    if lesson_course is not None and (
        not enrollment_course or lesson_course != enrollment_course
    ):
        frappe.throw(_("Lesson does not belong to this enrollment"), frappe.ValidationError)

    time_delta = int(time_spent_delta or 0)
    if time_delta < 0:
        frappe.throw(_("Invalid time delta: cannot be negative"), frappe.ValidationError)

    # Anti-cheat guard: heartbeat delta cannot exceed 300 seconds per call
    if time_delta > 300:
        frappe.throw(
            _("Heartbeat interval exceeds allowed limit (max 300 seconds, received {0})").format(time_delta),
            frappe.ValidationError,
        )

    # Retrieve or create course progress
    course_progress_name = frappe.db.get_value("ELMS Course Progress", {"enrollment": enrollment}, "name")
    if not course_progress_name:
        cp = frappe.new_doc("ELMS Course Progress")
        cp.enrollment = enrollment
        cp.user = enr_user
        cp.progress_percentage = 0.0
        cp.total_lessons = 1
        cp.completed_lessons = 0
        cp.total_time_spent_seconds = 0
        cp.exam_eligible = 0
        cp.flags.ignore_permissions = True
        cp.insert()
        course_progress_name = cp.name

    # Retrieve or create lesson progress
    lesson_prog_name = frappe.db.get_value(
        "ELMS Lesson Progress",
        {"course_progress": course_progress_name, "lesson_id": lesson_id},
        "name",
    )

    if lesson_prog_name:
        lp = frappe.get_doc("ELMS Lesson Progress", lesson_prog_name)
    else:
        lp = frappe.new_doc("ELMS Lesson Progress")
        lp.course_progress = course_progress_name
        lp.lesson_id = lesson_id
        lp.time_spent_seconds = 0
        lp.is_completed = 0

    lp.time_spent_seconds = int(lp.time_spent_seconds or 0) + time_delta
    minimum_time = 0
    if lesson_course is not None:
        minimum_time = _as_int(
            frappe.db.get_value("ELMS Course Lesson", lesson_id, "minimum_time_seconds")
        )
    if mark_completed and minimum_time and lp.time_spent_seconds < minimum_time:
        frappe.throw(
            _("Lesson requires at least {0} seconds of active study").format(minimum_time),
            frappe.ValidationError,
        )
    if mark_completed:
        lp.is_completed = 1
    lp.last_heartbeat_at = _now_datetime()
    lp.flags.ignore_permissions = True
    if lp.is_new():
        lp.insert()
    else:
        lp.save()

    # Recalculate summary course progress
    summary = calculate_course_progress(course_progress_name)

    # Log telemetry
    _record_user_activity(session_user, "Heartbeat", "ELMS Lesson Progress", lp.name)

    return {
        "lesson_id": lesson_id,
        "is_completed": lp.is_completed,
        "total_time_spent_seconds": lp.time_spent_seconds,
        "course_progress_percentage": summary["progress_percentage"],
        "exam_eligible": summary["exam_eligible"],
    }


@frappe.whitelist()
def calculate_course_progress(course_progress: str) -> Dict[str, Any]:
    """Calculate overall course progress percentage and update exam eligibility."""
    if not frappe.db.exists("ELMS Course Progress", course_progress):
        frappe.throw(_("Course Progress {0} not found").format(course_progress), frappe.DoesNotExistError)

    cp = frappe.get_doc("ELMS Course Progress", course_progress)
    lesson_progresses = frappe.get_all(
        "ELMS Lesson Progress",
        filters={"course_progress": course_progress},
        fields=["is_completed", "time_spent_seconds"],
    )

    # Once an enrollment is tied to a real course, count the course syllabus,
    # not only lessons that already have a progress row. This prevents a new
    # enrollment from becoming 100% after completing its first lesson.
    course_lessons: List[Dict[str, Any]] = []
    if getattr(cp, "enrollment", None):
        enrollment_course = frappe.db.get_value("ELMS Enrollment", cp.enrollment, "course")
        enrollment_batch = frappe.db.get_value("ELMS Enrollment", cp.enrollment, "batch")
        course = (
            enrollment_course
            if enrollment_course and frappe.db.get_value("ELMS Course", enrollment_course, "name")
            else None
        )
        if not course and enrollment_batch:
            course = frappe.db.get_value("ELMS Batch", enrollment_batch, "course")
        if course:
            course_lessons = frappe.get_all(
                "ELMS Course Lesson",
                filters={"course": course, "is_mandatory": 1},
                fields=["name"],
                order_by="sequence_id asc",
            )

    if course_lessons:
        progress_by_lesson = {row.get("lesson_id"): row for row in lesson_progresses}
        total_lessons = len(course_lessons)
        completed_lessons = sum(
            1
            for lesson in course_lessons
            if progress_by_lesson.get(lesson.get("name"), {}).get("is_completed")
        )
    else:
        total_lessons = len(lesson_progresses)
        completed_lessons = sum(1 for lp in lesson_progresses if lp.get("is_completed"))
    total_time = sum(int(lp.get("time_spent_seconds") or 0) for lp in lesson_progresses)

    percentage = 0.0
    if total_lessons > 0:
        percentage = round((completed_lessons / total_lessons) * 100.0, 2)

    # Exam eligible strictly when 100% of lessons are completed
    exam_eligible = 1 if (percentage >= 100.0 and total_lessons > 0) else 0

    cp.total_lessons = total_lessons
    cp.completed_lessons = completed_lessons
    cp.total_time_spent_seconds = total_time
    cp.progress_percentage = percentage
    cp.exam_eligible = exam_eligible

    if exam_eligible and not cp.completion_date:
        cp.completion_date = _now_datetime()
    elif not exam_eligible:
        cp.completion_date = None

    cp.flags.ignore_permissions = True
    cp.save()

    return {
        "course_progress": cp.name,
        "progress_percentage": cp.progress_percentage,
        "total_lessons": cp.total_lessons,
        "completed_lessons": cp.completed_lessons,
        "total_time_spent_seconds": cp.total_time_spent_seconds,
        "exam_eligible": cp.exam_eligible,
    }


@frappe.whitelist()
def record_video_watch(
    lesson_id: str,
    watched_seconds: int,
    playback_speed: float = 1.0,
) -> Dict[str, Any]:
    """Record verified video watch time compliant with Order 816 requirements."""
    session_user = _get_current_user()
    if session_user == "Guest":
        frappe.throw(_("Authentication required"), frappe.PermissionError)

    seconds = int(watched_seconds or 0)
    if seconds < 0:
        frappe.throw(_("Watched seconds cannot be negative"), frappe.ValidationError)

    speed = float(playback_speed or 1.0)
    if not (0.5 <= speed <= 3.0):
        frappe.throw(_("Playback speed out of bounds (0.5 - 3.0)"), frappe.ValidationError)

    log = frappe.new_doc("ELMS Video Watch Log")
    log.user = session_user
    log.lesson_id = lesson_id
    log.watched_seconds = seconds
    log.playback_speed = speed
    log.verified = 1
    log.flags.ignore_permissions = True
    log.insert()

    _record_user_activity(session_user, "Video Watch", "ELMS Video Watch Log", log.name)

    return {
        "status": "success",
        "log_name": log.name,
        "watched_seconds": seconds,
    }


@frappe.whitelist()
def get_learner_dashboard() -> Dict[str, Any]:
    """Fetch dashboard statistics and active course enrollments for the current learner."""
    session_user = _get_current_user()
    if session_user == "Guest":
        return {"authenticated": False, "courses": []}

    enrollments = frappe.get_all(
        "ELMS Enrollment",
        filters={"user": session_user, "status": "Active"},
        fields=["name", "batch", "enrollment_date", "status"],
    )

    courses_data = []
    for enr in enrollments:
        batch_info = frappe.db.get_value(
            "ELMS Batch", enr.batch, ["batch_name", "course", "course_name"], as_dict=True
        ) or {}
        course_name = batch_info.get("course_name", "")
        if batch_info.get("course"):
            course_name = frappe.db.get_value("ELMS Course", batch_info["course"], "course_name") or course_name
        progress_info = frappe.db.get_value(
            "ELMS Course Progress",
            {"enrollment": enr.name},
            ["name", "progress_percentage", "total_lessons", "completed_lessons", "exam_eligible"],
            as_dict=True,
        ) or {}

        courses_data.append({
            "enrollment": enr.name,
            "batch": enr.batch,
            "batch_name": batch_info.get("batch_name", ""),
            "course": batch_info.get("course", ""),
            "course_name": course_name,
            "course_progress": progress_info.get("name", ""),
            "progress_percentage": progress_info.get("progress_percentage", 0.0),
            "completed_lessons": progress_info.get("completed_lessons", 0),
            "total_lessons": progress_info.get("total_lessons", 0),
            "exam_eligible": progress_info.get("exam_eligible", 0),
        })

    activities = frappe.get_all(
        "ELMS User Activity",
        filters={"user": session_user},
        fields=["name", "activity_type", "reference_doctype", "reference_name", "ip_address", "timestamp"],
        order_by="timestamp desc",
        limit_page_length=50,
    )

    return {
        "authenticated": True,
        "user": session_user,
        "active_enrollments_count": len(courses_data),
        "courses": courses_data,
        "activities": activities,
    }
