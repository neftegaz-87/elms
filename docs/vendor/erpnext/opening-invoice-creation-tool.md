---
title: "Import Outstanding Invoices | ERPNext Documentation"
description: "Import outstanding Sales and Purchase Invoices into ERPNext with correct parties, dates, currencies, ageing, and reconciliation controls."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/opening-invoice-creation-tool"
updated: "2026-08-14"
---

One total receivable balance is not enough to continue collections after migration. ERPNext needs each unpaid customer invoice, and each unpaid supplier invoice, when users must see due dates, ageing, references, and later allocate payments accurately.



At the cut-off date, Northstar Retail owes Nova Industries for three invoices with different dates and due amounts. The Opening Invoice Creation Tool brings those invoices across without recreating the historical sales and stock workflow that originally produced them.



This page shows how to prepare the invoice file, create opening receivables and payables, verify party balances and ageing, and correct rejected or duplicated rows before go-live.

## When to use it

Use this tool for unpaid or partly paid invoices that must appear in Accounts Receivable or Accounts Payable after cutover.

Do not use it for:

- fully paid invoices;
- quotations or orders;
- detailed historical sales analysis;
- stock movement;
- invoice rows that must preserve Item-level tax or revenue detail.

## Prepare the invoice file

Include:

- Customer or Supplier;
- invoice number;
- posting date;
- due date;
- invoice currency;
- exchange rate;
- outstanding amount;
- receivable or payable account;
- Cost Center where required;
- legacy reference.

The amount entered should be the amount still outstanding at cutover, not the original invoice total, unless the entire invoice remains unpaid.

## Reconcile the source file

Before import:

- total Customer rows by currency and compare with receivable ageing;
- total Supplier rows by currency and compare with payable ageing;
- separate debit and credit notes;
- remove zero-outstanding rows;
- confirm party names match ERPNext;
- confirm dates fall in a valid Fiscal Year;
- confirm accounts belong to the selected Company.

## Import invoices

1. Go to **Home &gt; Accounting &gt; Opening and Closing &gt; Opening Invoice Creation Tool**.
2. Select the Company.
3. Select **Sales** or **Purchase**.
4. Enable **Create Missing Party** only if the migration plan permits the tool to create basic parties. Importing reviewed Customer and Supplier masters first is safer.
5. Download the template or add rows in the Invoices table.
6. Upload the completed file.
7. review the preview and errors.
8. Start invoice creation.
9. Wait for background processing to finish.

![Opening Invoice Creation Tool](/files/opening-invoice-creation-tool7c01cb.webp)

Run Sales and Purchase imports as separate controlled batches.

## After import

Open representative invoices and confirm:

- party and party account;
- posting and due dates;
- currency and exchange rate;
- opening status;
- outstanding amount;
- legacy invoice number;
- Cost Center or dimensions where used.

Run Accounts Receivable and Accounts Payable at the cutover date. Compare party totals, invoice counts, currency totals, ageing buckets, and due dates with the source schedules.

## Partly paid invoices

Import only the outstanding portion. If the legacy system must preserve the original invoice and payment amounts for audit, record them in the migration workbook or custom reference fields.

## Credit notes

Prepare credit notes with the correct sign and party. Test one Sales credit and one Purchase credit before the full batch. Confirm they reduce the party’s outstanding balance.

## Foreign currency

Retain the invoice currency, outstanding foreign amount, exchange rate, and company-currency balance. After import, reconcile both currency values. Record any approved exchange difference separately.

## Avoid double counting

The tool creates receivable or payable ledger balances. Exclude the same control-account balance from the opening Journal Entry.

## Correcting failures

Download the failure log, correct the approved import file, and rerun only failed rows. If an invoice was created with the wrong amount or party, cancel and correct it before go-live.

## Related topics

- [Accounts Receivable](https://docs.frappe.io/erpnext/accounts-receivable)
- [Accounts Payable](https://docs.frappe.io/erpnext/accounts-payable)
- [Opening Balance in Accounts](https://docs.frappe.io/erpnext/opening-balance)
- [Payment Reconciliation](https://docs.frappe.io/erpnext/payment-reconciliation)