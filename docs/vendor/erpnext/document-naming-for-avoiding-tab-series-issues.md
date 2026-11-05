---
title: "Document Naming for Avoiding tabSeries Issues"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/document-naming-for-avoiding-tab-series-issues"
updated: "2026-08-12"
---

When you save a document in ERPNext a Sales Invoice, Stock Entry, Payment, anything with an auto-generated number, the system has to figure out the next number in the sequence (eg. 0001, 0002, 0003 and so on).



To make sure two documents never get the same number, ERPNext keeps a single counter for each naming series in a table called tabSeries. Before giving out the next number, it locks that counter so nobody else can touch it, adds 1, and then unlocks it. This happens in a fraction of a second, so normally you never notice it.



If hundreds of documents are being created at the same time and they all use the same naming series, they all need the same counter. Only one can hold the lock at a time, so everyone else has to wait in line.



When the line gets long, you start seeing:

- Documents that take a long time to save
- Bulk imports or bulk submissions that crawl or get stuck
- Errors like "Record has changed since last read in table 'tabSeries'" or database lock/deadlock timeouts
- Background jobs piling up in the queue



This gets much worse after busy periods, month-end, or when more workers are added to handle load, because now even more transactions are fighting over that one counter.



### **Why it happens more with customisation**

A very common cause is a customisation that forces a lot of transactions through a single, restricted naming series. Everything funnels into one counter, so one counter becomes the bottleneck for the whole operation. The more you scale up, the longer the queue behind that single row.



### **The simple fix: use more than one naming series**

The counter is locked per naming series. So the trick is easy:

Give different groups of transactions their own naming series, so they use different counters and stop waiting on each other.

Instead of one big line at one counter, you open several counters. Each line moves independently and in parallel.



### **Good ways to split series**

Pick whatever naturally divides your transactions. For example:


|              |                                              |
| ------------ | -------------------------------------------- |
| **Split by** | **Example series**                           |
| Branch       | SINV-MUM-.YYYY.-.####, SINV-DEL-.YYYY.-.#### |
| Project      | SINV-PROJ-A-.####, SINV-PROJ-B-.####         |
| Cost Center  | SINV-CC01-.####, SINV-CC02-.####             |
| Department   | SINV-SALES-.####, SINV-SUPPORT-.####         |


The idea is the same in every case: transactions that run at the same time should not all sit on the same counter. The more you spread them out, the less each one has to wait.



### **Extra tips for very large operations**

If you regularly create huge batches of documents at once:



- Spread big imports across multiple series so the load is shared, instead of importing everything under one series.
- Provide the name yourself during imports/API calls where possible. If a document already has a name, ERPNext skips the counter entirely. No lock, no waiting. For example, customer ID is generated based on Customer Name itself.
- Avoid customisations that force everything into one narrow series. Review any custom naming logic to make sure it isn't funnelling all transactions through a single counter.
- Stagger very large jobs slightly rather than firing them all in the same instant, if the process allows it.