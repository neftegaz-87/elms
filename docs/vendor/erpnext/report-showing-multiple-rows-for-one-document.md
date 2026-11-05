---
title: "Report Showing Multiple Rows for One Document"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/report-showing-multiple-rows-for-one-document"
updated: "2026-07-05"
---

Sometimes a report may show the same document number in multiple rows. This usually does not mean that the document has been duplicated. It means the report is showing more than one matching row of data for that document.

This is common in reports that include child table fields, linked records, or detailed accounting and stock entries.

## Most Common Reason: A Child Table Is Selected

Many ERPNext documents have child tables. For example:

- A **Sales Invoice** has multiple **Sales Invoice Items**.
- A **Purchase Order** has multiple **Purchase Order Items**.
- A **Payment Schedule** can have multiple due dates.
- A transaction can have multiple taxes, deductions, or accounting rows.

When a report includes fields from a child table, the report shows one row for each child row.

For example, if Sales Invoice `SINV-0001` has 3 item rows, and the report includes fields from **Sales Invoice Item**, the report can show:

```text
SINV-0001    Item A
SINV-0001    Item B
SINV-0001    Item C
```

The invoice is still one document. The report is showing the invoice once for every item row.

## Why This Happens

Reports are built from database rows. A parent document and a child table have a one-to-many relationship.

One parent document can have many child rows:

```text
Sales Invoice
  - Item 1
  - Item 2
  - Item 3
```

When the report includes child table data, Frappe needs to display each child row separately so that the child table values are visible. This is expected behavior.

## Other Reasons A Report Can Show Multiple Rows

### 1. Multiple Child Tables Are Included

If a report includes fields from more than one child table, the number of rows can increase further.

For example, if an invoice has 3 item rows and 2 tax rows, a poorly structured custom report may show more rows than expected because both child tables are being joined together.

In such cases, review the report design and include only the child table that is required.

### 2. The Report Shows Ledger Or Detail Entries

Some reports are intentionally detail-level reports. They are not designed to show one row per document.

For example:

- A General Ledger style report may show one row per accounting entry.
- A stock report may show one row per stock ledger entry.
- A receivable or payable report may show rows based on invoices, payments, or outstanding references.

The same voucher number can appear more than once because one document can create multiple ledger entries.

### 3. The Report Includes Linked Records With Multiple Matches

A document may be connected to multiple related records. For example, one invoice can be linked to multiple payment entries, delivery notes, serial numbers, batches, or accounting references.

If the report includes data from those linked records, the parent document can appear once for every matching linked record.

### 4. A Custom Query Report Has A Join Issue

In a custom Query Report, repeated rows may happen if the SQL query joins tables without the correct condition.

For example, joining a parent table and child table without matching the child row to its parent document can produce too many rows.

Check that the query joins child tables using the correct parent fields, such as:

```sql
child.parent = parent.name
```

Also check fields like `parenttype` and `parentfield` when the child table is shared or when the query needs to be more specific.

### 5. The Report Is Not Grouped

If the goal is to see one row per document, the report may need grouping or aggregation.

For example, instead of showing each item row separately, a report can group by Sales Invoice and show:

- Total quantity
- Total amount
- Count of item rows
- First or last date

This depends on whether you need a summary report or a detail report.

## How To Check Why Rows Are Repeating

1. Open one of the repeated documents.
2. Check whether it has multiple rows in a child table, such as Items, Taxes, Payment Schedule, or other detail tables.
3. In the report, check whether any selected column comes from a child table.
4. If it is a custom report, review the joins and filters.
5. Decide whether the report should show detail rows or one summarized row per document.

## How To Show One Row Per Document

If you want one row per document, try one of these approaches:

- Remove child table columns from the report.
- Use only fields from the parent DocType.
- Use grouping, such as grouping by document name.
- Use aggregate values such as sum, count, min, or max.
- Build a custom Query Report or Script Report that returns one row per parent document.

## Summary

Multiple rows for the same document are usually expected when the report includes child table data or other detail-level records.

The key question is: should the report show each detail row, or should it summarize the document into one row?

If the report is meant to answer item-level, tax-level, ledger-level, or stock-entry-level questions, multiple rows are correct. If it is meant to answer document-level questions, use parent fields, grouping, or a custom report design.

## Related Topics

- [Reports](https://docs.frappe.io/framework/user/en/desk/reports)
- [Report Builder](https://docs.frappe.io/framework/user/en/desk/reports/report-builder)
- [Query Report](https://docs.frappe.io/framework/user/en/desk/reports/query-report)
- [Script Report](https://docs.frappe.io/framework/user/en/desk/reports/script-report)
- [Child / Table DocType](https://docs.frappe.io/framework/user/en/basics/doctypes/child-doctype)