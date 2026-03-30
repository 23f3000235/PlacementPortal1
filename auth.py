from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Admin, Company, Student
import os

auth = Blueprint("auth", __name__)

def login_required(role):

    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") != role:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return wrapper
    return decorator

@auth.route("/")
def index():
    if "role" in session:
        return redirect(url_for("auth.dashboard"))
    return redirect(url_for("auth.login"))

@auth.route("/dashboard")
def dashboard():
    role = session.get("role")
    if role == "admin":
        return redirect(url_for("auth.admin_dashboard"))
    if role == "company":
        return redirect(url_for("auth.company_dashboard"))
    if role == "student":
        return redirect(url_for("auth.student_dashboard"))
    return redirect(url_for("auth.login"))

@auth.route("/login", methods=["GET", "POST"])
def login():
    if "role" in session:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        role     = request.form.get("role")
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if role == "admin":
            user = Admin.query.filter_by(username=email).first()
            if user and user.check_password(password):
                session["role"]    = "admin"
                session["user_id"] = user.id
                session["name"]    = user.username
                flash("Welcome, Admin!", "success")
                return redirect(url_for("auth.admin_dashboard"))

        elif role == "company":
            user = Company.query.filter_by(email=email).first()
            if user and user.check_password(password):
                if user.is_blacklisted:
                    flash("Your account has been blacklisted. Contact admin.", "danger")
                    return redirect(url_for("auth.login"))
                session["role"]    = "company"
                session["user_id"] = user.id
                session["name"]    = user.company_name
                flash(f"Welcome, {user.company_name}!", "success")
                return redirect(url_for("auth.company_dashboard"))

        elif role == "student":
            user = Student.query.filter_by(email=email).first()
            if user and user.check_password(password):
                if user.is_blacklisted:
                    flash("Your account has been blacklisted. Contact admin.", "danger")
                    return redirect(url_for("auth.login"))
                session["role"]    = "student"
                session["user_id"] = user.id
                session["name"]    = user.name
                flash(f"Welcome, {user.name}!", "success")
                return redirect(url_for("auth.student_dashboard"))

        flash("Invalid credentials. Please try again.", "danger")

    return render_template("auth/login.html")

@auth.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

@auth.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        email       = request.form.get("email", "").strip().lower()
        password    = request.form.get("password", "")
        phone       = request.form.get("phone", "").strip()
        roll_number = request.form.get("roll_number", "").strip()
        education   = request.form.get("education", "").strip()
        skills      = request.form.get("skills", "").strip()

        if not all([name, email, password]):
            flash("Name, email and password are required.", "danger")
            return render_template("auth/register_student.html")

        if Student.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("auth/register_student.html")

        if roll_number and Student.query.filter_by(roll_number=roll_number).first():
            flash("Roll number already registered.", "danger")
            return render_template("auth/register_student.html")

        resume_filename = None
        resume_file = request.files.get("resume")
        if resume_file and resume_file.filename:
            from werkzeug.utils import secure_filename
            from config import Config
            ext = resume_file.filename.rsplit(".", 1)[-1].lower()
            if ext not in Config.ALLOWED_EXTENSIONS:
                flash("Resume must be a PDF, DOC, or DOCX file.", "danger")
                return render_template("auth/register_student.html")
            resume_filename = f"student_{email}_{secure_filename(resume_file.filename)}"
            resume_file.save(os.path.join(Config.UPLOAD_FOLDER, resume_filename))

        student = Student(
            name=name, email=email, phone=phone,
            roll_number=roll_number or None,
            education=education, skills=skills,
            resume_filename=resume_filename
        )
        student.set_password(password)
        db.session.add(student)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_student.html")

@auth.route("/register/company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        email        = request.form.get("email", "").strip().lower()
        password     = request.form.get("password", "")
        hr_contact   = request.form.get("hr_contact", "").strip()
        website      = request.form.get("website", "").strip()
        industry     = request.form.get("industry", "").strip()
        description  = request.form.get("description", "").strip()

        if not all([company_name, email, password, hr_contact]):
            flash("Company name, email, password and HR contact are required.", "danger")
            return render_template("auth/register_company.html")

        if Company.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("auth/register_company.html")

        company = Company(
            company_name=company_name, email=email,
            hr_contact=hr_contact, website=website,
            industry=industry, description=description
        )
        company.set_password(password)
        db.session.add(company)
        db.session.commit()

        flash("Registration submitted! Please wait for admin approval before logging in.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_company.html")

@auth.route("/admin/dashboard")
@login_required("admin")
def admin_dashboard():
    return render_template("admin/dashboard.html", name=session.get("name"))

@auth.route("/company/dashboard")
@login_required("company")
def company_dashboard():
    company = Company.query.get(session["user_id"])
    if company.approval_status != "Approved":
        return render_template("company/pending.html", company=company)
    return render_template("company/dashboard.html", company=company)

@auth.route("/student/dashboard")
@login_required("student")
def student_dashboard():
    student = Student.query.get(session["user_id"])
    return render_template("student/dashboard.html", student=student)