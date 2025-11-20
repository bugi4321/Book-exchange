from flask import url_for, render_template
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app.extensions import mail
from threading import Thread


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


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print(f"Email sent successfully")
        except Exception as e:
            print(f"Failed to send email: {e}")


def send_verification_email(user_email, user_name):
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
    
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
    return True


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
    
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
    return True