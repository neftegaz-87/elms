---
title: "Calculating Freight in taxes in ERPNext"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/calculatin-freight-in-taxes-in-erpnext"
updated: "2026-09-29"
---

## Use case: Calculate freight forwarding charges with a tax rate

When freight forwarding charges need to be calculated as a tax rate, follow the steps below.

1. Create a ledger for freight charges under the tax or expense accounts in the **Chart of Accounts**, for example, Freight and Forwarding Charges. Alternatively, you can use an existing tax account for calculating the freight charges.

![Freight and Forwarding Charges account](/files/buying-freight-account.webp)

2. Create a non-stock Item named **Freight and Forwarding**, with **Maintain Stock** unchecked and **Allow Purchase** checked.

![Freight and Forwarding item](/files/buying-freight-item.webp)

3. Create a Purchase Invoice for the supplier and add this item. In the **Purchase Taxes and Charges** table, add a row with the freight account as the **Account Head**. Set the **Type** to **On Net Total** or **On Item Quantity**, as per your company policy, and enter the **Tax Rate**.

![Purchase Taxes and Charges table](/files/buying-po-taxes-and-charges.webp)