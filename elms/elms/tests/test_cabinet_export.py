import csv
import io
import json
import re
from types import SimpleNamespace

import pytest

from elms.cabinet import api as api_module
from elms.cabinet import export as export_module


class FakeFrappe:
    PermissionError = PermissionError
    ValidationError = ValueError

    def __init__(self, user="company-admin@example.com"):
        self.session = SimpleNamespace(user=user)
        self.utils = SimpleNamespace(now_datetime=lambda: "2026-11-14 10:30:00")
        self.audit_rows = []

    def throw(self, message, exception=Exception):
        raise exception(message)

    def get_doc(self, values):
        frappe = self

        class AuditDocument:
            def __init__(self):
                self.values = values
                self.flags = SimpleNamespace(ignore_permissions=False)

            def insert(self, ignore_permissions=False):
                self.flags.ignore_permissions = ignore_permissions
                frappe.audit_rows.append(self)
                return self

        return AuditDocument()


@pytest.fixture
def roster_rows():
    return [
        {
            "user": "alice@example.com",
            "full_name": "Alice Example",
            "email": "alice@example.com",
            "user_enabled": True,
            "roles": ["ELMS Learner"],
            "enrollments": [
                {
                    "enrollment": "ENR-001",
                    "course": "COURSE-001",
                    "course_name": "Безопасность",
                    "status": "Active",
                    "progress_pct": 40.0,
                }
            ],
        },
        {
            "user": "bob@example.com",
            "full_name": "Bob Example",
            "email": "bob@example.com",
            "user_enabled": True,
            "roles": ["ELMS Learner"],
            "enrollments": [],
        },
    ]


def test_export_matches_roster_rows_and_writes_audit(monkeypatch, roster_rows):
    fake_frappe = FakeFrappe()
    calls = []

    def fake_roster(**kwargs):
        calls.append(kwargs)
        return {
            "organization": "org1",
            "total": len(roster_rows),
            "page": kwargs["page"],
            "page_size": kwargs["page_size"],
            "rows": roster_rows,
            "empty": False,
        }

    monkeypatch.setattr(export_module, "frappe", fake_frappe)
    monkeypatch.setattr(export_module, "build_org_roster", fake_roster)

    result = export_module.build_org_progress_export(
        organization="org1", status_filter="Active"
    )

    decoded = result["content_base64"]
    csv_text = result["csv_text"]
    assert result["organization"] == "org1"
    assert result["charset"] == "UTF-8"
    assert result["row_count"] == len(roster_rows)
    assert re.fullmatch(r"elms-org-org1-\d{8}\.csv", result["filename"])
    assert csv_text.startswith("\ufeff")
    assert decoded == __import__("base64").b64encode(csv_text.encode("utf-8")).decode()

    rows = list(csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff"))))
    assert [row["user"] for row in rows] == [row["user"] for row in roster_rows]
    assert rows[0]["full_name"] == "Alice Example"
    assert rows[0]["enrollments"].startswith("[")
    assert json.loads(rows[0]["enrollments"]) == roster_rows[0]["enrollments"]
    assert "org2" not in csv_text
    assert calls == [
        {
            "organization": "org1",
            "status_filter": "Active",
            "page": 1,
            "page_size": 500,
        }
    ]

    assert len(fake_frappe.audit_rows) == 1
    audit = fake_frappe.audit_rows[0]
    assert audit.values == {
        "doctype": "ELMS Cabinet Export Log",
        "user": "company-admin@example.com",
        "organization": "org1",
        "row_count": 2,
        "timestamp": "2026-11-14 10:30:00",
    }
    assert audit.flags.ignore_permissions is True


def test_export_collects_all_roster_pages_before_building_csv(monkeypatch, roster_rows):
    fake_frappe = FakeFrappe()
    calls = []
    trailing_row = {
        "user": "last@example.com",
        "full_name": "Last Example",
        "email": "last@example.com",
        "user_enabled": True,
        "roles": ["ELMS Learner"],
        "enrollments": [],
    }

    def fake_roster(**kwargs):
        calls.append(kwargs)
        if kwargs["page"] == 1:
            return {
                "organization": "org1",
                "total": 501,
                "page": 1,
                "page_size": 500,
                "rows": roster_rows * 250,
                "empty": False,
            }
        return {
            "organization": "org1",
            "total": 501,
            "page": 2,
            "page_size": 500,
            "rows": [trailing_row],
            "empty": False,
        }

    monkeypatch.setattr(export_module, "frappe", fake_frappe)
    monkeypatch.setattr(export_module, "build_org_roster", fake_roster)

    result = export_module.build_org_progress_export(organization="org1")

    assert result["row_count"] == 501
    assert [call["page"] for call in calls] == [1, 2]
    assert fake_frappe.audit_rows[0].values["row_count"] == 501


def test_export_denies_foreign_organization(monkeypatch):
    fake_frappe = FakeFrappe()

    def denied_roster(**kwargs):
        raise PermissionError("Нет доступа к этой организации")

    monkeypatch.setattr(export_module, "frappe", fake_frappe)
    monkeypatch.setattr(export_module, "build_org_roster", denied_roster)

    with pytest.raises(PermissionError, match="Нет доступа"):
        export_module.build_org_progress_export(organization="org2")

    assert fake_frappe.audit_rows == []


def test_export_rejects_more_than_5000_roster_rows(monkeypatch):
    fake_frappe = FakeFrappe()

    monkeypatch.setattr(export_module, "frappe", fake_frappe)
    monkeypatch.setattr(
        export_module,
        "build_org_roster",
        lambda **kwargs: {
            "organization": "org1",
            "total": 5001,
            "page": 1,
            "page_size": 500,
            "rows": [],
            "empty": False,
        },
    )

    with pytest.raises(ValueError, match="5000"):
        export_module.build_org_progress_export(organization="org1")

    assert fake_frappe.audit_rows == []


def test_api_exposes_export_whitelist(monkeypatch):
    expected = {"filename": "elms-org-org1-20261114.csv"}
    calls = []

    def fake_export(**kwargs):
        calls.append(kwargs)
        return expected

    monkeypatch.setattr(api_module, "build_org_progress_export", fake_export)

    assert api_module.export_org_progress("org1", "Active") == expected
    assert calls == [{"organization": "org1", "status_filter": "Active"}]
