import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "attendance_system.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # 1. Students Table (Added semester)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS students (
        mis_no TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        year TEXT NOT NULL,
        semester TEXT NOT NULL,
        section TEXT NOT NULL
    )''')

    # 2. Teachers Table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS teachers (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )''')

    # 3. Subjects Table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_code TEXT UNIQUE NOT NULL,
        subject_name TEXT NOT NULL
    )''')

    # 4. Teacher Allocations Table (Added semester)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS teacher_allocations (
        alloc_id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_username TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        year TEXT NOT NULL,
        semester TEXT NOT NULL,
        section TEXT NOT NULL,
        FOREIGN KEY(teacher_username) REFERENCES teachers(username),
        FOREIGN KEY(subject_id) REFERENCES subjects(subject_id)
    )''')

    # 5. Attendance Table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mis_no TEXT NOT NULL,
        date TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        marked_by_teacher TEXT, 
        FOREIGN KEY(mis_no) REFERENCES students(mis_no),
        FOREIGN KEY(subject_id) REFERENCES subjects(subject_id),
        UNIQUE(mis_no, date, subject_id)
    )''')

    # Create Default Admin
    cur.execute("SELECT * FROM teachers WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO teachers (username, password) VALUES (?, ?)",
                    ("admin", generate_password_hash("admin123")))

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn