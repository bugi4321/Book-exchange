from flask import Flask, render_template
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
    
    # ← DODANO: Rate limiter konfiguracija
    app.config["RATELIMIT_STORAGE_URL"] = "memory://"  # In-memory storage
    app.config["RATELIMIT_STRATEGY"] = "fixed-window"
    app.config["RATELIMIT_HEADERS_ENABLED"] = True  # Prikaži rate limit headere
    
    # INIT EXTENSIONS
    mongo.init_app(app)
    print("Mongo connected:", mongo.db)
    login_manager.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    principal.init_app(app)
    
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Molimo prijavite se da biste nastavili."

    # Identity loader za Principal
    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        """Učitava permisije korisnika pri svakom requestu"""
        from flask_login import current_user
        
        identity.user = current_user

        if hasattr(current_user, 'id'):
            identity.provides.add(UserNeed(current_user.id))

        if hasattr(current_user, 'role'):
            identity.provides.add(RoleNeed(current_user.role))

    # ← DODANO: Custom Rate Limit Error Handler
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template('errors/429.html', error=e), 429

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500

    # BLUEPRINTS
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(main)
    app.register_blueprint(books_bp, url_prefix="/books")

    return app




