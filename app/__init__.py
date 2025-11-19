from flask import Flask
from .extensions import mongo, login_manager, limiter, mail, User, principal, admin_permission
from .main import main
from .auth import auth
from .books import books_bp
from flask_login import UserMixin
from flask_pymongo import PyMongo
from .config import DevelopmentConfig
from bson.objectid import ObjectId
from flask_principal import identity_loaded, UserNeed, RoleNeed
import os
from flask import render_template

@login_manager.user_loader
def load_user(user_id):
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    except:
        return None

    if not user:
        return None

    return User(user)


def create_app():
    app = Flask(__name__)

    # CONFIG
    app.config.from_object(DevelopmentConfig)
    
    # Upload folder za slike
    app.config["UPLOAD_FOLDER"] = os.path.join("app", "static", "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Dozvoljene ekstenzije slika
    app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}
    
    # INIT EXTENSIONS
    mongo.init_app(app)
    print("Mongo connected:", mongo.db)
    login_manager.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    principal.init_app(app)  # ← DODANO: Principal init
    
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Molimo prijavite se da biste nastavili."

    # ← DODANO: Identity loader za Principal
    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        """Učitava permisije korisnika pri svakom requestu"""
        from flask_login import current_user
        
        # Postavi user id
        identity.user = current_user

        # Dodaj UserNeed (za vlasništvo resursa)
        if hasattr(current_user, 'id'):
            identity.provides.add(UserNeed(current_user.id))

        # Dodaj RoleNeed (za role-based permissions)
        if hasattr(current_user, 'role'):
            identity.provides.add(RoleNeed(current_user.role))

    # BLUEPRINTS
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(main)
    app.register_blueprint(books_bp, url_prefix="/books")
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500
    
    return app




