"""Tests for ELMS Learning Desk page, player surface, and anti-cheat telemetry."""

import json
import unittest
from pathlib import Path


class TestLearningUI(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.js_path = self.root / "elms" / "public" / "js" / "desk-learning.js"
        self.css_path = self.root / "elms" / "public" / "css" / "desk-learning.css"
        self.page_js_path = self.root / "elms" / "public" / "js" / "elms-learning-page.js"
        self.preview_page_js_path = self.root / "elms" / "public" / "js" / "elms-course-preview-page.js"
        self.studio_js_path = self.root / "elms" / "public" / "js" / "course-studio.js"
        self.studio_page_js_path = self.root / "elms" / "public" / "js" / "elms-course-studio-page.js"
        self.studio_css_path = self.root / "elms" / "public" / "css" / "course-studio.css"
        self.course_doctype_path = self.root / "elms" / "lms" / "doctype" / "elms_course" / "elms_course.json"
        self.category_doctype_path = self.root / "elms" / "lms" / "doctype" / "elms_course_category" / "elms_course_category.json"
        self.chapter_doctype_path = self.root / "elms" / "lms" / "doctype" / "elms_course_chapter" / "elms_course_chapter.json"
        self.lesson_doctype_path = self.root / "elms" / "lms" / "doctype" / "elms_course_lesson" / "elms_course_lesson.json"
        self.page_json_path = self.root / "elms" / "lms" / "page" / "elms_learning" / "elms_learning.json"
        self.preview_page_json_path = self.root / "elms" / "lms" / "page" / "elms_course_preview" / "elms_course_preview.json"
        self.studio_page_json_path = self.root / "elms" / "lms" / "page" / "elms_course_studio" / "elms_course_studio.json"
        self.hooks_path = self.root / "elms" / "hooks.py"
        self.workspaces_path = self.root / "elms" / "desk" / "workspaces.py"

    def test_learning_assets_exist(self):
        """desk-learning.js and desk-learning.css must exist."""
        self.assertTrue(self.js_path.is_file(), "desk-learning.js must exist")
        self.assertTrue(self.css_path.is_file(), "desk-learning.css must exist")

    def test_learning_assets_registered_in_hooks(self):
        """Assets must be included in app_include_css and app_include_js."""
        content = self.hooks_path.read_text(encoding="utf-8")
        self.assertIn("desk-learning.css", content)
        self.assertIn("desk-learning.js", content)
        self.assertIn("desk-assistant.css", content)
        self.assertIn("desk-assistant.js", content)
        self.assertIn('"elms-learning": "public/js/elms-learning-page.js"', content)
        self.assertIn('"elms-course-preview": "public/js/elms-course-preview-page.js"', content)
        self.assertIn('"elms-course-studio": "public/js/elms-course-studio-page.js"', content)
        self.assertIn("course-studio.css", content)

    def test_learning_direct_route_has_a_frappe_page_bootstrap(self):
        """Direct /app/elms-learning loads through Frappe's Page registry."""
        self.assertTrue(self.page_js_path.is_file(), "learning page bootstrap must exist")
        self.assertTrue(self.page_json_path.is_file(), "learning Page definition must exist")

        page_js = self.page_js_path.read_text(encoding="utf-8")
        page_json = self.page_json_path.read_text(encoding="utf-8")
        self.assertIn('frappe.pages["elms-learning"].on_page_load', page_js)
        self.assertIn('"name": "elms-learning"', page_json)
        self.assertIn('"module": "LMS"', page_json)

    def test_course_preview_direct_route_has_a_frappe_page_definition(self):
        """Direct /app/elms-course-preview must resolve through the Page registry."""
        self.assertTrue(self.preview_page_json_path.is_file(), "course preview Page definition must exist")
        page_json = self.preview_page_json_path.read_text(encoding="utf-8")
        self.assertIn('"name": "elms-course-preview"', page_json)
        self.assertIn('"module": "LMS"', page_json)

    def test_course_preview_direct_route_has_a_page_bootstrap(self):
        self.assertTrue(self.preview_page_js_path.is_file(), "course preview page bootstrap must exist")
        page_js = self.preview_page_js_path.read_text(encoding="utf-8")
        self.assertIn('frappe.pages["elms-course-preview"].on_page_load', page_js)
        self.assertIn("elms.lms.api.get_course_preview_catalog", page_js)
        self.assertIn("elms.lms.api.get_course_structure", page_js)
        self.assertIn("elms-preview-course-grid", page_js)

    def test_course_studio_direct_route_has_page_bootstrap_and_api_contract(self):
        self.assertTrue(self.studio_page_json_path.is_file(), "Course Studio Page definition must exist")
        self.assertTrue(self.studio_page_js_path.is_file(), "Course Studio page bootstrap must exist")
        self.assertTrue(self.studio_js_path.is_file(), "Course Studio asset must exist")
        self.assertTrue(self.studio_css_path.is_file(), "Course Studio CSS must exist")
        page_json = self.studio_page_json_path.read_text(encoding="utf-8")
        page_js = self.studio_page_js_path.read_text(encoding="utf-8")
        studio_js = self.studio_js_path.read_text(encoding="utf-8")
        self.assertIn('"name": "elms-course-studio"', page_json)
        self.assertIn('frappe.pages["elms-course-studio"].on_page_load', page_js)
        self.assertIn('frappe.require("/assets/elms/js/course-studio.js", start)', page_js)
        self.assertNotIn('course-studio.js?v=1', page_js)
        self.assertIn("elms.lms.api.get_course_editor_data", studio_js)
        self.assertIn("elms.lms.api.get_course_categories", studio_js)
        self.assertIn("elms.lms.api.save_course_draft", studio_js)
        self.assertIn("Предпросмотр", studio_js)
        self.assertIn("Сохранить черновик", studio_js)
        self.assertIn("+ Раздел", studio_js)
        self.assertIn("+ Урок", studio_js)
        self.assertIn("+ Добавить категорию", studio_js)
        self.assertIn("ELMS Course Category", studio_js)
        self.assertIn("state.selected = { type: type, id: id || null };\n\t\trender();", studio_js)
        self.assertIn("var title = state.course.course_name || \"Новый курс\";", studio_js)

    def test_learning_css_tokens_and_classes(self):
        """CSS must follow Neftegaz light tokens and define player classes."""
        css = self.css_path.read_text(encoding="utf-8")
        self.assertIn("--elms-action: #0d4cd3;", css)
        self.assertIn("--elms-paper: #f5f7fa;", css)
        self.assertIn(".elms-learning-shell", css)
        self.assertIn(".elms-course-card", css)
        self.assertIn(".elms-player-container", css)
        self.assertIn(".elms-pulse-dot", css)
        self.assertIn(".elms-timer-value", css)

    def test_learning_js_standard_page_and_telemetry(self):
        """JS must register elms-learning page and bind anti-cheat heartbeat."""
        js = self.js_path.read_text(encoding="utf-8")
        self.assertIn('frappe.standard_pages[pageName]', js)
        self.assertIn('<span>elms</span>', js)
        self.assertNotIn('ELMS СДО', js)
        self.assertIn('elms.lms.api.get_learner_dashboard', js)
        self.assertIn('elms.lms.api.get_learning_admin_data', js)
        self.assertIn('elms.lms.api.get_learning_relationships', js)
        self.assertIn('elms.lms.api.get_course_catalog', js)
        self.assertIn('elms.lms.api.enroll_self', js)
        self.assertIn('elms.lms.api.get_lesson_quiz', js)
        self.assertIn('elms.lms.api.start_quiz', js)
        self.assertIn('elms.lms.api.save_quiz_progress', js)
        self.assertIn('elms.lms.api.submit_quiz', js)
        self.assertIn('elms.lms.api.get_learner_profile', js)
        self.assertIn('elms.lms.api.get_program_catalog', js)
        self.assertIn('elms.lms.api.enroll_program', js)
        self.assertIn('Программы обучения', js)
        self.assertIn('Записаться на курс', js)
        self.assertIn('Каталог курсов', js)
        self.assertIn('Начать тест', js)
        self.assertIn('Сохранить прогресс', js)
        self.assertIn('Отвечено:', js)
        self.assertIn('История обучения по годам', js)
        self.assertIn('close-learner-profile', js)
        self.assertIn('Создать тест', js)
        self.assertIn('Управление обучением', js)
        self.assertIn('Создать курс', js)
        self.assertIn('Создать поток', js)
        self.assertIn('data-action="batch-new"', js)
        self.assertIn('Создать поток для курса', js)
        self.assertIn('data-action="batch-for-course"', js)
        self.assertIn('elms-course-studio', js)
        self.assertIn('openCourseStudio', js)
        self.assertNotIn('elms.lms.api.save_course', js)
        self.assertIn('Оформить зачисление', js)
        self.assertNotIn('elms.lms.api.save_chapter', js)
        self.assertIn('elms.lms.api.record_lesson_progress', js)
        self.assertIn('window.addEventListener("blur"', js)
        self.assertIn('window.addEventListener("focus"', js)
        self.assertIn('heartbeatInterval', js)
        self.assertIn('Поиск по связям', js)
        self.assertNotIn('data-elms-platform-assistant', js)
        self.assertNotIn('elms.ai.api.', js)
        self.assertNotIn('elms-assistant-fab', js)
        self.assertIn('relationshipOutline', js)
        self.assertIn('Курс → разделы → уроки', js)
        self.assertIn('Программы курса', js)
        self.assertIn('Потоки курса', js)
        self.assertIn('redirectLegacyAuthoringRoute', js)

    def test_learning_css_catalog_surface(self):
        """The learner catalogue has a scoped responsive card surface."""
        css = self.css_path.read_text(encoding="utf-8")
        self.assertIn(".elms-catalog-grid", css)
        self.assertIn(".elms-catalog-card", css)
        self.assertIn(".elms-quiz-question", css)
        self.assertIn(".elms-quiz-actions", css)
        self.assertIn(".elms-learner-profile", css)
        self.assertIn(".elms-history-year", css)
        self.assertIn(".elms-program-card", css)

    def test_learning_css_relationship_surface(self):
        css = self.css_path.read_text(encoding="utf-8")
        self.assertIn(".elms-relationship-search", css)
        self.assertIn(".elms-relationship-group", css)
        self.assertIn(".elms-relationship-columns", css)
        self.assertNotIn(".elms-assistant-panel", css)
        self.assertNotIn("[data-elms-assistant]", css)

    def test_learning_css_course_preview_surface(self):
        css = self.css_path.read_text(encoding="utf-8")
        self.assertIn(".elms-preview-course-grid", css)
        self.assertIn(".elms-preview-layout", css)
        self.assertIn(".elms-preview-lesson-item", css)
        self.assertIn(".elms-course-builder-preview", css)

    def test_course_studio_uses_scoped_lms_surface(self):
        css = self.studio_css_path.read_text(encoding="utf-8")
        self.assertIn(".elms-course-studio", css)
        self.assertIn(".elms-course-studio-outline", css)
        self.assertIn(".elms-course-studio-editor", css)
        self.assertIn("--elms-action: #0d4cd3", css)

    def test_course_links_search_by_human_titles(self):
        for path, title_field in (
            (self.course_doctype_path, "course_name"),
            (self.chapter_doctype_path, "chapter_name"),
            (self.lesson_doctype_path, "lesson_name"),
        ):
            content = path.read_text(encoding="utf-8")
            self.assertIn(f'"title_field": "{title_field}"', content)
            self.assertIn('"search_fields":', content)

    def test_lms_relationship_links_use_human_titles(self):
        doctype_dir = self.root / "elms" / "lms" / "doctype"
        title_doctypes = (
            "elms_course",
            "elms_course_chapter",
            "elms_course_lesson",
            "elms_program",
            "elms_quiz",
            "elms_batch",
            "elms_subscription",
            "elms_course_category",
            "elms_program_course",
            "elms_enrollment",
            "elms_program_enrollment",
            "elms_course_progress",
            "elms_lesson_progress",
            "elms_quiz_attempt",
        )
        for name in title_doctypes:
            manifest = json.loads((doctype_dir / name / f"{name}.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest.get("title_field"), name)
            self.assertEqual(manifest.get("show_title_field_in_link"), 1, name)

    def test_lesson_progress_exposes_learner_and_course_in_list(self):
        path = self.root / "elms" / "lms" / "doctype" / "elms_lesson_progress" / "elms_lesson_progress.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        fields = {field["fieldname"]: field for field in manifest["fields"]}
        self.assertEqual(fields["user"]["options"], "User")
        self.assertEqual(fields["user"]["fetch_from"], "course_progress.user")
        self.assertEqual(fields["user"]["in_list_view"], 1)
        self.assertEqual(fields["course_name"]["fetch_from"], "course_progress.course_name")
        self.assertEqual(fields["course_name"]["in_list_view"], 1)
        self.assertIn("user", manifest.get("search_fields", ""))
        self.assertIn("course_name", manifest.get("search_fields", ""))

    def test_course_progress_links_to_lesson_progress(self):
        path = self.root / "elms" / "lms" / "doctype" / "elms_course_progress" / "elms_course_progress.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        links = manifest.get("links") or []
        self.assertTrue(
            any(
                link.get("link_doctype") == "ELMS Lesson Progress"
                and link.get("link_fieldname") == "course_progress"
                for link in links
            )
        )

    def test_course_category_is_an_editable_lms_entity(self):
        self.assertTrue(self.category_doctype_path.is_file())
        category = self.category_doctype_path.read_text(encoding="utf-8")
        course = self.course_doctype_path.read_text(encoding="utf-8")
        self.assertIn('"name": "ELMS Course Category"', category)
        self.assertIn('"title_field": "category_name"', category)
        self.assertIn('"fieldtype": "Link"', course)
        self.assertIn('"options": "ELMS Course Category"', course)

    def test_lms_workspace_exposes_learning_cabinet_shortcut(self):
        """Workspace LMS must provide shortcut to /app/elms-learning."""
        from elms.desk.workspaces import ELMS_WORKSPACE_DEFINITIONS
        lms_ws = next((item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "LMS"), None)
        self.assertIsNotNone(lms_ws)
        shortcuts = lms_ws.get("shortcuts", ())
        urls = [sc.get("url") for sc in shortcuts]
        self.assertIn("/app/elms-learning", urls)

    def test_lms_workspace_exposes_authoring_assessment_and_tracker_links(self):
        from elms.desk.workspaces import ELMS_WORKSPACE_DEFINITIONS

        lms_ws = next(item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "LMS")
        link_to = [link[1] for link in lms_ws["links"]]
        self.assertIn("ELMS Course", link_to)
        self.assertIn("ELMS Course Category", link_to)
        self.assertNotIn("ELMS Course Chapter", link_to)
        self.assertNotIn("ELMS Course Lesson", link_to)
        self.assertIn("/app/elms-course-studio", [item.get("url") for item in lms_ws.get("shortcuts", ())])
        self.assertIn("ELMS Quiz", link_to)
        self.assertIn("ELMS Quiz Question", link_to)
        self.assertIn("ELMS Course Progress", link_to)
        self.assertIn("ELMS User Activity", link_to)

    def test_settings_workspace_exposes_users_and_roles(self):
        from elms.desk.workspaces import ELMS_WORKSPACE_DEFINITIONS

        settings = next(item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "Settings")
        link_to = [link[1] for link in settings["links"]]
        self.assertIn("User", link_to)
        self.assertIn("Role", link_to)
        self.assertIn("Role Profile", link_to)
        self.assertIn("ELMS Integration Settings", link_to)


if __name__ == "__main__":
    unittest.main()
