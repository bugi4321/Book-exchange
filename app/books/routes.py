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


#  Prikaz svih oglasa (SA PRETRAGOM I PAGINACIJOM)
@books_bp.route("/")
def list_books():
    
    search_query = request.args.get('search', '').strip()
    author_filter = request.args.get('author', '').strip()
    
    
    page = request.args.get('page', 1, type=int)
    per_page = 9  
    
    
    query = {}
    
    if search_query:
        
        query["title"] = {"$regex": search_query, "$options": "i"}
    
    if author_filter:
        
        query["author"] = {"$regex": author_filter, "$options": "i"}
    
    # Ukupan broj knjiga (za paginaciju)
    total_books = mongo.db.books.count_documents(query)
    total_pages = (total_books + per_page - 1) // per_page  
    
    # Dohvati knjige s paginacijom
    books = list(
        mongo.db.books.find(query)
        .sort("created_at", -1) 
        .skip((page - 1) * per_page)
        .limit(per_page)
    )
    
    # Konverzija Markdown → HTML 
    for book in books:
        if book.get("description"):
            book["description_html"] = markdown_to_html(book["description"])
    
    
    all_authors = mongo.db.books.distinct("author")
    
    return render_template(
        "books.html", 
        books=books,
        page=page,
        total_pages=total_pages,
        total_books=total_books,
        search_query=search_query,
        author_filter=author_filter,
        all_authors=sorted(all_authors)  
    )


# MOJE KNJIGE STRANICA
@books_bp.route("/my-books")
@login_required
def my_books():
    
    search_query = request.args.get('search', '').strip()
    
    
    page = request.args.get('page', 1, type=int)
    per_page = 9
    
    
    query = {"owner_id": current_user.id}
    
    if search_query:
        query["title"] = {"$regex": search_query, "$options": "i"}
    
    # Ukupan broj korisnikovih knjiga
    total_books = mongo.db.books.count_documents(query)
    total_pages = (total_books + per_page - 1) // per_page
    
    # Dohvati knjige
    books = list(
        mongo.db.books.find(query)
        .sort("created_at", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )
    
    # Markdown konverzija
    for book in books:
        if book.get("description"):
            book["description_html"] = markdown_to_html(book["description"])
    
    return render_template(
        "my_books.html",
        books=books,
        page=page,
        total_pages=total_pages,
        total_books=total_books,
        search_query=search_query
    )


#  Kreiranje oglasa
@books_bp.route("/create", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per hour")
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


#  Brisanje oglasa
@books_bp.route("/delete/<book_id>", methods=["POST"])
@login_required
@limiter.limit("20 per hour")
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


# Uređivanje oglasa
@books_bp.route("/edit/<book_id>", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per hour")
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

    form.title.data = book["title"]
    form.author.data = book["author"]
    form.description.data = book["description"]

    return render_template("edit_book.html", form=form, book=book)


#  Detalji knjige
@books_bp.route("/book/<book_id>")
def book_detail(book_id):
    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    
    if not book:
        abort(404)
    
    book["description_html"] = markdown_to_html(book.get("description", ""))
    
    return render_template("book_detail.html", book=book)



