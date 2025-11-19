import os
from pathlib import Path

basedir = Path(__file__).resolve().parent

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    DEBUG = False
    MONGO_URI ="mongodb+srv://bugarijaluka_db_user:HoeXvu8o27vEcX4u@cluster0.tnyqcg2.mongodb.net/booksharing?appName=Cluster0"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    # Flask-Limiter defaults
    RATELIMIT_HEADERS_ENABLED = True

     # --- DODANO: Upload slika ---
    UPLOAD_FOLDER = os.path.join("app", "static", "uploads", "books")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Max 5MB
class DevelopmentConfig(BaseConfig):
    DEBUG = True

class ProductionConfig(BaseConfig):
    DEBUG = False

