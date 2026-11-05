---
title: "Use Inline Serial / Batch Editor"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/use-inline-serial-batch-editor"
updated: "2026-07-19"
---

The Inline Serial / Batch Editor lets you add and manage Serial Numbers and Batches directly on the item row of your stock documents — no separate pop-up dialog needed. You see your entries in a simple table right where you are working, and everything is saved together when you save the document.

---

## How to Enable It

1. Open **Stock Settings** (search for "Stock Settings" in the search bar).
2. Go to the **Serial & Batch Item** section.
3. Make sure **"Use Serial No / Batch Fields"** is unchecked.
4. Tick the checkbox **"Use Inline Serial / Batch Editor"**.
5. Click **Save**.

That's it — the feature is now on for everyone on your site. (It is enabled by default on new installations.)

> Tip: If you don't see the editor after enabling it, refresh your browser page once.

---

## Where You Will See It

Open any of these documents, then click on an item row to expand it. You will find a **Serial / Batch Entries** table inside the row (for items that have Serial Numbers or Batches):

- Purchase Receipt and Purchase Invoice (including the Rejected quantity section)
- Sales Invoice, POS Invoice and Delivery Note (including bundled / packed items)
- Stock Entry
- Stock Reconciliation
- Subcontracting Receipt (items and supplied items)
- Pick List
- Asset Capitalization and Asset Repair

---

## Why Use It? (Benefits)

- **Everything in one place** — add, edit and remove serial numbers or batches right on the item row. No switching to a pop-up and back.
- **Faster** — your changes are collected as you type and saved to the system in one go when you save the document, instead of one server call per change. Adding 20 batches is one save, not 40 separate updates.
- **Nothing saved by accident** — until you click Save on the document, your serial/batch changes are only on your screen. The Save button appears as soon as you change anything, so you always know there is unsaved work.
- **Handles large lists easily** — entries are shown in pages of 10 with simple navigation buttons, so even hundreds of serial numbers stay easy to browse.
- **Missing serials and batches are created for you** — on incoming documents (like Purchase Receipt), if you enter a serial number or batch that doesn't exist yet, the system creates it automatically when you save.

---

## How to Use It

### Adding entries

1. Click on the item row to expand it and find the **Serial / Batch Entries** table.
2. Click **Add row**.
3. Pick the Serial Number / Batch from the dropdown (or type a new one) and enter the quantity.
4. Repeat for as many entries as you need, then **Save** the document.

The item's quantity and the Total Qty shown under the table update automatically as you add entries.

### Editing entries

- Click directly on a Serial No, Batch No or Qty cell in the table and type the new value — it works just like editing a spreadsheet cell.

### Deleting entries

- Tick the checkbox at the start of one or more rows, then click **Delete row**.
- To clear everything, tick the checkbox in the table header (select all) and click **Delete All**. If you remove all entries and save, the linked Serial and Batch Bundle is removed as well.

### The ⋯ (three dots) menu

At the bottom right of the table you will find a menu with extra tools:

- **Auto Fetch Serial Nos / Batch Nos** *(outgoing documents like Delivery Note)* — enter the quantity you want and the system picks the serial numbers / batches for you, based on the **Pick Serial / Batch Based On** rule in Stock Settings (FIFO, LIFO or Expiry). It replaces whatever is currently in the table, skips reserved stock, and saves the document for you.
- **Scan Serial Nos / Scan Batch Nos** — use a barcode scanner (or type and press Enter) to add entries one by one. Scanning the same batch again simply increases its quantity.
- **Create Serial Nos from Range** *(serial items)* — type a range like `SN-01::10` to add SN-01 through SN-10 in one step.
- **Download** — download the current entries (or a blank template) as a CSV file.
- **Upload** — fill the CSV template and upload it to load many entries at once. Missing serial numbers and batches are created automatically on incoming documents.

### Moving between pages

When there are more than 10 entries, use the arrows at the bottom of the table to move between pages, or type a page number directly. You can jump straight to the first or last page with the outer arrow buttons.

---

## Good to Know

- The editor appears only while the document is in **Draft**. After submission the entries are locked, as usual.
- If an item row has **"Use Serial No / Batch Fields"** ticked, that row keeps the simple text fields and the inline table is hidden for it.
- Prefer the old pop-up dialog? Untick **"Use Inline Serial / Batch Editor"** in Stock Settings and the previous behaviour returns.





![](/files/Screen Recording 2026-07-18 at 1.11.21 PM.mov)