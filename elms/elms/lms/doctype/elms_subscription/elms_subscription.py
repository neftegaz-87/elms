"""DocType controller for ELMS Subscription."""

import frappe
from frappe.model.document import Document


class QuotaExceededError(ValueError):
	"""Raised when a subscription cannot reserve the requested seats."""


class ELMSSubscription(Document):
	@staticmethod
	def reserve_seats(
		subscription_name: str,
		count: int,
		*,
		total_seats: int,
		seats_used: int,
	) -> int:
		return reserve_seats(
			subscription_name,
			count,
			total_seats=total_seats,
			seats_used=seats_used,
		)


def reserve_seats(
	subscription_name: str,
	count: int,
	*,
	total_seats: int | None = None,
	seats_used: int | None = None,
) -> int:
	"""Reserve a validated number of seats in the current transaction."""
	if count < 1:
		raise ValueError("Seat reservation count must be positive")
	if total_seats is None or seats_used is None:
		current = frappe.db.get_value(
			SUBSCRIPTION_DOCTYPE,
			subscription_name,
			["total_seats", "seats_used"],
			as_dict=True,
			for_update=True,
		)
		if not current:
			raise ValueError("Subscription not found")
		total_seats = int(current.get("total_seats") or 0)
		seats_used = int(current.get("seats_used") or 0)
	remaining = total_seats - seats_used
	if remaining < count:
		raise QuotaExceededError("Subscription quota exceeded")
	new_used = seats_used + count
	frappe.db.set_value(SUBSCRIPTION_DOCTYPE, subscription_name, "seats_used", new_used)
	return total_seats - new_used


SUBSCRIPTION_DOCTYPE = "ELMS Subscription"
