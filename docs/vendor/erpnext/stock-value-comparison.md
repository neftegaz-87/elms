---
title: "Stock Value Comparison"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/stock-value-comparison"
updated: "2026-10-06"
---

![](/files/Screenshot 2026-10-06 at 11.57.26 AM.webp)

## 1. What is this report?

Every stock transaction in ERPNext adds a line to the **Stock Ledger**. Each line stores a few numbers:

- the **balance qty** after the transaction
- the **change in stock value** caused by the transaction
- the **valuation rate**
- the **balance stock value**

Sometimes these numbers become wrong. Common reasons are:

- Many backdated entries for the same item and warehouse
- A repost that failed or was never run
- An old bug that has since been fixed, but whose wrong values are still in the ledger
- Customizations done on stock ledgers

When this happens, the stock value in your reports is wrong, and the stock value may no longer match your accounts. 



The **Stock Valuation Comparison** report finds these problems. It goes through the ledger of each item and warehouse from the very first entry and works out what each number **should be**. Then it puts the **actual** value next to the **expected** value. If they are not the same, the row is shown as a **difference**.



From the same report you can then fix the differences in one of two ways:

- **Option 1: Repost**
- **Option 2: Adjustment Entry**

This guide explains both options and when to use each one.

## 2. Opening the report

Go to **Stock &gt; Reports &gt; Stock Valuation Comparison**, or search for "Stock Valuation Comparison" in the search bar.

### Filters


| Filter                                             | What it does                                                                                                                                                                                                                                                                                   |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Company**                                        | Required. The company to check.                                                                                                                                                                                                                                                                |
| **From Date / To Date**                            | Show only entries between these dates. The report still reads the ledger from the first entry so that its numbers are correct.                                                                                                                                                                 |
| **Item / Item Group / Warehouse**                  | Check only these items or warehouses. A parent warehouse includes its child warehouses.                                                                                                                                                                                                        |
| **Show**                                           | **First Difference per Item-Warehouse** (default): only the first wrong entry of each item and warehouse. This is usually all you need, because one wrong entry makes every later entry wrong too.<br>**All Differences**: every wrong entry.<br>**All Entries**: every entry, right or wrong. |
| **Ignore Differences Below**                       | Small rounding differences below this amount are ignored. The default is 0.01.                                                                                                                                                                                                                 |
| **Show Differences Settled by Adjustment Entries** | Differences that an Adjustment Entry has already settled are hidden. Tick this to see them again.                                                                                                                                                                                              |


## 3. Reading the report

Each row is one Stock Ledger Entry. The columns come in groups of three: the **actual** value, the **expected** value, and the **difference** between them.


| Actual                    | Expected                           | Difference | Meaning                                                  |
| ------------------------- | ---------------------------------- | ---------- | -------------------------------------------------------- |
| (A) Balance Qty           | (B) Expected Balance Qty           | A - B      | Qty in stock after this entry                            |
| (C) Change in Stock Value | (D) Expected Change in Stock Value | C - D      | How much this entry added to or removed from stock value |
| (E) Valuation Rate        | (F) Expected Valuation Rate        | E - F      | Rate per unit after this entry                           |
| (G) Balance Stock Value   | (H) Expected Balance Stock Value   | G - H      | Total stock value after this entry                       |


Differences are shown in **red**.

Other useful columns:

- **Expected Value Based On**: how the report worked out the expected value. For example "FIFO queue", "Moving average", "Batch average", "Serial no receipt rate", "Standard cost" or "Reconciled qty and rate".
- **Adjusted By**: the Adjustment Entry that has already settled this difference, if there is one.
- **Pending Repost**: a Repost Item Valuation that is already queued or running for this item and warehouse.

> **Before you fix anything:** look at the first difference of an item and open its voucher. Make sure the expected value makes sense to you. If the expected value looks wrong, do not fix the entry. Report it to your ERPNext partner or support first.

---

## 4. Choosing what to fix

Both fix buttons are under **Fix Differences** at the top of the report.

- If you **tick some rows**, only those rows are fixed.
- If you **tick no rows**, every difference shown in the report is fixed.

For each item and warehouse, the fix always starts from its **earliest** selected difference.

---

## 5. Option 1: Repost

### What it does

**Repost** makes one **Repost Item Valuation** for each selected item and warehouse, starting from the date of its first difference. The repost runs in the background. It works out every stock ledger entry again from that date to today and corrects the stock values and the accounting entries behind them.

After the repost, the ledger is correct **from the start**, as if the mistake never happened.

### Steps

1. Select the rows to fix, or select none to fix everything shown.
2. Click **Fix Differences &gt; Repost**.
3. A preview opens. It shows:
  - each item and warehouse that will be reposted, and the date it starts from
  - any item and warehouse that already has a pending repost. These are left out.
  - a warning if the repost starts in a **previous fiscal year**
4. Click **Yes** to continue.
5. A message shows which reposts were queued, with links to them, and which could not be made and why.
6. Wait until the reposts are **Completed**. You can follow them in the **Repost Item Valuation** list.
7. Run the report again. The differences should be gone.

### Pros

- **Fixes the root of the problem.** Every entry from the first difference onwards is corrected, so all old and new reports show correct values.
- **Clean history.** No extra transaction is added to the ledger. Stock and accounting reports for past dates become correct too.
- **No limits on later entries.** You can keep posting backdated transactions as usual.
- **Nothing to account for by hand.** You don't need a difference account. The original vouchers' accounting entries are corrected.

### Cons

- **Changes past figures.** If the first difference is in an older period, closing stock, profit and balance sheet figures of that period can change. This is a problem if those figures are already **filed, audited or reported** to tax authorities.
- **Can be slow.** An item with many transactions, or a start date far in the past, can take a long time to repost. It also adds load to the system while it runs.
- **Can be blocked.** If the period is closed, for example by an **Accounting Period** or a **Period Closing Voucher**, or accounts are frozen before that date, the repost may not be allowed.
- **Can spread wider than expected.** Changing the value of an issue also changes the value of whatever used that stock, such as a manufactured item or a transfer to another warehouse.

---

## 6. Option 2: Adjustment Entry

### What it does

**Adjustment Entry** fixes the stock **from a date you choose**, without touching anything before that date.

On that date, it takes out the stock of each selected item and warehouse at the (wrong) value the ledger holds, and puts it back at the **correct** qty and value. Serial nos come back at their own rates, batches at their own rates, and the rest of the stock layer by layer, so that FIFO and moving average stay correct afterwards.

The difference in value is booked to a **Difference Account**. By default this is the company's **Stock Adjustment Account**.

An Adjustment Entry is a **Stock Reconciliation** with the purpose **"Adjustment Entry"**.

### Steps

1. Select the rows to fix, or select none to fix everything shown.
2. Click **Fix Differences &gt; Adjustment Entry**.
3. A dialog opens. Fill in:
  - **Adjustment Date** and **Adjustment Time**: the date from which the stock should be correct. A common choice is the first day of the current fiscal year, or today.
  - **Difference Account** (optional): where the value difference is booked. Leave it empty to use the company's Stock Adjustment Account.
4. Click **Make**.
5. A **draft** Stock Reconciliation opens. Check its rows:
  - **Current Qty / Current Amount**: what the ledger holds now
  - **Qty / Valuation Rate / Amount**: what it should hold
  - **Difference Amount**: the amount booked to the Difference Account
6. **Submit** it.
7. Run the report again. The differences before the date are now hidden. Tick **Show Differences Settled by Adjustment Entries** to see them.

> **Do not edit the rows.** They must match exactly what the stock should be. If you change them, you will get an error and must make the Adjustment Entry again from the report.

### Pros

- **Past figures stay the same.** Nothing before the adjustment date changes. Filed returns, audited accounts and closed periods are safe.
- **Fast.** It is one transaction. Nothing is reposted, even for items with years of history.
- **Easy to see and audit.** The correction is one document with one clear amount, booked to an account you choose. Your accountant can see exactly what was corrected and when.
- **Works when Repost cannot.** It can be used when the old period is closed or frozen.
- **Can be undone.** Cancelling the Adjustment Entry brings back the stock as it was before.

### Cons

- **Old reports stay wrong.** Stock and accounting reports for dates **before** the adjustment date still show the old, wrong values. Only values from the adjustment date onwards are correct.
- **Blocks backdated entries.** After it is submitted, **no stock transaction dated before the adjustment can be posted or cancelled** for that item and warehouse, or for the same serial nos or batches. To post one, you must first cancel the Adjustment Entry.
- **Needs a manual accounting step.** The difference is booked to the Difference Account. Your accountant may need to review it or explain it.
- **Does not work in every case.** An item and warehouse is left out, with a reason, when:
  - its stock qty and value are already correct on that date
  - its stock should be **negative** on that date
  - some of its serial nos or batches should be **short of stock** on that date
  - its first difference is **on or after** the adjustment date
  - it has no stock transactions by that date

  These need a **Repost** instead.

---

## 7. Side-by-side comparison


|                                        | **Repost**                                     | **Adjustment Entry**                        |
| -------------------------------------- | ---------------------------------------------- | ------------------------------------------- |
| What changes                           | Every entry from the first difference to today | Only stock from the adjustment date onwards |
| Past reports                           | Become correct                                 | Stay as they were (wrong)                   |
| Closed or filed periods                | Can change, or may be blocked                  | Not touched                                 |
| Speed                                  | Slow for long histories, runs in background    | Fast, one document                          |
| New document in the ledger             | No                                             | Yes, one Stock Reconciliation               |
| Accounting                             | Original accounting entries are corrected      | Difference booked to the Difference Account |
| Backdated entries afterwards           | Allowed                                        | Blocked before the adjustment date          |
| Negative stock / serial or batch short | Works                                          | Not supported, use Repost                   |
| How to undo                            | Hard, the old values are gone                  | Cancel the Adjustment Entry                 |


---

## 8. Which option should I use?

**Use Repost when:**

- the first difference is in the **current fiscal year**, or in a period that is **not yet filed or closed**
- you want **every** report, including old ones, to be correct
- you still need to post **backdated** entries for these items
- the Adjustment Entry says the item cannot be adjusted

**Use Adjustment Entry when:**

- the first difference is in a **past fiscal year** that is **closed, audited or filed**
- the repost would be **too slow**, or is **blocked** by a closed period
- you only need the stock to be correct **from now on**, and you are fine with old reports staying as they are

**A common approach:**

1. Repost the differences that are in the current fiscal year.
2. For the differences that start in older, closed years, make an Adjustment Entry dated the **first day of the current fiscal year**. Discuss this with your accountant first.

---

## 9. Good practice

- **Take a backup** before fixing a large number of items.
- **Check a few items by hand** before fixing everything. Make sure the expected values are correct.
- **Fix in small groups**, for example one item group or one warehouse at a time.
- **Run the report again** after each fix to confirm the differences are gone.
- **Talk to your accountant** before reposting into a past fiscal year, or before booking a large Adjustment Entry.