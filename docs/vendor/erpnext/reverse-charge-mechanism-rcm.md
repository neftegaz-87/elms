---
title: "Reverse Charge Mechanism (RCM)"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/reverse-charge-mechanism-rcm"
updated: "2026-08-14"
---

Nova Industries buys a specialist service from Orion Advisory, a supplier that does not charge tax on its invoice. Local rules require Nova, as the buyer, to recognise and settle the tax itself. Reverse charge accounting separates the supplier payable from the tax liability and, where allowed, records the related input tax credit.



ERPNext provides the accounting building blocks, but the tax rate, eligibility, return reporting, and account classification come from your local tax rules. Have a tax adviser approve the template before production use.

## Set up the accounts


| Account              | Purpose                                    |
| -------------------- | ------------------------------------------ |
| RCM Tax Payable      | Liability for tax the company must settle. |
| RCM Input Tax Credit | Eligible recoverable tax.                  |
| RCM Tax Expense      | Non-creditable portion, when applicable.   |


## Create a purchase tax template

1. Create a Purchase Taxes and Charges Template dedicated to reverse charge.
2. Add a tax row that credits the RCM payable account at the approved rate.
3. Add a matching input-credit row when the tax is recoverable, or use an expense account for the non-creditable portion.
4. Test the supplier payable, tax liability, input credit, and invoice total before enabling the template for routine use.

![Purchase Taxes and Charges Template used as the base for reverse charge](https://novacompanies.m.frappe.cloud/files/docs-tax-compliance-20260803-taxes-compliance-tax-templates-purchase-template-overview.png)



![Purchase tax row with calculation and account fields](https://novacompanies.m.frappe.cloud/files/docs-tax-compliance-20260803-taxes-compliance-tax-templates-purchase-template-tax-row.png)



## Apply and verify

1. Create the Purchase Invoice for the supplier’s bill amount.
2. Apply the RCM template in Taxes and Charges.
3. Confirm the supplier outstanding amount does not incorrectly include tax the supplier did not charge.
4. Submit and inspect Accounting Ledger or General Ledger.
5. Settle or adjust the RCM payable through the approved tax-payment process.

![Transaction result after applying a purchase tax template](https://novacompanies.m.frappe.cloud/files/docs-tax-compliance-20260803-taxes-compliance-tax-templates-purchase-template-result.png)



## Troubleshooting

### The supplier payable includes the reverse charge tax

Review Add or Deduct, Included in Print Rate, account heads, and the second input-credit or expense row. The supplier should normally remain payable only for the supplier bill when the supplier did not charge the tax.

### The tax credit is only partly eligible

Split the amount between an input-credit account and a tax-expense account using approved rates or rows.

## Frequently asked questions

### Is this configuration country-neutral?

The accounting pattern is reusable, but the legal rules are not. Use country-specific rates, accounts, returns, and evidence.

## Related topics

- [Accounting overview](/erpnext/accounting/introduction)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [General Ledger](/erpnext/general-ledger)
- [Fiscal Year](/erpnext/fiscal-year)