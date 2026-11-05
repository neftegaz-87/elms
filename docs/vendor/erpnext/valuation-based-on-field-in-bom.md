---
title: "Raw material valuation"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/valuation-based-on-field-in-bom"
updated: "2026-03-02"
---

**Question:** What are for various options in `Valuation Based On` in the Bill Of Materials (BOM)?

**Answer:** There are 3 available options in the *Valuation Based On* field:

![Nested BOM](/files/valuation-based-on-1.png)  


**Valuation Rate:** Item valuation rate is defined based on it's purchase or manufacture value.

For Purchase Item, it is defined based on charges entered in the Purchase Receipt. If you don't have any Purchase Receipt made for an item or a Stock Reconciliation, then there won't be any Valuation Rate for that item.

**Price List Rate:** This option allows to pull item rates from [Price List.](/erpnext/item-price)

**Last Purchase Rate:** It will be the last Purchase (Order) Rate of an item.

