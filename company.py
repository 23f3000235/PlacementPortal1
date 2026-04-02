from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Company, PlacementDrive, Application, Student, Placement
from utils import login_required
from datetime import date

company_bp = Blueprint("company", __name__, url_prefix="/company")


def get_current_company():
    """Helper — fetch the logged-in company from DB."""
    return Company.query.get(session["user_id"])


def approved_only(f):
    """Extra guard — company must be approved to access this route."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        company = get_current_company()
        if company.approval_status != "Approved":
            flash("Your account is pending admin approval.", "warning")
            return render_template("company/pending.html", company=company)
        return f(*args, **kwargs)
    return wrapper


# ── dashboard ──────────────────────────────────────────────────────────────────

@company_bp.route("/dashboard")
@login_required("company")
@approved_only
def dashboard():
    company = get_current_company()

    # Drives with applicant counts
    drives = PlacementDrive.query.filter_by(company_id=company.id)\
                                 .order_by(PlacementDrive.created_at.desc()).all()

    drive_data = []
    for drive in drives:
        applicant_count = Application.query.filter_by(drive_id=drive.id).count()
        drive_data.append({"drive": drive, "applicant_count": applicant_count})

    return render_template("company/dashboard.html", company=company, drive_data=drive_data)


# ── create drive ───────────────────────────────────────────────────────────────

@company_bp.route("/drive/create", methods=["GET", "POST"])
@login_required("company")
@approved_only
def create_drive():
    company = get_current_company()

    if request.method == "POST":
        job_title            = request.form.get("job_title", "").strip()
        job_description      = request.form.get("job_description", "").strip()
        eligibility_criteria = request.form.get("eligibility_criteria", "").strip()
        required_skills      = request.form.get("required_skills", "").strip()
        salary_range         = request.form.get("salary_range", "").strip()
        deadline_str         = request.form.get("application_deadline", "")

        if not all([job_title, job_description, deadline_str]):
            flash("Job title, description and deadline are required.", "danger")
            return render_template("company/create_drive.html", company=company)

        try:
            deadline = date.fromisoformat(deadline_str)
        except ValueError:
            flash("Invalid deadline date.", "danger")
            return render_template("company/create_drive.html", company=company)

        if deadline < date.today():
            flash("Deadline cannot be in the past.", "danger")
            return render_template("company/create_drive.html", company=company)

        drive = PlacementDrive(
            company_id=company.id,
            job_title=job_title,
            job_description=job_description,
            eligibility_criteria=eligibility_criteria,
            required_skills=required_skills,
            salary_range=salary_range,
            application_deadline=deadline,
            status="Pending"   # waits for admin approval
        )
        db.session.add(drive)
        db.session.commit()

        flash("Placement drive submitted for admin approval.", "success")
        return redirect(url_for("company.dashboard"))

    return render_template("company/create_drive.html", company=company)


# ── edit drive ─────────────────────────────────────────────────────────────────

@company_bp.route("/drive/<int:drive_id>/edit", methods=["GET", "POST"])
@login_required("company")
@approved_only
def edit_drive(drive_id):
    company = get_current_company()
    drive   = PlacementDrive.query.get_or_404(drive_id)

    # Ensure company owns this drive
    if drive.company_id != company.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("company.dashboard"))

    if drive.status == "Closed":
        flash("Closed drives cannot be edited.", "warning")
        return redirect(url_for("company.dashboard"))

    if request.method == "POST":
        drive.job_title            = request.form.get("job_title", "").strip()
        drive.job_description      = request.form.get("job_description", "").strip()
        drive.eligibility_criteria = request.form.get("eligibility_criteria", "").strip()
        drive.required_skills      = request.form.get("required_skills", "").strip()
        drive.salary_range         = request.form.get("salary_range", "").strip()
        deadline_str               = request.form.get("application_deadline", "")

        if not all([drive.job_title, drive.job_description, deadline_str]):
            flash("Job title, description and deadline are required.", "danger")
            return render_template("company/edit_drive.html", company=company, drive=drive)

        try:
            drive.application_deadline = date.fromisoformat(deadline_str)
        except ValueError:
            flash("Invalid deadline date.", "danger")
            return render_template("company/edit_drive.html", company=company, drive=drive)

        # Re-submit for approval if it was approved (editing resets it)
        if drive.status == "Approved":
            drive.status = "Pending"
            flash("Drive updated and re-submitted for admin approval.", "info")
        else:
            flash("Drive updated successfully.", "success")

        db.session.commit()
        return redirect(url_for("company.dashboard"))

    return render_template("company/edit_drive.html", company=company, drive=drive)


# ── close drive ────────────────────────────────────────────────────────────────

@company_bp.route("/drive/<int:drive_id>/close", methods=["POST"])
@login_required("company")
@approved_only
def close_drive(drive_id):
    company = get_current_company()
    drive   = PlacementDrive.query.get_or_404(drive_id)

    if drive.company_id != company.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("company.dashboard"))

    drive.status = "Closed"
    db.session.commit()
    flash(f'"{drive.job_title}" has been closed.', "info")
    return redirect(url_for("company.dashboard"))


# ── delete drive ───────────────────────────────────────────────────────────────

@company_bp.route("/drive/<int:drive_id>/delete", methods=["POST"])
@login_required("company")
@approved_only
def delete_drive(drive_id):
    company = get_current_company()
    drive   = PlacementDrive.query.get_or_404(drive_id)

    if drive.company_id != company.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("company.dashboard"))

    # Only allow deletion of Pending or Rejected drives
    if drive.status == "Approved":
        flash("Approved drives cannot be deleted. Close them instead.", "warning")
        return redirect(url_for("company.dashboard"))

    db.session.delete(drive)
    db.session.commit()
    flash(f'"{drive.job_title}" has been deleted.', "info")
    return redirect(url_for("company.dashboard"))


# ── view applications for a drive ──────────────────────────────────────────────

@company_bp.route("/drive/<int:drive_id>/applications")
@login_required("company")
@approved_only
def drive_applications(drive_id):
    company = get_current_company()
    drive   = PlacementDrive.query.get_or_404(drive_id)

    if drive.company_id != company.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("company.dashboard"))

    applications = Application.query.filter_by(drive_id=drive_id)\
                                    .order_by(Application.application_date.desc()).all()

    return render_template(
        "company/applications.html",
        company=company,
        drive=drive,
        applications=applications
    )


# ── update application status ──────────────────────────────────────────────────

@company_bp.route("/application/<int:application_id>/status", methods=["POST"])
@login_required("company")
@approved_only
def update_application_status(application_id):
    company     = get_current_company()
    application = Application.query.get_or_404(application_id)

    # Verify this application belongs to one of this company's drives
    if application.drive.company_id != company.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("company.dashboard"))

    new_status = request.form.get("status")
    allowed    = ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"]

    if new_status not in allowed:
        flash("Invalid status.", "danger")
        return redirect(url_for("company.drive_applications", drive_id=application.drive_id))

    application.status = new_status

    # If selected → create Placement record
    if new_status == "Selected":
        existing = Placement.query.filter_by(application_id=application.id).first()
        if not existing:
            placement = Placement(
                student_id     = application.student_id,
                company_id     = company.id,
                drive_id       = application.drive_id,
                application_id = application.id
            )
            db.session.add(placement)

    db.session.commit()
    flash(f"Application status updated to '{new_status}'.", "success")
    return redirect(url_for("company.drive_applications", drive_id=application.drive_id))