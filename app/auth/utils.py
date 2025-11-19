from flask import url_for, render_template
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app.extensions import mail
import secrets


def generate_verification_token(email):
    """
    Generira siguran token za email verifikaciju.
    Token vrijedi 1 sat (3600 sekundi).
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification-salt')


def verify_token(token, max_age=3600):
    """
    Verificira token i vraća email ako je validan.
    max_age: vrijeme trajanja tokena u sekundama (default 1 sat)
    
    Returns:
        str: email ako je token validan
        None: ako je token istekao ili nevažeći
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-verification-salt',
            max_age=max_age
        )
        return email
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None


def send_verification_email(user_email, user_name):
    """
    Šalje verifikacijski email korisniku.
    
    Args:
        user_email (str): Email adresa korisnika
        user_name (str): Ime korisnika
    """
    token = generate_verification_token(user_email)
    
    # Generiraj verifikacijski link
    verify_url = url_for(
        'auth.verify_email',
        token=token,
        _external=True  # Puni URL (https://...)
    )
    
    # HTML verzija email-a
    html_body = render_template(
        'auth/emails/verify_email.html',
        user_name=user_name,
        verify_url=verify_url
    )
    
    # Plain text verzija (fallback)
    text_body = f"""
    Pozdrav {user_name},

    Dobrodošli na Book Sharing platformu!

    Molimo potvrdite vašu email adresu klikom na sljedeći link:
    {verify_url}

    Ovaj link vrijedi 1 sat.

    Ako niste kreirali račun na našoj platformi, ignorirajte ovaj email.

    Srdačan pozdrav,
    Book Sharing Tim
    """
    
    # Kreiraj poruku
    msg = Message(
        subject="Potvrdite vašu email adresu - Book Sharing",
        recipients=[user_email],
        body=text_body,
        html=html_body
    )
    
    try:
        mail.send(msg)
        print(f"Verification email sent to {user_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_welcome_email(user_email, user_name):
    """
    Šalje welcome email nakon uspješne verifikacije.
    """
    html_body = render_template(
        'auth/emails/welcome_email.html',
        user_name=user_name
    )
    
    text_body = f"""
    Pozdrav {user_name},

    Vaša email adresa je uspješno verificirana!

    Sada možete u potpunosti koristiti sve funkcionalnosti Book Sharing platforme:
    - Dodavanje knjiga
    - Pregled i pretraga knjiga
    - Komunikacija s drugim korisnicima

    Srdačan pozdrav,
    Book Sharing Tim
    """
    
    msg = Message(
        subject="Dobrodošli na Book Sharing!",
        recipients=[user_email],
        body=text_body,
        html=html_body
    )
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        return False