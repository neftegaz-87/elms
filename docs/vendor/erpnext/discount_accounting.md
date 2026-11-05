---
title: "Discount Accounting | ERPNext Documentation"
description: "Configure ERPNext discount accounting to post sales discounts separately, then verify item, invoice total, and General Ledger values with a clear example."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/discount_accounting"
updated: "2026-08-03"
---

Discount Accounting lets ERPNext show a sales discount separately in the [General Ledger](/erpnext/general-ledger) instead of posting only the reduced revenue. Use it when finance needs to report gross sales and discounts allowed as distinct amounts.



This setting changes accounting presentation. It does not decide who receives a discount or calculate promotional eligibility. Configure the commercial discount using the normal [discount fields](/erpnext/applying-discount), a [Pricing Rule](/erpnext/pricing-rule), or another approved pricing method.



For example, Nova Electronics Trading invoices two phones at a list price of $699 each. It applies a 10% item discount and then a 5% additional discount. With Discount Accounting enabled, ERPNext posts:


| Account                 | Debit     | Credit    | Meaning                                                      |
| ----------------------- | ---------: | ---------: | ------------------------------------------------------------ |
| Debtors                 | $1,195.29 | $0.00     | Amount owed by the Customer.                                 |
| Sales                   | $0.00     | $1,398.00 | Revenue before the discounts.                                |
| Sales Discounts Allowed | $202.71   | $0.00     | Item discount of $139.80 plus additional discount of $62.91. |


Without separate discount accounting, the same commercial discount normally reduces the net revenue represented by the invoice lines instead of appearing as a separate discount-account debit.

## Before you begin

Confirm the following:

1. The discount account exists in the [Chart of Accounts](/erpnext/chart-of-accounts) for each Company that will use it. Confirm with your accountant whether it should be an expense account or a contra-revenue account in your reporting structure.
2. The [Item](/erpnext/item) has an applicable [Item Price](/erpnext/item-price) in the intended [Price List](/erpnext/price-lists). Item discounts use Price List Rate as their reference.
3. Users can create and submit a [Sales Invoice](/erpnext/sales-invoice) and view its ledger.
4. You have tested the expected posting with representative taxes, currencies, rounding, and discounts before enabling the workflow for regular transactions.

## Enable Discount Accounting for selling

Two settings control the current workflow.

1. Open [Selling Settings](/erpnext/selling-settings).
2. Select **Advanced Features**.
3. Enable **Enable discount accounting for selling** and save.

![Selling Settings with Enable discount accounting for selling highlighted](https://novacompanies.m.frappe.cloud/files/docs-gl-2026-discount-accounting-enable-selling-discount-accounting.png)

This setting tells ERPNext to create additional ledger entries for sales discounts in the selected Discount Account.

4. Open [Accounts Settings](/erpnext/accounts-settings).
5. Select **Invoice and Billing**.
6. Enable **Enable Discounts and Margin** and save.

![Accounts Settings with Enable Discounts and Margin highlighted](https://novacompanies.m.frappe.cloud/files/docs-gl-2026-discount-accounting-enable-discounts-and-margin.png)

This setting makes the discount and margin controls available for transaction items. It does not, by itself, create a separate discount-account posting.

## Set a default Discount Account for an Item

A default avoids selecting the account on every invoice row.

1. Open the Item.
2. Select **Accounting**.
3. In **Item Defaults**, find the row for the Company.
4. Select the highlighted pencil icon to open the complete row editor.

![Item Defaults row with the pencil icon highlighted](https://novacompanies.m.frappe.cloud/files/docs-gl-2026-discount-accounting-item-default-row.png)

5. Set **Discount Account** to the Company account that should receive item-level and invoice-level sales discounts.
6. Save the Item.

![Item Default with Discount Account highlighted](https://novacompanies.m.frappe.cloud/files/docs-gl-2026-discount-accounting-item-default-discount-account.png)

The Item Default is Company-specific. Configure a valid account and other defaults for each Company rather than copying an account from a parent or sibling Company.

## Record an item-level discount

1. Create a Sales Invoice and select the Company and Customer.
2. Add the Item to the **Items** table.
3. Select the highlighted pencil icon on the item row.

![Sales Invoice item row with the pencil icon highlighted](https://novacompanies.m.frappe.cloud/files/docs-gl-2026-discount-accounting-sales-invoice-item-row.png)

4. Expand **Discount and Margin**.
5. Enter **Discount (%) on Price List Rate with Margin** or **Discount Amount**.

![Sales Invoice item discount percentage highlighted](https://novacompanies.m.frappe.cloud/files/docs-gl-2026-discount-accounting-sales-invoice-item-discount-percentage.png)

6. Expand **Accounting Details**.
7. Confirm the **Discount Account**. ERPNext fetches the Item Default when one is configured, but you remain responsible for verifying the account on the transaction.

![Sales Invoice item Discount Account highlighted](https://novacompanies.m.frappe.cloud/files/docs-gl-2026-discount-accounting-sales-invoice-item-discount-account.png)

In the example, the Price List Rate is $699 and the item discount is 10%. For two units, ERPNext records an item discount of $139.80 and an amount of $1,258.20 before the invoice-wide discount.

## Record an additional discount on the invoice

Use an additional discount when the reduction applies to the complete transaction instead of one item row.

1. Expand **Additional Discount** on the Sales Invoice.
2. Set **Apply Additional Discount On** to **Net Total** or **Grand Total**.
3. Enter **Additional Discount Percentage** or **Additional Discount Amount**.
4. Select the **Discount Account**.

![Sales Invoice Additional Discount fields and Discount Account highlighted](https://novacompanies.m.frappe.cloud/files/docs-gl-2026-discount-accounting-sales-invoice-additional-discount.png)

In the example, 5% of the $1,258.20 Net Total is $62.91. The item and additional discounts therefore total $202.71.

Apply on Net Total and Apply on Grand Total can produce different tax and net-value results. Review the tax breakup, rounding, and final amount with the configuration used by your business.

## Submit and verify the ledger

1. Review the discount amounts, taxes, Grand Total, and Discount Accounts.
2. Save and submit the Sales Invoice.
3. Open **View &gt; Ledger**, or run General Ledger for the invoice voucher.

The submitted example has a Grand Total and outstanding amount of $1,195.29.



![Submitted Sales Invoice total after discounts](https://novacompanies.m.frappe.cloud/files/docs-gl-2026-discount-accounting-submitted-sales-invoice-total.png)

The ledger shows gross Sales of $1,398.00, a $202.71 debit to Sales Discounts Allowed, and a $1,195.29 debit to Debtors.



![General Ledger showing the separate Sales Discounts Allowed entry](https://novacompanies.m.frappe.cloud/files/docs-gl-2026-discount-accounting-discount-account-general-ledger.png)

Do not treat the invoice as verified merely because its total looks correct. Confirm that the discount account, gross revenue, receivable, tax, currency, Cost Center, and any other [accounting dimensions](/erpnext/accounting-dimensions) appear as intended.

## Important fields and what they mean


| Field                                    | What it controls                                                                                                                |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Enable discount accounting for selling   | Creates separate sales-discount ledger entries when the required Discount Accounts are present.                                 |
| Enable Discounts and Margin              | Makes discount and margin controls available on supported transaction item rows.                                                |
| Price List Rate                          | Reference rate before item discount and margin. Overwriting Rate can change the calculated discount relative to this reference. |
| Discount Percentage                      | Percentage reduction calculated against the Price List Rate after applicable margin behavior.                                   |
| Discount Amount                          | Monetary reduction represented on the item row.                                                                                 |
| Item Discount Account                    | Account used for the item-level discount ledger posting.                                                                        |
| Apply Additional Discount On             | Chooses whether the transaction-level discount uses Net Total or Grand Total as its basis.                                      |
| Additional Discount Percentage or Amount | Transaction-wide reduction after item-level pricing has been calculated.                                                        |
| Additional Discount Account              | Account used for the invoice-wide discount ledger posting.                                                                      |


## Purchase discounts

The current ERPNext develop version supports separate Discount Account posting for selling. A [Purchase Invoice](/erpnext/purchase-invoice) still supports item and additional discount values, but its current standard fields do not provide the equivalent Purchase Invoice Item Discount Account or Additional Discount Account used by this sales workflow.

Do not force a sales-only field into a Purchase Invoice through customization without reviewing the accounting logic. If your organization must report purchase discounts separately, define the required treatment with your accountant and validate the supported transaction or [Journal Entry](/erpnext/journal-entry) process in a test Company.

## Troubleshooting


| Issue                                                     | What to check                                                                                                                                                                                              |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Discount and Margin is unavailable                        | Confirm **Enable Discounts and Margin** is enabled, the invoice is in Draft, and Price List Rate is not zero. Open the item row with the pencil icon.                                                      |
| Discount Account is unavailable                           | Confirm **Enable discount accounting for selling** is enabled, reload the invoice after saving the setting, and expand **Accounting Details** in the item row.                                             |
| No separate discount ledger entry is posted               | Verify the selling setting, the item or additional Discount Account, and the submitted invoice ledger. A visible commercial discount does not automatically prove separate accounting is enabled.          |
| The discount amount is unexpectedly negative or too large | Compare Price List Rate, Margin, Rate, Discount Percentage, and Discount Amount. ERPNext treats the difference between the reference Price List Rate and the entered Rate as part of pricing calculations. |
| The wrong Company account is selected                     | Correct the Company-specific Item Default and the invoice row before submission. Accounts cannot be shared across unrelated Companies.                                                                     |


## Frequently asked questions

### Does Discount Accounting change the amount the Customer owes?

No, it changes how the discount is presented in the ledger. The invoice total still reflects the commercial discount entered on the transaction.

### Can I use both an item discount and an additional discount?

Yes, ERPNext applies both. Review the effective discount and the ledger, because both values can post to the selected discount account.

### Why is the calculated discount different after I overwrite Rate?

Item discount is based on Price List Rate and margin behavior. If you replace Rate directly, ERPNext can represent the difference from Price List Rate as a discount or negative discount. Set an intentional Item Price or editable Price List Rate when that better represents the commercial baseline.

### Should the Discount Account be an expense or contra-revenue account?

That depends on your chart and reporting policy. ERPNext posts the value to the account you select. Your accountant should decide its classification and where it appears in financial reports.

### Does the same separate-account workflow work for Purchase Invoices?

Not in the current standard develop fields. Purchase transactions support commercial discount values, but the equivalent purchase-side Discount Account controls documented on older versions are no longer present.

## Related topics

- [Apply Discounts to Sales Transactions](/erpnext/applying-discount)
- [Sales Invoice](/erpnext/sales-invoice)
- [Pricing Rule](/erpnext/pricing-rule)
- [Selling Settings](/erpnext/selling-settings)
- [Chart of Accounts](/erpnext/chart-of-accounts)
- [General Ledger](/erpnext/general-ledger)
- [Purchase Invoice](/erpnext/purchase-invoice)