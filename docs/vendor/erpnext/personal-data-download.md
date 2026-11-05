---
title: "Personal Data Download\n"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/personal-data-download"
updated: "2026-02-26"
---

Personal data download tool enables a user to automatically download all the personal data they have generated while using ERPNext. This includes personally identifiable data from your user account like: username, full name, birth date, phone numbers, mobile numbers, location, interests, bio, email signature, Email, Contact, Address, Communication, etc. It also includes data from Leads and Opportunities, the details you have saved like phone numbers, mobile numbers, fax, website, and name.

## How to request a user data download

1. To begin downloading data, the user has to **log in** and visit [host-name]/request-data (e.g. erpnext.com/request-data) in the URL field.
  ![](/files/imagef57ad4.png)
2. After submitting your request, you will receive a success response.
  ![](/files/image01d862.png)
3. This will send an email with a download link of the data to the email address associated with the user.The file available for download will be in the JSON format.

## Personal Data Download Request DocType

The request is also recorded in the DocType "Personal Data Download Request", the file link that is sent to the user via email is also attached to the doc. Search for Personal Data Download Request from the search bar.

![](/files/imaged1d56c.png)

