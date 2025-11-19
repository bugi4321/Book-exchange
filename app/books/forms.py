from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired

class BookForm(FlaskForm):
    title = StringField("Naslov knjige", validators=[DataRequired()])
    author = StringField("Autor", validators=[DataRequired()])
    description = TextAreaField("Opis", validators=[DataRequired()])
    image = FileField("Slika knjige", validators=[FileAllowed(["jpg", "png", "jpeg"])])
    submit = SubmitField("Objavi knjigu")
