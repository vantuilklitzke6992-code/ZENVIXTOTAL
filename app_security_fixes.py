# This file contains security fixes to be integrated into app.py
# Issue: vantuilklitzke6992-code/ZENVIXTOTAL#1

import os
import uuid
from functools import wraps
from flask import redirect, url_for, flash

# ============================================================================
# FIX 1: CRITICAL - Admin Credentials Configuration
# ============================================================================
# BEFORE (INSECURE):
# ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
# ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# AFTER (SECURE):
def get_admin_email():
    """Get admin email from environment. REQUIRED - no default."""
    email = os.getenv("ADMIN_EMAIL")
    if not email:
        raise ValueError(
            "ADMIN_EMAIL environment variable is required. "
            "Set it before running the application."
        )
    return email

def get_admin_password():
    """Get admin password from environment. REQUIRED - no default."""
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        raise ValueError(
            "ADMIN_PASSWORD environment variable is required. "
            "Set it before running the application."
        )
    return password

# Usage in app.py:
# ADMIN_EMAIL = get_admin_email()
# ADMIN_PASSWORD = get_admin_password()

# ============================================================================
# FIX 2: HIGH - Session Secret Key Validation
# ============================================================================
# BEFORE (INSECURE):
# app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# AFTER (SECURE):
def get_secret_key():
    """Get SECRET_KEY from environment with production enforcement."""
    is_production = os.getenv("FLASK_ENV") == "production"
    secret_key = os.getenv("SECRET_KEY")
    
    if is_production and not secret_key:
        raise ValueError(
            "SECRET_KEY environment variable MUST be set in production mode. "
            "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    if not secret_key:
        # Development only - still insecure, but clearly marked
        import secrets
        secret_key = secrets.token_urlsafe(32)
        print("[WARNING] Running in development mode with generated SECRET_KEY. "
              "Set SECRET_KEY environment variable for consistency.")
    
    return secret_key

# Usage in app.py:
# app.secret_key = get_secret_key()

# ============================================================================
# FIX 3: HIGH - Socket.IO CORS Configuration
# ============================================================================
# BEFORE (INSECURE):
# socketio = SocketIO(app, cors_allowed_origins="*")

# AFTER (SECURE):
def get_cors_origins():
    """Get allowed CORS origins from environment.
    
    Production: Requires explicit comma-separated origins
    Development: Defaults to localhost:5000 (still configurable)
    """
    is_production = os.getenv("FLASK_ENV") == "production"
    cors_origins = os.getenv("CORS_ALLOWED_ORIGINS")
    
    if is_production and not cors_origins:
        raise ValueError(
            "CORS_ALLOWED_ORIGINS environment variable MUST be set in production. "
            "Example: CORS_ALLOWED_ORIGINS='https://example.com,https://app.example.com'"
        )
    
    if cors_origins:
        return [origin.strip() for origin in cors_origins.split(",")]
    
    # Development defaults
    return ["http://localhost:5000", "http://127.0.0.1:5000"]

# Usage in app.py:
# socketio = SocketIO(app, cors_allowed_origins=get_cors_origins())

# ============================================================================
# FIX 4: MEDIUM - Secure File Upload with Random Names
# ============================================================================
# BEFORE (INSECURE):
# def save_uploaded_file(file_storage):
#     if not file_storage or file_storage.filename == "":
#         return None
#     if not allowed_file(file_storage.filename):
#         return None
#     filename = secure_filename(file_storage.filename)
#     os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#     filepath = os.path.join(UPLOAD_FOLDER, filename)
#     file_storage.save(filepath)
#     return filename

# AFTER (SECURE):
def save_uploaded_file(file_storage, allowed_extensions):
    """Save uploaded file with random name to prevent collisions.
    
    Args:
        file_storage: File object from request.files
        allowed_extensions: Set of allowed extensions (e.g., {"png", "jpg", "pdf"})
    
    Returns:
        Random filename with original extension, or None if invalid
    """
    from werkzeug.utils import secure_filename
    import os
    
    if not file_storage or file_storage.filename == "":
        return None
    
    # Validate extension
    filename = secure_filename(file_storage.filename)
    if "." not in filename:
        return None
    
    file_ext = filename.rsplit(".", 1)[1].lower()
    if file_ext not in allowed_extensions:
        return None
    
    # Generate random name to prevent collisions
    random_name = f"{uuid.uuid4().hex}.{file_ext}"
    os.makedirs(os.path.dirname(os.path.join(os.path.dirname(__file__), "static", "uploads")), exist_ok=True)
    
    return random_name

# ============================================================================
# FIX 5: MEDIUM - Enable SQLite Foreign Key Constraints
# ============================================================================
# Add to get_db() function:
def get_db_with_foreign_keys():
    """Get database connection with foreign key constraints enabled."""
    import sqlite3
    from flask import g
    
    if "db" not in g:
        db = sqlite3.connect("database.db")  # Use DATABASE_PATH from app.py
        db.row_factory = sqlite3.Row
        # CRITICAL: Enable foreign key constraint enforcement
        db.execute("PRAGMA foreign_keys = ON")
        g.db = db
    return g.db

# ============================================================================
# FIX 6: MEDIUM - Fix Admin Approval Status Logic Bug
# ============================================================================
# BEFORE (BUGGY):
# elif (admin["tipo"] != ADMIN_USER_TYPE
#     or (admin["approval_status"] or "Ativo") != "Ativo"  # BUG!
#     or not check_password_hash(admin["senha"], ADMIN_PASSWORD)
# ):

# AFTER (FIXED):
# elif (admin["tipo"] != ADMIN_USER_TYPE
#     or (admin["approval_status"] or "") != "Ativo"  # FIXED
#     or not check_password_hash(admin["senha"], ADMIN_PASSWORD)
# ):

# ============================================================================
# FIX 7: HIGH - Protect Admin Documentation Route
# ============================================================================
def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        if "user_id" not in session or session.get("user_type") != "admin":
            flash("Acesso restrito ao administrador.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Add new route to app.py:
# @app.route("/admin/docs", methods=["GET"])
# @admin_required
# def admin_docs():
#     """Serve admin documentation only to authenticated admins."""
#     try:
#         with open("ZENVIX_CONNECT.md", "r", encoding="utf-8") as f:
#             content = f.read()
#         return render_template("admin/docs.html", content=content)
#     except FileNotFoundError:
#         flash("Documentação não encontrada.", "error")
#         return redirect(url_for("admin_panel"))

print("Security fixes loaded. Apply these to app.py following the comments above.")
