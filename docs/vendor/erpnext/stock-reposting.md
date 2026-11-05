---
title: "Stock Ledger Variance Report"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/stock-reposting"
updated: "2026-02-27"
---



![Screenshot 2025 12 30 at 12.48.14 PM](/files/Screenshot%202025-12-30%20at%2012.48.14%20PM.png)


The Stock Ledger Variance report in the ERPNext helps identify incorrect Stock Ledger Entries (SLEs) where the Running Available Stock and Stock Balance are inconsistent. These inconsistencies usually occur due to reposting issues, backdated entries, or data mismatches.

This report allows users to easily detect affected entries and correct them by creating reposting entries.


### Use this report to:


* Identify Stock Ledger Entries with incorrect running balances
* Detect stock quantity mismatches between calculated and stored values
* Repost affected entries to fix stock inconsistencies


### How to Use the Report


* Open the Stock Ledger Variance report.
* Apply filters like 
    Quantity (A - B) to find ledgers with incorrect balance qty
    Value (G - D) to find ledgers with incorrect balance value
    Valuation (I - K) to find ledgers with incorrect valuation rate



### Reposting Affected Entries

To fix the incorrect stock ledger entries:


* Select the rows that show inconsistencies.
* Click on Create Reposting Entries.
* The system will generate reposting entries for the selected records.
* Once reposting is completed, re-run the report to verify that the issue is resolved.

### Notes


* Reposting may take time depending on the number of affected entries.
* It is recommended to perform reposting during non-peak hours.
* Always verify stock balances after reposting.


### When to Use This Report


* After fixing reposting-related issues
* When negative stock errors appear unexpectedly
* After importing or creating backdated stock transactions
* During stock audit or reconciliation