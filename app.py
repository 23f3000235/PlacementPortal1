from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# blueprints will be registered here in upcoming milestones

if __name__ == "__main__":
    app.run(debug=True)
