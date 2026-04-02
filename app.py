from flask import Flask
from config import Config
from models import db
from auth import auth
from admin import admin
from company import company_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(company_bp)

if __name__ == "__main__":
    app.run(debug=True)