---
title: "Filter Options in Select Field"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/filter-options-in-select-field"
updated: "2026-03-02"
---

Let's say you have two drop-down fields named State and City. State has two values Karnataka and Maharashtra and City has four values, Bangalore, Mysore, Mumbai, and Pune. If you would like to filter options in City based on the value chosen in State, you can write custom script as shown below.

```
frappe.ui.form.on("Lead", "state", function(frm) {
  if(frm.doc.state == "Karnataka") {
    set_field_options("city", ["Bangalore","Mysore"])
  } else if(frm.doc.state == "Maharashtra") {
    set_field_options("city", ["Mumbai","Pune"])
  } else if(frm.doc.state == "") {
    set_field_options("city", ["","Bangalore","Mysore","Mumbai","Pune"])
  }
});
  

```

![Opening Account](/files/filter_dropdown.gif)



Here’s an example of a custom script that filters options in a Select field within a child table:

```
frappe.ui.form.on('Parent DocType', {
    refresh: function (frm) {
        // Trigger this function when the form is refreshed or reloaded
        frm.fields_dict['child_table_fieldname'].grid.get_field('select_fieldname').get_query = function(doc, cdt, cdn) {
            return {
                filters: [
                    ['Some Field', '=', 'Some Value'] // Replace with your filter criteria
                ]
            };
        };
    }
});
```

### Example Scenario

Suppose you have a parent DocType called **Sales Order** with a child table field called **items**. The child table has a Select field named **itemcode**, and you want to filter the options to show only items from a specific category.

Here’s how your script might look:

```
frappe.ui.form.on('Sales Order', {
    refresh: function (frm) {
        frm.fields_dict['items'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
            return {
                filters: [
                    ['Item Group', '=', 'Specific Category'] // Adjust the filter criteria as needed
                ]
            };
        };
    }
});
  

```

