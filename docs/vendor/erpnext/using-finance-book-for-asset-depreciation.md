---
title: "Using Finance Book for Asset Depreciation | ERPNext Documentation"
description: "Maintain separate statutory and management depreciation schedules for one ERPNext Asset using Finance Books."
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/using-finance-book-for-asset-depreciation"
updated: "2026-08-15"
---

Imagine Nova Industries must report a machine one way in its statutory accounts, but management wants a second view for internal planning. The law may allow a ten-year useful life, while managers may prefer five years because they expect to replace the machine sooner.



Finance Books allow both views to exist without changing the original asset cost. ERPNext can keep a separate depreciation schedule for each book, so the finance team can compare statutory reporting with its internal view.

## Configure Finance Books

Create each [Finance Book](https://docs.frappe.io/erpnext/finance-book) and add its depreciation policy to the Asset Category.

![Statutory and management Finance Books on an Asset Category](https://novacompanies.m.frappe.cloud/files/03-asset-category-finance-books.png)

## Apply them to an Asset

Review the rows copied to the Asset. Each row can use its own method, frequency, useful life, residual value, and start date.

![Parallel Finance Book rows on an ERPNext Asset](https://novacompanies.m.frappe.cloud/files/08-asset-finance-books.png)

## Report by Finance Book

Select the intended Finance Book in asset and accounting reports. Leaving the filter blank can include default-book behavior and may not answer a policy-specific question.

![Asset balances report used with Finance Book filters](https://novacompanies.m.frappe.cloud/files/23-asset-depreciations-balances-v2.png)

## Troubleshooting

### A report shows the wrong depreciation values

Check the report's Finance Book filter and whether **Include Default Finance Book Assets** is enabled.

### Only one schedule exists

Confirm the Asset contains a complete row for every required Finance Book before submission.

## Frequently asked questions

### Does a Finance Book create a separate asset?

In ERPNext, no. It creates a separate accounting schedule for the same Asset.

### Can Finance Books use different methods?

In ERPNext, yes. That is one of their main purposes.

### Which Finance Book posts by default?

The company or transaction defaults determine the default view. Always set an explicit filter when validating a specific reporting basis.

## Related topics

- [Asset Category](https://docs.frappe.io/erpnext/asset-category)
- [Asset Location](https://docs.frappe.io/erpnext/asset-location)
- [Asset](https://docs.frappe.io/erpnext/asset)
- [Purchasing an Asset](https://docs.frappe.io/erpnext/purchasing-an-asset)
- [Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- [Asset Movement](https://docs.frappe.io/erpnext/asset-movement)
- [Asset Repair](https://docs.frappe.io/erpnext/asset-repair)
- [Asset Reports](https://docs.frappe.io/erpnext/asset-reports)