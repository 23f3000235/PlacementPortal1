from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Student, PlacementDrive, Application, Placement, Company
from utils import login_required
from datetime import date
import os

student_bp = Blueprint("student", __name__, url_prefix="/student")


def get_current_student():
    return Student.query.get(session["user_id"])


# ── dashboard ──────────────────────────────────────────────────────────────────

@student_bp.route("/dashboard")
@login_required("student")
def dashboard():
    student = get_current_student()

    # All approved drives (not yet applied to)
    applied_drive_ids = [a.drive_id for a in student.applications]

    approved_drives = PlacementDrive.query.filter_by(status="Approved")\
                                          .order_by(PlacementDrive.created_at.desc())\
                                          .all()

    # Applications with latest status — for notification-style display
    recent_applications = Application.query\
                            .filter_by(student_id=student.id)\
                            .order_by(Application.application_date.desc())\
                            .limit(5).all()

    return render_template(
        "student/dashboard.html",
        student=student,
        approved_drives=approved_drives,
        applied_drive_ids=applied_drive_ids,
        recent_applications=recent_applications
    )


# ── browse & search drives ─────────────────────────────────────────────────────

@student_bp.route("/drives")
@login_required("student")
def drives():
    student = get_current_student()

    search   = request.args.get("search", "").strip()
    query    = PlacementDrive.query.filter_by(status="Approved")

    if search:
        query = query.filter(
            db.or_(
                PlacementDrive.job_title.ilike(f"%{search}%"),
                PlacementDrive.required_skills.ilike(f"%{search}%"),
                PlacementDrive.eligibility_criteria.ilike(f"%{search}%"),
            )
        ).join(Company).filter(
            db.or_(
                PlacementDrive.job_title.ilike(f"%{search}%"),
                PlacementDrive.required_skills.ilike(f"%{search}%"),
                Company.company_name.ilike(f"%{search}%"),
            )
        )

    drives = query.order_by(PlacementDrive.application_deadline.asc()).all()

    # Track which drives the student already applied to
    applied_drive_ids = [a.drive_id for a in student.applications]

    return render_template(
        "student/drives.html",
        student=student,
        drives=drives,
        applied_drive_ids=applied_drive_ids,
        search=search,
        today=date.today() 
    )


# ── apply for a drive ──────────────────────────────────────────────────────────

@student_bp.route("/drive/<int:drive_id>/apply", methods=["POST"])
@login_required("student")
def apply(drive_id):
    student = get_current_student()
    drive   = PlacementDrive.query.get_or_404(drive_id)

    # Only approved drives can be applied to
    if drive.status != "Approved":
        flash("This drive is not open for applications.", "danger")
        return redirect(url_for("student.drives"))

    # Deadline check
    if drive.application_deadline < date.today():
        flash("The application deadline for this drive has passed.", "danger")
        return redirect(url_for("student.drives"))

    # Duplicate application check
    existing = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive_id
    ).first()

    if existing:
        flash("You have already applied to this drive.", "warning")
        return redirect(url_for("student.drives"))

    application = Application(
        student_id=student.id,
        drive_id=drive_id,
        status="Applied"
    )
    db.session.add(application)
    db.session.commit()

    flash(f"Successfully applied to {drive.job_title} at {drive.company.company_name}!", "success")
    return redirect(url_for("student.my_applications"))


# ── my applications ────────────────────────────────────────────────────────────

@student_bp.route("/applications")
@login_required("student")
def my_applications():
    student = get_current_student()

    applications = Application.query\
                    .filter_by(student_id=student.id)\
                    .order_by(Application.application_date.desc())\
                    .all()

    return render_template(
        "student/my_applications.html",
        student=student,
        applications=applications
    )


# ── placement history ──────────────────────────────────────────────────────────

@student_bp.route("/placements")
@login_required("student")
def placement_history():
    student    = get_current_student()
    placements = Placement.query\
                    .filter_by(student_id=student.id)\
                    .order_by(Placement.placement_date.desc())\
                    .all()

    return render_template(
        "student/placement_history.html",
        student=student,
        placements=placements
    )


# ── edit profile ───────────────────────────────────────────────────────────────

@student_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required("student")
def edit_profile():
    student = get_current_student()

    if request.method == "POST":
        student.name        = request.form.get("name", "").strip()
        student.phone       = request.form.get("phone", "").strip()
        student.education   = request.form.get("education", "").strip()
        student.skills      = request.form.get("skills", "").strip()
        student.roll_number = request.form.get("roll_number", "").strip() or None

        # Password change (optional)
        new_password = request.form.get("new_password", "").strip()
        if new_password:
            student.set_password(new_password)

        # Resume upload (optional)
        resume_file = request.files.get("resume")
        if resume_file and resume_file.filename:
            from werkzeug.utils import secure_filename
            from config import Config
            ext = resume_file.filename.rsplit(".", 1)[-1].lower()
            if ext not in Config.ALLOWED_EXTENSIONS:
                flash("Resume must be a PDF, DOC, or DOCX file.", "danger")
                return render_template("student/edit_profile.html", student=student)

            # Remove old resume if exists
            if student.resume_filename:
                old_path = os.path.join(Config.UPLOAD_FOLDER, student.resume_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)

            resume_filename = f"student_{student.email}_{secure_filename(resume_file.filename)}"
            resume_file.save(os.path.join(Config.UPLOAD_FOLDER, resume_filename))
            student.resume_filename = resume_filename

        db.session.commit()
        session["name"] = student.name     # update display name in navbar
        flash("Profile updated successfully.", "success")
        return redirect(url_for("student.dashboard"))

    return render_template("student/edit_profile.html", student=student)