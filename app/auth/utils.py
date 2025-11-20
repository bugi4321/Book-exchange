from flask import url_for, render_template
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app.extensions import mail


def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification-salt')


def verify_token(token, max_age=3600):
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
    print(f"[DEBUG] Starting email verification for {user_email}")
    token = generate_verification_token(user_email)
    
    verify_url = url_for(
        'auth.verify_email',
        token=token,
        _external=True  
    )
    
    html_body = render_template(
        'auth/emails/verify_email.html',
        user_name=user_name,
        verify_url=verify_url
    )
    
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
    
    msg = Message(
        subject="Potvrdite vašu email adresu - Book Sharing",
        recipients=[user_email],
        body=text_body,
        html=html_body
    )
    
    try:
        print(f"[DEBUG] Sending email to {user_email}")
        mail.send(msg)
        print(f"[DEBUG] Email sent successfully to {user_email}")
        return True
    except Exception as e:
        print(f"[DEBUG] Failed to send email: {e}")
        return False


def send_welcome_email(user_email, user_name):
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
        print(f"[DEBUG] Welcome email sent to {user_email}")
        return True
    except Exception as e:
        print(f"[DEBUG] Failed to send welcome email: {e}")
        return False