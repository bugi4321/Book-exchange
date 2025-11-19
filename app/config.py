import os
from pathlib import Path
from dotenv import load_dotenv

# Učitaj .env prije svega!
load_dotenv()

basedir = Path(__file__).resolve().parent

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    DEBUG = False
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://bugarijaluka_db_user:HoeXvu8o27vEcX4u@cluster0.tnyqcg2.mongodb.net/booksharing?appName=Cluster0")
    
    # Email konfiguracija
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or os.getenv("MAIL_USERNAME")
    
    # Flask-Limiter defaults
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"

    # Upload slika
    UPLOAD_FOLDER = os.path.join("app", "static", "uploads")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Max 5MB

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class ProductionConfig(BaseConfig):
    DEBUG = False
    # Production-specific settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'



