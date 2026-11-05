---
title: "Purchase invoice for Services"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/item-creation-not-required-in-purchase-invoice"
updated: "2026-09-29"
---

You can record the purchase of services, such as installation, maintenance, or consulting, using a Purchase Invoice with a non-stock service item.

### 1. Set Up Supplier

1. Go to **Buying &gt; Supplier**.
2. If the supplier does not exist, click **New**, enter the supplier's details (name, contact information, address), and click **Save**.

### 2. Create a Service Item

1. Go to **Stock &gt; Item** and click **New**.
2. Enter the **Item Name** and item code.
3. In the **Item Group** field, select or create a group for services, for example, Services.
4. Uncheck **Maintain Stock**, since services are not stocked.
5. Make sure **Allow Purchase** is checked.
6. Fill in other relevant details, such as the unit of measure and description, and click **Save**.

![Service Item](/files/buying-service-item.webp)

### 3. Create a Purchase Invoice

1. Go to **Buying &gt; Purchase Invoice** and click **New**.
2. Enter the invoice details:
  - **Supplier**: Select the supplier from whom the service was received.
  - **Posting Date**: Enter the date of the invoice.
  - **Supplier Invoice No**: Enter the invoice number provided by the supplier.
3. Add the service details in the **Items** table:
  - **Item**: Select the service item you created earlier.
  - **Qty** and **Rate**: Enter the quantity and rate for the service.
  - **Expense Account**: Ensure the service cost is booked to the appropriate expense account. You can set this in the item row's **Accounting Details**.
4. If applicable, add taxes or other charges in the **Purchase Taxes and Charges** table.
5. Review the details and click **Save**.

![Purchase Invoice for a service item](/files/buying-service-purchase-invoice.webp)

### 4. Submit the Invoice

Once the details are confirmed, click **Submit** to finalize the invoice.