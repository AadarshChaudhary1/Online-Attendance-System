from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import (
    get_class_report, change_teacher_password, get_teacher_subjects,
    get_students_for_class, get_existing_attendance, save_bulk_attendance
)
from db import get_db_connection
from utils import generate_csv_report, generate_pdf_report, generate_excel_report
import datetime

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_type" not in session or session["user_type"] != "teacher":
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@teacher_bp.route("/")
@login_required
def teacher_dashboard():
    return render_template("teacher_dashboard.html")

@teacher_bp.route("/mark_attendance", methods=["GET"])
@login_required
def mark_attendance_route():
    teacher_username = session["username"]
    teacher_subjects = get_teacher_subjects(teacher_username)
    
    alloc_id = request.args.get("alloc_id")
    date_str = request.args.get("date", datetime.date.today().isoformat())
    students_with_status = []
    selected_allocation = None
    selected_subject_id = None
    
    if alloc_id:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT ta.year, ta.semester, ta.section, ta.subject_id, s.subject_name, s.subject_code
            FROM teacher_allocations ta
            JOIN subjects s ON ta.subject_id = s.subject_id
            WHERE ta.alloc_id = ? AND ta.teacher_username = ?
        """, (alloc_id, teacher_username))
        selected_allocation = cur.fetchone()
        conn.close()

        if selected_allocation:
            students = get_students_for_class(
                selected_allocation['year'], 
                selected_allocation['semester'], 
                selected_allocation['section']
            )
            existing_records = get_existing_attendance(selected_allocation['subject_id'], date_str)
            selected_subject_id = selected_allocation['subject_id']
            for student in students:
                students_with_status.append({
                    'mis_no': student['mis_no'],
                    'name': student['name'],
                    'status': existing_records.get(student['mis_no'], 'Absent') 
                })
        else:
            flash("Invalid allocation selected.", "danger")

    return render_template(
        "mark_attendance.html", teacher_subjects=teacher_subjects, students=students_with_status,
        selected_alloc_id=alloc_id, selected_date=date_str, selected_subject_id=selected_subject_id, selected_allocation=selected_allocation
    )

@teacher_bp.route("/save_attendance", methods=["POST"])
@login_required
def save_attendance_route():
    teacher_username = session["username"]
    subject_id = request.form.get("subject_id")
    date = request.form.get("date")
    alloc_id = request.form.get("alloc_id")
    attendance_data = {}
    for key, value in request.form.items():
        if key.startswith("status_"):
            mis_no = key.split("_", 1)[1]
            attendance_data[mis_no] = value
            
    if not all([subject_id, date, attendance_data]):
        flash("Missing data.", "danger")
        return redirect(url_for("teacher.mark_attendance_route"))

    if save_bulk_attendance(subject_id, date, attendance_data, teacher_username):
        flash(f"Attendance for {date} saved/updated successfully!", "success")
    else:
        flash("Error saving attendance.", "danger")
    return redirect(url_for("teacher.mark_attendance_route", alloc_id=alloc_id, date=date))

@teacher_bp.route("/view_reports", methods=["GET", "POST"])
@login_required
def view_reports():
    teacher_username = session["username"]
    teacher_subjects = get_teacher_subjects(teacher_username)
    reports = []
    selected_alloc_id = request.form.get("alloc_id")
    selected_allocation = None
    total_classes = 0

    if request.method == "POST" and selected_alloc_id:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT ta.year, ta.semester, ta.section, ta.subject_id, s.subject_name, s.subject_code
            FROM teacher_allocations ta
            JOIN subjects s ON ta.subject_id = s.subject_id
            WHERE ta.alloc_id = ? AND ta.teacher_username = ?
        """, (selected_alloc_id, teacher_username))
        selected_allocation = cur.fetchone()
        conn.close()
        
        if selected_allocation:
            reports, total_classes = get_class_report(
                selected_allocation['year'], selected_allocation['semester'], 
                selected_allocation['section'], selected_allocation['subject_id']
            )
            if not reports and total_classes == 0: flash("No attendance marked.", "info")
            elif not reports: flash("No students found.", "warning")

    return render_template("teacher_view_reports.html", teacher_subjects=teacher_subjects, reports=reports, selected_alloc_id=selected_alloc_id, selected_allocation=selected_allocation, total_classes=total_classes)

@teacher_bp.route("/download_class_report/<file_type>", methods=["POST"])
@login_required
def download_class_report(file_type):
    teacher_username = session["username"]
    alloc_id = request.form.get("alloc_id")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ta.year, ta.semester, ta.section, ta.subject_id, s.subject_code, s.subject_name
        FROM teacher_allocations ta
        JOIN subjects s ON ta.subject_id = s.subject_id
        WHERE ta.alloc_id = ? AND ta.teacher_username = ?
    """, (alloc_id, teacher_username))
    alloc = cur.fetchone()
    conn.close()

    if not alloc: return redirect(url_for("teacher.view_reports"))

    reports, total_classes = get_class_report(alloc['year'], alloc['semester'], alloc['section'], alloc['subject_id'])
    data = [(mis_no, name, attended, total, percent) for mis_no, name, attended, total, percent in reports]
    columns = ["MIS Number", "Name", "Classes Attended", "Total Classes", "Attendance %"]
    filename = f"{alloc['year']}_Sem{alloc['semester']}_{alloc['section']}_{alloc['subject_code']}.{file_type}"
    chart_title = f"{alloc['year']} Sem {alloc['semester']} {alloc['section']}"

    if file_type == "csv": return generate_csv_report(data, columns, filename)
    elif file_type == "pdf": return generate_pdf_report(data, columns, filename, chart_title)
    elif file_type == "xlsx": return generate_excel_report(data, columns, filename)
    else: return "Invalid file type", 400

@teacher_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def teacher_change_password():
    if request.method == "POST":
        new_password = request.form["new_password"]
        username = session["username"]
        change_teacher_password(username, new_password)
        flash("Password changed successfully", "success")
        return redirect(url_for("teacher.teacher_dashboard"))
    return render_template("change_password.html", username=session["username"])