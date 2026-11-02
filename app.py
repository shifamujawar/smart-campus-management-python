"""BCA Smart Campus - Integrated College Management System (Flask + SQLite).
Python version of the PHP project: Sample College, Demo City.  Run:  python app.py
"""
import os, sqlite3, time, re
from datetime import date, datetime, timedelta
from functools import wraps
from flask import (Flask, g, render_template, request, redirect, url_for, session, flash,
                   send_from_directory, abort)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from college_config import *
from seed import init_db, DB, BASE

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smart-campus-change-this-key")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
UPLOADS = os.path.join(BASE, "uploads", "materials")
os.makedirs(UPLOADS, exist_ok=True)
ALLOWED = {"pdf", "ppt", "pptx", "doc", "docx", "zip", "mp4", "txt"}

# ───────────────────────── DB helpers ─────────────────────────
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB); g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db
@app.teardown_appcontext
def close_db(e=None):
    c = g.pop("db", None)
    if c: c.close()
def q(sql, args=()): return db().execute(sql, args).fetchall()
def one(sql, args=()): return db().execute(sql, args).fetchone()
def run(sql, args=()):
    cur = db().execute(sql, args); db().commit(); return cur
def scalar(sql, args=()):
    r = one(sql, args); return (r[0] if r and r[0] is not None else 0)

# ───────────────────────── Auth ─────────────────────────
def login_required(*roles):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            if "user_id" not in session: return redirect(url_for("login"))
            if roles and session["role"] not in roles:
                flash("You do not have access to that page.", "danger"); return redirect(url_for("dashboard"))
            return f(*a, **k)
        return w
    return deco
def role(): return session.get("role")
def ref(): return session.get("ref_id") or ""

def check_pw(stored, pw):
    try:
        if check_password_hash(stored, pw): return True
    except Exception: pass
    return stored == pw          # plain text (testing), as in the PHP version

# ───────────────────────── Menu / template context ─────────────────────────
MENU = {
 "admin": [("OVERVIEW", [("Dashboard", "fa-house", "admin_dash", "admin_dash")]),
           ("PEOPLE", [("Students", "fa-user-group", "students_list", "students"), ("Faculty", "fa-chalkboard-user", "faculty_list", "faculty_list"),
                       ("User Accounts", "fa-user-shield", "accounts", "accounts")]),
           ("ACADEMIC", [("Attendance", "fa-calendar-check", "attendance", "attendance"), ("Assignments", "fa-list-check", "assignments", "assignment"),
                         ("Exam Schedule", "fa-file-pen", "exams", "exams"), ("Study Materials", "fa-folder-open", "materials", "materials")]),
           ("FINANCE & CAMPUS", [("Fee Management", "fa-credit-card", "fees", "fees"), ("Hostel", "fa-bed", "hostel", "hostel")]),
           ("RESOURCES", [("Library", "fa-book", "library", "library"), ("Notices & Events", "fa-bell", "notices", "notices")])],
 "faculty": [("OVERVIEW", [("Dashboard", "fa-house", "faculty_dash", "faculty_dash"), ("My Profile", "fa-user", "profile", "profile")]),
             ("TEACHING", [("Mark Attendance", "fa-calendar-check", "attendance", "attendance"), ("My Students", "fa-user-group", "my_students", "my_students"),
                           ("Assignments", "fa-list-check", "assignments", "assignment")]),
             ("ACADEMIC", [("Marks / Results", "fa-chart-simple", "exams", "exams"), ("Study Material", "fa-upload", "materials", "materials"),
                           ("Exam Schedule", "fa-file-pen", "exams", "exams_x")]),
             ("ADMINISTRATION", [("Leave Requests", "fa-file-medical", "leave", "leave"), ("Post Notices", "fa-bell", "notices", "notices")])],
 "student": [("OVERVIEW", [("Dashboard", "fa-house", "student_dash", "student_dash"), ("My Profile", "fa-circle-user", "profile", "profile")]),
             ("ACADEMICS", [("Attendance", "fa-calendar-check", "attendance", "attendance"), ("Performance", "fa-chart-line", "performance", "performance"),
                            ("Timetable", "fa-table-cells", "timetable", "timetable"), ("Exams", "fa-file-pen", "exams", "exams")]),
             ("LEARNING", [("Assignments", "fa-list-check", "assignments", "assignment"), ("Study Material", "fa-folder-open", "materials", "materials"),
                           ("Library", "fa-book", "library", "library")]),
             ("CAMPUS", [("Fee Status", "fa-credit-card", "fees", "fees"), ("Hostel", "fa-bed", "hostel", "hostel"),
                         ("Leave", "fa-file-medical", "leave", "leave"), ("Notices", "fa-bell", "notices", "notices")])],
}
ROLE_ICON = {"admin": "fa-shield-halved", "faculty": "fa-chalkboard-user", "student": "fa-user-graduate"}
ROLE_TITLE = {"admin": "Admin Panel", "faculty": "Faculty Portal", "student": "Student Portal"}

@app.context_processor
def inject():
    ctx = dict(C=COLLEGE, now=datetime.now(), today=date.today().isoformat(), role=role(), ROLE_ICON=ROLE_ICON, ROLE_TITLE=ROLE_TITLE,
               MENU=MENU.get(role(), []), FEE_TOTAL=FEE_TOTAL, current_subjects=current_subjects, sections=SECTIONS)
    if "user_id" in session:
        ctx["alerts"] = scalar("SELECT COUNT(*) FROM notices WHERE expires_at IS NULL OR expires_at >= ?", (date.today().isoformat(),))
    return ctx

@app.template_filter("dmy")
def dmy(v, fmt="%d %b %Y"):
    try: return datetime.strptime(str(v)[:10], "%Y-%m-%d").strftime(fmt)
    except Exception: return v or "—"
@app.template_filter("hm")
def hm(v):
    try: return datetime.strptime(str(v)[:5], "%H:%M").strftime("%I:%M %p").lstrip("0")
    except Exception: return v or ""
@app.template_filter("inr")
def inr(v): return "₹{:,.0f}".format(v or 0)
@app.template_filter("daysleft")
def daysleft(v):
    try:
        n = (datetime.strptime(str(v)[:10], "%Y-%m-%d").date() - date.today()).days
        return "Today" if n == 0 else ("In %d day%s" % (n, "" if n == 1 else "s") if n > 0 else "%d days ago" % -n)
    except Exception: return ""

def grade_for(marks, mx):
    p = (marks / mx * 100) if mx else 0
    return "O" if p >= 90 else "A+" if p >= 80 else "A" if p >= 70 else "B" if p >= 60 else "C" if p >= 50 else "F"

def pct(p, t): return round(p / t * 100) if t else 0
def sanitize(s): return re.sub(r"<[^>]*>", "", (s or "").strip())
def me_student(): return one("SELECT * FROM students WHERE student_id=?", (ref(),))
def me_faculty(): return one("SELECT * FROM faculty WHERE faculty_id=?", (ref(),))
def active_notices(limit=None):
    sql = "SELECT * FROM notices WHERE expires_at IS NULL OR expires_at >= ? ORDER BY CASE priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END, created_at DESC, id DESC"
    if limit: sql += " LIMIT %d" % limit
    return q(sql, (date.today().isoformat(),))
def upcoming_events(limit=6):
    return q("SELECT * FROM events WHERE event_date >= ? ORDER BY event_date LIMIT ?", (date.today().isoformat(), limit))

# ───────────────────────── Public pages ─────────────────────────
@app.route("/")
def index():
    tabs = {y: [(sem, subs) for sem, subs in CURRICULUM[y].items()] for y in CURRICULUM}
    return render_template("index.html", n_students=scalar("SELECT COUNT(*) FROM students"), n_faculty=scalar("SELECT COUNT(*) FROM faculty"),
        n_books=scalar("SELECT COUNT(*) FROM books"), fees=FEE_STRUCTURE, faculty=q("SELECT * FROM faculty ORDER BY faculty_id"),
        tabs=tabs, cur=CURRENT_SEM, notices=active_notices(6), events=upcoming_events(4))

@app.route("/campus-map")
def campus_map(): return render_template("campus_map.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session: return redirect(url_for("dashboard"))
    error = ""
    if request.method == "POST":
        u = one("SELECT * FROM users WHERE username=?", (request.form.get("username", "").strip(),))
        if u and check_pw(u["password"], request.form.get("password", "").strip()):
            session.clear(); session.update(user_id=u["id"], username=u["username"], role=u["role"], ref_id=u["ref_id"] or "")
            name = u["username"].capitalize()
            if u["role"] == "student" and u["ref_id"]:
                r = one("SELECT name FROM students WHERE student_id=?", (u["ref_id"],)); name = r["name"] if r else name
            elif u["role"] == "faculty" and u["ref_id"]:
                r = one("SELECT name FROM faculty WHERE faculty_id=?", (u["ref_id"],)); name = r["name"] if r else name
            session["name"] = name
            return redirect(url_for("dashboard"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
@login_required()
def dashboard(): return redirect(url_for({"admin": "admin_dash", "faculty": "faculty_dash"}.get(role(), "student_dash")))

# ───────────────────────── Dashboards ─────────────────────────
@app.route("/admin")
@login_required("admin")
def admin_dash():
    yr = {y: scalar("SELECT COUNT(*) FROM students WHERE year=?", (y,)) for y in (1, 2, 3)}
    st = dict(students=scalar("SELECT COUNT(*) FROM students"), faculty=scalar("SELECT COUNT(*) FROM faculty"),
              collected=scalar("SELECT SUM(paid_amount) FROM fees"), pending=scalar("SELECT COUNT(*) FROM fees WHERE status!='Paid'"),
              notices=len(active_notices()), occ=scalar("SELECT COUNT(*) FROM hostel_allotments WHERE status='Active'"),
              rooms=scalar("SELECT SUM(capacity) FROM hostel_rooms"))
    return render_template("admin_dash.html", title="Admin Dashboard", yr=yr, st=st, students=q("SELECT * FROM students ORDER BY created_at DESC, student_id LIMIT 6"), notices=active_notices(5))

@app.route("/faculty")
@login_required("faculty")
def faculty_dash():
    f = me_faculty(); fid = ref(); today = datetime.now().strftime("%A")
    st = dict(students=scalar("SELECT COUNT(*) FROM students"),
              classes=scalar("SELECT COUNT(DISTINCT date) FROM attendance WHERE strftime('%Y-%m',date)=strftime('%Y-%m','now')"),
              assigns=scalar("SELECT COUNT(*) FROM assignments WHERE faculty_id=?", (fid,)),
              leaves=scalar("SELECT COUNT(*) FROM leave_requests WHERE status='Pending'"),
              exams=scalar("SELECT COUNT(*) FROM exam_schedule WHERE exam_date >= ?", (date.today().isoformat(),)),
              mats=scalar("SELECT COUNT(*) FROM study_materials WHERE faculty_id=?", (fid,)))
    sched = q("SELECT * FROM timetable WHERE faculty_id=? AND day_of_week=? ORDER BY start_time", (fid, today))
    leaves = q("SELECT l.*, s.name, s.year FROM leave_requests l JOIN students s ON s.student_id=l.student_id WHERE l.status='Pending' ORDER BY l.created_at DESC LIMIT 5")
    return render_template("faculty_dash.html", title="Faculty Dashboard", f=f, st=st, sched=sched, leaves=leaves, today_name=today)

@app.route("/student")
@login_required("student")
def student_dash():
    s = me_student()
    if not s: abort(404)
    tot = scalar("SELECT COUNT(*) FROM attendance WHERE student_id=?", (s["student_id"],))
    pres = scalar("SELECT COUNT(*) FROM attendance WHERE student_id=? AND status IN ('Present','Late')", (s["student_id"],))
    res = q("SELECT marks_obtained m, max_marks x FROM exam_results WHERE student_id=?", (s["student_id"],))
    cgpa = round(sum(r["m"] / r["x"] * 10 for r in res if r["x"]) / len(res), 1) if res else "—"
    pending = scalar("SELECT COUNT(*) FROM assignments a WHERE a.year=? AND NOT EXISTS (SELECT 1 FROM assignment_submissions x WHERE x.assignment_id=a.id AND x.student_id=?)", (s["year"], s["student_id"]))
    st = dict(att=pct(pres, tot), cgpa=cgpa, pending=pending, due=scalar("SELECT SUM(amount-paid_amount) FROM fees WHERE student_id=? AND status!='Paid'", (s["student_id"],)),
              books=scalar("SELECT COUNT(*) FROM book_issues WHERE student_id=? AND status='Issued'", (s["student_id"],)),
              exams=scalar("SELECT COUNT(*) FROM exam_schedule WHERE year=? AND exam_date>=?", (s["year"], date.today().isoformat())))
    today = datetime.now().strftime("%A")
    classes = q("SELECT t.*, f.name fname FROM timetable t LEFT JOIN faculty f ON f.faculty_id=t.faculty_id WHERE year=? AND section=? AND day_of_week=? ORDER BY start_time", (s["year"], s["section"] or "A", today))
    hour = datetime.now().hour; greet = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"
    return render_template("student_dash.html", title="Student Dashboard", s=s, st=st, classes=classes, today_name=today, greet=greet,
                           sem=CURRENT_SEM[s["year"]], notices=active_notices(5))

# ───────────────────────── Students (admin) ─────────────────────────
@app.route("/students")
@login_required("admin")
def students_list():
    y, sec, term = request.args.get("year", ""), request.args.get("section", ""), request.args.get("q", "").strip()
    sql, a = "SELECT * FROM students WHERE 1=1", []
    if y: sql += " AND year=?"; a.append(int(y))
    if sec: sql += " AND section=?"; a.append(sec)
    if term: sql += " AND (name LIKE ? OR student_id LIKE ? OR email LIKE ?)"; a += ["%%%s%%" % term] * 3
    counts = {y_: scalar("SELECT COUNT(*) FROM students WHERE year=?", (y_,)) for y_ in (1, 2, 3)}
    return render_template("students.html", title="BCA Students", rows=q(sql + " ORDER BY year, student_id", a), counts=counts, f=dict(year=y, section=sec, q=term))

def student_form_data():
    f = request.form
    return dict(student_id=sanitize(f.get("student_id")), name=sanitize(f.get("name")), email=sanitize(f.get("email")), phone=sanitize(f.get("phone")),
                year=int(f.get("year") or 1), section=sanitize(f.get("section")), gender=sanitize(f.get("gender")), dob=f.get("dob") or None, address=sanitize(f.get("address")))

@app.route("/students/add", methods=["GET", "POST"])
@login_required("admin")
def students_add():
    if request.method == "POST":
        d = student_form_data()
        if not d["student_id"] or not d["name"] or not d["email"]:
            flash("Student ID, Name and Email are required.", "danger")
        elif one("SELECT 1 FROM students WHERE student_id=? OR email=?", (d["student_id"], d["email"])):
            flash("A student with this ID or email already exists.", "danger")
        else:
            run("INSERT INTO students(student_id,name,email,phone,year,section,gender,dob,address) VALUES(:student_id,:name,:email,:phone,:year,:section,:gender,:dob,:address)", d)
            if request.form.get("create_login"):
                un = sanitize(request.form.get("username")) or d["student_id"].lower()
                if one("SELECT 1 FROM users WHERE username=?", (un,)): flash("Student added, but the username was already taken (no login created).", "warning")
                else: run("INSERT INTO users(username,password,role,name,email,ref_id) VALUES(?,?,?,?,?,?)", (un, generate_password_hash(request.form.get("password") or "student123"), "student", d["name"], d["email"], d["student_id"]))
            flash("Student '%s' added successfully!" % d["name"], "success"); return redirect(url_for("students_list"))
    return render_template("student_form.html", title="Add Student", s=None)

@app.route("/students/edit/<sid>", methods=["GET", "POST"])
@login_required("admin")
def students_edit(sid):
    s = one("SELECT * FROM students WHERE student_id=?", (sid,)) or abort(404)
    if request.method == "POST":
        d = student_form_data(); d["student_id"] = sid
        run("UPDATE students SET name=:name,email=:email,phone=:phone,year=:year,section=:section,gender=:gender,dob=:dob,address=:address WHERE student_id=:student_id", d)
        run("UPDATE users SET name=? WHERE ref_id=? AND role='student'", (d["name"], sid))
        flash("Student updated.", "success"); return redirect(url_for("students_list"))
    return render_template("student_form.html", title="Edit Student", s=s)

@app.route("/students/view/<sid>")
@login_required("admin", "faculty")
def students_view(sid):
    s = one("SELECT * FROM students WHERE student_id=?", (sid,)) or abort(404)
    tot = scalar("SELECT COUNT(*) FROM attendance WHERE student_id=?", (sid,)); pr = scalar("SELECT COUNT(*) FROM attendance WHERE student_id=? AND status IN ('Present','Late')", (sid,))
    return render_template("student_view.html", title="Student Profile", s=s, att=pct(pr, tot), results=q("SELECT * FROM exam_results WHERE student_id=? ORDER BY exam_date DESC", (sid,)),
                           fees=q("SELECT * FROM fees WHERE student_id=?", (sid,)))

@app.route("/students/delete/<sid>")
@login_required("admin")
def students_delete(sid):
    run("DELETE FROM users WHERE ref_id=? AND role='student'", (sid,)); run("DELETE FROM students WHERE student_id=?", (sid,))
    flash("Student deleted.", "success"); return redirect(url_for("students_list"))

@app.route("/my-students")
@login_required("faculty")
def my_students():
    rows = q("""SELECT s.*, COALESCE(ROUND(100.0*SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END)/NULLIF(COUNT(a.id),0)),0) att_pct
                FROM students s LEFT JOIN attendance a ON a.student_id=s.student_id GROUP BY s.student_id ORDER BY s.year, s.name""")
    return render_template("my_students.html", title="My Students", rows=rows)

# ───────────────────────── Faculty (admin) + Accounts ─────────────────────────
@app.route("/faculty-members", methods=["GET", "POST"])
@login_required("admin")
def faculty_list():
    if request.method == "POST":
        f = request.form; fid = sanitize(f.get("faculty_id")); nm = sanitize(f.get("name")); em = sanitize(f.get("email"))
        if not fid or not nm or not em: flash("Faculty ID, Name and Email are required.", "danger")
        elif one("SELECT 1 FROM faculty WHERE faculty_id=? OR email=?", (fid, em)): flash("Faculty ID or email already exists.", "danger")
        else:
            run("INSERT INTO faculty(faculty_id,name,email,phone,designation,qualification,subjects) VALUES(?,?,?,?,?,?,?)",
                (fid, nm, em, sanitize(f.get("phone")), sanitize(f.get("designation")), sanitize(f.get("qualification")), sanitize(f.get("subjects"))))
            if f.get("create_login"):
                un = sanitize(f.get("username")) or fid.lower()
                if not one("SELECT 1 FROM users WHERE username=?", (un,)):
                    run("INSERT INTO users(username,password,role,name,email,ref_id) VALUES(?,?,?,?,?,?)", (un, generate_password_hash(f.get("password") or "faculty123"), "faculty", nm, em, fid))
            flash("Faculty added.", "success")
        return redirect(url_for("faculty_list"))
    term = request.args.get("q", "").strip()
    rows = q("SELECT * FROM faculty WHERE name LIKE ? OR faculty_id LIKE ? ORDER BY faculty_id", ("%%%s%%" % term,) * 2)
    return render_template("faculty.html", title="BCA Faculty", rows=rows, designations=DESIGNATIONS)

@app.route("/faculty-members/delete/<fid>")
@login_required("admin")
def faculty_delete(fid):
    run("DELETE FROM users WHERE ref_id=? AND role='faculty'", (fid,)); run("DELETE FROM faculty WHERE faculty_id=?", (fid,))
    flash("Faculty deleted.", "success"); return redirect(url_for("faculty_list"))

@app.route("/accounts", methods=["GET", "POST"])
@login_required("admin")
def accounts():
    if request.method == "POST":
        f = request.form; un = sanitize(f.get("username")); r = f.get("role"); rf = f.get("ref_id") or None
        if not un or not f.get("password"): flash("Username and password are required.", "danger")
        elif one("SELECT 1 FROM users WHERE username=?", (un,)): flash("Username already exists.", "danger")
        else:
            nm = sanitize(f.get("name")) or un.capitalize()
            run("INSERT INTO users(username,password,role,name,ref_id) VALUES(?,?,?,?,?)", (un, generate_password_hash(f["password"]), r, nm, rf)); flash("Account created.", "success")
        return redirect(url_for("accounts"))
    return render_template("accounts.html", title="User Accounts", rows=q("SELECT * FROM users ORDER BY role, username"),
                           students=q("SELECT student_id,name FROM students ORDER BY name"), faculty=q("SELECT faculty_id,name FROM faculty ORDER BY name"))

@app.route("/accounts/delete/<int:uid>")
@login_required("admin")
def accounts_delete(uid):
    if uid == session["user_id"]: flash("You cannot delete your own account.", "danger")
    else: run("DELETE FROM users WHERE id=?", (uid,)); flash("Account deleted.", "success")
    return redirect(url_for("accounts"))

@app.route("/profile", methods=["GET", "POST"])
@login_required("faculty", "student")
def profile():
    if request.method == "POST":
        pw = request.form.get("new_password", "")
        if len(pw) < 6: flash("Password must be at least 6 characters.", "danger")
        else: run("UPDATE users SET password=? WHERE id=?", (generate_password_hash(pw), session["user_id"])); flash("Password changed.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html", title="My Profile", p=me_student() if role() == "student" else me_faculty())

# ───────────────────────── Attendance ─────────────────────────
@app.route("/attendance", methods=["GET", "POST"])
@login_required()
def attendance():
    if role() == "student":
        s = me_student()
        rows = q("""SELECT subject, COUNT(*) total, SUM(status='Present') present, SUM(status='Absent') absent, SUM(status='Late') late
                    FROM attendance WHERE student_id=? GROUP BY subject ORDER BY subject""", (s["student_id"],))
        tot = sum(r["total"] for r in rows); pr = sum(r["present"] + r["late"] for r in rows)
        return render_template("attendance_student.html", title="Attendance", rows=rows, tot=tot, pr=sum(r["present"] for r in rows), ab=sum(r["absent"] for r in rows), overall=pct(pr, tot))
    yr, sec = request.args.get("year", ""), request.args.get("section", "")
    if request.method == "POST":
        f = request.form; yr_i = int(f["year"]); sec = f.get("section", ""); dt = f["date"]; subj = sanitize(f["subject"])
        ids = [r["student_id"] for r in q("SELECT student_id FROM students WHERE year=?" + (" AND section=?" if sec else ""), (yr_i, sec) if sec else (yr_i,))]
        for sid in ids: db().execute("DELETE FROM attendance WHERE student_id=? AND date=? AND subject=?", (sid, dt, subj))
        n = 0
        for sid in ids:
            stt = f.get("status[%s]" % sid)
            if stt in ("Present", "Absent", "Late"):
                db().execute("INSERT INTO attendance(student_id,subject,status,date,year,section,marked_by) VALUES(?,?,?,?,?,?,?)", (sid, subj, stt, dt, yr_i, sec or None, session["username"])); n += 1
        db().commit(); flash("Attendance marked for %d student(s) — %s on %s." % (n, subj, dmy(dt)), "success")
        return redirect(url_for("attendance", year=yr_i, section=sec))
    studs = []; recent = []
    if yr:
        sql, a = "SELECT * FROM students WHERE year=?", [int(yr)]
        if sec: sql += " AND section=?"; a.append(sec)
        studs = q(sql + " ORDER BY name", a)
        sql2 = """SELECT a.date, a.subject, s.section, COUNT(*) total, SUM(a.status='Present') present, SUM(a.status='Absent') absent FROM attendance a
                  JOIN students s ON s.student_id=a.student_id WHERE s.year=?""" + (" AND s.section=?" if sec else "") + " GROUP BY a.date,a.subject,s.section ORDER BY a.date DESC LIMIT 15"
        recent = q(sql2, a)
    else:
        recent = q("""SELECT a.date, a.subject, s.year, s.section, COUNT(*) total, SUM(a.status='Present') present, SUM(a.status='Absent') absent FROM attendance a
                      JOIN students s ON s.student_id=a.student_id GROUP BY a.date,a.subject,s.year,s.section ORDER BY a.date DESC LIMIT 15""")
    return render_template("attendance.html", title="Attendance", year=yr, section=sec, studs=studs, recent=recent, subjects=current_subjects(int(yr)) if yr else [])

# ───────────────────────── Assignments ─────────────────────────
@app.route("/assignments", methods=["GET", "POST"])
@login_required()
def assignments():
    if request.method == "POST":
        f = request.form
        if role() in ("faculty", "admin") and f.get("post_assignment"):
            if not f.get("title") or not f.get("subject") or not f.get("due_date"): flash("Title, Subject and Due Date are required!", "danger")
            else:
                run("INSERT INTO assignments(title,description,subject,year,section,faculty_id,due_date,max_marks,priority) VALUES(?,?,?,?,?,?,?,?,?)",
                    (sanitize(f["title"]), sanitize(f.get("description")), sanitize(f["subject"]), int(f["year"]), f.get("section", ""), ref() or None, f["due_date"], int(f.get("max_marks") or 10), f.get("priority", "Medium")))
                flash("Assignment '%s' posted successfully!" % f["title"], "success")
        elif role() == "student" and f.get("submit_assignment"):
            s = me_student(); aid = int(f["assignment_id"]); ans = sanitize(f.get("answer_text"))
            a = one("SELECT * FROM assignments WHERE id=?", (aid,))
            if not ans: flash("Please write your answer.", "danger")
            elif one("SELECT 1 FROM assignment_submissions WHERE assignment_id=? AND student_id=?", (aid, s["student_id"])): flash("You have already submitted this assignment!", "danger")
            else:
                late = a and a["due_date"] < date.today().isoformat()
                run("INSERT INTO assignment_submissions(assignment_id,student_id,submission_text,status) VALUES(?,?,?,?)", (aid, s["student_id"], ans, "Late" if late else "Submitted"))
                flash("Assignment submitted successfully!", "success")
        return redirect(url_for("assignments"))
    if role() == "student":
        s = me_student()
        rows = q("""SELECT a.*, f.name fname, x.id sub_id, x.status sub_status, x.marks_obtained, x.remarks, x.submission_text FROM assignments a
                    LEFT JOIN faculty f ON f.faculty_id=a.faculty_id LEFT JOIN assignment_submissions x ON x.assignment_id=a.id AND x.student_id=?
                    WHERE a.year=? ORDER BY a.due_date""", (s["student_id"], s["year"]))
        return render_template("assignments_student.html", title="Assignments", rows=rows, s=s)
    where, a = ("WHERE a.faculty_id=?", (ref(),)) if role() == "faculty" else ("", ())
    rows = q("SELECT a.*, f.name fname, (SELECT COUNT(*) FROM assignment_submissions x WHERE x.assignment_id=a.id) subs FROM assignments a LEFT JOIN faculty f ON f.faculty_id=a.faculty_id %s ORDER BY a.created_at DESC, a.id DESC" % where, a)
    return render_template("assignments.html", title="Assignments", rows=rows, all_subjects=all_subjects())

@app.route("/assignments/<int:aid>/submissions", methods=["GET", "POST"])
@login_required("faculty", "admin")
def assignment_subs(aid):
    a = one("SELECT * FROM assignments WHERE id=?", (aid,)) or abort(404)
    if request.method == "POST":
        sid = int(request.form["submission_id"]); mk = float(request.form.get("marks") or 0)
        run("UPDATE assignment_submissions SET marks_obtained=?, marks=?, remarks=?, status='Graded' WHERE id=?", (min(mk, a["max_marks"]), int(mk), sanitize(request.form.get("remarks")), sid))
        flash("Marks saved!", "success"); return redirect(url_for("assignment_subs", aid=aid))
    subs = q("SELECT x.*, s.name, s.year FROM assignment_submissions x JOIN students s ON s.student_id=x.student_id WHERE x.assignment_id=? ORDER BY x.submitted_at", (aid,))
    return render_template("assignment_subs.html", title="Submissions", a=a, subs=subs)

@app.route("/assignments/delete/<int:aid>")
@login_required("faculty", "admin")
def assignment_delete(aid):
    run("DELETE FROM assignment_submissions WHERE assignment_id=?", (aid,)); run("DELETE FROM assignments WHERE id=?", (aid,))
    flash("Assignment deleted.", "success"); return redirect(url_for("assignments"))

# ───────────────────────── Exams ─────────────────────────
@app.route("/exams", methods=["GET", "POST"])
@login_required()
def exams():
    if role() == "student":
        s = me_student()
        return render_template("exams_student.html", title="Exams", up=q("SELECT * FROM exam_schedule WHERE year=? AND exam_date>=? ORDER BY exam_date", (s["year"], date.today().isoformat())),
                               res=q("SELECT * FROM exam_results WHERE student_id=? ORDER BY exam_date DESC", (s["student_id"],)), s=s)
    tab = request.args.get("tab", "schedule")
    if request.method == "POST":
        f = request.form
        if f.get("add_exam"):
            run("INSERT INTO exam_schedule(subject,year,section,exam_date,start_time,end_time,hall,faculty_id,exam_type,max_marks) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (sanitize(f["subject"]), int(f["year"]), f.get("section", ""), f["exam_date"], f.get("start_time") or "10:00", f.get("end_time") or "13:00", sanitize(f.get("hall")) or "L-101", ref() or None, f.get("exam_type", "Internal"), int(f.get("max_marks") or 20)))
            flash("Exam scheduled.", "success"); return redirect(url_for("exams"))
        if f.get("save_result"):
            mo, mx = float(f["marks_obtained"]), int(f.get("max_marks") or 20)
            run("""INSERT INTO exam_results(student_id,subject,year,exam_type,marks_obtained,max_marks,grade,remarks,faculty_id,exam_date) VALUES(?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(student_id,subject,exam_type) DO UPDATE SET marks_obtained=excluded.marks_obtained, max_marks=excluded.max_marks, grade=excluded.grade, remarks=excluded.remarks, exam_date=excluded.exam_date""",
                (f["student_id"], sanitize(f["subject"]), int(f["year"]), f["exam_type"], mo, mx, f.get("grade") or grade_for(mo, mx), sanitize(f.get("remarks")), ref() or None, f.get("exam_date") or date.today().isoformat()))
            flash("Result saved successfully!", "success"); return redirect(url_for("exams", tab="results"))
    ry = request.args.get("ryear", "3")
    return render_template("exams.html", title="Exam Management", tab=tab, sched=q("SELECT * FROM exam_schedule ORDER BY exam_date"), ryear=ry,
        studs=q("SELECT student_id,name,year FROM students WHERE year=? ORDER BY name", (int(ry),)), results=q("SELECT r.*, s.name FROM exam_results r JOIN students s ON s.student_id=r.student_id ORDER BY r.exam_date DESC LIMIT 20"))

@app.route("/exams/delete/<int:eid>")
@login_required("faculty", "admin")
def exams_delete(eid):
    run("DELETE FROM exam_schedule WHERE id=?", (eid,)); flash("Exam deleted.", "success"); return redirect(url_for("exams"))

@app.route("/performance")
@login_required("student")
def performance():
    s = me_student(); res = q("SELECT * FROM exam_results WHERE student_id=? ORDER BY exam_date DESC", (s["student_id"],))
    mo = sum(r["marks_obtained"] for r in res); mx = sum(r["max_marks"] for r in res)
    return render_template("performance.html", title="Academic Performance", res=res, score=pct(mo, mx), grade=grade_for(mo, mx) if mx else "—")

@app.route("/timetable")
@login_required("student")
def timetable():
    s = me_student(); days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    rows = q("SELECT t.*, f.name fname FROM timetable t LEFT JOIN faculty f ON f.faculty_id=t.faculty_id WHERE year=? AND section=? ORDER BY start_time", (s["year"], s["section"] or "A"))
    return render_template("timetable.html", title="Timetable", days=days, rows=rows, s=s)

# ───────────────────────── Study materials ─────────────────────────
@app.route("/materials", methods=["GET", "POST"])
@login_required()
def materials():
    if request.method == "POST" and role() in ("faculty", "admin"):
        f = request.form; fp, ft, fs = "", "PDF", ""; file = request.files.get("material_file"); ok = True
        if file and file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext not in ALLOWED: flash("File type not allowed!", "danger"); ok = False
            else:
                fp = "mat_%d_%s" % (time.time(), secure_filename(file.filename)); file.save(os.path.join(UPLOADS, fp))
                ft = {"pdf": "PDF", "ppt": "PPT", "pptx": "PPT", "doc": "DOC", "docx": "DOC", "zip": "ZIP", "mp4": "Video"}.get(ext, ext.upper())
                sz = os.path.getsize(os.path.join(UPLOADS, fp)); fs = "%.1f MB" % (sz / 1048576) if sz > 1048576 else "%d KB" % round(sz / 1024)
        if ok:
            run("INSERT INTO study_materials(title,subject,year,section,faculty_id,file_path,file_type,file_size,description) VALUES(?,?,?,?,?,?,?,?,?)",
                (sanitize(f["title"]), sanitize(f["subject"]), int(f["year"]), f.get("section", ""), ref() or None, fp, ft, fs, sanitize(f.get("description"))))
            flash("Material added successfully!", "success")
        return redirect(url_for("materials"))
    if role() == "student":
        s = me_student(); rows = q("SELECT m.*, f.name fname FROM study_materials m LEFT JOIN faculty f ON f.faculty_id=m.faculty_id WHERE m.year=? ORDER BY m.created_at DESC", (s["year"],))
    else:
        rows = q("SELECT m.*, f.name fname FROM study_materials m LEFT JOIN faculty f ON f.faculty_id=m.faculty_id ORDER BY m.created_at DESC")
    return render_template("materials.html", title="Study Materials", rows=rows, all_subjects=all_subjects())

@app.route("/materials/file/<path:name>")
@login_required()
def material_file(name):
    return send_from_directory(UPLOADS, name, as_attachment=bool(request.args.get("dl")))

@app.route("/materials/delete/<int:mid>")
@login_required("faculty", "admin")
def materials_delete(mid):
    r = one("SELECT file_path FROM study_materials WHERE id=?", (mid,))
    if r and r["file_path"]:
        try: os.remove(os.path.join(UPLOADS, r["file_path"]))
        except OSError: pass
    run("DELETE FROM study_materials WHERE id=?", (mid,)); flash("Material deleted.", "success"); return redirect(url_for("materials"))

# ───────────────────────── Fees ─────────────────────────
def refresh_overdue():
    run("UPDATE fees SET status='Overdue' WHERE status='Pending' AND due_date IS NOT NULL AND due_date < ?", (date.today().isoformat(),))

@app.route("/fees", methods=["GET", "POST"])
@login_required("admin", "student")
def fees():
    refresh_overdue()
    if role() == "student":
        s = me_student()
        if request.method == "POST":
            run("UPDATE fees SET status='Paid', payment_date=?, paid_amount=amount WHERE student_id=? AND status!='Paid'", (date.today().isoformat(), s["student_id"]))
            flash("Payment successful. Thank you!", "success"); return redirect(url_for("fees"))
        rows = q("SELECT * FROM fees WHERE student_id=? ORDER BY created_at DESC", (s["student_id"],))
        return render_template("fees_student.html", title="Fee Status", pend=[r for r in rows if r["status"] != "Paid"], hist=[r for r in rows if r["status"] == "Paid"], s=s)
    if request.method == "POST":
        f = request.form
        if f.get("bulk_add"):
            n = 0
            for st in q("SELECT student_id FROM students WHERE year=?", (int(f["bulk_year"]),)):
                if not one("SELECT 1 FROM fees WHERE student_id=? AND fee_type=? AND due_date=?", (st["student_id"], f["bulk_fee_type"], f["bulk_due_date"])):
                    db().execute("INSERT INTO fees(student_id,fee_type,amount,due_date,status) VALUES(?,?,?,?,'Pending')", (st["student_id"], f["bulk_fee_type"], float(f["bulk_amount"]), f["bulk_due_date"])); n += 1
            db().commit(); flash("Bulk fee added for %d students." % n, "success")
        else:
            paid = float(f["amount"]) if f.get("status") == "Paid" else 0
            run("INSERT INTO fees(student_id,fee_type,amount,paid_amount,due_date,payment_date,status) VALUES(?,?,?,?,?,?,?)",
                (f["student_id"], f["fee_type"], float(f["amount"]), paid, f["due_date"], date.today().isoformat() if paid else None, f.get("status", "Pending")))
            flash("Fee record added.", "success")
        return redirect(url_for("fees"))
    y, stt, term = request.args.get("year", ""), request.args.get("status", ""), request.args.get("q", "").strip()
    sql, a = "SELECT f.*, s.name, s.year FROM fees f JOIN students s ON s.student_id=f.student_id WHERE 1=1", []
    if y: sql += " AND s.year=?"; a.append(int(y))
    if stt: sql += " AND f.status=?"; a.append(stt)
    if term: sql += " AND (s.name LIKE ? OR s.student_id LIKE ?)"; a += ["%%%s%%" % term] * 2
    rows = q(sql + " ORDER BY f.created_at DESC, f.id DESC", a)
    st = dict(collected=scalar("SELECT SUM(paid_amount) FROM fees"), pending=scalar("SELECT SUM(amount-paid_amount) FROM fees WHERE status!='Paid'"),
              defaulters=scalar("SELECT COUNT(DISTINCT student_id) FROM fees WHERE status!='Paid'"), total=scalar("SELECT COUNT(*) FROM fees"))
    return render_template("fees.html", title="BCA Fee Management", rows=rows, st=st, fee_structure=FEE_STRUCTURE, amounts=FEE_AMOUNTS,
                           studs=q("SELECT student_id,name,year FROM students ORDER BY year,name"), f=dict(year=y, status=stt, q=term))

@app.route("/fees/pay/<int:fid>")
@login_required("admin")
def fees_pay(fid):
    run("UPDATE fees SET status='Paid', payment_date=?, paid_amount=amount WHERE id=?", (date.today().isoformat(), fid)); flash("Fee marked as paid.", "success"); return redirect(url_for("fees"))
@app.route("/fees/delete/<int:fid>")
@login_required("admin")
def fees_delete(fid):
    run("DELETE FROM fees WHERE id=?", (fid,)); flash("Fee record deleted.", "success"); return redirect(url_for("fees"))

# ───────────────────────── Hostel ─────────────────────────
@app.route("/hostel", methods=["GET", "POST"])
@login_required("admin", "student")
def hostel():
    if role() == "student":
        s = me_student()
        al = one("SELECT a.*, r.room_number, r.block, r.room_type FROM hostel_allotments a JOIN hostel_rooms r ON r.id=a.room_id WHERE a.student_id=? AND a.status='Active'", (s["student_id"],))
        return render_template("hostel_student.html", title="Hostel", al=al)
    if request.method == "POST":
        f = request.form
        if f.get("add_room"):
            if one("SELECT 1 FROM hostel_rooms WHERE room_number=?", (sanitize(f["room_number"]),)): flash("Room already exists.", "danger")
            else: run("INSERT INTO hostel_rooms(room_number,block,room_type,capacity) VALUES(?,?,?,?)", (sanitize(f["room_number"]), sanitize(f["block"]), f["room_type"], 1 if f["room_type"] == "Single" else 2)); flash("Room added.", "success")
        elif f.get("allot"):
            r = one("SELECT * FROM hostel_rooms WHERE id=?", (int(f["room_id"]),))
            occ = scalar("SELECT COUNT(*) FROM hostel_allotments WHERE room_id=? AND status='Active'", (r["id"],))
            if one("SELECT 1 FROM hostel_allotments WHERE student_id=? AND status='Active'", (f["student_id"],)): flash("This student already has a room.", "danger")
            elif occ >= r["capacity"]: flash("Room is full.", "danger")
            else: run("INSERT INTO hostel_allotments(student_id,room_id,allotment_date) VALUES(?,?,?)", (f["student_id"], r["id"], f["allotment_date"])); flash("Room allotted.", "success")
        return redirect(url_for("hostel"))
    rooms = q("SELECT r.*, (SELECT COUNT(*) FROM hostel_allotments a WHERE a.room_id=r.id AND a.status='Active') occ FROM hostel_rooms r ORDER BY block, room_number")
    allots = q("SELECT a.*, s.name, s.year, r.room_number, r.block FROM hostel_allotments a JOIN students s ON s.student_id=a.student_id JOIN hostel_rooms r ON r.id=a.room_id WHERE a.status='Active' ORDER BY a.allotment_date DESC")
    return render_template("hostel.html", title="BCA Hostel Management", rooms=rooms, allots=allots, studs=q("SELECT student_id,name,year FROM students ORDER BY name"))

@app.route("/hostel/vacate/<int:aid>")
@login_required("admin")
def hostel_vacate(aid):
    run("UPDATE hostel_allotments SET status='Vacated', vacate_date=? WHERE id=?", (date.today().isoformat(), aid)); flash("Room vacated.", "success"); return redirect(url_for("hostel"))

# ───────────────────────── Library ─────────────────────────
@app.route("/library", methods=["GET", "POST"])
@login_required("admin", "student")
def library():
    if request.method == "POST" and role() == "admin":
        f = request.form
        if f.get("add_book"):
            try:
                n = int(f.get("total_copies") or 1)
                run("INSERT INTO books(title,author,isbn,category,total_copies,available_copies,location) VALUES(?,?,?,?,?,?,?)", (sanitize(f["title"]), sanitize(f.get("author")), sanitize(f.get("isbn")) or None, f.get("category"), n, n, sanitize(f.get("location"))))
                flash("Book added.", "success")
            except sqlite3.IntegrityError: flash("A book with this ISBN already exists.", "danger")
        elif f.get("issue"):
            b = one("SELECT * FROM books WHERE id=?", (int(f["book_id"]),))
            if b["available_copies"] < 1: flash("No copies available.", "danger")
            else:
                run("INSERT INTO book_issues(book_id,student_id,issue_date,due_date) VALUES(?,?,?,?)", (b["id"], f["student_id"], date.today().isoformat(), f["due_date"]))
                run("UPDATE books SET available_copies=available_copies-1 WHERE id=?", (b["id"],)); flash("Book issued.", "success")
        return redirect(url_for("library"))
    term = request.args.get("q", "").strip()
    books = q("SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? ORDER BY title", ("%%%s%%" % term,) * 3)
    sid = ref() if role() == "student" else None
    issues = q("""SELECT i.*, b.title, s.name, s.year FROM book_issues i JOIN books b ON b.id=i.book_id JOIN students s ON s.student_id=i.student_id
                  WHERE i.status='Issued' %s ORDER BY i.due_date""" % ("AND i.student_id=?" if sid else ""), (sid,) if sid else ())
    st = dict(total=scalar("SELECT COUNT(*) FROM books"), avail=scalar("SELECT SUM(available_copies) FROM books"), issued=len(issues),
              overdue=sum(1 for i in issues if i["due_date"] < date.today().isoformat()))
    return render_template("library.html", title="BCA Library", books=books, issues=issues, st=st, term=term, studs=q("SELECT student_id,name,year FROM students ORDER BY name") if role() == "admin" else [],
                           due=(date.today() + timedelta(days=14)).isoformat())

@app.route("/library/return/<int:iid>")
@login_required("admin")
def library_return(iid):
    i = one("SELECT * FROM book_issues WHERE id=?", (iid,))
    if i and i["status"] == "Issued":
        late = max(0, (date.today() - datetime.strptime(i["due_date"], "%Y-%m-%d").date()).days)
        run("UPDATE book_issues SET status='Returned', return_date=?, fine=? WHERE id=?", (date.today().isoformat(), late * 2, iid))
        run("UPDATE books SET available_copies=available_copies+1 WHERE id=?", (i["book_id"],)); flash("Book returned%s." % (" — fine ₹%d" % (late * 2) if late else ""), "success")
    return redirect(url_for("library"))

# ───────────────────────── Notices & events ─────────────────────────
@app.route("/notices", methods=["GET", "POST"])
@login_required()
def notices():
    if request.method == "POST" and role() in ("admin", "faculty"):
        f = request.form
        if f.get("post_notice"):
            run("INSERT INTO notices(title,content,category,priority,posted_by,expires_at) VALUES(?,?,?,?,?,?)", (sanitize(f["title"]), sanitize(f["content"]), f.get("category"), f.get("priority"), session["name"], f.get("expires_at") or None)); flash("Notice posted.", "success")
        elif f.get("post_event"):
            run("INSERT INTO events(title,event_date,event_time,venue,category,description,organizer) VALUES(?,?,?,?,?,?,?)", (sanitize(f["title"]), f["event_date"], f.get("event_time"), sanitize(f.get("venue")), f.get("category"), sanitize(f.get("description")), session["name"])); flash("Event added.", "success")
        return redirect(url_for("notices"))
    return render_template("notices.html", title="Notices & Events", rows=q("SELECT * FROM notices ORDER BY created_at DESC, id DESC") if role() != "student" else active_notices(),
                           events=upcoming_events(20), cats=NOTICE_CATEGORIES, ecats=EVENT_CATEGORIES)

@app.route("/notices/delete/<kind>/<int:nid>")
@login_required("admin", "faculty")
def notices_delete(kind, nid):
    run("DELETE FROM %s WHERE id=?" % ("events" if kind == "event" else "notices"), (nid,)); flash("Deleted.", "success"); return redirect(url_for("notices"))

# ───────────────────────── Leave ─────────────────────────
@app.route("/leave", methods=["GET", "POST"])
@login_required("student", "faculty", "admin")
def leave():
    if role() == "student":
        s = me_student()
        if request.method == "POST":
            f = request.form
            if f["to_date"] < f["from_date"]: flash("To-date cannot be before from-date.", "danger")
            else:
                run("INSERT INTO leave_requests(student_id,leave_type,from_date,to_date,reason) VALUES(?,?,?,?,?)", (s["student_id"], f["leave_type"], f["from_date"], f["to_date"], sanitize(f.get("reason")))); flash("Leave application submitted.", "success")
            return redirect(url_for("leave"))
        return render_template("leave_student.html", title="Leave", rows=q("SELECT * FROM leave_requests WHERE student_id=? ORDER BY created_at DESC", (s["student_id"],)))
    rows = q("SELECT l.*, s.name, s.year, s.section FROM leave_requests l JOIN students s ON s.student_id=l.student_id ORDER BY CASE l.status WHEN 'Pending' THEN 0 ELSE 1 END, l.created_at DESC")
    return render_template("leave.html", title="Leave Requests", rows=rows)

@app.route("/leave/<int:lid>/<act>")
@login_required("faculty", "admin")
def leave_act(lid, act):
    if act in ("approve", "reject"):
        run("UPDATE leave_requests SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", ("Approved" if act == "approve" else "Rejected", lid))
        flash("Leave %s." % ("approved!" if act == "approve" else "rejected"), "success")
    return redirect(request.referrer or url_for("leave"))

@app.errorhandler(404)
def nf(e): return render_template("error.html", title="Not found", msg="The page you are looking for does not exist."), 404

init_db()
if __name__ == "__main__":
    app.run(debug=True, port=5000)
