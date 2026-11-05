---
title: "Import Accounting Masters | ERPNext Documentation"
description: "Import ERPNext accounting masters in dependency order using Data Import, test representative records, correct failures, and validate links and defaults."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/import-accounting-masters"
updated: "2026-07-30"
---

Import masters before opening transactions and balances. Use ERPNext’s Data Import tool for records that do not have a specialized importer.

## Import order

1. Groups and parent records
2. Company-independent masters
3. Company-specific masters
4. Parties and addresses
5. Items and Warehouses
6. Banks, payments, taxes, and terms

For example, import Customer Groups and Territories before Customers, and Item Groups and UOMs before Items.

## Download the ERPNext template

1. Go to **Home &gt; Data Import and Settings &gt; Import Data**.
2. Create a new Data Import.
3. Select the DocType.
4. Choose **Insert New Records**.
5. Download the template.
6. Include only the columns needed for the approved mapping.

![Data Import configured for a migration master](/files/data-import.webp)

Do not build a template from memory. Current mandatory and dependent fields may differ from an older version.

## Fill the template

Keep column headers unchanged. Use exact ERPNext names for Link fields.

For tree masters, import parents first and set **Is Group** correctly. For child tables, use the importer’s row structure and test with one record before loading the full file.

## Test a small batch

Import two to five representative records:

- one simple record;
- one record with every optional link;
- one record with a child table;
- one foreign-currency party, if applicable;
- one disabled or historical record.

Open each imported record and test it in a draft transaction.

## Run the full import

1. Upload the approved file.
2. Start the import.
3. Download or copy the failure log.
4. Correct the source working file, not only the failed ERPNext row.
5. Re-import rejected records.
6. Record imported and rejected counts in the control workbook.

## Addresses and Contacts

Import Address and Contact only after parties exist. Add the Links child table so each record is connected to its Customer, Supplier, or other party.

For primary records, set the appropriate billing, shipping, or primary flags and verify the party form shows the correct defaults.

## Items and accounting defaults

For Items, verify:

- Maintain Stock;
- stock UOM;
- Item Group;
- default Warehouse;
- income and expense accounts;
- Cost Center;
- tax template;
- valuation method where relevant.

A successful import does not prove that accounting defaults are correct.

## Correcting master imports

Use **Update Existing Records** for approved corrections. Do not create a second record because the first import had a spelling error. If a duplicate has already been used in a transaction, follow the supported rename or merge process.

## Validation checklist

- source count equals imported plus rejected count;
- no unexpected duplicates;
- parent trees are correct;
- party and Item defaults are correct;
- addresses and contacts are linked;
- disabled records remain disabled;
- draft sales, purchase, payment, and stock transactions fetch expected values.

## Related topics

- [Data Import](https://docs.frappe.io/erpnext/data-import)
- [Accounting Masters for Migration](https://docs.frappe.io/erpnext/accounting-masters)
- [Prepare and Map Legacy Data](https://docs.frappe.io/erpnext/prepare-and-map-legacy-data)
- [Import Chart of Accounts](https://docs.frappe.io/erpnext/import-chart-of-accounts)