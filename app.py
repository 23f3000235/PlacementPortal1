from flask import Flask
from config import Config
from models import db
from auth import auth

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(auth)

if __name__ == "__main__":
    app.run(debug=True)