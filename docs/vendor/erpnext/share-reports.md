---
title: "Share Reports\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/share-reports"
updated: "2026-08-14"
---

Nova Electronics Trading starts with three shareholders: Elena Brooks holds 6,000 shares, Marcus Lee holds 4,000, and Horizon Ventures LLC holds 1,000. Elena then transfers 1,000 shares to Horizon. The new balances should be 5,000 for Elena, 4,000 for Marcus, and 2,000 for Horizon. Management wants to verify two things. It needs the ownership position today and the transaction trail that explains how that position changed.



ERPNext separates these questions into two reports. Share Balance is the current snapshot. Share Ledger is the history behind the snapshot. Use both when reviewing ownership, investigating a disagreement, or preparing information for professional review.

## Share Balance

Open **Share Balance** and filter by Company or Shareholder. The report shows the shares currently held by each shareholder and their value. Use it to answer “Who owns what now?”

![Current Nova shareholders used in share reporting](https://novacompanies.m.frappe.cloud/files/budgets-capital-equity-20260814-shareholder-list.png)

## Share Ledger

Open **Share Ledger** and filter by Company, date range, or Shareholder. The report lists submitted [Share Transfers](/erpnext/share-transfer) such as issues, purchases, and owner-to-owner transfers. Use it to answer “How did this balance arise?”

![Submitted share transfer quantity used in the Share Ledger](https://novacompanies.m.frappe.cloud/files/budgets-capital-equity-20260814-share-transfer-result.png)

## Choose the right report


| Question                                     | Report                                                        |
| -------------------------------------------- | ------------------------------------------------------------- |
| How many shares does each owner hold now?    | Share Balance                                                 |
| Which issue or transfer changed the holding? | Share Ledger                                                  |
| What is one owner's current position?        | Share Balance filtered by [Shareholder](/erpnext/shareholder) |
| What happened during a particular period?    | Share Ledger filtered by date                                 |


## Troubleshooting

### A recently created shareholder does not appear

A shareholder with no submitted share issue has no holding to report. Submit an Issue and refresh the report.

### A transfer is missing

Confirm that the Share Transfer is submitted, the Company and date filters include it, and the correct shareholder is selected.

## Frequently asked questions

### Can Share Balance replace the Share Ledger?

Share Balance shows the result but not the sequence of transactions. Keep the Share Ledger when you need an audit trail.

### Do these reports replace statutory shareholder registers?

ERPNext provides operational ownership records. Confirm the statutory format, approvals, and filing requirements with a qualified professional in your jurisdiction.

## Related topics

- [Shareholder](/erpnext/shareholder)
- [Shareholder Management](/erpnext/shareholder-management)
- [Share Transfer](/erpnext/share-transfer)
- [Accounting Reports](/erpnext/accounting-reports)