---
title: "DATEV Integration"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/datev-integration"
updated: "2026-07-04"
---

## Overview

The DATEV Integration app connects ERPNext with DATEV workflows used by German accounting teams and tax consultants. The app is listed on Frappe Cloud Marketplace as [DATEV Integration](https://cloud.frappe.io/marketplace/apps/erpnext_datev) and is published by ALYF GmbH, Raffael's team.

## What It Does

- **DATEV Unternehmen Online:** Sends submitted vouchers to DATEV Unternehmen Online by email. Outgoing vouchers can be converted to PDF, while incoming vouchers can send attached files.
- **DATEV CSV Export:** Exports raw General Ledger entries from ERPNext in DATEV CSV format.
- **Tax consultant handoff:** Exports the DATEV report with master data as a ZIP file for import into the tax consultant's DATEV system.

## Setup Summary

Configure DATEV Settings with the client number, tax consultant number, and temporary contra account. For DATEV Unternehmen Online, enable the integration, choose the sending email account, select the voucher type, add the target email address from DATEV, and choose whether to send attachments or generated prints.

## Compatibility

The marketplace listing shows support for ERPNext versions 13, 14, 15, and 16. Test the integration on a staging site before using it for accounting handoff.

## Links

- [DATEV Integration on Frappe Cloud Marketplace](https://cloud.frappe.io/marketplace/apps/erpnext_datev)

## Disclaimer

DATEV and DATEV Unternehmen Online are trademarks of DATEV eG. The marketplace listing notes that this integration is not approved or endorsed by DATEV eG.