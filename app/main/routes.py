from flask import render_template
from . import main

@main.route('/')
def index():
    return render_template("index.html")

@main.route('/books')
def books():
    return render_template("books.html")

@main.route('/add-book')
def add_book():
    return render_template("add_book.html")

@main.route('/about')
def about():
    return render_template("about.html")


@main.route('/register')
def register():
    return render_template("register.html")

