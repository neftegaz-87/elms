---
title: "Remove Description in Print Format"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/removing-description-removed-item-code-and-name"
updated: "2026-03-02"
---

 

**Question:**

I want to remove the description from the from my print format since it takes up too much space:

![](/files/cDYxb5o.png)

 

But when I do so using the [print format builder](/erpnext/print-format-builder), I end up losing my Item Code and Name as well. How to fix this?

![](/files/Fredaow.png)

 

 

**Answer:**

This is because you have **Compact Item Print** option enabled in the Print Settings.

![](/files/lCGM2tO.png)

 

You can disable this option and then uncheck the Description in the print format builder. This should solve the issue for you.

![](/files/6MI1aNw.png)