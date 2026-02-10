import sqlite3
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

# --- TEACHERS ---
def add_teacher(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO teachers (username, password) VALUES (?, ?)", 
                    (username, generate_password_hash(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False 
    finally:
        conn.close()

def remove_teacher(username):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM teachers WHERE username=?", (username,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def verify_teacher(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password FROM teachers WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    if user:
        return check_password_hash(user["password"], password)
    return False

def change_teacher_password(username, new_password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE teachers SET password=? WHERE username=?", 
                (generate_password_hash(new_password), username))
    conn.commit()
    conn.close()

def get_teacher_name(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM teachers WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row["username"] if row else "Teacher"

# --- STUDENTS (With Semester) ---
def add_student(mis_no, name, year, semester, section, password):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO students (mis_no, name, password, year, semester, section) VALUES (?, ?, ?, ?, ?, ?)",
            (mis_no, name, generate_password_hash(password), year, semester, section)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False 
    finally:
        conn.close()

def remove_student(mis_no):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM attendance WHERE mis_no=?", (mis_no,))
        cur.execute("DELETE FROM students WHERE mis_no=?", (mis_no,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def verify_student(mis_no, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password FROM students WHERE mis_no=?", (mis_no,))
    user = cur.fetchone()
    conn.close()
    if user:
        return check_password_hash(user["password"], password)
    return False

def change_student_password(mis_no, new_password):
    conn = get_db_connection()
    cur = conn.cursor()
    hashed_password = generate_password_hash(new_password)
    cur.execute("UPDATE students SET password=? WHERE mis_no=?", (hashed_password, mis_no))
    conn.commit()
    conn.close()

# --- SUBJECTS ---
def add_subject(subject_code, subject_name):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO subjects (subject_code, subject_name) VALUES (?, ?)", 
                    (subject_code, subject_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False 
    finally:
        conn.close()

def remove_subject(subject_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM teacher_allocations WHERE subject_id=?", (subject_id,))
        cur.execute("DELETE FROM attendance WHERE subject_id=?", (subject_id,))
        cur.execute("DELETE FROM subjects WHERE subject_id=?", (subject_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_all_subjects():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subjects ORDER BY subject_name")
    subjects = cur.fetchall()
    conn.close()
    return subjects

# --- ALLOCATIONS (With Semester) ---
def allocate_subject(teacher_username, subject_id, year, semester, section):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO teacher_allocations (teacher_username, subject_id, year, semester, section) VALUES (?, ?, ?, ?, ?)",
                    (teacher_username, subject_id, year, semester, section))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_allocations():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ta.alloc_id, t.username, s.subject_code, s.subject_name, ta.year, ta.semester, ta.section
        FROM teacher_allocations ta
        JOIN teachers t ON ta.teacher_username = t.username
        JOIN subjects s ON ta.subject_id = s.subject_id
        ORDER BY t.username, ta.year, ta.semester, ta.section, s.subject_name
    """)
    allocations = cur.fetchall()
    conn.close()
    return allocations

def remove_allocation(alloc_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM teacher_allocations WHERE alloc_id=?", (alloc_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_teacher_subjects(teacher_username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ta.alloc_id, s.subject_id, s.subject_code, s.subject_name, ta.year, ta.semester, ta.section
        FROM teacher_allocations ta
        JOIN subjects s ON ta.subject_id = s.subject_id
        WHERE ta.teacher_username = ?
        ORDER BY ta.year, ta.semester, ta.section, s.subject_name
    """, (teacher_username,))
    subjects = cur.fetchall()
    conn.close()
    return subjects

# --- ATTENDANCE (With Semester) ---
def get_students_for_class(year, semester, section):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT mis_no, name FROM students WHERE year=? AND semester=? AND section=? ORDER BY name", 
                (year, semester, section))
    students = cur.fetchall()
    conn.close()
    return students

def get_existing_attendance(subject_id, date):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT mis_no, status FROM attendance WHERE subject_id=? AND date=?", (subject_id, date))
    records = {row['mis_no']: row['status'] for row in cur.fetchall()}
    conn.close()
    return records

def save_bulk_attendance(subject_id, date, attendance_data, teacher_username):
    conn = get_db_connection()
    cur = conn.cursor()
    insert_data = []
    for mis_no, status in attendance_data.items():
        insert_data.append((mis_no, date, subject_id, status, teacher_username))

    try:
        cur.executemany("""
            INSERT INTO attendance (mis_no, date, subject_id, status, marked_by_teacher)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(mis_no, date, subject_id) DO UPDATE SET
                status = excluded.status,
                marked_by_teacher = excluded.marked_by_teacher
        """, insert_data)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error in save_bulk_attendance: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- REPORTS (With Semester) ---
def get_class_report(year, semester, section, subject_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(DISTINCT date) FROM attendance WHERE subject_id=?", (subject_id,))
    total_classes_row = cur.fetchone()
    total_classes = total_classes_row[0] if total_classes_row else 0

    if total_classes == 0:
        conn.close()
        return [], 0  

    cur.execute("""
        SELECT s.mis_no, s.name,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) as attended
        FROM students s
        LEFT JOIN attendance a ON s.mis_no = a.mis_no AND a.subject_id = ?
        WHERE s.year=? AND s.semester=? AND s.section=?
        GROUP BY s.mis_no, s.name
        ORDER BY s.name
    """, (subject_id, year, semester, section))

    results = []
    for mis_no, name, attended in cur.fetchall():
        attended = attended or 0
        percent = round((attended / total_classes) * 100, 2) if total_classes > 0 else 0
        results.append((mis_no, name, attended, total_classes, percent))

    conn.close()
    return results, total_classes

def fetch_student_attendance_summary(mis_no):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT name FROM students WHERE mis_no=?", (mis_no,))
    name_row = cur.fetchone()
    name = name_row["name"] if name_row else "Student"

    # Updated to verify semester alignment
    cur.execute("""
        SELECT a.subject_id, s.subject_name, s.subject_code, COUNT(DISTINCT a.date) as total_classes
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.subject_id
        JOIN students st ON a.mis_no = st.mis_no
        WHERE st.year = (SELECT year FROM students WHERE mis_no = ?)
          AND st.semester = (SELECT semester FROM students WHERE mis_no = ?)
          AND st.section = (SELECT section FROM students WHERE mis_no = ?)
        GROUP BY a.subject_id, s.subject_name, s.subject_code
    """, (mis_no, mis_no, mis_no))
    total_classes_map = {row['subject_id']: row for row in cur.fetchall()}

    cur.execute("""
        SELECT subject_id, COUNT(*) as present_count
        FROM attendance
        WHERE mis_no = ? AND status = 'Present'
        GROUP BY subject_id
    """, (mis_no,))
    present_classes_map = {row['subject_id']: row['present_count'] for row in cur.fetchall()}

    summary = []
    for subject_id, subject_data in total_classes_map.items():
        present = present_classes_map.get(subject_id, 0)
        total = subject_data['total_classes']
        percent = round((present / total) * 100, 2) if total > 0 else 0
        summary.append({
            'subject_code': subject_data['subject_code'],
            'subject_name': subject_data['subject_name'],
            'present': present,
            'total': total,
            'percent': percent
        })

    conn.close()
    return name, summary

def get_student_detailed_report(mis_no):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.date, s.subject_name, a.status
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.subject_id
        WHERE a.mis_no = ?
        ORDER BY a.date DESC, s.subject_name
    """, (mis_no,))
    records = cur.fetchall()
    conn.close()
    return records