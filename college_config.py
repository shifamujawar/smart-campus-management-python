"""College constants: curriculum, fee structure, college info (from the project documentation)."""
COLLEGE = {
    "name": "Sample College, Demo City", "full": "Sample Mahavidyalaya, Demo City", "code": "000",
    "address": "Demo City, Tal. Sample, Dist. Demo, Maharashtra - 000000",
    "university": "Demo University", "web": "www.example.edu",
    "trust": "Sample Education Trust's", "academic_year": "2025-26",
}
# Semester-wise BCA (CBCS) NEP 2020 curriculum. Sem 5/6 come from the documentation screenshots;
# Sem 1-4 are filled from the subject table in the documentation (edit freely).
CURRICULUM = {
    1: {1: [("Introduction to Programming Using C", "Prof. Pawar S.K."), ("Fundamentals of Computer", "Prof. Kulkarni M.A."),
            ("Mathematics for Computing", "Prof. Kulkarni M.A."), ("English Communication", "Prof. Kulkarni M.A."), ("Skill Development I", "Prof. Kulkarni M.A.")],
        2: [("DBMS", "Prof. Pawar S.K."), ("Web Technology I", "Prof. Deshmukh A.R."), ("Operating System", "Prof. Deshmukh A.R."),
            ("Environmental Studies", "Prof. Kulkarni M.A."), ("Skill Development II", "Prof. Kulkarni M.A.")]},
    2: {3: [("RDBMS", "Prof. Pawar S.K."), ("Data Structure using C", "Prof. Pawar S.K."), ("Computer Organization", "Prof. Deshmukh A.R."),
            ("Web Technology II", "Prof. Deshmukh A.R."), ("Skill Development III", "Prof. Kulkarni M.A.")],
        4: [("PHP Programming", "Prof. Deshmukh A.R."), ("Object Oriented Programming C++", "Prof. Pawar S.K."), ("Software Engineering", "Prof. Deshmukh A.R."),
            ("Entrepreneurship Development", "Prof. Kulkarni M.A."), ("Computer Networks", "Prof. Deshmukh A.R.")]},
    3: {5: [("Java Programming", "Prof. Deshmukh A.R."), ("Linux", "Prof. Deshmukh A.R."), (".NET Technology", "Prof. Pawar S.K."),
            ("Management Information System", "Prof. Kulkarni M.A."), ("Skill Development IV", "Prof. Kulkarni M.A.")],
        6: [("Python", "Prof. Deshmukh A.R."), ("R Programming", "Prof. Deshmukh A.R."), ("IT Security", "Prof. Pawar S.K."),
            ("Knowledge Management", "Prof. Kulkarni M.A."), ("Soft Skills & Personality Development", "Prof. Kulkarni M.A.")]},
}
CURRENT_SEM = {1: 2, 2: 4, 3: 6}   # Term II (even semesters) running
def current_subjects(year):
    return [s for s, _ in CURRICULUM[year][CURRENT_SEM[year]]]
def all_subjects():
    return sorted({s for y in CURRICULUM.values() for sem in y.values() for s, _ in sem})

FEE_STRUCTURE = [("Tuition Fee", 16500), ("Admission Fee", 10), ("Ashwamegh Fee", 36), ("Development Fund", 200),
    ("Emergency Fund", 10), ("E-Shulak", 49), ("Flag Fund", 10), ("Gymkhana Fee", 150), ("Lead College", 25),
    ("Library Fee", 500), ("Magazine Fee", 100), ("NSS Fee", 10), ("Pro-rata", 50), ("Student Insurance", 100),
    ("Students Aid Fund", 25), ("Yuvak Mohastav Fee", 80)]
FEE_TOTAL = sum(a for _, a in FEE_STRUCTURE)   # 17855
FEE_AMOUNTS = dict(FEE_STRUCTURE)
SECTIONS = ["A", "B"]
NOTICE_CATEGORIES = ["General", "Academic", "Exam", "Sports", "Cultural", "Holiday"]
EVENT_CATEGORIES = ["Cultural", "Sports", "Academic", "Technical"]
DESIGNATIONS = ["Professor", "HOD - BCA", "Lecturer", "Assistant Professor"]
