from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = "admin"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Company(db.Model):
    __tablename__ = "company"

    id              = db.Column(db.Integer, primary_key=True)
    company_name    = db.Column(db.String(150), nullable=False)
    email           = db.Column(db.String(150), unique=True, nullable=False)
    password_hash   = db.Column(db.String(256), nullable=False)
    hr_contact      = db.Column(db.String(150), nullable=False)
    website         = db.Column(db.String(200))
    industry        = db.Column(db.String(100))
    description     = db.Column(db.Text)

    approval_status = db.Column(db.String(20), default="Pending", nullable=False)
    is_blacklisted  = db.Column(db.Boolean, default=False, nullable=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    drives     = db.relationship("PlacementDrive", backref="company", lazy=True)
    placements = db.relationship("Placement", backref="company", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    __tablename__ = "student"

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(150), nullable=False)
    email           = db.Column(db.String(150), unique=True, nullable=False)
    password_hash   = db.Column(db.String(256), nullable=False)
    phone           = db.Column(db.String(20))
    roll_number     = db.Column(db.String(50), unique=True)
    education       = db.Column(db.Text)
    skills          = db.Column(db.Text)
    resume_filename = db.Column(db.String(200))
    is_blacklisted  = db.Column(db.Boolean, default=False, nullable=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship("Application", backref="student", lazy=True)
    placements   = db.relationship("Placement", backref="student", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PlacementDrive(db.Model):
    __tablename__ = "placement_drive"

    id                   = db.Column(db.Integer, primary_key=True)
    company_id           = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    job_title            = db.Column(db.String(150), nullable=False)
    job_description      = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.Text)
    required_skills      = db.Column(db.Text)
    salary_range         = db.Column(db.String(100))
    application_deadline = db.Column(db.Date, nullable=False)

    status               = db.Column(db.String(20), default="Pending", nullable=False)
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship("Application", backref="drive", lazy=True)
    placements   = db.relationship("Placement", backref="drive", lazy=True)

class Application(db.Model):
    __tablename__ = "application"

    id               = db.Column(db.Integer, primary_key=True)
    student_id       = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    drive_id         = db.Column(db.Integer, db.ForeignKey("placement_drive.id"), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)

    status           = db.Column(db.String(20), default="Applied", nullable=False)

    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),
    )

    placement = db.relationship("Placement", backref="application", uselist=False)

class Placement(db.Model):
    __tablename__ = "placement"

    id             = db.Column(db.Integer, primary_key=True)
    student_id     = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    company_id     = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    drive_id       = db.Column(db.Integer, db.ForeignKey("placement_drive.id"), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False)
    placement_date = db.Column(db.Date, default=datetime.utcnow)
    package        = db.Column(db.String(100))