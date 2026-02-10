from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import (
    add_teacher, remove_teacher, add_student, remove_student, 
    change_teacher_password, get_class_report,
    add_subject, remove_subject, get_all_subjects,
    allocate_subject, get_all_allocations, remove_allocation
)
from utils import generate_csv_report, generate_pdf_report, generate_excel_report
from db import get_db_connection

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_type" not in session or session["user_type"] != "admin":
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route("/")
@login_required
def admin_dashboard():
    return render_template("admin_dashboard.html")

@admin_bp.route("/add_teacher", methods=["GET","POST"])
@login_required
def admin_add_teacher():
    if request.method=="POST":
        username = request.form["username"]
        password = request.form["password"]
        if add_teacher(username,password):
            flash(f"Teacher '{username}' added successfully!", "success")
        else:
            flash(f"Teacher '{username}' already exists!", "danger")
    return render_template("add_teacher.html")

@admin_bp.route("/remove_teacher", methods=["GET","POST"])
@login_required
def admin_remove_teacher():
    conn = get_db_connection()
    cur = conn.cursor()
    search = request.args.get("search", "").strip()
    
    query = "SELECT username FROM teachers WHERE username!='admin'"
    params = []

    if search:
        query += " AND username LIKE ?"
        params.append(f"%{search}%")
    
    query += " ORDER BY username"
    cur.execute(query, tuple(params))
    teachers = cur.fetchall()
    conn.close()

    if request.method=="POST":
        username = request.form["username"]
        if remove_teacher(username):
            flash(f"Teacher '{username}' removed successfully!", "success")
        else:
            flash(f"Failed to remove teacher '{username}'!", "danger")
        return redirect(url_for("admin.admin_remove_teacher"))

    return render_template("remove_teacher.html", teachers=teachers, search=search)

@admin_bp.route("/add_student", methods=["GET","POST"])
@login_required
def admin_add_student():
    if request.method == "POST":
        mis_no = request.form["mis_no"]
        name = request.form["name"]
        year = request.form["year"]
        semester = request.form["semester"]
        section = request.form["section"]
        password = request.form["password"]

        if add_student(mis_no, name, year, semester, section, password):
            flash(f"Student {mis_no} added successfully!", "success")
        else:
            flash(f"Student {mis_no} already exists!", "danger")
    return render_template("add_student.html")

# --- UPDATED FUNCTION: REMOVE STUDENT ---
@admin_bp.route("/remove_student", methods=["GET", "POST"])
@login_required
def admin_remove_student():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Get Filters
    year = request.args.get("year")
    semester = request.args.get("semester") # Added Semester
    section = request.args.get("section")
    search = request.args.get("search", "").strip()

    # 2. Get distinct years for dropdown
    cur.execute("SELECT DISTINCT year FROM students")
    years = [row["year"] for row in cur.fetchall()]

    sections = []
    if year:
        cur.execute("SELECT DISTINCT section FROM students WHERE year=?", (year,))
        sections = [row["section"] for row in cur.fetchall()]

    students = []
    
    # 3. Flexible Filtering Logic
    # Run query if ANY filter is provided (Year, Sem, Section OR Search)
    if year or semester or section or search:
        query = "SELECT mis_no, name, year, semester, section FROM students WHERE 1=1"
        params = []

        if year:
            query += " AND year=?"
            params.append(year)
        if semester:
            query += " AND semester=?"
            params.append(semester)
        if section:
            query += " AND section=?"
            params.append(section)
        if search:
            query += " AND (mis_no LIKE ? OR name LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        cur.execute(query, tuple(params))
        students = cur.fetchall()

    conn.close()

    # 4. Handle Removal (POST)
    if request.method == "POST":
        mis_no = request.form["mis_no"]
        if remove_student(mis_no):
            flash(f"Student '{mis_no}' removed successfully!", "success")
        else:
            flash(f"Failed to remove student '{mis_no}'!", "danger")
        return redirect(url_for("admin.admin_remove_student", year=year, semester=semester, section=section, search=search))

    return render_template(
        "remove_student.html", 
        years=years, sections=sections, students=students, 
        selected_year=year, selected_semester=semester, selected_section=section, search=search
    )
# ----------------------------------------

@admin_bp.route("/update_student", methods=["GET", "POST"])
@login_required
def admin_update_student():
    conn = get_db_connection()
    cur = conn.cursor()

    year = request.args.get("year")
    semester = request.args.get("semester")
    section = request.args.get("section")
    search = request.args.get("search", "").strip()

    cur.execute("SELECT DISTINCT year FROM students")
    years = [row["year"] for row in cur.fetchall()]
    sections = []
    if year:
        cur.execute("SELECT DISTINCT section FROM students WHERE year=?", (year,))
        sections = [row["section"] for row in cur.fetchall()]

    query = "SELECT mis_no, name, year, semester, section FROM students WHERE 1=1"
    params = []
    if year: query += " AND year=?" ; params.append(year)
    if semester: query += " AND semester=?" ; params.append(semester)
    if section: query += " AND section=?" ; params.append(section)
    if search:
        query += " AND (mis_no LIKE ? OR name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    cur.execute(query, tuple(params))
    students = cur.fetchall()
    
    if request.method == "POST":
        mis_no = request.form["mis_no"]
        name = request.form["name"]
        year_new = request.form["year"]
        semester_new = request.form["semester"]
        section_new = request.form["section"]
        password = request.form.get("password")

        conn_post = get_db_connection()
        cur_post = conn_post.cursor()
        if password:
            from werkzeug.security import generate_password_hash
            cur_post.execute(
                "UPDATE students SET name=?, year=?, semester=?, section=?, password=? WHERE mis_no=?",
                (name, year_new, semester_new, section_new, generate_password_hash(password), mis_no),
            )
        else:
            cur_post.execute(
                "UPDATE students SET name=?, year=?, semester=?, section=? WHERE mis_no=?",
                (name, year_new, semester_new, section_new, mis_no),
            )
        conn_post.commit()
        conn_post.close()
        
        flash(f"Student '{mis_no}' updated successfully!", "success")
        return redirect(
            url_for("admin.admin_update_student", year=year, semester=semester, section=section, search=search)
        )

    conn.close()
    return render_template(
        "update_student.html",
        years=years, sections=sections, students=students,
        selected_year=year, selected_semester=semester, selected_section=section, search=search,
    )

@admin_bp.route("/manage_subjects", methods=["GET", "POST"])
@login_required
def admin_manage_subjects():
    if request.method == "POST":
        subject_code = request.form["subject_code"]
        subject_name = request.form["subject_name"]
        if add_subject(subject_code, subject_name):
            flash(f"Subject '{subject_name}' added successfully!", "success")
        else:
            flash(f"Subject code '{subject_code}' already exists!", "danger")
        return redirect(url_for("admin.admin_manage_subjects"))
    
    subjects = get_all_subjects()
    return render_template("manage_subjects.html", subjects=subjects)

@admin_bp.route("/remove_subject/<int:subject_id>", methods=["POST"])
@login_required
def admin_remove_subject(subject_id):
    if remove_subject(subject_id):
        flash("Subject and related data removed successfully!", "success")
    else:
        flash("Failed to remove subject!", "danger")
    return redirect(url_for("admin.admin_manage_subjects"))

@admin_bp.route("/allocate_subjects", methods=["GET", "POST"])
@login_required
def admin_allocate_subjects():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM teachers WHERE username!='admin'")
    teachers = cur.fetchall()
    cur.execute("SELECT subject_id, subject_name, subject_code FROM subjects")
    subjects = cur.fetchall()
    cur.execute("SELECT DISTINCT year FROM students")
    years = [row['year'] for row in cur.fetchall()]
    cur.execute("SELECT DISTINCT section FROM students")
    sections = [row['section'] for row in cur.fetchall()]
    conn.close()

    if request.method == "POST":
        teacher_username = request.form["teacher_username"]
        subject_id = request.form["subject_id"]
        year = request.form["year"]
        semester = request.form["semester"]
        section = request.form["section"]
        
        if allocate_subject(teacher_username, subject_id, year, semester, section):
            flash("Subject allocated successfully!", "success")
        else:
            flash("Failed to allocate subject. Maybe a duplicate?", "danger")
        return redirect(url_for("admin.admin_allocate_subjects"))

    allocations = get_all_allocations()
    return render_template("allocate_subjects.html", 
                           teachers=teachers, subjects=subjects,
                           years=years, sections=sections,
                           allocations=allocations)

@admin_bp.route("/remove_allocation/<int:alloc_id>", methods=["POST"])
@login_required
def admin_remove_allocation(alloc_id):
    if remove_allocation(alloc_id):
        flash("Allocation removed successfully!", "success")
    else:
        flash("Failed to remove allocation!", "danger")
    return redirect(url_for("admin.admin_allocate_subjects"))

@admin_bp.route("/view_reports", methods=["GET","POST"])
@login_required
def admin_view_reports():
    reports = []
    year, section, subject_id = None, None, None
    total_classes = 0
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT year FROM students")
    years = [row['year'] for row in cur.fetchall()]
    cur.execute("SELECT DISTINCT section FROM students")
    sections = [row['section'] for row in cur.fetchall()]
    cur.execute("SELECT subject_id, subject_name, subject_code FROM subjects")
    all_subjects = cur.fetchall()
    conn.close()

    if request.method == "POST":
        year = request.form["year"]
        section = request.form["section"]
        subject_id = request.form["subject_id"]
        semester = request.form.get("semester", "1")

        if year and section and subject_id:
             reports, total_classes = get_class_report(year, semester, section, subject_id)
             if not reports and total_classes == 0:
                flash(f"No attendance records found.", "info")
             elif not reports:
                 flash(f"No students found.", "warning")

    return render_template(
        "admin_view_reports.html", 
        reports=reports, year=year, section=section, subject_id=subject_id,
        years=years, sections=sections, all_subjects=all_subjects, total_classes=total_classes
    )

@admin_bp.route("/download_all_reports/<file_type>", methods=["POST"])
@login_required
def download_all_reports(file_type):
    year = request.form.get("year")
    section = request.form.get("section")
    subject_id = request.form.get("subject_id")
    semester = request.form.get("semester", "1")
    
    if not all([year, section, subject_id]):
        flash("Year, Section, and Subject are required for download.", "danger")
        return redirect(url_for("admin.admin_view_reports"))

    reports, total_classes = get_class_report(year, semester, section, subject_id)
    data = [(mis_no, name, attended, total, percent) for mis_no, name, attended, total, percent in reports]
    columns = ["MIS Number", "Name", "Classes Attended", "Total Classes", "Attendance %"]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT subject_code FROM subjects WHERE subject_id=?", (subject_id,))
    row = cur.fetchone()
    subject_code = row['subject_code'] if row else "SUB"
    conn.close()
    
    filename = f"{year}_Sem{semester}_{section}_{subject_code}_attendance.{file_type}"

    if file_type == "csv":
        return generate_csv_report(data, columns, filename)
    elif file_type == "pdf":
        return generate_pdf_report(data, columns, filename, chart_title=f"{year} {section} - {subject_code}")
    elif file_type == "xlsx":
        return generate_excel_report(data, columns, filename)
    else:
        return "Invalid file type", 400

@admin_bp.route("/change_password", methods=["GET","POST"])
@login_required
def admin_change_password():
    if request.method=="POST":
        new_password = request.form["new_password"]
        username = session["username"]
        change_teacher_password(username, new_password)
        flash("Password changed successfully", "success")
        return redirect(url_for("admin.admin_dashboard"))
    return render_template("change_password.html", username=session["username"])