import pyotp
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from  django.contrib.auth import get_user_model
from celery import shared_task
User=get_user_model()

@shared_task
def send_code_to_user(request, email):
    user = User.objects.get(email=email)
    if not user.secret_key:
        user.secret_key = pyotp.random_base32()
    otp = pyotp.TOTP(user.secret_key, interval=300).now()
    request.session["user_email"] = email
    current_site = "example.com"
    subject = "Email Verification"
    email_body = f"""
    <html>
    <body>
       Hello👋 {user.username}, Thank you for registering on {current_site}
            To complete your registration, verify your email address, please use the following one-time passcode: {otp}
            This code is valid for 5 minutes. Please use it promptly. If you did not sign up for an account, please disregard this email.
            <p>Best regards,<br>The {current_site} Team</p>
    </body>
    </html>
    """
    from_email = settings.EMAIL_HOST_USER
    send_email = EmailMessage(
        subject=subject, body=email_body, from_email=from_email, to=[email]
    )
    send_email.content_subtype = "html"
    send_email.send(fail_silently=False)
    user.otp_created_at = timezone.now()
    user.save()

@shared_task
def send_reset_email(data):
    email = EmailMessage(
        subject=data["email_subject"],
        body=data["email_body"],
        from_email=settings.EMAIL_HOST_USER,
        to=[data["to_email"]],
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)