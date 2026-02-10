from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import (
    fetch_student_attendance_summary, get_student_detailed_report, 
    change_student_password
)
from utils import generate_pdf_report, generate_csv_report

student_bp = Blueprint("student", __name__, url_prefix="/student")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_type" not in session or session["user_type"] != "student":
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@student_bp.route("/dashboard")
@login_required
def student_dashboard():
    mis_no = session.get("mis_no")
    name, summary = fetch_student_attendance_summary(mis_no)
    records = get_student_detailed_report(mis_no)
    
    
    total_present = sum(s['present'] for s in summary)
    total_classes = sum(s['total'] for s in summary)
    overall_percent = round((total_present / total_classes) * 100, 2) if total_classes > 0 else 0

    return render_template(
        "student_dashboard.html",
        name=name,
        mis_no=mis_no,
        summary=summary,
        records=records,
        total_present=total_present,
        total_classes=total_classes,
        overall_percent=overall_percent
    )

@student_bp.route("/download_report/<report_type>", methods=["GET"])
@login_required
def download_report(report_type):
    mis_no = session.get("mis_no")
    if not mis_no:
        flash("MIS Number not found in session", "danger")
        return redirect(url_for("student.student_dashboard"))

    report_data = get_student_detailed_report(mis_no)
    
    
    data = [(row["date"], row["subject_name"], row["status"]) for row in report_data]
    columns = ["Date", "Subject", "Status"]
    filename = f"{mis_no}_full_attendance.{report_type}"
    chart_title = f"Attendance Report for {mis_no}"

    if report_type == "csv":
        return generate_csv_report(data, columns, filename)
    elif report_type == "pdf":
       
        return generate_pdf_report(data, columns, filename, chart_title=chart_title)
    else:
        flash("Invalid report type", "danger")
        return redirect(url_for("student.student_dashboard"))


@student_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def student_change_password():
    if request.method == "POST":
        new_password = request.form["new_password"]
        mis_no = session.get("mis_no")
        if mis_no:
            change_student_password(mis_no, new_password)
            flash("Password changed successfully", "success")
            return redirect(url_for("student.student_dashboard"))
        else:
            flash("Error: Student MIS not found", "danger")
            return redirect(url_for("student.student_dashboard"))

    return render_template("student_change_password.html", username=session.get("mis_no"))