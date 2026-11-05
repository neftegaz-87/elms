---
title: "Setting Up Taxes | ERPNext Documentation"
description: "Configure tax accounts, sales and purchase tax templates, Tax Categories, Tax Rules, and item-specific rates in ERPNext."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/setting-up-taxes"
updated: "2026-08-14"
---

Tax setup connects a legal calculation to the ordinary sales and purchase workflow. The goal is not merely to add a percentage to an invoice, but to calculate the right charge, post it to the right account, and retain enough detail for reporting and compliance.



Nova Industries may sell the same electronics to retail customers, resellers, and customers in another region. The applicable tax can depend on the Item, party, address, transaction type, and jurisdiction. Reusable templates and rules allow ERPNext to choose consistently instead of asking users to rebuild the calculation on every invoice.



This page provides the setup sequence and explains how accounts, templates, Item Tax Templates, Tax Categories, and Tax Rules work together. Confirm the exact rates and legal treatment with a qualified local adviser.

## Before you begin

Confirm the tax registration, rates, place-of-supply rules, recoverability, and reporting requirements with a qualified adviser. Create the required tax ledgers in the [Chart of Accounts](https://docs.frappe.io/erpnext/chart-of-accounts).

## Create sales and purchase tax templates

Open **Sales Taxes and Charges Template** or **Purchase Taxes and Charges Template**.

1. Select the company.
2. Add a row for each tax or charge.
3. Choose the calculation type.
4. Select the tax ledger.
5. Enter the rate and description.
6. Mark a template as default only when it applies to most transactions.
7. Save.

![Sales tax template](/files/sales-tax-template.webp)

Review whether purchase tax should be added to valuation, treated as recoverable input tax, or posted as an expense.

## Use Tax Categories

A Tax Category identifies a tax treatment, such as domestic standard, export, or exempt.

![Tax Category](/files/tax-category.webp)

Assign the category to parties or transactions. Then use a [Tax Rule](https://docs.frappe.io/erpnext/tax-rule) to choose the correct template based on company, Customer, Supplier, item, territory, billing or shipping location, and validity dates.

## Configure item-specific tax rates

Use an [Item Tax Template](https://docs.frappe.io/erpnext/item-tax-template) when particular Items have a different rate or exemption. Link the template on the Item or transaction row.

## Test the configuration

Create representative draft Sales Invoices and Purchase Invoices for each tax treatment. Check the taxable value, each tax row, grand total, General Ledger preview, and printed tax information. Include discounts, returns, and foreign-currency cases in testing when they apply.

## Withholding and localization

Withholding tax uses separate [Tax Withholding Category](https://docs.frappe.io/erpnext/tax-withholding-category) configuration. Country-specific apps may add tax identifiers, reports, e-invoicing, and statutory validations. Follow the localization documentation when it overrides generic setup.

## Troubleshooting

**The wrong tax template is selected**

Check the Tax Category, Tax Rule priority and validity, party and address data, company, and transaction date.

**Tax is missing for one Item**

Review its Item Tax Template and the tax account mapping in the transaction template.

**Tax is calculated on the wrong value**

Check the row calculation type and whether the charge is based on Net Total, Previous Row Total, Previous Row Amount, or Actual.

## Related topics

- [Tax Rule](https://docs.frappe.io/erpnext/tax-rule)
- [Item Tax Template](https://docs.frappe.io/erpnext/item-tax-template)
- [Sales Taxes and Charges Template](https://docs.frappe.io/erpnext/sales-taxes-and-charges-template)
- [Tax Withholding Category](https://docs.frappe.io/erpnext/tax-withholding-category)