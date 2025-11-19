from flask import Flask
from .extensions import mongo, login_manager, limiter, mail , User
from .main import main
from .auth import auth
from .books import books_bp
from flask_login import UserMixin
from flask_pymongo import PyMongo
from .config import DevelopmentConfig
from bson.objectid import ObjectId
import os

@login_manager.user_loader
def load_user(user_id):
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    except:
        return None

    if not user:
        return None

    return User(user)  # ← koristi pravu User klasu!!



def create_app():
    app = Flask(__name__)

    # CONFIG
    app.config.from_object(DevelopmentConfig)
      # ➤ Upload folder za slike
    app.config["UPLOAD_FOLDER"] = os.path.join("app", "static", "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ➤ Dozvoljene ekstenzije slika
    app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}
    # INIT EXTENSIONS
    mongo.init_app(app)
    print("Mongo connected:", mongo.db)
    login_manager.init_app(app)
    limiter.init_app(app)      # ← OVDJE IDE
    mail.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Molimo prijavite se da biste nastavili."


    # BLUEPRINTS
    
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(main)
    app.register_blueprint(books_bp, url_prefix="/books")

    return app




