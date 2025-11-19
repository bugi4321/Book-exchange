from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_login import UserMixin
from flask import abort
from flask_login import current_user
from flask_principal import Principal, Permission, RoleNeed, identity_loaded, UserNeed

mongo = PyMongo()
login_manager = LoginManager()

# ← PROMIJENJENO: Limiter s boljom konfiguracijom
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],  # Globalni limiti
    storage_uri="memory://",  # In-memory storage
    strategy="fixed-window"  # Fixed window strategija
)

mail = Mail()
principal = Principal()

# Definiraj permisije
admin_permission = Permission(RoleNeed('admin'))
user_permission = Permission(RoleNeed('user'))

class User(UserMixin):
    def __init__(self, user_dict):
        self.id = str(user_dict["_id"])
        self.email = user_dict["email"]
        self.first_name = user_dict.get("first_name")
        self.last_name = user_dict.get("last_name")
        self.role = user_dict.get("role", "user")

