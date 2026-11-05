---
title: "Track Semi-Finished Goods"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/track-semi-finished-goods"
updated: "2026-02-26"
---

```
Note: This feature will be available in the ERPNext version 16
```

Semi-finished goods are materials that result from the completion of one operation and are used as raw materials to make final products or other semi-finished goods.

In ERPNext, if you want to track semi-finished goods, you need to create an item for each semi-finished good and also have an active Bill of Materials for each one.

So we thought, why can't we have a provision to define the finished/semi-finished goods against the operation as well as raw materials? With this, once we complete the operation, the semi-finished goods will be produced and the raw materials will be consumed. Similarly, after the completion of the last operation, the finished goods will be produced and all semi-finished goods will be consumed.

The user has to create a Bill of Materials for each finished/semi-finished good and assign it to operations of the final Bill of Materials, or they can manually select the raw materials required to produce the finished/semi-finished goods.


BOM (with Operations)
-----------------------------



* If you want to track "Semi Finished Goods", you need to enable "Track Operations" and "Track Semi Finished Goods" while making the BOM.
* While creating a BOM, the user will have the option to define the operation, operation time, workstation, and workstation type.
* The user will also have the option to set default warehouses, such as the source warehouse, work in progress warehouse, and finished goods warehouse.
* If the user has set 'skip material transfer' they can consume materials from the source warehouse or work-in-progress warehouse.
* If users perform specific operations through subcontracting, they will have options to define subcontracted operations. Users will also have the option to create a subcontracted purchase order against the subcontracted job cards.

Work Order
----------

![work-order-with-semi-fg](/files/work-order-with-semi-fg.gif)  


In the work order, users can see the finished/semi-finished good as well raw materials against each operations. On submission of the work order system will create the job cards automatically and users have to complete the job cards manually. User can complete the job cards using job card view or from workstation dashboard. Below are different ways to complete the job cards

1. If the 'Skip Material Transfer to WIP' checkbox is enabled and the 'Backflush Materials From WIP Warehouse' checkbox is enabled, then users must consume raw materials from the 'WIP Warehouse'. Users need to click the 'Start Job' button to begin the job and the 'Complete Job' button to stop the job. After that, users must submit the job card to create a stock entry to consume materials from the 'WIP Warehouse' and add finished/semi-finished goods to the 'Target Warehouse'.
2. If the 'Skip Material Transfer to WIP' checkbox is enabled and the 'Backflush Materials From WIP Warehouse' checkbox is disabled, then users must consume raw materials from the 'Source Warehouse'. Users need to click the 'Start Job' button to begin the job and the 'Complete Job' button to stop the job. After that, users must submit the job card to create a stock entry to consume materials from the 'Source Warehouse' and add finished/semi-finished goods to the 'Target Warehouse'.
3. If the 'Skip Material Transfer to WIP' is disabled, then users must have to transfer raw materials from the 'Source Warehouse' to 'Wip Warehouse'. After that, users need to click the 'Start Job' button to begin the job and the 'Complete Job' button to stop the job. After that, users must submit the job card to create a stock entry to consume materials from the 'WIP Warehouse' and add finished/semi-finished goods to the 'Target Warehouse'.


Job Card
---------------------

Users have to complete the Job Card, and once all Job Cards are completed, the system will complete the Work Order. From the Job Card, users must transfer materials from the Store to the Work In Progress warehouse, if the Skip Material Transfer option is disabled on the respective job card. After that, users need to create a Manufacture Stock Entry against the Job Card for the semi-finished or finished goods.

While making the Manufacture Stock Entry, the system will prompt the user to confirm whether they want to submit the entry. If the user selects "Yes," the system will create the Stock Entry in a Submitted state; otherwise, it will be created in a Draft state.

Workstation Dashboard
---------------------

![workstation-dashboard-png](/files/workstation-dashboard-png.png) Using the workstation dashboard, users can start, pause, resume, and complete job cards. Also, users can transfer raw materials from the source warehouse to the WIP warehouse against the job cards from the workstation dashboard. If "Skip Material Transfer" has enabled then no need to transfer raw materials. Also users don't get the subcontracted operations in the workstation dashboard.

### Transfer Materials

For the 'Brake Making' operation, the user has not enabled 'Skip Material Transfer', so they must transfer raw materials from the 'Stores' to the 'Work In Progress' warehouse. For the 'Chain Making' operation, the user has enabled 'Skip Material Transfer,' so they do not need to transfer raw materials.

![transfer-materials](/files/transfer-materials.gif)  


### Start Job

To start the job card, click on the 'Start' button from the menu. On start system auto fetch the employee of the logged in user and set it in the modal.

### Pause Job

To pause the job card, click on the 'Pause' button from the menu.

### Resume Job

To resume the job card, click on the 'Resume' button from the menu.


### Complete Job with Auto Stock Entry

On click of 'Complete' button, system asks you to enter the quantity and system creates the auto stock entry with type as 'Manufacture'. This stock entry, consume the raw materials and add finished/semi-finished goods.

------------

Start and Complete Jobs Using **QR code**
-----------------------------------------

If you have QR codes for the job cards, you can use them to start and complete the job cards by scanning the QR codes in the 'Start Job'/'Complete Job' QR code fields.

![start-complete-job-suing-qrcode](/files/start-complete-job-suing-qrcode.gif)  


