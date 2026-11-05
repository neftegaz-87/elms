---
title: "Healthcare Module in ERPNext"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/frappe-healthcare"
updated: "2026-07-04"
---

Frappe Healthcare was earlier available as the Healthcare module inside ERPNext. It has now been separated into a dedicated open-source app called Marley Health.

Marley Health is owned and maintained by earthians Health Informatics Private Limited. It can be installed alongside ERPNext when an organization wants to manage healthcare workflows such as patients, appointments, consultations, clinical records, laboratory tests, procedures, and billing.

Marley Health documentation: [https://marley.frappe.cloud/docs](https://marley.frappe.cloud/docs)

## Basic features

### Patient management

Marley Health helps maintain patient records, demographics, contact details, medical history, and related healthcare documents. The patient record becomes the central place from which appointments, consultations, lab tests, procedures, and billing can be tracked.

### Healthcare practitioners

Organizations can maintain doctors, consultants, therapists, and other healthcare practitioners. These records are used for appointments, schedules, consultations, and clinical documentation.

### Appointments and scheduling

The app supports appointment booking and scheduling so front-desk and clinical teams can manage patient visits. Appointments can be linked to patients, practitioners, departments, and service units.

### Patient encounters and consultations

Healthcare teams can record consultations using patient encounters. Encounters help capture symptoms, diagnosis, observations, notes, prescriptions, investigations, and follow-up advice.

### Clinical records

Marley Health helps maintain structured healthcare records such as vital signs, prescriptions, medical observations, and other clinical information. This gives practitioners a clearer view of the patient's treatment history.

### Laboratory tests and procedures

The app supports lab test and clinical procedure workflows. Tests and procedures can be ordered, recorded, and linked back to the patient record.

### Inpatient care

For facilities that admit patients, Marley Health can help manage inpatient records, admissions, service units, and patient movement inside the healthcare facility.

### Billing integration

Because Marley Health works with ERPNext, healthcare services can be connected to ERPNext billing documents such as Sales Invoices. This helps combine clinical operations with accounting and revenue tracking.

## Typical healthcare cycle

```
Patient Registration
        |
        v
Appointment Booking
        |
        v
Patient Encounter / Consultation
        |
        +-------------------+
        |                   |
        v                   v
Prescription          Lab Test / Procedure
        |                   |
        +---------+---------+
                  v
              Billing
                  |
                  v
              Follow-up
```

## When should you install Marley Health?

Install Marley Health if your ERPNext site is used by a clinic, hospital, diagnostic center, therapy center, or any healthcare organization that needs patient and clinical workflows.

Read the Marley Health documentation here:

[https://marley.frappe.cloud/docs](https://marley.frappe.cloud/docs)