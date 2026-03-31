from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Company, Student, PlacementDrive, Application, Placement
from utils import login_required

admin = Blueprint("admin", __name__, url_prefix="/admin")

@admin.route("/dashboard")
@login_required("admin")
def dashboard():
    stats = {
        "total_students"   : Student.query.count(),
        "total_companies"  : Company.query.count(),
        "total_drives"     : PlacementDrive.query.count(),
        "total_applications": Application.query.count(),
    }
    pending_companies = Company.query.filter_by(approval_status="Pending").all()
    pending_drives    = PlacementDrive.query.filter_by(status="Pending").all()

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        pending_companies=pending_companies,
        pending_drives=pending_drives
    )

@admin.route("/companies")
@login_required("admin")
def companies():
    search = request.args.get("search", "").strip()
    query  = Company.query

    if search:
        query = query.filter(
            db.or_(
                Company.company_name.ilike(f"%{search}%"),
                Company.industry.ilike(f"%{search}%")
            )
        )

    all_companies = query.order_by(Company.created_at.desc()).all()
    return render_template("admin/companies.html", companies=all_companies, search=search)

@admin.route("/company/<int:company_id>/approve", methods=["POST"])
@login_required("admin")
def approve_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = "Approved"
    db.session.commit()
    flash(f"{company.company_name} has been approved.", "success")
    return redirect(request.referrer or url_for("admin.companies"))

@admin.route("/company/<int:company_id>/reject", methods=["POST"])
@login_required("admin")
def reject_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = "Rejected"
    db.session.commit()
    flash(f"{company.company_name} has been rejected.", "warning")
    return redirect(request.referrer or url_for("admin.companies"))

@admin.route("/company/<int:company_id>/blacklist", methods=["POST"])
@login_required("admin")
def blacklist_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.is_blacklisted = not company.is_blacklisted
    status = "blacklisted" if company.is_blacklisted else "reactivated"
    db.session.commit()
    flash(f"{company.company_name} has been {status}.", "info")
    return redirect(request.referrer or url_for("admin.companies"))

@admin.route("/students")
@login_required("admin")
def students():
    search = request.args.get("search", "").strip()
    query  = Student.query

    if search:
        query = query.filter(
            db.or_(
                Student.name.ilike(f"%{search}%"),
                Student.email.ilike(f"%{search}%"),
                Student.phone.ilike(f"%{search}%"),
                Student.roll_number.ilike(f"%{search}%")
            )
        )

    all_students = query.order_by(Student.created_at.desc()).all()
    return render_template("admin/students.html", students=all_students, search=search)

@admin.route("/student/<int:student_id>/blacklist", methods=["POST"])
@login_required("admin")
def blacklist_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_blacklisted = not student.is_blacklisted
    status = "blacklisted" if student.is_blacklisted else "reactivated"
    db.session.commit()
    flash(f"{student.name} has been {status}.", "info")
    return redirect(request.referrer or url_for("admin.students"))

@admin.route("/drives")
@login_required("admin")
def drives():
    all_drives = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    return render_template("admin/drives.html", drives=all_drives)

@admin.route("/drive/<int:drive_id>/approve", methods=["POST"])
@login_required("admin")
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "Approved"
    db.session.commit()
    flash(f'"{drive.job_title}" has been approved.', "success")
    return redirect(request.referrer or url_for("admin.drives"))

@admin.route("/drive/<int:drive_id>/reject", methods=["POST"])
@login_required("admin")
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "Rejected"
    db.session.commit()
    flash(f'"{drive.job_title}" has been rejected.', "warning")
    return redirect(request.referrer or url_for("admin.drives"))

@admin.route("/applications")
@login_required("admin")
def applications():
    all_applications = Application.query.order_by(Application.application_date.desc()).all()
    return render_template("admin/applications.html", applications=all_applications)