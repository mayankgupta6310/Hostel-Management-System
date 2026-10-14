from django.conf import settings
from django.core.mail import send_mail


def notify_user(user, subject, message):
    """User ka email ho to mail bhejo. Mail fail ho to app crash na ho."""
    if not user or not user.email:
        return False
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as exc:
        print(f"[email error] {exc}")
        return False