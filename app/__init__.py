from flask import Flask
from config import Config

from .main import main  # blueprint

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Registracija blueprinta
    app.register_blueprint(main)

    return app

