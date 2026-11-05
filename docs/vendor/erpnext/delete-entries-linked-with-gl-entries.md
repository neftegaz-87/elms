---
title: "Delete entries linked with GL entries"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/delete-entries-linked-with-gl-entries"
updated: "2026-08-14"
---

ERPNext prevents Nova Industries from deleting a cancelled invoice because its accounting and stock ledger rows form part of the audit trail. Deleting a transaction is different from cancelling it, and should be rare. First decide whether you only need to reverse the business effect, which cancellation already does.

## Before enabling deletion

- Confirm the document is cancelled and no statutory or audit rule requires it to remain.
- Take a backup and test in a non-production environment.
- Understand that deleting ledger rows reduces traceability and may allow the naming series number to be reused depending on configuration.

## Enable the setting

1. Open **Accounts Settings**.
2. Find **Delete Accounting and Stock Ledger Entries on deletion of Transaction**.
3. Enable it, save, and reload.
4. Delete only the intended cancelled document.
5. Disable the setting again if it was approved for a one-time cleanup.

![Accounts Settings option for deleting linked accounting and stock ledger entries](https://novacompanies.m.frappe.cloud/files/final-accounting-20260814-delete-linked-ledger-setting.png)



## Troubleshooting

### The document is still linked

Open the document’s links and identify dependent records, allocations, returns, or amendments. Remove or resolve dependencies in the correct business order. Do not delete database rows directly.

## Frequently asked questions

### Should I delete an incorrect submitted invoice?

Normally cancel and amend it. That preserves the original document, its reversal, and the correction for audit.

## Related topics

- [Accounting overview](/erpnext/accounting/introduction)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [General Ledger](/erpnext/general-ledger)
- [Fiscal Year](/erpnext/fiscal-year)