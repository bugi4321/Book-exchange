from flask import Blueprint

books_bp = Blueprint(
    "books",
    __name__,
    template_folder="templates",    # očekuje se app/books/templates/
    static_folder="static"          # opcionalno
)

from . import routes

