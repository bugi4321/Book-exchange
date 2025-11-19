from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_login import UserMixin
from flask import abort
from flask_login import current_user

mongo = PyMongo()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()

class User(UserMixin):
    def __init__(self, user_dict):
        self.id = str(user_dict["_id"])
        self.email = user_dict["email"]
        self.first_name = user_dict.get("first_name")
        self.last_name = user_dict.get("last_name")
        self.role = user_dict.get("role", "user")

