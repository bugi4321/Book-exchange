from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length, EqualTo

class RegisterForm(FlaskForm):
    first_name = StringField("Ime", validators=[InputRequired(), Length(min=2, max=30)])
    last_name = StringField("Prezime", validators=[InputRequired(), Length(min=2, max=30)])
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Lozinka", validators=[InputRequired(), Length(min=6)])
    password_confirm = PasswordField("Ponovi lozinku", validators=[
        InputRequired(), EqualTo("password")
    ])
    submit = SubmitField("Registriraj se")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Lozinka", validators=[InputRequired()])
    submit = SubmitField("Prijava")
