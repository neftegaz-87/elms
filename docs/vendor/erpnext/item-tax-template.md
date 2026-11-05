---
title: "Item Tax Template\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/item-tax-template"
updated: "2026-08-14"
---

An Item Tax Template changes the tax rate for a particular item without replacing the tax structure of the transaction. Use it when most items follow the standard rate but selected goods or services are reduced-rated, zero-rated, exempt, or outside a particular tax component.



The Sales or Purchase Taxes and Charges Template still supplies the tax account and calculation row. ERPNext then uses the Item Tax Template rate for the net amount of the matching item.



At Nova Industries, an electronics manufacturer and distributor, one Sales Invoice can contain:


| Item                 | Net amount  | Applicable rate | Tax        |
| -------------------- | -----------: | ---------------: | ----------: |
| NovaPhone X1         | $699.00     | 8%              | $55.92     |
| Device Setup Service | $149.00     | 4%              | $5.96      |
| Extended Warranty    | $99.00      | 0%              | $0.00      |
| **Total**            | **$947.00** |                 | **$61.88** |


The standard transaction template remains at 8%, while item templates override that rate for the second and third lines.

## Before you begin

Create the required tax account in the [Chart of Accounts](/erpnext/chart-of-accounts). Then create the relevant [Sales Taxes and Charges Template](/erpnext/sales-taxes-and-charges-template) or [Purchase Taxes and Charges Template](/erpnext/purchase-taxes-and-charges-template).

The tax account in the transaction template must match the account in the Item Tax Template. An item rate cannot calculate against an account row that is absent from the transaction.

In [Accounts Settings](/erpnext/accounts-settings), enable **Automatically Add Taxes and Charges from Item Tax Template** when ERPNext should add a missing tax row from an item's template. Even with this enabled, test the complete transaction because company, category, and template configuration still determine the final result.



![Automatically add Taxes and Charges from Item Tax Template](https://novacompanies.m.frappe.cloud/files/docs-tax-compliance-20260803-taxes-compliance-item-tax-template-enable-item-tax-template.png)

Decide whether the item is reduced-rated, zero-rated, exempt, or not applicable under your local rules. These classifications can have different reporting consequences, so confirm the intended treatment with your tax adviser.

## Create an Item Tax Template

Go to **Accounting &gt; Taxes &gt; Item Tax Template** and select **Add Item Tax Template**.

1. Enter a descriptive **Title**, such as `Nova Reduced Item Tax 4%`.
2. Select the **Company**.
3. In **Tax Rates**, add a row.
4. Select the tax account and enter the overriding rate.
5. Save the template.

Use the pencil icon to open the child-table row and review all its fields.



![Open an Item Tax Template rate row](https://novacompanies.m.frappe.cloud/files/docs-tax-compliance-20260803-taxes-compliance-item-tax-template-reduced-template-row.png)



![Tax account and rate in the Item Tax Template row](https://novacompanies.m.frappe.cloud/files/docs-tax-compliance-20260803-taxes-compliance-item-tax-template-reduced-template-fields.png)

You can add multiple rows when more than one tax component applies to the item. Each row must use the account that the corresponding transaction tax row uses.

## Important fields and what they mean


| Field          | What it controls                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------------------ |
| Title          | A reusable name that helps users identify the intended rate or treatment                               |
| Company        | Restricts the template to transactions for that company                                                |
| Tax            | The ledger account and tax component whose rate is overridden                                          |
| Tax Rate       | The rate used for the matching item's net amount                                                       |
| Not Applicable | Indicates that this tax component does not apply to the item, which is distinct from applying it at 0% |
| Disabled       | Prevents the template from being selected without deleting its history                                 |


Use a 0% rate when the supply is reported as taxable at zero percent. Use **Not Applicable** when the tax component does not apply to the item. Do not treat these as interchangeable unless that is correct for your jurisdiction and reporting setup.

## Assign the template to an Item

Open the [Item](/erpnext/item) and go to the **Tax** tab. In the **Taxes** table, add a row and use the pencil icon to open it.



![Open the Item Tax assignment row](https://novacompanies.m.frappe.cloud/files/docs-tax-compliance-20260803-taxes-compliance-item-tax-template-item-tax-assignment-row.png)

Set the Item Tax Template and, when relevant, its Tax Category and validity conditions.



![Item Tax Template assignment, Tax Category, and Valid From](https://novacompanies.m.frappe.cloud/files/docs-tax-compliance-20260803-taxes-compliance-item-tax-template-item-tax-assignment-fields.png)


| Assignment field             | What it controls                                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Item Tax Template            | The rate or treatment available for the item                                                                  |
| Tax Category                 | Restricts the assignment to transactions using that category; a blank category acts as the default assignment |
| Valid From                   | The first date on which ERPNext can use this assignment                                                       |
| Minimum and Maximum Net Rate | Restricts the assignment by the item's transaction net rate when configured                                   |


You can add multiple assignments for different Tax Categories or validity periods. Keep their conditions mutually clear so the intended row is easy to predict.

## How ERPNext chooses an item template

ERPNext first considers the Tax Category and transaction date. It uses the first valid matching assignment for the item. When no category-specific row matches, a valid row with a blank Tax Category can act as the default.

For most transactions, the posting or transaction date determines validity. On a [Purchase Invoice](/erpnext/purchase-invoice), ERPNext considers the Supplier Invoice Date before falling back to Posting Date. This matters when a supplier invoice arrives after a rate change but carries an earlier invoice date.

If more than one assignment is valid for the same category and date, ERPNext can use the first matching row. Avoid overlapping validity periods. Give the earlier assignment a clear end in your migration or change-control process, and verify a draft transaction on both sides of the rate-change date.

## Assign a template to an Item Group

Use an [Item Group](/erpnext/item-group) assignment when every item in a group shares the treatment. This reduces repeated setup for large catalogs.

An assignment on the Item is more specific and takes precedence over a group-level default. Use the group for the common rate and item-level rows for genuine exceptions. Test an item with its own assignment and another that inherits the group assignment before relying on the setup in production.

## Use the template in a transaction

Create a draft Sales Invoice, Purchase Invoice, Quotation, Sales Order, Purchase Order, Delivery Note, or Purchase Receipt that supports item tax calculation.

1. Select the company and party.
2. Confirm the [Tax Category](/erpnext/tax-category), when used.
3. Select the transaction Taxes and Charges Template.
4. Add the items.
5. Review the Item Tax Template on each applicable row.
6. Check the item-wise tax calculation, total tax, and Grand Total before submission.

The mixed-rate invoice below contains standard, reduced, and zero-rated lines. Open a row with the pencil icon when you need to inspect or change the Item Tax Template selected for that transaction line.



![Mixed-rate items on one Sales Invoice](https://novacompanies.m.frappe.cloud/files/docs-tax-compliance-20260803-taxes-compliance-item-tax-template-mixed-rate-invoice-items.png)



![Item Tax Template selected on a transaction row](https://novacompanies.m.frappe.cloud/files/docs-tax-compliance-20260803-taxes-compliance-item-tax-template-transaction-item-tax-template.png)

ERPNext calculates $55.92 on the $699 phone, $5.96 on the $149 service, and $0 on the $99 warranty. Total tax is therefore $61.88 and the Grand Total is $1,008.88.



![Mixed-rate tax and Grand Total result](https://novacompanies.m.frappe.cloud/files/docs-tax-compliance-20260803-taxes-compliance-item-tax-template-mixed-rate-tax-result.png)

## Select a different template on a transaction line

The Item master supplies the normal default. A user can select another eligible Item Tax Template directly in a draft transaction row when the specific transaction needs a different supported treatment.

Use manual selection as a controlled exception, not as a substitute for maintaining the Item master. The chosen template must belong to the correct company, match the transaction Tax Category when one is set, be valid for the transaction date, and use tax accounts present in the transaction tax table.

After changing a category, date, item, or item template, review the full Taxes and Charges table again. Re-add the affected item row when stale tax context does not refresh as expected.

## Use different rates on one invoice

Current ERPNext can calculate different item rates against the same tax account by maintaining an item-wise breakdown behind the transaction tax row. Separate tax accounts are still appropriate when the tax components must post or report separately, but different rates alone do not always require different ledger accounts.

If only templated items should be taxed, the standard transaction row can use a 0% rate while the Item Tax Templates supply the applicable rates. Test non-templated items carefully because they will inherit the transaction row's rate.

## Troubleshooting

### The Item Tax Template is marked invalid

Compare its company, Tax Category, validity date, and account with the transaction. Confirm that the matching account exists in the selected Sales or Purchase Taxes and Charges Template. Recheck the item row after changing the transaction category or date.

### The standard rate is applied to every item

Open the affected item row and confirm its Item Tax Template. Check the Item or Item Group assignment, Valid From date, Tax Category, and the transaction date. Verify that item-wise tax values are present before submission.

### Tax from one template appears on unrelated items

Review every tax account row and item assignment. Ensure templates use the intended account and category, and remove overlapping default assignments. Recreate a small draft with one item per treatment to isolate the configuration.

### A zero-rated item still appears in the tax breakdown

A 0% item can still belong to the tax component and appear in reporting with zero tax. If the component should not apply at all, evaluate the **Not Applicable** option and confirm the legal and reporting treatment before changing the setup.

## Frequently asked questions

### Does an Item Tax Template replace the transaction tax template?

1. It overrides the rate for matching item amounts. The transaction template still provides the tax row, account, charge type, and ledger destination.

### Can one invoice contain items taxed at several rates?

Y

es. Assign the appropriate item templates and keep the matching tax account in the transaction tax table. Review the item-wise breakdown and calculated total before submission.

### Should a tax-exempt item use 0% or Not Applicable?

That depends on how the supply must be classified and reported. A 0% rate generally means the tax applies at zero percent, while Not Applicable means the tax component does not apply. Confirm the correct treatment for your jurisdiction.

### Why does a template work on one transaction date but not another?

Check the assignment's Valid From value and any overlapping rows. For Purchase Invoices, also inspect Supplier Invoice Date because it can determine which assignment is valid.

### Can I set the template on an Item Group instead of every Item?

Y

es. Use an Item Group assignment for a shared default and Item-level assignments for exceptions. The more specific Item assignment takes precedence.

## Related topics

- [Taxes](/erpnext/taxes)
- [Tax Category](/erpnext/tax-category)
- [Tax Rule](/erpnext/tax-rule)
- [Sales Taxes and Charges Template](/erpnext/sales-taxes-and-charges-template)
- [Purchase Taxes and Charges Template](/erpnext/purchase-taxes-and-charges-template)
- [Sales Invoice](/erpnext/sales-invoice)
- [Purchase Invoice](/erpnext/purchase-invoice)