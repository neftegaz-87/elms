---
title: "Course Progress Calculation"
space: "Learning"
url: "https://docs.frappe.io/learning/others/course-progress-calculation"
updated: "2026-04-15"
---

Frappe Learning automatically tracks learner progress to provide a seamless experience for both students and instructors. Progress is calculated at three levels: the individual lesson, the overall course, and the program.

**Note:** course progress is only applicable for enrolled users i.e. if you are a instructor/moderator/evaluator, you need to enroll yourself in the course manually to see progress for yourself.

---

## How Lesson Completion is Triggered

A lesson is marked as "Complete" based on the type of content it contains. The system uses specific triggers to ensure a learner has actually engaged with the material.

### 1. Automatic Triggers

For lessons consisting primarily of text or images, the system uses a time-based trigger:

- **Time on Page:** A lesson is automatically marked as complete if a logged-in student stays on the lesson page for at least **30 seconds**.

### 2. Video Lessons

If a lesson contains a video (via the Upload block or supported Video Hosting), completion is tied to the playback:

- **Watch to End:** The lesson is marked complete only when the video reaches its full duration.

### 3. Interactive Requirements

If a lesson contains assessments, the "30-second rule" is ignored. The lesson will only be marked complete once the following conditions are met:

- **Quizzes:** The student must attempt the quiz and achieve a score equal to or higher than the **Passing Percentage**.
- **Assignments:** The student must successfully upload a file or submit a URL as required by the assignment.
- **Programming Exercises:** The student must submit code that passes the required test cases.

---

## Understanding Progress Levels

### Course Progress

Course progress is represented as a percentage (0–100%). It is calculated by dividing the number of **Completed Lessons** by the **Total Lessons** available in the course.

- This percentage is updated in real-time every time a student completes a lesson.
- Instructors can view this percentage in the **Enrollment List** to see how far each student has advanced.

### Program Progress

For students enrolled in a **Program (Learning Path)**, the system calculates an aggregate score.

- **Average Completion:** Program progress is the average of the completion percentages of all courses within that program.
- Completion of a Program often triggers the issuance of a final Program Certificate.

