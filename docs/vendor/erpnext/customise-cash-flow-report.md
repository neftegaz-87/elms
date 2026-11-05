---
title: "Customise Cash Flow Report"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/customise-cash-flow-report"
updated: "2026-08-14"
---

Nova Industries's default Cash Flow report explains how cash moved through operating, investing, and financing activities. Finance wants a reusable IFRS-style presentation with clearer lines for profit before tax, depreciation, finance costs, receivables, payables, inventory, equipment purchases, and financing.



In the current ERPNext develop version, Nova can create or adapt a [Financial Report Template](/erpnext/financial-report-template) with Report Type set to **Cash Flow**. The template controls report headings, account selection, calculations, indentation, signs, hidden rows, and charts. It changes presentation, not the underlying [General Ledger](/erpnext/general-ledger) entries.

## Before you begin

- Run the standard [Cash Flow Report](/erpnext/cash-flow-report) and reconcile it with the General Ledger.
- Have an accountant approve the required headings, classifications, signs, and calculations.
- Review the [Chart of Accounts](/erpnext/chart-of-accounts) and assign consistent Account Categories where template rows use them.
- Test the template with representative transactions before using it for management or external reporting.

## Review the current report

Run Cash Flow for Nova Industries with a period containing operating, investing, and financing transactions. Save the baseline totals before enabling a custom format.

![Loaded Cash Flow report for Nova Industries before mapping review](https://novacompanies.m.frappe.cloud/files/docs-20260814-nova-industries-cash-flow-loaded.png)

## Create or copy a Cash Flow template

1. Open Financial Report Template.
2. Create a template, or copy an existing Cash Flow template when it is a suitable starting point.
3. Set **Report Type** to **Cash Flow**.
4. Enter a clear Template Name and keep the template enabled.

## Build and arrange the report lines

Add rows to **Report Line Items** in the exact order they should appear. Use blank or visual rows for section headings, Account Data rows for ledger-derived values, and Calculated Amount rows for subtotals. Indent supporting lines beneath their section and use stable Line References for formulas.

![Standard Cash Flow Statement IFRS template showing its ordered report line items](https://novacompanies.m.frappe.cloud/files/docs-20260814-financial-report-template-form.png)


| Example line                                    | Typical source      | Presentation                                              |
| ----------------------------------------------- | ------------------- | --------------------------------------------------------- |
| Cash flows from operating activities            | Visual or blank row | Section heading at indent level 0                         |
| Profit before tax                               | Account Data        | Period movement with the appropriate sign                 |
| Depreciation and amortisation                   | Account Data        | Indented non-cash adjustment                              |
| Operating profit before working-capital changes | Calculated Amount   | Formula based on earlier Line References                  |
| Change in trade receivables                     | Account Data        | Working-capital movement with reversed sign when required |


## Verify the custom report

![Cash Flow report after mapping with an account group opened for verification](https://novacompanies.m.frappe.cloud/files/docs-20260814-financial-report-template-ifrs-output-v2.png)



1. Refresh Cash Flow for the same company and period used for the baseline.
2. Confirm every expected line appears under the correct section.
3. Compare section totals and closing cash with the standard report and General Ledger.
4. Open unusual balances and verify the mapped accounts.
5. Repeat the test for a second period before relying on the format.

## Troubleshooting

### A line is missing

Confirm that the row is enabled, its Account Data filter matches the intended accounts, and the selected period contains relevant ledger activity. Check whether **Hide If Zero** is suppressing the row.

### A value appears twice

Review the template's account coverage for overlap. The same account may be included by more than one Account Data row, or a parent account and its children may both be selected.

### Net cash does not reconcile

Run the template and standard Cash Flow report with identical company, dates, Finance Book, dimensions, currency, and opening-balance options. Then check omitted accounts, duplicated coverage, formulas, Line References, and sign reversal.

## Frequently asked questions

### Does customisation change ledger entries?

The configuration changes how existing balances are classified and displayed. It does not repost transactions.

### Can I add a fourth cash-flow section?

The standard structure uses Operating, Investing, and Financing Activities. Use approved labels and mappings inside those sections unless a current product extension explicitly supports another structure.

### Should parent or child accounts be mapped?

Use an approach that avoids overlap and matches how the account tree is maintained. Parent accounts work best when all children share the same cash-flow treatment.

## Related topics

- [Accounting Reports](/erpnext/accounting-reports)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [Accounts Settings](/erpnext/accounts-settings)
- [General Ledger](/erpnext/general-ledger)
- [Financial Report Template](/erpnext/financial-report-template)