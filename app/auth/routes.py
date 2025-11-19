from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from flask import abort
from flask_principal import Identity, AnonymousIdentity, identity_changed
from . import auth
from .forms import RegisterForm, LoginForm
from ..extensions import mongo, User, admin_permission, limiter
from .utils import send_verification_email, verify_token, send_welcome_email


# -------------------
#  REGISTER
# -------------------
@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        # postoji li email?
        existing = mongo.db.users.find_one({"email": form.email.data})
        if existing:
            flash("Email već postoji!", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(form.password.data)

        count_users = mongo.db.users.count_documents({})
        new_user = {
            "first_name": form.first_name.data,
            "last_name": form.last_name.data,
            "email": form.email.data,
            "password": hashed_password,
            "email_verified": False,  # ← VAŽNO: Početno neverificirano
            "role": "admin" if count_users == 0 else "user"
        }

        user_id = mongo.db.users.insert_one(new_user).inserted_id

        # ← DODANO: Pošalji verifikacijski email
        send_verification_email(form.email.data, form.first_name.data)

        flash("Uspješna registracija! Provjerite email za verifikaciju.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


# -------------------
#  LOGIN
# -------------------
@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = mongo.db.users.find_one({"email": form.email.data})

        if not user or not check_password_hash(user["password"], form.password.data):
            flash("Neispravan email ili lozinka!", "danger")
            return redirect(url_for("auth.login"))

        # ← DODANO: Provjera email verifikacije
        if not user.get("email_verified", False):
            flash("Molimo verificirajte email prije prijave. Provjerite inbox!", "warning")
            return redirect(url_for("auth.login"))

        # Koristi pravu klasu User
        user_obj = User(user)
        login_user(user_obj)
        
        # Notifikacija Principal o prijavi
        from flask import current_app
        identity_changed.send(
            current_app._get_current_object(),
            identity=Identity(user_obj.id)
        )
        
        flash("Prijava uspješna!", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/login.html", form=form)


# ← DODANO: Verify email ruta
@auth.route("/verify-email/<token>")
def verify_email(token):
    """
    Verificira email korisnika pomoću tokena.
    """
    email = verify_token(token)
    
    if not email:
        flash("Verifikacijski link je nevažeći ili je istekao!", "danger")
        return redirect(url_for("auth.login"))
    
    # Pronađi korisnika
    user = mongo.db.users.find_one({"email": email})
    
    if not user:
        flash("Korisnik nije pronađen!", "danger")
        return redirect(url_for("auth.login"))
    
    # Provjeri je li već verificiran
    if user.get("email_verified", False):
        flash("Email je već verificiran!", "info")
        return redirect(url_for("auth.login"))
    
    # Verificiraj email
    mongo.db.users.update_one(
        {"email": email},
        {"$set": {"email_verified": True}}
    )
    
    # Pošalji welcome email
    send_welcome_email(email, user.get("first_name", ""))
    
    flash("Email uspješno verificiran! Sada se možete prijaviti.", "success")
    return redirect(url_for("auth.login"))


# ← DODANO: Resend verification email
@auth.route("/resend-verification", methods=["GET", "POST"])
@limiter.limit("3 per hour")  # Max 3 resenda po satu
def resend_verification():
    """
    Ponovno slanje verifikacijskog email-a.
    """
    if request.method == "POST":
        email = request.form.get("email")
        
        if not email:
            flash("Molimo unesite email adresu!", "danger")
            return redirect(url_for("auth.resend_verification"))
        
        user = mongo.db.users.find_one({"email": email})
        
        if not user:
            # Ne otkrivaj postoji li email (sigurnost)
            flash("Ako email postoji u sustavu, poslan je verifikacijski link.", "info")
            return redirect(url_for("auth.login"))
        
        if user.get("email_verified", False):
            flash("Email je već verificiran!", "info")
            return redirect(url_for("auth.login"))
        
        # Pošalji novi token
        send_verification_email(email, user.get("first_name", ""))
        flash("Verifikacijski email poslan! Provjerite inbox.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("auth/resend_verification.html")


@auth.route("/profile")
@login_required
def profile():
    user = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    return render_template("auth/profile.html", user=user)


# -------------------
#  LOGOUT
# -------------------
@auth.route("/logout")
@login_required
def logout():
    from flask import current_app
    identity_changed.send(
        current_app._get_current_object(),
        identity=AnonymousIdentity()
    )
    
    logout_user()
    flash("Odjavljeni ste.", "info")
    return redirect(url_for("main.index"))


# -------------------
#  DELETE USER
# -------------------
@auth.route("/delete_user/<user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    user_to_delete = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if not user_to_delete:
        flash("Korisnik ne postoji.", "danger")
        return redirect(url_for("auth.profile"))

    is_owner = (current_user.id == user_id)
    is_admin = admin_permission.can()
    
    if not (is_owner or is_admin):
        abort(403)

    admin_count = mongo.db.users.count_documents({"role": "admin"})

    if user_to_delete["role"] == "admin" and admin_count == 1:
        flash("Ne možete obrisati jedini admin račun!", "danger")
        return redirect(url_for("auth.profile"))

    result = mongo.db.users.delete_one({"_id": ObjectId(user_id)})

    if result.deleted_count:
        flash("Korisnik je uspješno obrisan.", "success")

        if current_user.id == user_id:
            logout_user()
            return redirect(url_for("main.index"))
        else:
            return redirect(url_for("main.index"))
    else:
        flash("Došlo je do pogreške prilikom brisanja korisnika.", "danger")
        return redirect(url_for("auth.profile"))


# -------------------
#  ADMIN DASHBOARD
# -------------------
@auth.route("/admin/dashboard")
@login_required
@admin_permission.require(http_exception=403)
def admin_dashboard():
    raw_users = mongo.db.users.find()
    users = []

    for u in raw_users:
        u["id"] = str(u["_id"])
        users.append(u)

    return render_template("auth/admin/dashboard.html", users=users)


# -------------------
#  SET ROLE
# -------------------
@auth.route("/set_role/<user_id>/<role>", methods=["POST"])
@login_required
@admin_permission.require(http_exception=403)
def set_role(user_id, role):
    if role not in ["user", "admin"]:
        flash("Nevažeća rola.", "danger")
        return redirect(url_for("auth.admin_dashboard"))
    
    admin_count = mongo.db.users.count_documents({"role": "admin"})
    if current_user.id == user_id and admin_count == 1:
        flash("Ne možete ukloniti sami sebe jer ste jedini administrator!", "danger")
        return redirect(url_for("auth.admin_dashboard"))
    
    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": role}}
    )

    flash("Uloga uspješno promijenjena!", "success")
    return redirect(url_for("auth.admin_dashboard"))
