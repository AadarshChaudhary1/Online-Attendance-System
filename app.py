from flask import Flask
from db import init_db
from auth import auth_bp
from admin import admin_bp
from teacher import teacher_bp
from student import student_bp

app = Flask(__name__)
app.secret_key = "attendance_secret"


init_db()


app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(student_bp)

if __name__ == "__main__":
    app.run(debug=True)
