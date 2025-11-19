from flask import render_template, request, redirect, url_for, flash
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
                img.thumbnail((600, 800))      # max 600x800 px
                img.save(save_path)            # spremi preko originala

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

    is_admin = getattr(current_user, "role", "user") == "admin"
    is_owner = (book["owner_id"] == current_user.id)

    if not (is_admin or is_owner):
        flash("Nemate ovlasti za brisanje ovog oglasa.", "danger")
        return redirect(url_for("books.list_books"))

    mongo.db.books.delete_one({"_id": ObjectId(book_id)})
    flash("Oglas obrisan!", "success")

    return redirect(url_for("books.list_books"))



