---
title: "Fetch shipping charges based item's value or weight "
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/can-we-fetch-shipping-charges-based-items-value-or-weight-in-po"
updated: "2026-09-29"
---

In a Purchase Order, you can fetch the shipping charges for items automatically, based on their value or weight, using a Shipping Rule.

To set this up:

1. Go to the **Shipping Rule** list and click **New**.
2. Enter the **Shipping Rule Label** and set the **Shipping Rule Type** to **Buying**.
3. Select the **Company** and the **Shipping Account**.
4. Set **Calculate Based On** to **Net Total** or **Net Weight**.
5. In the **Shipping Rule Conditions** table, add the **From Value**, **To Value**, and **Shipping Amount** for each range. A To Value of 0 means there is no upper limit.
6. Click **Save**.

![Shipping Rule](/files/buying-shipping-rule.webp)

Now, select this rule in the **Shipping Rule** field of a Purchase Order. The shipping charges are added automatically as a row in the **Purchase Taxes and Charges** table, based on the items' net total or net weight. In the example below, the total net weight is 2 kg, so a shipping charge of $25 is applied.

![Shipping charges in Purchase Order](/files/buying-po-shipping-charges.webp)