---
title: "Downloading Backups"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/download-backup"
updated: "2026-02-26"
---

In ERPNext, you can manually download a database backup.

To get the latest database backup, go to:

> Home  > Download Backups

Backup available for the download is updated every eight hours. Click on the link to download the backup at a given time.

If you want to set the number of Backups available for download at a time, then click on 'Set Number of Backups', which will navigate you to 'System Settings', where you can set the number.

![](/files/imageb48716.png)
*Download backup post backup taken*

![](/files/imageef9524.png)

## Downloading Files Backup

Clicking on Download Files Backup will send an email with links to the backup for both private and public files. Email must be configured for this to work.

![](/files/image0646b1.png)

## Getting Backup Encryption Key

In order to get the backup encryption key, click on the designated button. Upon getting your system password validated, the system will provide you with the encryption key.

![](/files/imageed3623.png)

## Automating Backups to Cloud Storage

You can also automate your backups to be uploaded directly to a cloud storage platform. Currently, ERPNext supports:

1. Amazon S3
2. Dropbox
3. Google Drive