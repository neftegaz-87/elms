---
title: "Shareholder\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/shareholder"
updated: "2026-08-14"
---

Nova Electronics Trading has three shareholders. Elena Brooks initially holds 6,000 shares, Marcus Lee holds 4,000, and Horizon Ventures LLC holds 1,000. Finance needs to know who owns shares, how to contact each owner, and which ownership transactions belong to each one. Keeping names in a spreadsheet makes it easy to lose the connection between the owner, their folio number, and their share history.



A Shareholder is the master record for a person or organisation that owns shares in a Company. It becomes the anchor for [share issues and transfers](/erpnext/share-transfer), balances, and the Share Ledger. Creating the master does not give the owner any shares. Ownership begins only after an Issue is submitted.

## Create a Shareholder

Open the Shareholder list and select **Add Shareholder**. Enter the shareholder's name and Company. Enable **Is Company** when the owner is an organisation rather than an individual.

![Shareholder list with fictional Nova owners](https://novacompanies.m.frappe.cloud/files/budgets-capital-equity-20260814-shareholder-list.png)

Save the record. ERPNext assigns a Shareholder ID using the configured [naming series](/erpnext/document-naming-settings). Add the shareholder's [Contact](/erpnext/contact) and [Address](/erpnext/address) from the linked records so correspondence remains separate from ownership transactions.

![Shareholder name, company, and folio number highlighted](https://novacompanies.m.frappe.cloud/files/budgets-capital-equity-20260814-shareholder-details.png)

## Folio number and share balance

The folio number uniquely connects a shareholder to their ownership transactions. It appears after the first share issue. The Share Balance section then shows holdings created by submitted Share Transfers.

## Frequently asked questions

### Why is the share balance empty after I create a Shareholder?

Saving the master records the owner but does not issue shares. Create a Share Transfer with Transfer Type set to Issue and submit it.

### Can a company be a shareholder?

An organisation can be maintained as a shareholder by enabling Is Company on its master record.

## Related topics

- [Shareholder Management](/erpnext/shareholder-management)
- [Share Transfer](/erpnext/share-transfer)
- [Share Reports](/erpnext/share-reports)
- [Company](/erpnext/company)