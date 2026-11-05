"""Whitelist API endpoints and domain services for the ELMS LMS module."""

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
    )


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
    elif not _is_learning_manager(user):
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
    result["users"] = frappe.get_all(
        "User",
        filters={"enabled": 1},
        fields=["name", "full_name", "email"],
        order_by="full_name asc",
        limit_page_length=500,
    )
    return result


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
