# BCA Smart Campus (Python / Flask)
Sample College, Demo City — Smart Campus Management System (PHP project converted to Python).

> All students, faculty, phone numbers and emails in the demo data are **fictional** (generated for demo purposes).

## Run
```
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000 . The database (`smart_campus.db`, SQLite) is created automatically with demo data.
To reset everything: delete `smart_campus.db` and run again (or `python seed.py`).

## Demo logins
| Role | Username | Password |
|---|---|---|
| Admin | admin | admin123 |
| Faculty | faculty | faculty123 |
| Student | student | student123 |

## Modules
Public homepage (hero, features, fee structure, faculty, syllabus tabs, notices carousel, events, portals) · Login ·
**Admin:** students, faculty, user accounts, attendance, assignments, exams, study materials, fees (+bulk), hostel, library, notices & events ·
**Faculty:** dashboard, attendance, my students, assignments + grading, marks/results, study material upload, exam schedule, notices, leave approve/reject ·
**Student:** dashboard, attendance, performance, timetable, exams, assignments (submit), study material, library, fee status (pay), hostel, leave, notices.

## Database
Same tables/columns as the documentation (students, users, faculty, attendance, assignments, assignment_submissions, fees, study_materials,
exam_schedule, exam_results, notices, events, leave_requests, timetable, books). Added because they are in the ERD but missing from the
documentation SQL: **hostel_rooms, hostel_allotments, book_issues**. See `schema.sql`.

## Files
`app.py` routes · `schema.sql` tables · `seed.py` demo data · `college_config.py` fees/curriculum/college info · `templates/` pages · `static/` css+js · `uploads/` study material files.
Notes: Sem 1–4 subject names in `college_config.py` are assumed (edit them); Sem 5–6 are from the documentation. Passwords are stored hashed.
