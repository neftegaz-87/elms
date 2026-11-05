---
title: "Batch Split"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/batch-split"
updated: "2026-08-28"
---

Turn one big batch of material into many small, individually traceable batches, one per piece you cut from it.

## The story: cutting a 50 KG rod

Your factory buys a 50 KG iron rod. It arrives as **one batch**, one purchase, one quality certificate, one batch number. On the shop floor you cut it into **five pieces of 10 KG each**, and from that moment the pieces live separate lives: they go into different machines, different orders, maybe different customers.

If all five pieces keep the rod's single batch number, you lose track of them individually. Batch Split fixes this: at the moment of cutting, ERPNext automatically creates **one new batch per piece**, and every new batch remembers which rod it came from.

```
BCH-000001  Iron Rod · 50 KG
     │
     ✂  cut into pieces of 10 KG
     │
     ├─ BCH-000002  10 KG
     ├─ BCH-000003  10 KG
     ├─ BCH-000004  10 KG
     ├─ BCH-000005  10 KG
     └─ BCH-000006  10 KG
```

Each piece gets its own batch number from the item's normal batch series. Each one records BCH-000001 as its **parent batch**, so a complaint about any piece traces back to the exact rod, its supplier, and its purchase receipt.

## When to use this feature

Use Batch Split whenever bulk material is **physically divided into pieces** and you need to follow each piece on its own:

- Metal rods, bars, or pipes cut to length
- Steel or paper coils slit into smaller coils
- Fabric or film rolls cut into shorter rolls
- Timber planks cut from a log

It is **not** meant for mixing or blending (many inputs becoming one output), or for items you don't track by batch at all.

## Before you start

On the **Item** that represents the cut piece (the output), enable:


| Item setting                       | Why                                                                            |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| **Has Batch No**                   | Pieces are tracked by batch.                                                   |
| **Automatically Create New Batch** | ERPNext creates the piece batches for you at the moment of cutting.            |
| **Batch Number Series**            | New piece batches are numbered from the item's own series, e.g. `BCH-.######`. |


The raw material you cut (the rod) must also be a batch-tracked item, so the system knows exactly which rod each piece came from.

## Way 1 - As a step in manufacturing

Use this when cutting is one operation inside a production process, for example, an operation called *Rod Cutting* in the routing of a machined part.

1. **Open the BOM** and enable **Track Semi Finished Goods**, so each operation produces its own output item.
2. **On the cutting operation row**, tick **Batch Split** and set **Weight Per Piece** — for our rod, **10**.
3. **Run production as usual**: create the Work Order, then the Job Card for the cutting operation. Both carry the Batch Split settings automatically.
4. **Complete the Job Card** and make its Stock Entry. Raw material consumption and the produced quantity stay exactly as they always are — producing 50 still consumes 50.
5. **Submit.** ERPNext divides the produced quantity by Weight Per Piece (50 ÷ 10 = 5) and creates five batches of 10 each, every one linked to its parent rod batch.

> **Good to know:** Weight Per Piece only controls how the **output is batched**. It never changes how much raw material is consumed, that still follows your BOM quantities.

## Way 2 - A manual split from the stores

Use this when there is no production order, the storekeeper simply cuts a rod and wants the pieces on the shelf as separate batches.

1. **Create a Stock Entry** and choose the type **Batch Split** (it comes built in, with purpose *Repack*).
2. **Set Weight Per Piece** — the field appears as soon as you pick the Batch Split type.
3. **Add two rows**: the rod being consumed (source warehouse, quantity 50) and the piece item being produced (target warehouse, quantity 50, marked as the finished item).
4. **Submit.** Five 10-unit batches are created and put into stock, each pointing to the rod it was cut from.

## What the system checks for you


| Rule                                                                                                                             | Example                                                                                                       |
| -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| The produced quantity must divide evenly by Weight Per Piece.                                                                    | 50 ÷ 10 = 5 pieces ✓ · 55 ÷ 10 is rejected.                                                                   |
| Exactly one batch-tracked raw material may be consumed, so the parentage is unambiguous.                                         | Cutting consumes rod only — not rod and coil together.                                                        |
| Each consumed batch must be able to supply **whole** pieces. A piece is always cut from one rod — never glued together from two. | Two 25 KG rods can yield four whole 10 KG pieces, not five. Asking for five is rejected with a clear message. |
| When several rods are consumed, the pieces are shared out in proportion to what each rod supplied.                               | Rods of 30 KG and 20 KG making five pieces → 3 pieces from the first, 2 from the second.                      |


## Tracing a split afterwards

Open any batch that was part of a split and you'll see a **Batch Split Tree** button. It opens a report showing the full family, top down — the original rod at the root, its pieces indented below, and any further cuts below those:

```
BCH-000001   Iron Rod        50 KG   ← the purchased rod
├─ BCH-000002   10 KG
├─ BCH-000003   10 KG
│  ├─ BCH-000007    5 KG   ← this piece was cut again
│  └─ BCH-000008    5 KG
├─ BCH-000004   10 KG
├─ BCH-000005   10 KG
└─ BCH-000006   10 KG
```

Every batch has exactly **one** parent, because every physical piece was cut from one physical rod. A piece cut again simply becomes a parent itself — the tree can go as deep as your process does.

## If a split entry is cancelled

Cancelling the Stock Entry reverses the stock movement, but the created batch records are kept, this is standard ERPNext behaviour for automatically created batches. They hold no stock, they disappear from the Batch Split Tree, and they don't get in the way. Simply make a fresh entry to split again.