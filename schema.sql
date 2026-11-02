-- Smart Campus (BCA) - SQLite schema, same tables/columns as the project documentation
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS students (
  student_id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT,
  course TEXT DEFAULT 'BCA', year INTEGER NOT NULL, section TEXT, gender TEXT, dob DATE, address TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('admin','faculty','student')), name TEXT, email TEXT, ref_id TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS faculty (
  faculty_id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE, phone TEXT, department TEXT DEFAULT 'BCA',
  designation TEXT, qualification TEXT, subjects TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS attendance (
  id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT REFERENCES students(student_id) ON DELETE CASCADE,
  subject TEXT NOT NULL, status TEXT CHECK(status IN ('Present','Absent','Late')), date DATE NOT NULL,
  year INTEGER, section TEXT, marked_by TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, subject TEXT NOT NULL,
  course TEXT DEFAULT 'BCA', year INTEGER NOT NULL, section TEXT, faculty_id TEXT REFERENCES faculty(faculty_id),
  due_date DATE NOT NULL, max_marks INTEGER DEFAULT 10, priority TEXT DEFAULT 'Medium',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS assignment_submissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, assignment_id INTEGER REFERENCES assignments(id) ON DELETE CASCADE,
  student_id TEXT REFERENCES students(student_id) ON DELETE CASCADE, submission_text TEXT,
  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, marks INTEGER, marks_obtained REAL, remarks TEXT,
  status TEXT DEFAULT 'Submitted' CHECK(status IN ('Submitted','Graded','Late')),
  UNIQUE(assignment_id, student_id));

CREATE TABLE IF NOT EXISTS fees (
  id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT REFERENCES students(student_id) ON DELETE CASCADE,
  fee_type TEXT NOT NULL, amount REAL NOT NULL, paid_amount REAL DEFAULT 0, due_date DATE, payment_date DATE,
  status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending','Paid','Partial','Overdue')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS study_materials (
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, subject TEXT NOT NULL, year INTEGER NOT NULL,
  section TEXT, faculty_id TEXT REFERENCES faculty(faculty_id), file_path TEXT, file_type TEXT DEFAULT 'PDF',
  file_size TEXT, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS exam_schedule (
  id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL, year INTEGER NOT NULL, section TEXT,
  exam_date DATE NOT NULL, start_time TIME DEFAULT '10:00', end_time TIME DEFAULT '13:00', hall TEXT DEFAULT 'L-101',
  faculty_id TEXT REFERENCES faculty(faculty_id),
  exam_type TEXT DEFAULT 'Internal' CHECK(exam_type IN ('Internal','External','Practical','Viva')),
  max_marks INTEGER DEFAULT 20, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS exam_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT REFERENCES students(student_id) ON DELETE CASCADE,
  subject TEXT NOT NULL, year INTEGER NOT NULL, exam_type TEXT, marks_obtained REAL DEFAULT 0, max_marks INTEGER DEFAULT 20,
  grade TEXT, remarks TEXT, faculty_id TEXT REFERENCES faculty(faculty_id), exam_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(student_id, subject, exam_type));

CREATE TABLE IF NOT EXISTS notices (
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT NOT NULL, category TEXT DEFAULT 'General',
  priority TEXT DEFAULT 'Medium' CHECK(priority IN ('High','Medium','Low')), posted_by TEXT, expires_at DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

-- Added by me (in ERD, missing from documentation SQL): hostel + library issue tables
CREATE TABLE IF NOT EXISTS hostel_rooms (
  id INTEGER PRIMARY KEY AUTOINCREMENT, room_number TEXT UNIQUE NOT NULL, block TEXT, room_type TEXT DEFAULT 'Double',
  capacity INTEGER DEFAULT 2, occupied INTEGER DEFAULT 0, status TEXT DEFAULT 'Available');

CREATE TABLE IF NOT EXISTS hostel_allotments (
  id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT REFERENCES students(student_id) ON DELETE CASCADE,
  room_id INTEGER REFERENCES hostel_rooms(id), allotment_date DATE, vacate_date DATE, status TEXT DEFAULT 'Active');

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, event_date DATE NOT NULL, event_time TIME, venue TEXT,
  category TEXT, description TEXT, organizer TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS leave_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT REFERENCES students(student_id) ON DELETE CASCADE,
  leave_type TEXT CHECK(leave_type IN ('Medical','Personal','Family','Other')), from_date DATE NOT NULL, to_date DATE NOT NULL,
  reason TEXT, status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending','Approved','Rejected')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS timetable (
  id INTEGER PRIMARY KEY AUTOINCREMENT, year INTEGER NOT NULL, section TEXT DEFAULT 'A',
  day_of_week TEXT NOT NULL, start_time TIME NOT NULL, end_time TIME NOT NULL, subject TEXT NOT NULL,
  faculty_id TEXT, room TEXT DEFAULT 'L-101', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS books (
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author TEXT, isbn TEXT UNIQUE, publisher TEXT, pub_year INTEGER,
  total_copies INTEGER DEFAULT 1, available_copies INTEGER DEFAULT 1, category TEXT, location TEXT);

CREATE TABLE IF NOT EXISTS book_issues (
  id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER REFERENCES books(id), student_id TEXT REFERENCES students(student_id),
  issue_date DATE, due_date DATE, return_date DATE, fine REAL DEFAULT 0, status TEXT DEFAULT 'Issued');
