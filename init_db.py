from app import app
from models import db, Admin

with app.app_context():
    db.create_all()
    print("All tables created.")

    if not Admin.query.filter_by(username="admin").first():
        admin = Admin(username="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Admin user seeded: username=admin, password=admin123")
    else:
        print("Admin already exists, skipping seed.")