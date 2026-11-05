---
title: "Stock Reposting Settings"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/stock-reposting-settings"
updated: "2026-05-15"
---

![Screenshot 2024-04-24 at 12.54.08 PM](/files/Screenshot 2024-04-24 at 12.54.08 PM.png)



### **Limit timeslot for Stock Reposting**

If you want to run the reposting in a specific time then you can enable the checkbox "**Limit timeslot for Stock Reposting**". With this configuration you can avoid deadlock issues which occurs during the reposting.

### Limits don't apply on

If you want to run the reposting full day and not on a specific time, especially when you have weekly off then you can use this configuration.

### Use Item Based Reposting

This option is helpful when you want to speed up reposting. The system skips reposting for duplicate items and warehouses to improve speed.

### Do reposting for each Stock Transaction

The system creates a reposting record for backdated entries. This means that the system only generates a reposting record if a future transaction exists for the same item and warehouse. We have seen cases where system has not created reposting entry for backdated transaction because of concurrency issues. So to solve them added this option which won't check whether the future transaction exists for the same item and warehouse to make reporting record. This is also added for an audit purpose.

### **Notify Reposting Error to Role**

If reposting fails due to any issues, the system sends emails to the system managers. If you don't want to send failure emails to the system managers, you can configure a role, and the system will then send the email to the users assigned to that respective role.

### **Enable Parallel Reposting**

![Screenshot 2025 12 10 at 5.54.21 PM](/files/Screenshot%202025-12-10%20at%205.54.21%20PM.png)

Allows the system to use multiple background workers to repost stock entries in parallel per item. This setting is effective only when Item-Based Reposting is enabled.

#### No of Parallel Reposting (Per Item)

Defines the number of parallel workers that can execute repost item valuation entries in parallel. Higher values may speed up reposting but can increase system load.



### **Note for usage**

Reposting is a tough computational problem to solve because it involves reposting 1000s may be 10,000s of entries depending on volume of transaction. Please use Reposting Wisely. It is recommended to limit back dated entries to not more than one month. Reposting entries with dates ranging more than one month may lead to failure in reposting for multiple reasons including but not limited to 

1. Reposting Time may be limited to prevent utilisation of resources during working hours, therefore the actual reposting may come up at a later date than when it was created, therefore leading to inconsistencies in the vouchers on the system
2. Reposting is limited to a timeout of 1500 seconds, which may be exceeded if the volume of reposting is too long

### **Issue for Legacy Serial Numbers**

For example

- Inward serial number ABC with a rate of 14,000
- Outward transaction for the same serial number with a valuation rate of 14,000 
- Inward the same serial number ABC again with a rate of 4,000 
- Outward transaction for the same serial number with a valuation rate of 4,000



At this point, the incoming rate stored in the serial number becomes 4,000.  If reposting is performed from the second transaction (outward), the valuation rate is calculated incorrectly  

- Inward serial number ABC with a rate of 14,000
- Outward transaction for the same serial number with a valuation rate of 4,000 (**Incorrect because fetched from Serial No document**)
- Inward the same serial number ABC with a rate of 4,000
- Outward transaction for the same serial number with a valuation rate of 4,000



The valuation rate in the second row should be 14,000, not 4,000.  This issue affects legacy serial numbers created before Version 15, when the Serial and Batch Bundle feature was not available.  

**Solution**  

Provided an option to fetch the incoming rate either from the last inward transaction during reposting. To enable this users needs to enable the checkbox "Do not fetch incoming rate from Serial No" in the Stock Reposting Settings