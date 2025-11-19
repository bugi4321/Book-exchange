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
from app.extensions import admin_permission, limiter
from app.utils import markdown_to_html

def allowed_image(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


# ➤ Prikaz svih oglasa
@books_bp.route("/")
def list_books():
    books = list(mongo.db.books.find())
    
    # Konverzija Markdown → HTML za sve knjige
    for book in books:
        if book.get("description"):
            book["description_html"] = markdown_to_html(book["description"])
    
    return render_template("books.html", books=books)


# ➤ Kreiranje oglasa
@books_bp.route("/create", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per hour")  # ← DODANO: Max 10 knjiga po satu
def create_book():
    form = BookForm()

    if form.validate_on_submit():
        image_filename = None

        if form.image.data:
            image = form.image.data

            if allowed_image(image.filename):
                filename = secure_filename(image.filename)
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

                image.save(save_path)

                img = Image.open(save_path)
                img.thumbnail((600, 800))
                img.save(save_path)

                image_filename = filename
            else:
                flash("Nevažeći format slike! Dozvoljeno: png, jpg, jpeg, gif", "danger")
                return redirect(url_for("books.create_book"))

        # Spremi raw Markdown u bazu
        mongo.db.books.insert_one({
            "first_name": current_user.first_name,
            "title": form.title.data,
            "author": form.author.data,
            "description": form.description.data,  # raw Markdown
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
@limiter.limit("20 per hour")  # ← DODANO: Max 20 brisanja po satu
def delete_book(book_id):
    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})

    if not book:
        flash("Oglas nije pronađen.", "danger")
        return redirect(url_for("books.list_books"))

    owner_permission = Permission(UserNeed(book["owner_id"]))
    
    if not (admin_permission.can() or owner_permission.can()):
        abort(403)

    mongo.db.books.delete_one({"_id": ObjectId(book_id)})
    flash("Oglas obrisan!", "success")

    return redirect(url_for("books.list_books"))


# ➤ Uređivanje oglasa
@books_bp.route("/edit/<book_id>", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per hour")  # ← DODANO: Max 20 edit-a po satu
def edit_book(book_id):
    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})

    if not book:
        flash("Oglas nije pronađen.", "danger")
        return redirect(url_for("books.list_books"))

    owner_permission = Permission(UserNeed(book["owner_id"]))
    
    if not (admin_permission.can() or owner_permission.can()):
        abort(403)

    form = BookForm()

    if form.validate_on_submit():
        image_filename = book.get("image")

        if form.image.data:
            image = form.image.data

            if allowed_image(image.filename):
                if book.get("image"):
                    old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], book["image"])
                    if os.path.exists(old_path):
                        os.remove(old_path)

                filename = secure_filename(image.filename)
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                image.save(save_path)

                img = Image.open(save_path)
                img.thumbnail((600, 800))
                img.save(save_path)

                image_filename = filename
            else:
                flash("Nevažeći format slike!", "danger")
                return redirect(url_for("books.edit_book", book_id=book_id))

        # Spremi raw Markdown
        mongo.db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {
                "title": form.title.data,
                "author": form.author.data,
                "description": form.description.data,  # raw Markdown
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


# ➤ Detalji knjige
@books_bp.route("/book/<book_id>")
def book_detail(book_id):
    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    
    if not book:
        abort(404)
    
    # Konverzija Markdown → HTML
    book["description_html"] = markdown_to_html(book.get("description", ""))
    
    return render_template("book_detail.html", book=book)



