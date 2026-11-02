"""Creates the database and inserts demo data (admin/faculty/student logins, students, fees, notices ...)."""
import sqlite3, os
from datetime import date, timedelta
from werkzeug.security import generate_password_hash as H
from college_config import *

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "smart_campus.db")

def init_db(force=False):
    if force and os.path.exists(DB): os.remove(DB)
    new = not os.path.exists(DB)
    con = sqlite3.connect(DB)
    con.executescript(open(os.path.join(BASE, "schema.sql"), encoding="utf-8").read())
    if new: seed(con)
    con.commit(); con.close()

def seed(c):
    today = date.today(); d = lambda n: (today + timedelta(days=n)).isoformat()
    c.executemany("INSERT INTO faculty(faculty_id,name,email,phone,designation,qualification,subjects) VALUES(?,?,?,?,?,?,?)", [
        ("FAC1", "Prof. Anil R. Deshmukh", "deshmukh@example.com", "9000000001", "HOD - BCA", "MCA, M.phil.", "Computer Architecture, Software Engineering, OOP Using Java, Computer Networks, Python, Programming, Linux, R Programming"),
        ("FAC2", "Prof. Suresh K. Pawar", "pawar@example.com", "9000000002", "Professor", "MCA", "Problem Solving Techniques, DBMS, Operating System, RDBMS, AI, Dot NET Technology, IT Security"),
        ("FAC3", "Prof. Meera A. Kulkarni", "kulkarni@example.com", "9000000003", "Professor", "MBA", "Two Indian Vision For Human Society, NSS, Indian Constitution, Skill Development, Management Information System, Knowledge Management, Soft skill and pe")])
    studs = [("STUD0001","Aarav Patil",1),("STUD0002","Diya Kulkarni",1),("STUD0003","Ishaan Joshi",1),("STUD0004","Kavya Desai",1),("STUD0005","Rohan More",1),
             ("STUD02","Ananya Shinde",2),("STUD03","Vivaan Gaikwad",2),("STUD04","Sneha Pawar",2),("STUD05","Omkar Jagtap",2),("STUD06","Neha Kadam",2),
             ("STUD01","Riya Sharma",3),("STUD07","Aditi Mehta",3),("STUD08","Karan Verma",3),("STUD09","Neha Joshi",3),("STUD10","Arjun Rao",3)]
    for i,(sid,name,yr) in enumerate(studs):
        em = name.split()[0].lower() + str(12+i) + "@example.com"
        c.execute("INSERT INTO students(student_id,name,email,phone,year,section,gender,dob,address) VALUES(?,?,?,?,?,?,?,?,?)",
                  (sid, name, em, "9%09d" % (500000000+i*7919), yr, "A", "Male" if name.split()[0] in ("Aarav","Ishaan","Rohan","Vivaan","Omkar","Karan","Arjun") else "Female", "2005-0%d-1%d" % (i%9+1, i%9), "Demo City"))
    users = [("admin","admin123","admin","Administrator","admin@example.com",None),("faculty","faculty123","faculty","Prof. Anil R. Deshmukh","deshmukh@example.com","FAC1"),
             ("student","student123","student","Riya Sharma","riya@example.com","STUD01")]
    for u,p,r,n,e,ref in users:
        c.execute("INSERT INTO users(username,password,role,name,email,ref_id) VALUES(?,?,?,?,?,?)",(u,H(p),r,n,e,ref))
    # fees (Year-wise development fund pending for demo)
    c.execute("INSERT INTO fees(student_id,fee_type,amount,due_date,status) VALUES('STUD01','Development Fund',200,?, 'Pending')",(d(10),))
    c.execute("INSERT INTO fees(student_id,fee_type,amount,paid_amount,due_date,payment_date,status) VALUES('STUD01','Tuition Fee',16500,16500,?,?,'Paid')",(d(-60),d(-70)))
    # attendance sample
    for k in range(6):
        for sid in ("STUD01","STUD07","STUD08"):
            for subj in ("Python","R Programming"):
                st = "Absent" if (k==2 and sid=="STUD07") else "Present"
                c.execute("INSERT INTO attendance(student_id,subject,status,date,year,section,marked_by) VALUES(?,?,?,?,?,?,?)",(sid,subj,st,d(-k-1),3,"A","faculty"))
    # notices
    for t,ct,cat,pr,ex in [("Internal Exam Schedule - Semester VI","Internal examinations for BCA Semester VI will be held soon. Students are advised to prepare accordingly. Timetable will be displayed on notice board.","Exam","High",None),
        ("Assignment Submission Deadline","All pending assignments must be submitted before the deadline. No late submissions will be accepted after the deadline.","Academic","High",None),
        ("College Annual Function 2026","The Annual Cultural Function of Sample College, Demo City will be held soon. All students are requested to participate.","Cultural","Medium",None),
        ("Library Timing Update","Library will remain open from 9 AM to 5 PM on all working days.","General","Low",None),
        ("NSS Camp Registration","Interested students may register for the NSS winter camp with the NSS coordinator.","Sports","Medium",None),
        ("Holiday on Ambedkar Jayanti","College will remain closed on account of Ambedkar Jayanti.","Holiday","Low",None)]:
        c.execute("INSERT INTO notices(title,content,category,priority,posted_by,expires_at) VALUES(?,?,?,?,?,?)",(t,ct,cat,pr,"Administrator",ex))
    for t,n,tm,v,cat in [("Guest Lecture - AI & ML",6,"11:00","Auditorium","Academic"),("Annual Sports Day",11,"09:00","Sports Ground","Sports"),
                        ("Tech Fest - Code Sprint",18,"10:00","Computer Lab","Technical"),("Annual Cultural Function",25,"16:00","Main Hall","Cultural")]:
        c.execute("INSERT INTO events(title,event_date,event_time,venue,category,description,organizer) VALUES(?,?,?,?,?,?,?)",(t,d(n),tm,v,cat,t+" at Sample College, Demo City","BCA Department"))
    # exam schedule + result
    c.execute("INSERT INTO exam_schedule(subject,year,section,exam_date,start_time,end_time,hall,faculty_id,exam_type,max_marks) VALUES('Python',3,'A',?,'11:00','12:00','L-101','FAC1','Internal',20)",(d(4),))
    c.execute("INSERT INTO exam_results(student_id,subject,year,exam_type,marks_obtained,max_marks,grade,remarks,faculty_id,exam_date) VALUES('STUD01','R Programming',3,'Internal',18,20,'A','Good work! Answers are clear and well-explained.','FAC1',?)",(d(-3),))
    # assignment
    c.execute("INSERT INTO assignments(title,description,subject,year,section,faculty_id,due_date,max_marks,priority) VALUES('Python Unit 1 Assignment','Write programs on lists, tuples, dictionaries and functions.','Python',3,'','FAC1',?,10,'High')",(d(7),))
    # timetable (Mon-Sat for each year)
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    slots = [("08:00","09:00"),("09:00","10:00"),("10:15","11:15")]
    for yr in (1,2,3):
        subs = CURRICULUM[yr][CURRENT_SEM[yr]]
        for di,day in enumerate(days):
            for si,(a,b) in enumerate(slots):
                s,pf = subs[(di+si) % len(subs)]
                c.execute("INSERT INTO timetable(year,section,day_of_week,start_time,end_time,subject,faculty_id,room) VALUES(?,?,?,?,?,?,?,?)",(yr,"A",day,a,b,s,{"Prof. Deshmukh A.R.":"FAC1","Prof. Pawar S.K.":"FAC2"}.get(pf,"FAC3"),"L-%d" % (101+yr*100+si)))
    # hostel rooms
    for blk,pre,n in (("Boys Block A","B",8),("Girls Block A","G",8)):
        for i in range(1,n+1):
            c.execute("INSERT INTO hostel_rooms(room_number,block,room_type,capacity) VALUES(?,?,?,?)",("%s%d" % (pre,100+i),blk,"Double" if i%2 else "Single",2 if i%2 else 1))
    # library
    for t,a,i,p,y,cat,loc,n in [("Introduction to Python Programming","R. Nageswara Rao","978-9386551016","Dreamtech",2018,"Computer Science","BCA Section - Shelf 1",5),
        ("Let Us C","Yashavant Kanetkar","978-8183331630","BPB",2020,"Computer Science","BCA Section - Shelf 1",5),
        ("Database System Concepts","Silberschatz","978-0078022159","McGraw Hill",2019,"Computer Science","BCA Section - Shelf 2",3),
        ("PHP and MySQL Web Development","Luke Welling","978-0321833891","Addison-Wesley",2016,"Web Technology","BCA Section - Shelf 3",3),
        ("Operating System Concepts","Galvin","978-1118063330","Wiley",2018,"Computer Science","BCA Section - Shelf 2",4)]:
        c.execute("INSERT INTO books(title,author,isbn,publisher,pub_year,total_copies,available_copies,category,location) VALUES(?,?,?,?,?,?,?,?,?)",(t,a,i,p,y,n,n,cat,loc))
    c.execute("INSERT INTO study_materials(title,subject,year,faculty_id,file_path,file_type,file_size,description) VALUES('Python Unit 1','Python',3,'FAC1','','PDF','1014 KB','Unit 1 notes')")

if __name__ == "__main__":
    init_db(force=True); print("Database created:", DB)
