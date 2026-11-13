"""Organization identity and validation."""

import re

import frappe
from frappe.model.document import Document


class ELMSOrganization(Document):
    """Company boundary used by B2B access and User Permission scope."""

    def validate(self) -> None:
        if self.inn and not re.fullmatch(r"\d{10}|\d{12}", str(self.inn).strip()):
            frappe.throw("ИНН должен содержать 10 или 12 цифр", frappe.ValidationError)
        if self.ogrn and not re.fullmatch(r"\d{13}|\d{15}", str(self.ogrn).strip()):
            frappe.throw("ОГРН должен содержать 13 или 15 цифр", frappe.ValidationError)
        if self.kpp and not re.fullmatch(r"\d{9}", str(self.kpp).strip()):
            frappe.throw("КПП должен содержать 9 цифр", frappe.ValidationError)
