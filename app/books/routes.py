from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from bson import ObjectId
from datetime import datetime
from app import mongo
from . import books_bp
from .forms import BookForm
import os
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image
from flask_principal import Permission, UserNeed
from app.extensions import admin_permission

def allowed_image(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


# ➤ Prikaz svih oglasa
@books_bp.route("/")
def list_books():
    books = list(mongo.db.books.find())
    return render_template("books.html", books=books)


# ➤ Kreiranje oglasa (WTForms + Resize slika)
@books_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_book():
    form = BookForm()

    if form.validate_on_submit():
        image_filename = None

        # Ako korisnik upload-a sliku
        if form.image.data:
            image = form.image.data

            if allowed_image(image.filename):
                filename = secure_filename(image.filename)
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

                # 1) Spremi original
                image.save(save_path)

                # 2) OTVORI i SMANJI
                img = Image.open(save_path)
                img.thumbnail((600, 800))
                img.save(save_path)

                image_filename = filename
            else:
                flash("Nevažeći format slike! Dozvoljeno: png, jpg, jpeg, gif", "danger")
                return redirect(url_for("books.create_book"))

        # Spremi oglas u bazu
        mongo.db.books.insert_one({
            "first_name": current_user.first_name,
            "title": form.title.data,
            "author": form.author.data,
            "description": form.description.data,
            "image": image_filename,
            "owner_id": current_user.id,
            "owner_email": current_user.email,
            "created_at": datetime.utcnow()
        })

        flash("Oglas uspješno dodan!", "success")
        return redirect(url_for("books.list_books"))

    return render_template("add_book.html", form=form)


# ➤ Brisanje oglasa
@books_bp.route("/delete/<book_id>", methods=["POST"])
@login_required
def delete_book(book_id):
    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})

    if not book:
        flash("Oglas nije pronađen.", "danger")
        return redirect(url_for("books.list_books"))

    # ← PROMIJENJENO: Koristi Principal permission
    # Kreiraj permisiju za vlasništvo ovog resursa
    owner_permission = Permission(UserNeed(book["owner_id"]))
    
    # Admin ILI vlasnik mogu brisati
    if not (admin_permission.can() or owner_permission.can()):
        abort(403)

    mongo.db.books.delete_one({"_id": ObjectId(book_id)})
    flash("Oglas obrisan!", "success")

    return redirect(url_for("books.list_books"))


# ➤ Uređivanje oglasa
@books_bp.route("/edit/<book_id>", methods=["GET", "POST"])
@login_required
def edit_book(book_id):
    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})

    if not book:
        flash("Oglas nije pronađen.", "danger")
        return redirect(url_for("books.list_books"))

    # ← DODANO: Provjera permisija za uređivanje
    owner_permission = Permission(UserNeed(book["owner_id"]))
    
    if not (admin_permission.can() or owner_permission.can()):
        abort(403)

    form = BookForm()

    if form.validate_on_submit():
        image_filename = book.get("image")  # zadrži staru sliku

        # Ako korisnik šalje novu sliku
        if form.image.data:
            image = form.image.data

            if allowed_image(image.filename):
                # Obriši staru sliku ako postoji
                if book.get("image"):
                    old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], book["image"])
                    if os.path.exists(old_path):
                        os.remove(old_path)

                # Spremi novu sliku
                filename = secure_filename(image.filename)
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                image.save(save_path)

                # Smanji sliku
                img = Image.open(save_path)
                img.thumbnail((600, 800))
                img.save(save_path)

                image_filename = filename
            else:
                flash("Nevažeći format slike!", "danger")
                return redirect(url_for("books.edit_book", book_id=book_id))

        # Update u bazi
        mongo.db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {
                "title": form.title.data,
                "author": form.author.data,
                "description": form.description.data,
                "image": image_filename,
                "updated_at": datetime.utcnow()
            }}
        )

        flash("Oglas uspješno ažuriran!", "success")
        return redirect(url_for("books.list_books"))

    # Popuni formu postojećim podacima
    form.title.data = book["title"]
    form.author.data = book["author"]
    form.description.data = book["description"]

    return render_template("edit_book.html", form=form, book=book)



