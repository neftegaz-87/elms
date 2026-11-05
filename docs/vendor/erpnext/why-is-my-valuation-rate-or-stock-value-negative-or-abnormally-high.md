---
title: "Why is my valuation rate or stock value negative or abnormally high?"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/why-is-my-valuation-rate-or-stock-value-negative-or-abnormally-high"
updated: "2026-10-13"
---

A negative or very high valuation rate almost always comes from one wrong stock transaction, not from a bug in the valuation method. Find that transaction in the **Stock Ledger**, correct it, then run **Repost Item Valuation** so every later entry is recalculated.

You may be seeing one of these symptoms:

- **Stock Balance** shows a negative *Balance Value* while the quantity is positive.
- The valuation rate of an item suddenly jumps to 10x or 1000x its normal cost.
- *Cost of Goods Sold* on a Delivery Note or Sales Invoice is far too high, or negative.
- A BOM or Stock Entry picks up an unexpected rate for a raw material.

## Common causes

The valuation rate is the balance value divided by the balance quantity. So when a value is booked at the wrong rate, and only a small quantity is left, the rate is pushed far off.


| Cause                    | What goes wrong                                                                                                                                                                                                                         | What you see in the Stock Ledger                                                                                                 |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Negative stock**       | With *Allow negative stock* on in **Stock Settings**, stock is issued before it is received. The outgoing entries use a guessed or old rate. When the receipt arrives, its rate is different, and the gap stays in the balance value.   | *Balance Qty* goes below zero, then a receipt is followed by a jump in *Avg Rate (Balance Stock)* or a negative *Balance Value*. |
| **Zero-rate receipts**   | A Purchase Receipt, Material Receipt or Stock Reconciliation is saved with a rate of 0 (often with *Allow Zero Valuation Rate* ticked). This drags the average down. Later issues at the old rate can take out more value than is left. | *Incoming Rate* is 0 on a receipt, followed by a falling rate and later a negative *Balance Value*.                              |
| **Backdated entries**    | A transaction posted before existing entries changes the rate of every later entry. If the repost is still queued or has failed, later entries keep their old values.                                                                   | Entries after the backdated one do not add up. A **Repost Item Valuation** record for that item shows *Queued* or *Failed*.      |
| **Serial No items**      | Each Serial No carries the rate it was received at. If a serial number came in at the wrong rate (or at 0), every transfer and delivery of it moves that wrong rate.                                                                    | *Incoming Rate* on a Material Transfer or Delivery Note is very different from the item's usual cost.                            |
| **Wrong UOM conversion** | The item is bought in one UOM (for example *Box*) but stocked in another (*Nos*). A wrong *UOM Conversion Factor* divides the amount over too few or too many units.                                                                    | *In Qty* looks wrong for the document, and *Incoming Rate* is a multiple (for example 12x) of the expected rate.                 |


## Find the entry where the rate went wrong

The **Stock Ledger** report lists every movement of the item in order, so you can see the exact voucher where the rate broke.

1. Go to **Stock &gt; Reports &gt; Stock Ledger**.
2. Set *Company*, *Item* and *Warehouse*. Set *From Date* far enough back to cover the last time the rate looked normal.
3. Read these columns from top to bottom:
  - **Incoming Rate** — the rate of each receipt. Look for a 0, or a rate far above the normal cost.
  - **Balance Qty** — look for any row where it goes below zero.
  - **Avg Rate (Balance Stock)** — the valuation rate after each entry. Find the first row where it jumps or turns negative.
  - **Balance Value** — this should be close to *Balance Qty* x *Avg Rate*. A negative value with a positive quantity marks the problem.
4. Open the voucher in *Voucher #* on that first wrong row, and the receipt just before it. One of them is your source entry.

Check one warehouse at a time. Each warehouse has its own valuation rate, so a problem in one can look like a sudden jump in a transfer to another.

To find all affected items at once, use the **Stock Ledger Invariant Check** and **Incorrect Stock Value Report** reports. Also check the **Repost Item Valuation** list for records with status *Failed*.

## Fix the source entry, then repost

Correct the source entry first. Reposting alone runs the same wrong numbers again.

**1. Correct the source entry**


| If the cause is                      | Do this                                                                                                                              |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Negative stock                       | Post the missing receipt with a posting date and time *before* the first issue, so stock never goes below zero.                      |
| Zero-rate receipt                    | Cancel and amend the receipt with the correct rate. For a Stock Reconciliation, amend it with the right *Valuation Rate*.            |
| Wrong rate on a Purchase Receipt     | Cancel and amend it. If only freight or duty is missing, use a **Landed Cost Voucher** instead.                                      |
| Wrong UOM conversion                 | Fix the *Conversion Factor* in the item's UOM table. Then cancel and amend the affected documents.                                   |
| Serial No received at the wrong rate | Cancel and amend the original receipt of that Serial No. Later transfers and deliveries pick up the corrected rate after the repost. |


**2. Run Repost Item Valuation**

Cancelling or amending a backdated entry usually creates a repost on its own. Create one by hand if it did not, or if the earlier one failed.

1. Go to **Repost Item Valuation &gt; New**.
2. Set *Based On*:
  - **Item and Warehouse** — enter *Item Code*, *Warehouse*, and the *Posting Date* and *Posting Time* of the source entry (or slightly earlier).
  - **Transaction** — enter the *Voucher Type* and *Voucher No* of the source entry.
3. Save and submit. The repost runs in the background. Its *Status* moves from *Queued* to *In Progress* to *Completed*.
4. If the status is *Failed*, read the *Error Log* field. It usually names a negative-stock row you still need to fix. Fix it and click *Restart*.
5. Run the **Stock Ledger** again and confirm that *Avg Rate (Balance Stock)* is now normal.

The repost also updates the General Ledger, so stock and accounts values match again. Reposts can be limited to certain hours in **Stock Reposting Settings**; if nothing happens, check the timeslot there.

## Why the BOM or Sales Invoice rate can differ from the Stock Ledger

The rates in a BOM and on a Sales Invoice are taken at a different time, or from a different place, than the Stock Ledger. A difference is not always an error.


| Document                        | Where its rate comes from                                                                                                                                                      | Why it differs                                                                                                                                                                                                       |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **BOM**                         | *Rate of Materials based on*: Valuation Rate, Last Purchase Rate or Price List. With Valuation Rate, it takes the average across warehouses (or the source warehouse, if set). | The cost is fixed when the BOM is saved. It changes only when you click **Update Cost**, or when *Update BOM Cost Automatically* is on in **Manufacturing Settings**. The Stock Ledger is per warehouse and current. |
| **Sales Invoice**               | The *Rate* is the selling price from the Price List or Pricing Rule, not the cost.                                                                                             | Cost of goods sold is booked by the Delivery Note, or by the invoice only when *Update Stock* is ticked. That uses the valuation rate at its posting date and time.                                                  |
| **Delivery Note / Stock Entry** | The valuation rate at the posting date and time, in the source warehouse.                                                                                                      | A later backdated entry changes this rate after the document is submitted. The repost updates it, but a printed copy keeps the old value.                                                                            |


If the BOM shows a wrong raw material cost, fix the raw material's valuation first (see above). Then open the BOM and click **Update Cost**.

## Prevent it

Most of these problems stop once negative stock is off and every receipt carries a real rate.

- **Keep negative stock disabled.** In **Stock Settings**, leave *Allow negative stock* unticked. Users then cannot issue stock before it is received.
- **Set a valuation rate on every receipt.** Do not tick *Allow Zero Valuation Rate* unless the item is truly free, such as a free sample. Set a *Valuation Rate* on the Item master for opening stock and free items.
- **Check UOM conversion factors** on the Item master before the first purchase in a new UOM.
- **Limit backdated entries.** Use *Role allowed to create/edit back-dated transactions* in **Stock Settings** so only a few users can post them.
- **Watch the repost queue.** Check the **Repost Item Valuation** list each week for *Failed* records. Fix each one before more entries pile up on top.

## Still need help?

If the rate is still wrong after a completed repost, raise a ticket on [support.frappe.io](https://support.frappe.io). Include:

- The item code and warehouse
- A Stock Ledger export covering the period where the rate went wrong
- The name of the Repost Item Valuation record, and its *Error Log* if it failed