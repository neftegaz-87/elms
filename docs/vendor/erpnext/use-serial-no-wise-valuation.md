---
title: "Use Serial No Wise Valuation"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/use-serial-no-wise-valuation"
updated: "2026-09-16"
---

A new checkbox on the **Item** master that decides *how a serialised item is costed* (COGS / Valuation Rate). It does not change whether serial numbers are tracked - they are always tracked. It only changes how the cost of an outgoing piece (COGS / Valuation Rate) is worked out.

It is **ticked by default**, so nothing changes for your existing items unless you untick it.

## The Short Version


|                                    | Ticked (default)                    | Unticked                |
| ---------------------------------- | ----------------------------------- | ----------------------- |
| Serial numbers created and tracked | Yes                                 | Yes                     |
| Cost stored per serial number      | Yes                                 | No                      |
| Cost of an outgoing piece          | The price paid for that exact piece | The item's average cost |
| Good for                           | Hundreds of serials                 | Millions of serials     |


**Rule of thumb:** if you can imagine counting your serial numbers by hand, keep it ticked. If you receive them by the truckload, untick it.

## What It Actually Does

### When it is ticked

Every serial number carries its own cost.

You buy laptop `LAP-001` for ₹50,000 and laptop `LAP-002` for ₹55,000. When `LAP-002` is delivered, ERPNext looks up that exact serial number and takes ₹55,000 out of stock value. Exactly right, piece by piece.

To do this, ERPNext stores and reads a cost for **every single serial number**.

### When it is unticked

Serial numbers are still created. You can still see which piece went to which customer, still handle warranty claims, still trace a recall. Nothing about traceability changes.

The only difference is costing. ERPNext stops keeping a separate cost per serial number and uses **one average cost** for the whole item.

## When You Should Keep It Ticked

Keep serial-wise valuation on when **the price of each piece genuinely differs and that difference matters to your accounts**.

Typical cases:

- **Machinery and equipment** — each unit is expensive and bought at a negotiated price.
- **Laptops, servers, medical devices** — configurations differ, so prices differ.
- **Vehicles** — every unit has its own cost, and you need the exact cost of the one you sold.
- **Anything where one unit can cost double another** and your margin report would be wrong if you averaged them.

In these cases you are dealing with tens, hundreds, maybe a few thousand serial numbers. Storing a cost for each one is no burden at all, and the accuracy is worth it.

## When You Should Untick It

Untick it when **you have a very large number of serial numbers and the pieces are basically identical in cost**.

### Example: SIM Cards

A telecom distributor buys SIM cards. Every SIM card has a unique serial number, because the regulator requires it and because each one must be traceable to the customer who activated it.

The numbers look like this:

- Each SIM card costs about **₹20**.
- A single purchase is **500,000 cards**.
- Over a year the company handles **millions** of serial numbers.

With serial-wise valuation ticked, ERPNext has to store and read a cost for **every one of those millions of cards**. Every delivery of 10,000 SIM cards means looking up 10,000 individual costs. Stock entries become slow and heavy, and the data becomes hard to manage.

And what does all that work buy you? Card number 4,271,905 cost ₹20. Card number 4,271,906 cost ₹20. **The costs are the same.** You are paying a very large performance price to track a difference that does not exist.

This is exactly the case to untick the box. You keep full traceability of every SIM card — which batch it came in, which dealer it went to, when it was activated — while the costing uses one simple average.

### Other items in the same situation

- Cables, connectors, fasteners sold by the thousand but serialised for compliance.
- Electricity or water meters issued in bulk.
- Set-top boxes, smart cards, RFID tags.
- Any low-value item that is serialised because a **regulation or a customer** demands it, not because you need per-unit costing.

## How to Decide

Ask these three questions:

1. **How many serial numbers will this item have?** Thousands are fine. Millions are a problem.
2. **Do two pieces of this item ever cost meaningfully different amounts?** If they always cost about the same, per-serial costing gives you nothing.
3. **Would anyone ever ask "what did *that specific piece* cost?"** If the answer is no, you do not need serial-wise valuation.

If the count is huge **and** the costs are all alike **and** nobody asks about individual piece cost, untick the box.

## Rules You Need to Know

### You can untick it any time

Even if the item already has stock and serial numbers, you can turn serial-wise valuation off whenever you like.

### You cannot tick it back on once serial numbers exist

This one is important. While the box was unticked, ERPNext was **not recording a cost for each serial number**. That information was never saved. If you ticked the box again, the system would have no cost to look up for those existing pieces and would value them wrongly.

So think of unticking as a decision you should make deliberately. For a brand new item with no serial numbers yet, you can switch it back and forth freely.

### Valuation Method becomes Moving Average — but only after the first stock entry

Once the item has actually been used in a stock transaction, unticking the box sets the item's **Valuation Method** to **Moving Average**, and you will not be able to change it to FIFO or LIFO.

The reason is simple. FIFO and LIFO work by picking cost layers in order — "the oldest piece cost ₹20, the next one cost ₹21". That only makes sense if the system knows which piece is which. Once per-serial costs are no longer tracked, those layers no longer match the piece actually going out. Moving Average uses one average for everything, so it does not need to know which piece it is.

**If the item has no stock movement yet, nothing is locked.** You can untick the box and still choose FIFO or LIFO. The lock only starts with the first stock entry.

### Returns follow the same rule

When the box is unticked, a purchase return is valued at the item's average cost, just like any other outgoing movement — not at the original price paid for that exact serial number.

## A Worked Example

An item is stocked as follows:

- 2 pieces bought at ₹100 each
- 2 pieces bought at ₹200 each
- Average cost is therefore ₹150

Now one piece that was **bought at ₹200** is sent out.


| Transaction     | Ticked | Unticked |
| --------------- | ------ | -------- |
| Delivery        | ₹200   | ₹150     |
| Sales return    | ₹200   | ₹150     |
| Purchase return | ₹200   | ₹150     |


Ticked, the system finds that exact piece and uses its real cost of ₹200. Unticked, it uses the average of ₹150 without needing to know which piece it was.

## What Does Not Change

Unticking this box does **not** affect any of the following:

- Serial numbers are still generated and recorded.
- You can still see which serial number was received, where it is stored, and which customer received it.
- Warranty, AMC, recall and traceability reports all work exactly as before.
- Stock Ledger, Stock Balance and Stock Ageing reports continue to show correct values.

Only the **costing method** changes.

## Existing Items

When you upgrade, every item that already has serial numbers gets this box **ticked**. Your current valuation behaviour is preserved exactly. Nothing changes until you decide to untick it on a specific item.