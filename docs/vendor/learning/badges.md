---
title: "Badges\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t"
space: "Learning"
url: "https://docs.frappe.io/learning/badges"
updated: "2026-02-24"
---

Admins can create badges with rules in the learning system. When a user completes the actions defined in the rules the badge gets assigned to them.

There are 3 types of events on which badges get assigned to learners. Let us understand them with examples.

### Assign a badge when a learner completes a quiz

You can assign a badge to learners when they complete a quiz. Each time a learner submits a quiz, a new record gets created under LMS Quiz Submission. So this is your event to assign the badge.

![Screenshot 2024-06-06 at 5.32.27 PM](/files/Screenshot 2024-06-06 at 5.32.27 PM.png)



So when creating a badge for this, you enter a title and description for the badge. You also attach the badge image.

Then you select the Event as **New** and select the DocType on which this rule applies. As this badge would be assigned on quiz submission, you select the DocType as LMS Quiz Submission.

You can also add a specific condition to it. For example, we want the badge to be assigned only if the learner gets 100% correct answers for a quiz.

Then you select the user who should receive this badge. In most DocTypes of Learning, the learner is scored in a field called Member. The same is true for quiz submission. So we select the user as **Member**.

Once you have entered all this information you save the document. Now each time a learner submits a quiz and scores 100% they would be assigned this badge.

If you want this badge to be assigned to the learner only once and not each time they submit the quiz, you enabled the option **Grant only once**.

### Assign a badge when the user completes a course

To create this badge the rules would be a bit different. When a student enrolls for a course, a new entry gets created in the LMS Enrollment doctype. Then each time they make progress in that course, the progress percentage gets updated in the same document. So you should select **LMS Enrollment** as the Reference Document Type and the event will be **Value Changed**.

The User Field would be **Member** and the Field To Check would be **progress**.

Then we need to apply a condition to check if the course is completed or not which is indicated by progress percentage. So we add this as the condition **doc.progress == float("100.0")**.

You can then add a relevant title and image and enable the badge to start using it.

![](/files/Screenshot%202025-02-06%20at%203.22.47%E2%80%AFPM.png)

### Assign a badge when a student completes a training

Trainings are done with the help of Batches. As such there is no progress tracking for an individual batch, such badges can be auto assigned. 

So select the Event as **Auto Assign**. Reference Document Type would be **Batch Student** as this is the child table where the students of a batch are stored. User Field would be **Student**. 

For condition we need to tell it which batch do these students belong to. For this we enter condition as a json where we specify the batch name as parent.

**{**  
    **"parent": "CLS-03050"**  
**}**



![](/files/Screenshot%202025-02-06%20at%203.22.54%E2%80%AFPM.png)

