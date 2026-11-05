---
title: "Freeze an Account | ERPNext Documentation"
description: "Learn how to freeze an Account in ERPNext, restrict new postings, authorize exception roles, preserve ledger history, verify defaults, and unfreeze it safely."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/freeze-account"
updated: "2026-08-03"
---

Freeze an individual ledger Account when users should be able to see its history but should no longer post new transactions to it. This is useful after replacing a bank, expense, income, receivable, or payable account without deleting the older ledger.



Freezing does not remove the Account or its existing [General Ledger](https://docs.frappe.io/erpnext/general-ledger) entries. It prevents ordinary users from using that Account in new accounting transactions. An explicitly authorized role can still set frozen Accounts and create or modify entries against them.

> Freeze only an Account that should no longer receive postings. If you need to prevent entries for a past date range instead, use [Freeze Accounting Entries](https://docs.frappe.io/erpnext/freeze-accounting-entries) or an [Accounting Period](https://docs.frappe.io/erpnext/accounting-period).

## Before you begin

Confirm that:

1. The Account is a ledger Account, not a group used to organize the [Chart of Accounts](https://docs.frappe.io/erpnext/chart-of-accounts).
2. Users should retain access to its historical transactions and balances.
3. A replacement Account is available if future invoices, payments, or journals still need a ledger for the same purpose.
4. Defaults in the Company, Customer, Supplier, Item, tax templates, and [Mode of Payment](https://docs.frappe.io/erpnext/mode-of-payment) no longer point to the Account you plan to freeze.
5. The role permitted to manage frozen Accounts has been reviewed.

## Authorize a role to manage frozen Accounts

The permission is company-specific in the current ERPNext interface.

1. Open the required **Company**.
2. Select the **Accounts Closing** tab.
3. In **Roles Allowed to Set and Edit Frozen Account Entries**, select the role that may freeze Accounts and post or modify entries against them.
4. Save the Company.

![Company Accounts Closing tab with Roles Allowed to Set and Edit Frozen Account Entries highlighted](https://novacompanies.m.frappe.cloud/files/docs-gl-refresh-20260803-freeze-an-account-role-allowed-for-frozen-accounts.png)

Grant this role sparingly. A user with it can bypass the restriction when posting to a frozen Account. In older ERPNext documentation, this control may be described as an Accounts Settings field. On the current develop interface it appears in the Company's **Accounts Closing** tab.

## Freeze an Account

1. Open **Accounting &gt; Chart of Accounts**.
2. Select the Company.
3. Open the ledger Account that should stop receiving transactions.
4. Set **Frozen** to **Yes**.
5. Save the Account.

![Ledger Account with Frozen set to No before the change](https://novacompanies.m.frappe.cloud/files/docs-gl-refresh-20260803-freeze-an-account-account-not-frozen.png)



![Ledger Account with Frozen set to Yes and Save highlighted](https://novacompanies.m.frappe.cloud/files/docs-gl-refresh-20260803-freeze-an-account-freeze-account-before-save.png)

After saving, ordinary users cannot use the Account in accounting transactions. Existing [Journal Entries](https://docs.frappe.io/erpnext/journal-entry), invoices, payments, and reports remain connected to it.

## What freezing changes


| Area                                | Result                                                                                                                                 |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| New accounting transactions         | Ordinary users cannot post entries against the frozen Account.                                                                         |
| Authorized role                     | Users with the Company role configured for frozen Account entries can set the Account as frozen and post or modify entries against it. |
| Existing ledger history             | Remains available in the General Ledger and financial reports.                                                                         |
| Account master                      | Remains in the Chart of Accounts and can be unfrozen later.                                                                            |
| Defaults that reference the Account | Are not automatically replaced. Update them before users create new transactions.                                                      |
| Date-based locks                    | Are unchanged. Freezing one Account is separate from freezing entries through a date or closing an Accounting Period.                  |


## Verify the change

After saving:

1. Reopen the Account and confirm **Frozen** is **Yes**.
2. Check that active defaults now use the intended replacement ledger.
3. Open the [General Ledger report](https://docs.frappe.io/erpnext/general-ledger) and confirm the historical Account balance remains visible.
4. If your controls require a test, use a draft transaction with a test user who does not have the exception role. Do not submit an incorrect entry merely to test the restriction.

## Unfreeze an Account

An authorized user can reopen the Account, set **Frozen** to **No**, and save. Before unfreezing, confirm why postings need to resume and whether a newer Account has already replaced it. Allowing both Accounts to remain active can split transactions and make [financial statements](https://docs.frappe.io/erpnext/accounting-reports) harder to reconcile.

## Troubleshooting


| Issue                                           | What to check                                                                                                                               |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Frozen cannot be changed                        | Confirm that your user has the role selected in the Company's Accounts Closing settings.                                                    |
| A transaction still posts to the frozen Account | Check whether the user has the authorized role. Also confirm that the transaction used the Account you froze, not a similarly named ledger. |
| New transactions default to the frozen Account  | Replace the Account in Company and master defaults, tax templates, payment modes, and transaction templates.                                |
| A past period must be locked                    | Use Accounts Frozen Till Date or an Accounting Period. Freezing an Account controls a ledger, not a date range.                             |
| Reports still show the Account                  | This is expected. Freezing stops new postings and does not remove historical balances.                                                      |


## Frequently asked questions

### Does freezing an Account delete it?

No, The Account and its historical ledger entries remain available. The restriction applies to new or modified accounting entries.

### Is a frozen Account the same as a disabled Account?

No, **Frozen** is an accounting control that blocks ordinary postings while permitting a configured role to handle exceptions. **Disable** is a broader master-state control. Use the option that matches your control objective.

### Can an authorized user post to a frozen Account?

Yes, A user with the role configured in **Roles Allowed to Set and Edit Frozen Account Entries** can create or modify entries against it. Keep that role limited and review its assignments.

### Does freezing an Account affect its balance?

No, Existing debits, credits, and balances remain unchanged. The Account continues to appear in reports based on its historical postings.

### When should I use a date freeze instead?

Use **Accounts Frozen Till Date** when the restriction should apply to accounting entries before a cutoff date. Use an Accounting Period when selected transaction types must be closed for a completed period. Use **Frozen** on the Account when one specific ledger should stop receiving entries regardless of date.

## Related topics

- [Chart of Accounts](https://docs.frappe.io/erpnext/chart-of-accounts)
- [Freeze Accounting Entries](https://docs.frappe.io/erpnext/freeze-accounting-entries)
- [Accounting Period](https://docs.frappe.io/erpnext/accounting-period)
- [Company](https://docs.frappe.io/erpnext/company-setup)
- [General Ledger](https://docs.frappe.io/erpnext/general-ledger)
- [Journal Entry](https://docs.frappe.io/erpnext/journal-entry)