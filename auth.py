from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import verify_teacher, verify_student, get_teacher_name

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_type = request.form["user_type"]
        username = request.form["username"]
        password = request.form["password"]

        if user_type == "admin" and verify_teacher(username, password) and username=="admin":
            session["user_type"] = "admin"
            session["username"] = username
            return redirect(url_for("admin.admin_dashboard"))

        elif user_type == "teacher" and verify_teacher(username, password):
            session["user_type"] = "teacher"
            session["username"] = username

           
            session["teacher_name"] = get_teacher_name(username)

            return redirect(url_for("teacher.teacher_dashboard"))

        elif user_type == "student" and verify_student(username, password):
            session["user_type"] = "student"
            session["mis_no"] = username
            return redirect(url_for("student.student_dashboard"))

        flash("Invalid credentials!", "danger")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
