---
title: "Buying Reports"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/buying_reports"
updated: "2026-09-29"
---

Data pertaining to purchases made by an organization can be analyzed and visualized through various reports available in the Buying module. All buying reports are listed under the Reports section in the Buying sidebar. Most reports have three sections: a filter bar, a chart, and a data table. Any change to the filters is immediately reflected in the chart and the data.

## Purchase Analytics

To access the report, go to:

> Buying &gt; Reports &gt; Purchase Analytics

![Purchase Analytics report](/files/buying-purchase-analytics.webp)

The Purchase Analytics report lets you analyze purchase data by Supplier, Supplier Group, Item, or Item Group over a given period and frequency (Weekly, Monthly, Quarterly, or Yearly). You can base the report on Purchase Orders, Purchase Receipts, or Purchase Invoices, and view either the value or the quantity. Select rows in the data table to plot them on the chart. For a parent company, enable Show Aggregate Value from Subsidiary Companies to include data from its subsidiaries.

## Purchase Order Analysis

To access the report, go to:

> Buying &gt; Reports &gt; Purchase Order Analysis

![Purchase Order Analysis report](/files/buying-purchase-order-analysis.webp)

This report helps you track items in Purchase Orders over a given period, along with their receipt and billing status. The chart compares the billed amount with the amount still to be billed. You can filter by Project, Purchase Order, and Status, and enable Group by Purchase Order to view the data per order.

## Requested Items to Order and Receive

To access the report, go to:

> Buying &gt; Reports &gt; Requested Items to Order and Receive

![Requested Items to Order and Receive report](/files/requested-items-to-order-and-receive.webp)

This report shows items requested through Material Requests of type Purchase, and how much of each item is still to be ordered and received. The chart compares Qty to Order, Ordered Qty, Received Qty, and Qty to Receive for each item. You can filter by Material Request and Item, and enable Group by Material Request to view the data per request.

## Purchase Order Trends

To access the report, go to:

> Buying &gt; Reports &gt; Purchase Order Trends

![Purchase Order Trends report](/files/buying-purchase-order-trends.webp)

Through this report, you can visualize Purchase Order trends for a given fiscal year. The trend can be based on Item, Item Group, Supplier, Supplier Group, or Project, and shown Monthly, Quarterly, Half-Yearly, or Yearly. Use the Group By filter to further group the data by Item or Supplier, and enable Include Closed Orders to include closed Purchase Orders.

## Procurement Tracker

To access the report, go to:

> Buying &gt; Reports &gt; Procurement Tracker

![Procurement Tracker report](/files/procurement-tracker.webp)

This report tracks the entire procurement cycle in one view, from Material Requests to the Purchase Orders created against them. For each item, it shows the requestor, quantity, status, supplier, estimated and actual costs, and the expected and actual delivery dates. You can filter by Cost Center, Project, and date range.

## Other Reports

The following reports are also available under Buying &gt; Reports:

- **Items To Be Requested**: Items that need to be requested based on their stock levels.
- **Item-wise Purchase History**: Item-level purchase history from Purchase Orders.
- **Purchase Receipt Trends**: Trends for Purchase Receipts over a fiscal year.
- **Purchase Invoice Trends**: Trends for Purchase Invoices over a fiscal year.
- **Item Wise Consumption**: Consumption of items based on stock transactions.
- **Supplier Quotation Comparison**: Compares rates quoted by different suppliers for the same items.
- **Supplier Addresses And Contacts**: Addresses and contacts of all suppliers.
- **Subcontract Order Summary**: Summary of Subcontracting Orders and their status.
- **Materials To Be Transferred**: Raw materials yet to be transferred to subcontractors.
- **Items To Be Received**: Subcontracted items yet to be received from subcontractors.