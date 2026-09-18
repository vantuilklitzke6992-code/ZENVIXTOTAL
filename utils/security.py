import secrets
from flask import request, session


def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


def validate_csrf_token():
    if request.method == "GET":
        return True

    token = session.get("_csrf_token")
    if not token:
        return False

    form_token = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
    if not form_token:
        return False

    return secrets.compare_digest(form_token, token)
