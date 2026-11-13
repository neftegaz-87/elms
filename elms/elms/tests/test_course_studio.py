"""Contract tests for the course-first LMS authoring facade."""

from __future__ import annotations

import unittest
import json
from unittest.mock import MagicMock, patch

import frappe

if not hasattr(frappe, "db"):
	frappe.db = MagicMock()
if not hasattr(frappe, "get_doc"):
	frappe.get_doc = MagicMock()
if not hasattr(frappe, "get_all"):
	frappe.get_all = MagicMock()
if not hasattr(frappe, "ValidationError"):
	class ValidationError(Exception):
		pass
	frappe.ValidationError = ValidationError
if not hasattr(frappe, "PermissionError"):
	class PermissionError(Exception):
		pass
	frappe.PermissionError = PermissionError
if not hasattr(frappe, "DoesNotExistError"):
	class DoesNotExistError(Exception):
		pass
	frappe.DoesNotExistError = DoesNotExistError

import elms.lms.api as lms_api


class TestCourseStudio(unittest.TestCase):
    def test_relationship_search_groups_batch_hit_under_course(self):
        course = [{"name": "COURSE-1", "course_name": "Стропальные работы", "course_code": "STR-2026"}]
        batches = [{"name": "BATCH-1", "batch_name": "Демо-поток 2026 · Стропальные работы", "course": "COURSE-1", "status": "Active"}]
        users = [{"name": "learner@example.ru", "full_name": "Иван Слушатель", "email": "learner@example.ru"}]
        with (
            patch.object(lms_api, "_require_learning_manager", return_value="methodologist@example.ru"),
            patch.object(
                frappe,
                "get_all",
                side_effect=[course, batches, [], [], [], [], [], [], [], users],
            ),
        ):
            result = lms_api.get_learning_relationships(search="Демо-поток 2026 · Стропальные работы")

        self.assertEqual(len(result["groups"]), 1)
        self.assertEqual(result["groups"][0]["course"]["name"], "COURSE-1")
        self.assertEqual(result["groups"][0]["matches"][0]["type"], "batch")
        self.assertEqual(result["groups"][0]["matches"][0]["name"], "BATCH-1")

    def test_relationship_search_rejects_unknown_entity_type(self):
        with (
            patch.object(lms_api, "_require_learning_manager", return_value="methodologist@example.ru"),
            patch.object(frappe, "get_all", return_value=[]),
        ):
            with self.assertRaises(frappe.ValidationError):
                lms_api.get_learning_relationships(entity_type="not-a-lms-entity")

    def test_course_categories_are_returned_for_the_studio_selector(self):
        with (
            patch.object(lms_api, "_require_learning_manager", return_value="methodologist@example.ru"),
            patch.object(
                frappe,
                "get_all",
                return_value=[{"name": "Охрана труда", "category_name": "Охрана труда", "description": ""}],
            ),
        ):
            result = lms_api.get_course_categories()

        self.assertEqual(result["categories"][0]["category_name"], "Охрана труда")

    def test_relationship_search_returns_programs_and_lessons_under_their_chapter(self):
        course = [{"name": "COURSE-1", "course_name": "Стропальные работы", "course_code": "STR-2026"}]
        batches = []
        subscriptions = []
        enrollments = []
        chapters = [
            {"name": "CH-1", "chapter_name": "Подготовка", "course": "COURSE-1", "sequence_id": 1},
            {"name": "CH-2", "chapter_name": "Практика", "course": "COURSE-1", "sequence_id": 2},
        ]
        lessons = [
            {"name": "LESSON-1", "lesson_name": "Проверка строп", "course": "COURSE-1", "chapter": "CH-1", "sequence_id": 1, "content_type": "Article"},
            {"name": "LESSON-2", "lesson_name": "Работа с грузом", "course": "COURSE-1", "chapter": "CH-2", "sequence_id": 1, "content_type": "Video"},
        ]
        quizzes = []
        program_courses = [
            {"name": "PC-1", "program": "PROGRAM-1", "course": "COURSE-1", "sequence_id": 1, "is_mandatory": 1},
            {"name": "PC-2", "program": "PROGRAM-2", "course": "COURSE-1", "sequence_id": 3, "is_mandatory": 0},
        ]
        programs = [
            {"name": "PROGRAM-1", "program_name": "Охрана труда", "program_code": "OT-1"},
            {"name": "PROGRAM-2", "program_name": "Подготовка стропальщиков", "program_code": "STR-2"},
        ]
        users = []
        with (
            patch.object(lms_api, "_require_learning_manager", return_value="methodologist@example.ru"),
            patch.object(
                frappe,
                "get_all",
                side_effect=[course, batches, subscriptions, enrollments, chapters, lessons, quizzes, program_courses, programs, users],
            ),
        ):
            result = lms_api.get_learning_relationships(search="Проверка строп")

        group = result["groups"][0]
        self.assertEqual([item["name"] for item in group["programs"]], ["PROGRAM-1", "PROGRAM-2"])
        self.assertEqual(len(group["outline"]), 2)
        self.assertEqual(group["outline"][0]["chapter"]["title"], "Подготовка")
        self.assertEqual(group["outline"][0]["lessons"][0]["title"], "Проверка строп")
        self.assertEqual(group["outline"][0]["lessons"][0]["chapter_name"], "Подготовка")
        self.assertEqual(group["outline"][1]["lessons"][0]["chapter_name"], "Практика")

    def test_editor_data_is_returned_as_a_nested_outline(self):
        course = {
            "name": "COURSE-1",
            "course_name": "Безопасность",
            "course_code": "SAFE-1",
            "category": "Охрана труда (ПП РФ № 2464)",
            "academic_hours": 40,
            "is_published": 0,
            "passing_percentage": 80,
            "short_description": "Курс",
            "description": "Цели",
        }
        chapters = [{"name": "CH-1", "chapter_name": "Введение", "sequence_id": 1, "description": ""}]
        lessons = [{
            "name": "LESSON-1",
            "lesson_name": "Правила",
            "chapter": "CH-1",
            "sequence_id": 1,
            "content_type": "Article",
            "duration_minutes": 15,
            "minimum_time_seconds": 180,
            "is_mandatory": 1,
            "video_url": "",
            "body": "Текст",
        }]

        with (
            patch.object(lms_api, "_require_learning_manager", return_value="methodologist@example.ru"),
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(frappe, "get_doc", return_value=course),
            patch.object(frappe, "get_all", side_effect=[chapters, lessons, []]),
        ):
            result = lms_api.get_course_editor_data("COURSE-1")

        self.assertEqual(result["course"]["name"], "COURSE-1")
        self.assertEqual(result["chapters"][0]["lessons"][0]["name"], "LESSON-1")
        self.assertEqual(result["chapters"][0]["lessons"][0]["chapter"], "CH-1")

    def test_save_draft_persists_children_in_outline_order(self):
        payload = {
            "course": {"course_name": "Новый курс", "course_code": "NEW-1", "academic_hours": 24},
            "chapters": [
                {
                    "chapter_name": "Раздел 1",
                    "lessons": [
                        {"lesson_name": "Урок 1", "content_type": "Article"},
                        {"lesson_name": "Урок 2", "content_type": "Video"},
                    ],
                },
                {"chapter_name": "Раздел 2", "lessons": []},
            ],
        }
        saved = []

        def save_doc(doctype, name, values):
            saved.append((doctype, name, values.copy()))
            return {"name": f"{doctype}-{len(saved)}", **values}

        with (
            patch.object(lms_api, "_require_learning_manager", return_value="methodologist@example.ru"),
            patch.object(lms_api, "_save_doc", side_effect=save_doc),
            patch.object(lms_api, "_unlink_lesson_quiz", return_value=None),
            patch.object(lms_api, "get_course_editor_data", return_value={"course": {"name": "ELMS Course-1"}}),
        ):
            result = lms_api.save_course_draft(json.dumps(payload))

        self.assertEqual(result["course"]["name"], "ELMS Course-1")
        self.assertEqual(saved[0][0], "ELMS Course")
        self.assertEqual(saved[1][0:2], ("ELMS Course Chapter", None))
        self.assertEqual(saved[1][2]["sequence_id"], 1)
        self.assertEqual(saved[2][2]["chapter"], "ELMS Course Chapter-2")
        self.assertEqual(saved[3][2]["sequence_id"], 2)
        self.assertEqual(saved[4][2]["sequence_id"], 2)

    def test_editor_data_embeds_quiz_draft_with_question_variants(self):
        course = {
            "name": "COURSE-1",
            "course_name": "Безопасность",
            "course_code": "SAFE-1",
            "category": "Охрана труда",
            "academic_hours": 40,
            "is_published": 0,
            "passing_percentage": 80,
            "short_description": "Курс",
            "description": "Цели",
        }
        chapters = [{"name": "CH-1", "chapter_name": "Контроль", "sequence_id": 1, "description": ""}]
        lessons = [{
            "name": "LESSON-Q",
            "lesson_name": "Контрольная",
            "chapter": "CH-1",
            "sequence_id": 1,
            "content_type": "Quiz",
            "duration_minutes": 20,
            "minimum_time_seconds": 0,
            "is_mandatory": 1,
            "video_url": "",
            "body": "",
        }]
        quizzes = [{
            "name": "QUIZ-1",
            "quiz_name": "Тренировка",
            "lesson": "LESSON-Q",
            "quiz_type": "Practice",
            "passing_percentage": 70,
            "time_limit_minutes": 15,
            "max_attempts": 0,
            "is_published": 1,
            "instructions": "Инструкция",
        }]
        questions = [
            {
                "name": "Q1",
                "quiz": "QUIZ-1",
                "question_text": "Один ответ",
                "sequence_id": 1,
                "question_type": "Single Choice",
                "options_json": json.dumps([
                    {"id": "A", "text": "Да", "correct": True},
                    {"id": "B", "text": "Нет", "correct": False},
                ], ensure_ascii=False),
                "points": 1,
                "topic": "Тема",
                "explanation": "Потому что",
            },
            {
                "name": "Q2",
                "quiz": "QUIZ-1",
                "question_text": "Несколько",
                "sequence_id": 2,
                "question_type": "Multiple Choice",
                "options_json": json.dumps([
                    {"id": "A", "text": "A", "correct": True},
                    {"id": "B", "text": "B", "correct": True},
                    {"id": "C", "text": "C", "correct": False},
                ], ensure_ascii=False),
                "points": 2,
                "topic": "Тема",
                "explanation": "",
            },
            {
                "name": "Q3",
                "quiz": "QUIZ-1",
                "question_text": "Верно или нет",
                "sequence_id": 3,
                "question_type": "True/False",
                "options_json": json.dumps([
                    {"id": "A", "text": "Верно", "correct": True},
                    {"id": "B", "text": "Неверно", "correct": False},
                ], ensure_ascii=False),
                "points": 1,
                "topic": "Тема",
                "explanation": "",
            },
        ]

        with (
            patch.object(lms_api, "_require_learning_manager", return_value="methodologist@example.ru"),
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(frappe, "get_doc", return_value=course),
            patch.object(frappe, "get_all", side_effect=[chapters, lessons, quizzes, questions]),
        ):
            result = lms_api.get_course_editor_data("COURSE-1")

        draft = result["chapters"][0]["lessons"][0]["quiz_draft"]
        self.assertEqual(draft["quiz_type"], "Practice")
        self.assertEqual([q["question_type"] for q in draft["questions"]], [
            "Single Choice", "Multiple Choice", "True/False",
        ])
        self.assertTrue(draft["questions"][1]["options"][0]["correct"])
        self.assertTrue(draft["questions"][1]["options"][1]["correct"])

    def test_save_draft_persists_inline_quiz_with_all_question_types(self):
        payload = {
            "course": {"course_name": "Курс с тестом", "course_code": "Q-1"},
            "chapters": [{
                "chapter_name": "Раздел",
                "lessons": [{
                    "lesson_name": "Контроль знаний",
                    "content_type": "Quiz",
                    "quiz_draft": {
                        "quiz_name": "Конструкторный тест",
                        "quiz_type": "Assessment",
                        "passing_percentage": 80,
                        "time_limit_minutes": 10,
                        "max_attempts": 1,
                        "is_published": 1,
                        "instructions": "Ответьте на все вопросы",
                        "questions": [
                            {
                                "question_text": "Один",
                                "question_type": "Single Choice",
                                "points": 1,
                                "options": [
                                    {"id": "A", "text": "Верный", "correct": True},
                                    {"id": "B", "text": "Нет", "correct": False},
                                ],
                            },
                            {
                                "question_text": "Несколько",
                                "question_type": "Multiple Choice",
                                "points": 2,
                                "options": [
                                    {"id": "A", "text": "A", "correct": True},
                                    {"id": "B", "text": "B", "correct": True},
                                    {"id": "C", "text": "C", "correct": False},
                                ],
                            },
                            {
                                "question_text": "Утверждение",
                                "question_type": "True/False",
                                "points": 1,
                                "options": [
                                    {"id": "A", "text": "Верно", "correct": True},
                                    {"id": "B", "text": "Неверно", "correct": False},
                                ],
                            },
                        ],
                        "deleted_questions": [],
                    },
                }],
            }],
        }
        saved = []

        def save_doc(doctype, name, values):
            saved.append((doctype, name, dict(values)))
            return {"name": f"{doctype}-{len(saved)}", **values}

        with (
            patch.object(lms_api, "_require_learning_manager", return_value="methodologist@example.ru"),
            patch.object(lms_api, "_save_doc", side_effect=save_doc),
            patch.object(frappe, "get_all", return_value=[]),
            patch.object(lms_api, "get_course_editor_data", return_value={"course": {"name": "COURSE-Q"}}),
        ):
            lms_api.save_course_draft(payload)

        quiz_saves = [row for row in saved if row[0] == "ELMS Quiz"]
        question_saves = [row for row in saved if row[0] == "ELMS Quiz Question"]
        self.assertEqual(len(quiz_saves), 1)
        self.assertEqual(quiz_saves[0][2]["quiz_type"], "Assessment")
        self.assertEqual(quiz_saves[0][2]["lesson"], "ELMS Course Lesson-3")
        self.assertEqual(len(question_saves), 3)
        self.assertEqual(
            [row[2]["question_type"] for row in question_saves],
            ["Single Choice", "Multiple Choice", "True/False"],
        )
        multi_options = json.loads(question_saves[1][2]["options_json"])
        self.assertEqual([option["correct"] for option in multi_options], [True, True, False])

    def test_save_draft_rejects_quiz_without_correct_option(self):
        payload = {
            "course": {"course_name": "Курс", "course_code": "BAD"},
            "chapters": [{
                "chapter_name": "Раздел",
                "lessons": [{
                    "lesson_name": "Тест",
                    "content_type": "Quiz",
                    "quiz_draft": {
                        "quiz_name": "Битый",
                        "quiz_type": "Practice",
                        "questions": [{
                            "question_text": "Без верного",
                            "question_type": "Single Choice",
                            "options": [
                                {"id": "A", "text": "A", "correct": False},
                                {"id": "B", "text": "B", "correct": False},
                            ],
                        }],
                    },
                }],
            }],
        }

        with (
            patch.object(lms_api, "_require_learning_manager", return_value="methodologist@example.ru"),
            patch.object(lms_api, "_save_doc", side_effect=lambda doctype, name, values: {"name": f"{doctype}-1", **values}),
        ):
            with self.assertRaises(frappe.ValidationError):
                lms_api.save_course_draft(payload)

    def test_save_draft_rejects_child_from_another_course(self):
        payload = {
            "course": {"name": "COURSE-2", "course_name": "Курс 2"},
            "chapters": [{"name": "CH-OTHER", "chapter_name": "Чужой раздел", "lessons": []}],
        }

        with (
            patch.object(lms_api, "_require_learning_manager", return_value="methodologist@example.ru"),
            patch.object(lms_api, "_save_doc", return_value={"name": "COURSE-2"}),
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(frappe.db, "get_value", return_value="COURSE-1"),
        ):
            with self.assertRaises(frappe.ValidationError):
                lms_api.save_course_draft(payload)

    def test_guest_cannot_open_editor(self):
        with patch.object(lms_api, "_require_learning_manager", side_effect=frappe.PermissionError):
            with self.assertRaises(frappe.PermissionError):
                lms_api.get_course_editor_data()


if __name__ == "__main__":
    unittest.main()
