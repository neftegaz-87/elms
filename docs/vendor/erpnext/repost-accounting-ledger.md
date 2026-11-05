---
title: "Repost Accounting Ledger | ERPNext Documentation"
description: "Safely regenerate General Ledger entries with Repost Accounting Ledger in ERPNext, preview old and new postings, process vouchers, and verify reports."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/repost-accounting-ledger"
updated: "2026-08-14"
---

Nova Industries corrects a supported accounting field on a submitted transaction, but a report still reflects the earlier ledger values. The business document is now correct, yet its General Ledger entries must be rebuilt so reports agree with it.



Repost Accounting Ledger regenerates ledger entries for selected submitted transactions. It is an administrative repair tool, not a way to change the commercial meaning of a transaction.



Use it only for supported corrections or system repairs, then verify the affected document and accounting reports before treating the issue as resolved.



## Before you begin

Confirm the following:

1. You have the **System Manager** role. Standard Accounts roles do not have permission to create or submit this administrative record.
2. The source transaction is submitted and belongs to the company you will select.
3. The source document now contains the correct accounts, dimensions, amounts, taxes, and valuation information.
4. The voucher type is listed under **Allowed DocTypes** in [Accounts Settings](https://docs.frappe.io/erpnext/accounts-settings).
5. The affected posting period is open. ERPNext does not repost vouchers covered by a submitted [Period Closing Voucher](https://docs.frappe.io/erpnext/period-closing-voucher).
6. You have a backup and a test plan before processing a large or production-critical correction.

Reposting is supported only for configured voucher types. Common examples include [Sales Invoice](https://docs.frappe.io/erpnext/sales-invoice), [Purchase Invoice](https://docs.frappe.io/erpnext/purchase-invoice), [Payment Entry](https://docs.frappe.io/erpnext/payment-entry), [Journal Entry](https://docs.frappe.io/erpnext/journal-entry), Purchase Receipt, and Expense Claim.

## Allow a voucher type to be reposted

Open **Accounts Settings** and select the **Payments** tab. In the **Repost** section, add each permitted transaction type to **Allowed DocTypes**, then save.

Changing supported accounting fields after submission can trigger reposting for the DocTypes listed here. Remove a DocType when your organization does not want those post-submit changes to initiate a repost.



![Allowed DocTypes in the Repost section of ERPNext Accounts Settings](https://novacompanies.m.frappe.cloud/files/repost-accounting-ledger-20260802-repost-allowed-doctypes-settings327aa6.png)

Keep the list deliberate. Adding a DocType authorizes a sensitive accounting repair workflow; it is not a requirement to add every accounting transaction.

## Create a Repost Accounting Ledger record

Search for **Repost Accounting Ledger** from the Awesome Bar. The list shows draft and submitted repost records.



![Draft and submitted Repost Accounting Ledger records in ERPNext](https://novacompanies.m.frappe.cloud/files/repost-accounting-ledger-20260802-repost-listbadaf9.png)

Select **Add Repost Accounting Ledger**.

Choose the **Company** that owns the source vouchers. Leave **Delete Cancelled Ledger Entries** cleared for a normal repost.



![Company and Delete Cancelled Ledger Entries fields on a draft repost](https://novacompanies.m.frappe.cloud/files/repost-accounting-ledger-20260802-repost-draft-fields67744b.png)

In **Vouchers**, add the submitted documents that need recalculation. Select a **Voucher Type**, then select the corresponding **Voucher No**. The voucher list is restricted to submitted records from the selected company.

Select the pencil icon when you need to open and review the child-table row.



![A Journal Entry selected in the Vouchers table with the row pencil highlighted](https://novacompanies.m.frappe.cloud/files/repost-accounting-ledger-20260802-repost-voucher-row3d73a8.png)

The example uses Journal Entry `ACC-JV-2026-00005`, a $250 transfer from **Demo Bank Account** to **Cash**.



![The source Journal Entry with its balanced debit and credit highlighted](https://novacompanies.m.frappe.cloud/files/docs-gl-correction-20260803-repost-accounting-ledger-repost-source-journal-entry.png)

Save the repost as a draft.

## Preview the regenerated entries

Select **Show Preview** before submitting. ERPNext generates the ledger map again from the current source document and compares it with the existing entries.



![Repost preview comparing existing and regenerated General Ledger entries](https://novacompanies.m.frappe.cloud/files/docs-gl-correction-20260803-repost-accounting-ledger-repost-preview.png)

In the preview:

- Red rows are the existing General Ledger entries that will be replaced or reversed.
- Green rows are the entries ERPNext will generate from the current source document.

Check the accounts, debit and credit values, voucher number, Cost Center, and other dimensions. If a proposed row is wrong, return to the source transaction and correct it before continuing. Do not submit the repost in the hope that it will correct an incorrect source document.

## Submit and verify the repost

Submit the Repost Accounting Ledger record only after the preview is correct.



![A submitted Repost Accounting Ledger record](https://novacompanies.m.frappe.cloud/files/repost-accounting-ledger-20260802-repost-submittedb002eb.png)

ERPNext processes five or fewer selected vouchers immediately. When the record contains more than five vouchers, it queues the work in the background and displays a message that reposting has started.

After processing, open each source voucher and use **View &gt; Ledger**, or run the General Ledger report with the voucher number. Confirm that:

1. The intended accounts and dimensions are present.
2. Total debit equals total credit.
3. Old values no longer affect the report.
4. The related financial report now shows the expected result.

![General Ledger after reposting the example Journal Entry](https://novacompanies.m.frappe.cloud/files/repost-accounting-ledger-20260802-repost-general-ledgerb20a75.png)

Reposting changes ledger entries, not the submitted status or commercial meaning of the source transaction. If the transaction itself should be reversed, use its supported cancellation, return, credit note, debit note, or amendment workflow instead.

## Important fields and what they mean


| Field                           | What it controls                                                                                   | Guidance                                                                                                                |
| ------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Company                         | Limits the selectable vouchers and ledger rebuild to one company                                   | Select the company that owns every voucher in the table.                                                                |
| Delete Cancelled Ledger Entries | Deletes existing cancelled GL, Payment Ledger, and Advance Payment Ledger rows before regeneration | Leave this cleared for normal use. Use it only for a diagnosed cleanup case under technical or implementation guidance. |
| Voucher Type                    | Identifies the transaction DocType to regenerate                                                   | The type must be present in Accounts Settings under Allowed DocTypes.                                                   |
| Voucher No                      | Identifies the submitted source document                                                           | Review the source document and its current ledger before adding it.                                                     |
| Show Preview                    | Compares current entries with the newly generated ledger map                                       | Treat the preview as a required review step, especially when accounts or dimensions changed.                            |


## Restrictions and safeguards

### Closed fiscal periods

ERPNext blocks reposting when a selected voucher falls on or before the latest submitted Period Closing Voucher date for that company. Reopen or correct a closed period only through your approved accounting controls.

### Deferred revenue and expense

A Sales Invoice with deferred revenue or a Purchase Invoice with deferred expense cannot be reposted through this tool. Use the supported [Deferred Accounting](https://docs.frappe.io/erpnext/deferred-accounting) workflow and verify the related schedules and entries.

### Immutable ledger

Reposting preserves the audit-oriented behavior of the [immutable ledger](https://docs.frappe.io/erpnext/immutable-ledger-in-erpnext). With the normal option, ERPNext reverses the old accounting effect and creates the regenerated effect through supported ledger logic instead of inviting users to edit GL Entry rows directly.

### Large batches

Do not combine unrelated corrections merely to process them together. Test a representative voucher first, process the smallest useful batch, wait for background work to complete, and verify reports before continuing.

## Troubleshooting

### The Voucher Type is not available

Add the DocType to **Accounts Settings &gt; Payments &gt; Repost &gt; Allowed DocTypes**, save the settings, then reopen the repost record. If the type should not permit post-submit accounting changes in your organization, do not add it merely to bypass the restriction.

### The voucher number is not available

Confirm that the Company matches the source document, the voucher is submitted, and the selected Voucher Type is correct. Draft and cancelled vouchers are not offered for a normal repost.

### ERPNext says the voucher is in a closed fiscal year

The voucher date is covered by a submitted Period Closing Voucher. Do not bypass the close casually. Follow your controlled period-reopening process and obtain the required accounting approval.

### ERPNext says deferred accounting is enabled

The selected invoice contains deferred revenue or deferred expense. Reposting that invoice is blocked because it can conflict with its deferred schedules. Review the deferred accounting records and use the appropriate process for that feature.

### The preview does not match the intended correction

Stop and inspect the source transaction. Check its account, amount, tax, Cost Center, dimensions, exchange rate, and linked stock valuation. The preview reflects the source document as it exists now.

### The report still shows an unexpected balance

Refresh the report and confirm its company, date range, finance book, currency, account, and voucher filters. Then compare the source document, preview, and General Ledger. Another voucher may also contribute to the balance.

## FAQs

### Does reposting change the source document?

No, It recalculates ledger entries from the source document's current data. It does not change the document's submitted status, items, party, or commercial purpose.

### Should I use this instead of cancelling and amending a wrong transaction?

No, Correct the transaction through its supported business workflow when the source document itself is wrong. Repost only when the source is correct and its accounting entries need regeneration.

### Can I repost several vouchers together?

Yes, Add multiple vouchers from the same company. Five or fewer are processed immediately; more than five are queued in the background. Smaller, related batches are easier to verify.

### What does Delete Cancelled Ledger Entries do?

It removes existing cancelled GL, Payment Ledger, and Advance Payment Ledger rows for the selected vouchers before rebuilding them. It is an exceptional cleanup option, not the default way to repost.

### Why are the old and new rows identical in the preview?

That can be correct when you are verifying or rebuilding entries without changing their accounting values. If you expected a difference, confirm that the intended source-field correction was saved before generating the preview.

### Does a draft repost affect accounting reports?

No, Saving the record and generating a preview do not replace the ledger entries. The accounting rebuild occurs when the repost is submitted and processed.

## Related topics

- [General Ledger](https://docs.frappe.io/erpnext/general-ledger)
- [Journal Entry](https://docs.frappe.io/erpnext/journal-entry)
- [Accounting Entries](https://docs.frappe.io/erpnext/accounting-entries)
- [Immutable Ledger](https://docs.frappe.io/erpnext/immutable-ledger-in-erpnext)
- [Accounts Settings](https://docs.frappe.io/erpnext/accounts-settings)
- [Period Closing Voucher](https://docs.frappe.io/erpnext/period-closing-voucher)