import os
import webbrowser
from flask import Flask
from flask_socketio import SocketIO

from utils.db import init_db
from utils.security import generate_csrf_token
from utils.presence import online_users
from routes import auth_bp, public_bp

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
ADMIN_USER_TYPE = "admin"
DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
PORT = int(os.getenv("PORT", "5000"))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
import os


app.config["ASSET_VERSION"] = "1.0"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

socketio = SocketIO(app, cors_allowed_origins="*")
app.register_blueprint(public_bp)
app.register_blueprint(auth_bp)


@app.context_processor
def inject_online_users():
    return {"online_users": online_users}


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": generate_csrf_token()}


@app.template_filter("brl")
def format_brl(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return value if value is not None else ""
    formatted = f"R$ {amount:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def open_browser(port=PORT):
    webbrowser.open(f"http://127.0.0.1:{port}/")


with app.app_context():
    init_db()
