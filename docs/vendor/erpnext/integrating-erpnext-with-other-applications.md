---
title: "Integrating ERPNext with other Applications"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/integrating-erpnext-with-other-applications"
updated: "2026-07-04"
---

ERPNext is designed to be integrated with other applications. Because ERPNext is built on Frappe Framework, business records are exposed through a consistent REST API. This makes it straightforward to connect ERPNext with external systems such as CRM platforms, logistics providers, order management systems, recommerce platforms, Google services, banking systems, payment gateways, and internal business applications.

## Why ERPNext Is Easy To Integrate

Most ERPNext business objects are DocTypes. Customers, Items, Sales Orders, Purchase Orders, Sales Invoices, Delivery Notes, Payment Entries, Stock Entries, Projects, and many other records follow the same document model. Frappe automatically provides REST API access for DocTypes, so integrations can read, create, update, and delete records using predictable endpoints.

This means a third-party application does not need a separate custom API for every ERPNext module. Once the external system knows the DocType and field names, it can exchange data with ERPNext using standard HTTPS requests and JSON payloads.

Custom fields added in ERPNext become part of the DocType metadata and are available to integrations immediately. For example, if a business adds a custom field such as `marketplace_order_id` on Sales Order or `courier_tracking_id` on Delivery Note, third-party applications can send and receive those values through the same REST API used for standard fields.

This is especially useful when ERPNext is connected to external systems that need their own identifiers, statuses, references, or operational data. Custom fields let teams extend ERPNext without breaking the standard data model.

## How REST APIs Work

Frappe provides REST API endpoints for DocTypes. A third-party application can authenticate with an API key and API secret, then call endpoints to list documents, fetch a specific document, create a new record, update an existing record, or delete a record where permissions allow it.

Common integration patterns include:

- **Read from ERPNext:** Fetch customers, items, prices, stock levels, invoices, or payment status.
- **Write to ERPNext:** Create leads, customers, sales orders, purchase orders, delivery notes, payment entries, or support tickets.
- **Update ERPNext:** Send shipping updates, reconciliation references, bank transaction IDs, marketplace order IDs, or fulfillment statuses.
- **React to ERPNext events:** Use webhooks to notify another application when a document is created, updated, submitted, or cancelled.

## Examples Of Integrations

- **CRM:** Sync leads, opportunities, customers, quotations, and follow-up status between ERPNext and a sales CRM.
- **Logistics:** Send delivery notes or shipment requests to a courier platform and receive tracking numbers back into ERPNext.
- **Order Management:** Push orders from an order management system into ERPNext as Sales Orders, then send fulfillment and invoice status back.
- **Recommerce Platforms:** Sync product catalog, customer orders, stock availability, returns, refurbishment status, and payouts.
- **Google Services:** Connect ERPNext with Google Workspace, Google Calendar, Google Sheets, or reporting workflows.
- **Banks And Payment Systems:** Import bank transactions, update payment references, reconcile payments, or connect payment collection workflows.

## Typical Integration Flow

1. Identify the ERPNext DocTypes involved, such as Customer, Item, Sales Order, Delivery Note, Sales Invoice, Payment Entry, or a custom DocType.
2. Map the fields between ERPNext and the external application, including any custom fields required by the business process.
3. Create an integration user in ERPNext with only the roles and permissions required for the integration.
4. Generate API credentials for that user and authenticate API calls securely.
5. Use REST API endpoints to create, fetch, update, or delete records as needed.
6. Use webhooks or background jobs for event-driven sync, retries, and asynchronous processing.

## Good Practices

- Use a dedicated integration user instead of an administrator account.
- Apply role-based permissions so the integration can access only the records it needs.
- Store external IDs in custom fields to make reconciliation and troubleshooting easier.
- Design integrations to be idempotent, so retrying a request does not create duplicate records.
- Use webhooks or queues for high-volume workflows instead of making everything synchronous.
- Log request IDs, external references, and error messages so failures can be traced quickly.

## Related Topics

- [Frappe REST API](https://docs.frappe.io/framework/user/en/api/rest)
- [Token Based Authentication](https://docs.frappe.io/framework/user/en/guides/integration/token_based_authentication)
- [Webhooks](https://docs.frappe.io/framework/user/en/guides/integration/webhooks)
- [Insert A Document Via API](https://docs.frappe.io/framework/user/en/guides/app-development/insert-a-document-via-api)
- [Custom Field](https://docs.frappe.io/erpnext/custom-field)