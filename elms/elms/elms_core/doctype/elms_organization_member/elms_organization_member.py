"""Organization membership and scope validation."""

import frappe

try:
    from frappe.model.document import Document
except (ImportError, ModuleNotFoundError):
    class Document:
        pass


class ELMSOrganizationMember(Document):
    """Explicit membership; access is enforced by User Permission."""

    def _reconcile_scope(self) -> None:
        if not self.user or not self.organization:
            return
        from elms.access.api import _ensure_user_permission

        _ensure_user_permission(str(self.user), str(self.organization))

    def validate(self) -> None:
        if not self.user or not self.organization:
            frappe.throw("Пользователь и организация обязательны", frappe.ValidationError)

    def after_insert(self) -> None:
        self._reconcile_scope()

    def on_update(self) -> None:
        previous = None
        get_previous = getattr(self, "get_doc_before_save", None)
        if callable(get_previous):
            previous = get_previous()
        self._reconcile_scope()
        if previous and (
            str(getattr(previous, "user", "")) != str(self.user)
            or str(getattr(previous, "organization", "")) != str(self.organization)
        ):
            from elms.access.api import _remove_user_permission

            _remove_user_permission(str(previous.user), str(previous.organization))

    def after_delete(self) -> None:
        if not self.user or not self.organization:
            return
        from elms.access.api import _remove_user_permission

        _remove_user_permission(str(self.user), str(self.organization))
