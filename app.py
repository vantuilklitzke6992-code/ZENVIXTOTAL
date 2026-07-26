from flask import Flask, render_template, g, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, join_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import send_from_directory
import sqlite3
import os
import threading
import webbrowser
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
ADMIN_USER_TYPE = "admin"
DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
PORT = int(os.getenv("PORT", "5000"))

def open_browser(port=PORT):
    webbrowser.open(f"http://127.0.0.1:{port}/")

app = Flask(__name__)
app.config["ASSET_VERSION"] = "1.0"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")  # Use env var in production
socketio = SocketIO(app, cors_allowed_origins="*")
online_users = set()

@app.context_processor
def inject_online_users():
    return {"online_users": online_users}

def generate_csrf_token():
    """Generate a CSRF token for the session."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]

def validate_csrf_token():
    """Validate CSRF token from request. Returns True if valid, False otherwise."""
    if request.method == "GET":
        return True

    token = session.get("_csrf_token")
    if not token:
        return False

    # Check token from form data or headers
    form_token = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
    if not form_token:
        return False

    # Simple timing-safe comparison
    return secrets.compare_digest(form_token, token)

@app.context_processor
def inject_csrf_token():
    return {"csrf_token": generate_csrf_token()}

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def add_column_if_missing(table, column_name, column_def):
    db = get_db()
    columns = [row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()]
    if column_name not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")

def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            telefone TEXT,
            cidade TEXT,
            tipo TEXT NOT NULL,
            bio TEXT,
            especialidade TEXT,
            empresa_nome TEXT,
            estado TEXT,
            bairro TEXT,
            cpf TEXT,
            documento TEXT,
            foto_perfil TEXT,
            cnpj TEXT,
            documento_empresa TEXT,
            logo_empresa TEXT,
            approval_status TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            profissional_id INTEGER,
            categoria TEXT,
            descricao TEXT,
            status TEXT,
            valor REAL,
            data_solicitacao TEXT,
            FOREIGN KEY(cliente_id) REFERENCES usuarios(id),
            FOREIGN KEY(profissional_id) REFERENCES usuarios(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            profissional_id INTEGER,
            nota INTEGER,
            comentario TEXT,
            servico_id INTEGER,
            FOREIGN KEY(cliente_id) REFERENCES usuarios(id),
            FOREIGN KEY(profissional_id) REFERENCES usuarios(id),
            FOREIGN KEY(servico_id) REFERENCES servicos(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS favoritos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            profissional_id INTEGER,
            FOREIGN KEY(cliente_id) REFERENCES usuarios(id),
            FOREIGN KEY(profissional_id) REFERENCES usuarios(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            servico_id INTEGER,
            remetente_id INTEGER,
            mensagem TEXT,
            criado_em TEXT,
            FOREIGN KEY(servico_id) REFERENCES servicos(id),
            FOREIGN KEY(remetente_id) REFERENCES usuarios(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS disponibilidade (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profissional_id INTEGER,
            dia_semana TEXT,
            horario_inicio TEXT,
            horario_fim TEXT,
            FOREIGN KEY(profissional_id) REFERENCES usuarios(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS servicos_empresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            titulo TEXT,
            descricao TEXT,
            valor REAL,
            FOREIGN KEY(empresa_id) REFERENCES usuarios(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS conversas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS conversa_participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversa_id INTEGER,
            usuario_id INTEGER,
            FOREIGN KEY(conversa_id) REFERENCES conversas(id),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS conversa_mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversa_id INTEGER,
            remetente_id INTEGER,
            mensagem TEXT,
            criado_em TEXT,
            lida INTEGER DEFAULT 0,
            FOREIGN KEY(conversa_id) REFERENCES conversas(id),
            FOREIGN KEY(remetente_id) REFERENCES usuarios(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
        """
    )
    add_column_if_missing("usuarios", "bio", "bio TEXT")
    add_column_if_missing("usuarios", "especialidade", "especialidade TEXT")
    add_column_if_missing("usuarios", "empresa_nome", "empresa_nome TEXT")
    add_column_if_missing("usuarios", "estado", "estado TEXT")
    add_column_if_missing("usuarios", "bairro", "bairro TEXT")
    add_column_if_missing("usuarios", "cpf", "cpf TEXT")
    add_column_if_missing("usuarios", "documento", "documento TEXT")
    add_column_if_missing("usuarios", "foto_perfil", "foto_perfil TEXT")
    add_column_if_missing("usuarios", "cnpj", "cnpj TEXT")
    add_column_if_missing("usuarios", "documento_empresa", "documento_empresa TEXT")
    add_column_if_missing("usuarios", "logo_empresa", "logo_empresa TEXT")
    add_column_if_missing("usuarios", "approval_status", "approval_status TEXT")
    add_column_if_missing("usuarios", "status_online", "status_online TEXT DEFAULT 'offline'")
    add_column_if_missing("usuarios", "ultimo_acesso", "ultimo_acesso TEXT")
    add_column_if_missing("usuarios", "deletion_requested", "deletion_requested INTEGER DEFAULT 0")
    add_column_if_missing("usuarios", "rejection_reason", "rejection_reason TEXT")
    add_column_if_missing("servicos", "status", "status TEXT")
    add_column_if_missing("servicos", "valor", "valor REAL")
    add_column_if_missing("servicos", "data_solicitacao", "data_solicitacao TEXT")
    add_column_if_missing("avaliacoes", "servico_id", "servico_id INTEGER")
    db.commit()

    admin = db.execute("SELECT * FROM usuarios WHERE email = ?", (ADMIN_EMAIL,)).fetchone()
    if not admin:
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status) VALUES (?, ?, ?, ?, ?)",
            (
                "Admin Zenvix",
                ADMIN_EMAIL,
                generate_password_hash(ADMIN_PASSWORD),
                ADMIN_USER_TYPE,
                "Ativo",
            ),
        )
        db.commit()
    elif (
        admin["tipo"] != ADMIN_USER_TYPE
        or (admin["approval_status"] or "Ativo") != "Ativo"
        or not check_password_hash(admin["senha"], ADMIN_PASSWORD)
    ):
        db.execute(
            "UPDATE usuarios SET nome = ?, senha = ?, tipo = ?, approval_status = ? WHERE id = ?",
            ("Admin Zenvix", generate_password_hash(ADMIN_PASSWORD), ADMIN_USER_TYPE, "Ativo", admin["id"]),
        )
        db.commit()

# Ensures schema migrations and the default administrator exist for Flask, WSGI and tests.
with app.app_context():
    init_db()

def query_user_by_email(email):
    db = get_db()
    return db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()

def get_user_by_id(user_id):
    db = get_db()
    return db.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()

def is_provider_active(user):
    return bool(
        user
        and user["tipo"] in ("profissional", "empresa")
        and (user["approval_status"] or "Ativo") == "Ativo"
    )

def get_pending_users():
    db = get_db()
    return db.execute(
        "SELECT * FROM usuarios WHERE tipo IN ('profissional', 'empresa') AND approval_status = 'Pendente' ORDER BY tipo, nome"
    ).fetchall()

def get_provider_rating(provider_id):
    db = get_db()
    row = db.execute(
        "SELECT AVG(nota) AS avg_rating, COUNT(*) AS total FROM avaliacoes WHERE profissional_id = ?",
        (provider_id,),
    ).fetchone()
    avg_rating = row["avg_rating"]
    return (round(avg_rating, 1), row["total"]) if avg_rating is not None else (None, row["total"])

# BEGIN CHANGE

def get_provider_recommendation_score(provider, requested_category=None):
    requested_category = (requested_category or "").strip().lower()
    rating = provider.get("rating") or 0.0
    rating_count = provider.get("rating_count") or 0
    availability_count = provider.get("availability_count") or 0
    completed_services = provider.get("completed_services") or 0
    online_bonus = 6 if provider.get("online") else 0
    category_bonus = 0

    if requested_category:
        specialty = (provider.get("especialidade") or "").lower()
        if requested_category in specialty:
            category_bonus = 20

    score = (
        (rating * 10)
        + min(rating_count * 4, 30)
        + min(availability_count * 8, 24)
        + min(completed_services * 0.4, 12)
        + online_bonus
        + category_bonus
    )
    return round(score, 2)

# END CHANGE

def get_providers(search=None, category=None, city=None, online_only=False):
    db = get_db()
    db.execute(
        "UPDATE usuarios SET status_online = 'offline' WHERE status_online = 'online' AND ultimo_acesso < datetime('now', '-5 minutes')"
    )
    db.commit()
    query = """
        SELECT *,
        CASE WHEN status_online = 'online' AND ultimo_acesso >= datetime('now', '-5 minutes') THEN 1 ELSE 0 END AS online
        FROM usuarios
        WHERE tipo IN ('profissional', 'empresa') AND (approval_status = 'Ativo' OR approval_status IS NULL)
    """
    filters = []
    params = []

    if search:
        like_value = f"%{search}%"
        filters.append("(nome LIKE ? OR especialidade LIKE ? OR empresa_nome LIKE ? OR bio LIKE ? OR cidade LIKE ?)")
        params.extend([like_value] * 5)

    if category:
        filters.append("especialidade LIKE ?")
        params.append(f"%{category}%")

    if city:
        filters.append("cidade LIKE ?")
        params.append(f"%{city}%")

    if online_only:
        filters.append("status_online = 'online' AND ultimo_acesso >= datetime('now', '-5 minutes')")

    if filters:
        query += " AND " + " AND ".join(filters)

    return db.execute(query, tuple(params)).fetchall()

def enrich_provider(provider):
    rating, rating_count = get_provider_rating(provider["id"])
    db = get_db()
    completed_services = db.execute(
        "SELECT COUNT(*) AS total FROM servicos WHERE profissional_id = ? AND status = 'Concluído'",
        (provider["id"],),
    ).fetchone()["total"]
    availability = get_availability_for_user(provider["id"])
    online = provider["online"] if "online" in provider.keys() else db.execute(
        "SELECT CASE WHEN status_online = 'online' AND ultimo_acesso >= datetime('now', '-5 minutes') THEN 1 ELSE 0 END AS online FROM usuarios WHERE id = ?",
        (provider["id"],),
    ).fetchone()["online"]
    provider_data = {**dict(provider), "rating": rating, "rating_count": rating_count, "completed_services": completed_services, "online": bool(online), "availability_count": len(availability)}
    provider_data["recommendation_score"] = get_provider_recommendation_score(provider_data)
    return provider_data

def get_online_providers(limit=None):
    providers = [enrich_provider(provider) for provider in get_providers(online_only=True)]
    return providers[:limit] if limit else providers

def get_service_by_id(service_id):
    db = get_db()
    return db.execute(
        """
        SELECT s.*, c.nome AS cliente_nome, p.nome AS profissional_nome, p.tipo AS profissional_tipo, c.cidade AS cliente_cidade
        FROM servicos s
        LEFT JOIN usuarios c ON s.cliente_id = c.id
        LEFT JOIN usuarios p ON s.profissional_id = p.id
        WHERE s.id = ?
        """,
        (service_id,),
    ).fetchone()

def get_favorite_providers(client_id):
    db = get_db()
    rows = db.execute(
        """
        SELECT u.*, AVG(a.nota) AS rating, COUNT(a.id) AS rating_count
        FROM favoritos f
        JOIN usuarios u ON f.profissional_id = u.id
        LEFT JOIN avaliacoes a ON u.id = a.profissional_id
        WHERE f.cliente_id = ?
        GROUP BY u.id
        """,
        (client_id,),
    ).fetchall()
    return rows

def get_user_review_count(user_id):
    db = get_db()
    row = db.execute("SELECT COUNT(*) AS total FROM avaliacoes WHERE cliente_id = ?", (user_id,)).fetchone()
    return row["total"] if row else 0

def get_messages_for_service(service_id):
    db = get_db()
    return db.execute(
        """
        SELECT m.*, u.nome AS sender_name, u.telefone AS sender_phone
        FROM mensagens m
        JOIN usuarios u ON m.remetente_id = u.id
        WHERE m.servico_id = ?
        ORDER BY m.id ASC
        """,
        (service_id,),
    ).fetchall()

def get_availability_for_user(user_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM disponibilidade WHERE profissional_id = ? ORDER BY id DESC",
        (user_id,),
    ).fetchall()

def get_company_services(company_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM servicos_empresa WHERE empresa_id = ? ORDER BY id DESC",
        (company_id,),
    ).fetchall()

def get_categories():
    db = get_db()
    return db.execute("SELECT * FROM categorias ORDER BY nome").fetchall()

def get_all_users():
    db = get_db()
    return db.execute("SELECT * FROM usuarios ORDER BY tipo, nome").fetchall()

def get_system_metrics():
    db = get_db()
    total_users = db.execute("SELECT COUNT(*) AS total FROM usuarios").fetchone()["total"]
    active_providers = db.execute(
        "SELECT COUNT(*) AS total FROM usuarios WHERE tipo IN ('profissional', 'empresa') AND approval_status = 'Ativo'"
    ).fetchone()["total"]
    company_count = db.execute("SELECT COUNT(*) AS total FROM usuarios WHERE tipo = 'empresa'").fetchone()["total"]
    completed_services = db.execute("SELECT COUNT(*) AS total FROM servicos WHERE status = 'Concluído'").fetchone()["total"]
    return {
        "total_users": total_users,
        "active_providers": active_providers,
        "company_count": company_count,
        "completed_services": completed_services,
    }

def get_services_for_user(user_id, user_type):
    db = get_db()
    if user_type == "cliente":
        return db.execute(
            """
            SELECT s.*, u.nome AS profissional_nome, u.tipo AS profissional_tipo
            FROM servicos s
            LEFT JOIN usuarios u ON s.profissional_id = u.id
            WHERE s.cliente_id = ?
            ORDER BY s.id DESC
            """,
            (user_id,),
        ).fetchall()

    return db.execute(
        """
        SELECT s.*,
               cliente.nome AS cliente_nome,
               cliente.tipo AS cliente_tipo,
               cliente.cidade AS cliente_cidade,
               profissional.nome AS profissional_nome,
               profissional.tipo AS profissional_tipo
        FROM servicos s
        LEFT JOIN usuarios cliente ON s.cliente_id = cliente.id
        LEFT JOIN usuarios profissional ON s.profissional_id = profissional.id
        WHERE s.profissional_id = ? OR s.cliente_id = ?
        ORDER BY s.id DESC
        """,
        (user_id, user_id),
    ).fetchall()

def get_chat_conversations_for_user(user_id):
    db = get_db()
    rows = db.execute(
        """
        SELECT s.id AS service_id,
               CASE
                   WHEN s.cliente_id = ? THEN profissional.nome
                   ELSE cliente.nome
               END AS participant_name,
               CASE
                   WHEN s.cliente_id = ? THEN profissional.telefone
                   ELSE cliente.telefone
               END AS participant_phone,
               COALESCE(s.categoria, s.descricao, 'Solicitação') AS service_label,
               COUNT(m.id) AS message_count,
               MAX(m.criado_em) AS last_message_time
        FROM servicos s
        LEFT JOIN usuarios cliente ON s.cliente_id = cliente.id
        LEFT JOIN usuarios profissional ON s.profissional_id = profissional.id
        LEFT JOIN mensagens m ON m.servico_id = s.id
        WHERE s.cliente_id = ? OR s.profissional_id = ?
        GROUP BY s.id
        ORDER BY last_message_time DESC
        """,
        (user_id, user_id, user_id, user_id),
    ).fetchall()

    conversations = []
    for row in rows:
        last_message = db.execute(
            "SELECT mensagem FROM mensagens WHERE servico_id = ? ORDER BY id DESC LIMIT 1",
            (row["service_id"],),
        ).fetchone()
        conversations.append({
            "service_id": row["service_id"],
            "participant_name": row["participant_name"] or "Participante",
            "participant_phone": row["participant_phone"],
            "service_label": row["service_label"] or "Solicitação",
            "last_message": last_message["mensagem"] if last_message else "Sem mensagens",
            "last_message_time": row["last_message_time"] or "—",
            "message_count": row["message_count"] or 0,
        })

    return conversations

def get_all_chat_conversations():
    db = get_db()
    rows = db.execute(
        """
        SELECT s.id AS service_id,
               cliente.nome AS cliente_name,
               cliente.telefone AS cliente_phone,
               profissional.nome AS profissional_name,
               profissional.telefone AS profissional_phone,
               COALESCE(s.categoria, s.descricao, 'Solicitação') AS service_label,
               COUNT(m.id) AS message_count,
               MAX(m.criado_em) AS last_message_time
        FROM servicos s
        LEFT JOIN usuarios cliente ON s.cliente_id = cliente.id
        LEFT JOIN usuarios profissional ON s.profissional_id = profissional.id
        LEFT JOIN mensagens m ON m.servico_id = s.id
        GROUP BY s.id
        ORDER BY last_message_time DESC
        """
    ).fetchall()

    conversations = []
    for row in rows:
        last_message = db.execute(
            "SELECT mensagem FROM mensagens WHERE servico_id = ? ORDER BY id DESC LIMIT 1",
            (row["service_id"],),
        ).fetchone()
        conversations.append({
            "service_id": row["service_id"],
            "participant_name": f"{row['cliente_name'] or 'Cliente'} / {row['profissional_name'] or 'Profissional'}",
            "participant_phone": f"{row['cliente_phone'] or '—'} / {row['profissional_phone'] or '—'}",
            "service_label": row["service_label"] or "Solicitação",
            "last_message": last_message["mensagem"] if last_message else "Sem mensagens",
            "last_message_time": row["last_message_time"] or "—",
            "message_count": row["message_count"] or 0,
        })

    return conversations

def get_conversation_for_participants(user_id, other_user_id):
    db = get_db()
    rows = db.execute(
        """
        SELECT cp.conversa_id
        FROM conversa_participantes cp
        WHERE cp.usuario_id IN (?, ?)
        GROUP BY cp.conversa_id
        HAVING COUNT(DISTINCT cp.usuario_id) = 2
        """,
        (user_id, other_user_id),
    ).fetchall()

    for row in rows:
        participants = [
            participant["usuario_id"]
            for participant in db.execute(
                "SELECT usuario_id FROM conversa_participantes WHERE conversa_id = ?",
                (row["conversa_id"],),
            ).fetchall()
        ]
        if {user_id, other_user_id}.issubset(set(participants)):
            return row["conversa_id"]
    return None

def get_conversation_messages(conversation_id):
    db = get_db()
    return db.execute(
        """
        SELECT cm.*, u.nome AS sender_name, u.tipo AS sender_type
        FROM conversa_mensagens cm
        LEFT JOIN usuarios u ON cm.remetente_id = u.id
        WHERE cm.conversa_id = ?
        ORDER BY cm.id ASC
        """,
        (conversation_id,),
    ).fetchall()

def get_unread_conversation_count(conversation_id, user_id):
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) AS total FROM conversa_mensagens WHERE conversa_id = ? AND remetente_id != ? AND lida = 0",
        (conversation_id, user_id),
    ).fetchone()
    return row["total"] if row else 0

def mark_conversation_messages_read(conversation_id, user_id):
    db = get_db()
    db.execute(
        "UPDATE conversa_mensagens SET lida = 1 WHERE conversa_id = ? AND remetente_id != ? AND lida = 0",
        (conversation_id, user_id),
    )
    db.commit()

@app.route("/conversar/<int:partner_id>")
def iniciar_conversa(partner_id):
    if "user_id" not in session:
        flash("Faça login para conversar com este usuário.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    if partner_id == user_id:
        flash("Você não pode iniciar uma conversa consigo mesmo.", "error")
        return redirect(url_for("dashboard"))

    partner = get_user_by_id(partner_id)
    if not partner:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for("profissionais"))

    # Validate partner eligibility
    if partner["approval_status"] != "Ativo":
        flash("Este usuário não está disponível para conversas.", "error")
        return redirect(url_for("profissionais"))

    user = get_user_by_id(user_id)
    # Clients cannot talk with other clients
    if user["tipo"] == "cliente" and partner["tipo"] == "cliente":
        flash("Clientes não podem conversar entre si.", "error")
        return redirect(url_for("profissionais"))

    conversation_id = get_conversation_for_participants(user_id, partner_id)
    if conversation_id is None:
        db = get_db()
        cursor = db.execute("INSERT INTO conversas (criado_em) VALUES (datetime('now'))")
        conversation_id = cursor.lastrowid
        db.execute("INSERT INTO conversa_participantes (conversa_id, usuario_id) VALUES (?, ?)", (conversation_id, user_id))
        db.execute("INSERT INTO conversa_participantes (conversa_id, usuario_id) VALUES (?, ?)", (conversation_id, partner_id))
        db.commit()
        flash("Conversa iniciada. Você pode trocar mensagens antes da contratação.", "success")

    return redirect(url_for("visualizar_conversa", conversation_id=conversation_id))

@app.route("/conversa/<int:conversation_id>", methods=["GET", "POST"])
def visualizar_conversa(conversation_id):
    if "user_id" not in session:
        flash("Faça login para acessar a conversa.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    db = get_db()
    participant = db.execute(
        "SELECT 1 FROM conversa_participantes WHERE conversa_id = ? AND usuario_id = ?",
        (conversation_id, user_id),
    ).fetchone()
    if not participant:
        flash("Você não tem acesso a esta conversa.", "error")
        return redirect(url_for("dashboard"))

    conversation = db.execute("SELECT * FROM conversas WHERE id = ?", (conversation_id,)).fetchone()
    if not conversation:
        flash("Conversa não encontrada.", "error")
        return redirect(url_for("dashboard"))

    participants = [
        row["usuario_id"]
        for row in db.execute(
            "SELECT usuario_id FROM conversa_participantes WHERE conversa_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
    ]
    other_user_id = next((item for item in participants if item != user_id), None)
    partner = get_user_by_id(other_user_id) if other_user_id else None

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Token de segurança inválido. Tente novamente.", "error")
            return redirect(url_for("visualizar_conversa", conversation_id=conversation_id))

        mensagem = request.form.get("mensagem", "").strip()
        if not mensagem:
            flash("Escreva uma mensagem para enviar.", "error")
            return redirect(url_for("visualizar_conversa", conversation_id=conversation_id))

        db.execute(
            "INSERT INTO conversa_mensagens (conversa_id, remetente_id, mensagem, criado_em, lida) VALUES (?, ?, ?, datetime('now'), 0)",
            (conversation_id, user_id, mensagem),
        )
        db.commit()

        sender = get_user_by_id(user_id)
        payload = {
            "conversation_id": conversation_id,
            "remetente_id": user_id,
            "usuario": sender["nome"] if sender else "Usuário",
            "mensagem": mensagem,
            "criado_em": "Agora",
        }
        socketio.emit("nova_mensagem_conversa", payload, room=f"conversation_{conversation_id}")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": True, "payload": payload})

        return redirect(url_for("visualizar_conversa", conversation_id=conversation_id))

    unread_count = get_unread_conversation_count(conversation_id, user_id)
    mark_conversation_messages_read(conversation_id, user_id)
    messages = get_conversation_messages(conversation_id)

    return render_template(
        "conversa.html",
        conversation=conversation,
        partner=partner,
        messages=messages,
        unread_count=unread_count,
    )

@app.route("/chat", strict_slashes=False)
@app.route("/chat/", strict_slashes=False)
def chat_index():
    if "user_id" not in session:
        flash("Faça login para acessar o chat.", "error")
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])
    if not user:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for("login"))

    if session.get("user_type") == ADMIN_USER_TYPE:
        service_conversations = get_all_chat_conversations()
        services = []
        admin_view = True
    else:
        service_conversations = get_chat_conversations_for_user(session["user_id"])
        services = get_services_for_user(session["user_id"], user["tipo"])
        admin_view = False

    return render_template(
        "chat/index.html",
        user=user,
        service_conversations=service_conversations,
        services=services,
        admin_view=admin_view,
    )

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file_storage):
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        return None
    filename = secure_filename(file_storage.filename)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file_storage.save(filepath)
    return filename

def user_has_reviewed_service(service_id):
    db = get_db()
    row = db.execute("SELECT id FROM avaliacoes WHERE servico_id = ?", (service_id,)).fetchone()
    return row is not None

@app.before_request
def before_request():
    get_db()
    if session.get("user_id"):
        user = get_user_by_id(session["user_id"])
        if user:
            db = get_db()
            db.execute(
                "UPDATE usuarios SET status_online = 'online', ultimo_acesso = datetime('now') WHERE id = ?",
                (user["id"],),
            )
            db.commit()
            # Ensure consistency between memory and DB
            online_users.add(user["id"])
            session["approval_status"] = user["approval_status"] or "Ativo"
            session["user_name"] = user["nome"]
            session["user_type"] = user["tipo"]

@app.teardown_appcontext
def teardown_appcontext(exception):
    close_db(exception)

@app.route("/")
def home():
    featured_providers = [enrich_provider(provider) for provider in get_providers()[:3]]
    online_providers = get_online_providers(limit=4)
    return render_template(
        "public/home.html",
        featured_providers=featured_providers,
        online_providers=online_providers,
    )

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        if not validate_csrf_token():
            flash("Token de segurança inválido. Tente novamente.", "error")
            return render_template("auth/cadastro.html")

        tipo = request.form.get("tipo", "cliente")
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirm_senha = request.form.get("confirm_senha", "")
        telefone = request.form.get("telefone", "").strip()
        estado = request.form.get("estado", "").strip()
        cidade = request.form.get("cidade", "").strip()
        bairro = request.form.get("bairro", "").strip()
        bio = request.form.get("bio", "").strip()
        especialidade = request.form.get("especialidade", "").strip()
        cpf = request.form.get("cpf", "").strip()
        empresa_nome = request.form.get("empresa_nome", "").strip()
        cnpj = request.form.get("cnpj", "").strip()

        documento = request.files.get("documento")
        documento_empresa = request.files.get("documento_empresa")
        foto_perfil_file = request.files.get("foto_perfil")
        logo_empresa_file = request.files.get("logo_empresa")

        form_data = {
            "tipo": tipo,
            "nome": nome,
            "email": email,
            "telefone": telefone,
            "estado": estado,
            "cidade": cidade,
            "bairro": bairro,
            "bio": bio,
            "especialidade": especialidade,
            "cpf": cpf,
            "empresa_nome": empresa_nome,
            "cnpj": cnpj,
        }
        current_step = 2

        if not nome or not email or not senha or not confirm_senha:
            flash("Preencha os dados obrigatórios da conta.", "error")
            return render_template("auth/cadastro.html", form_data=form_data, tipo=tipo, current_step=current_step)

        if "@" not in email or "." not in email:
            flash("Informe um e-mail válido.", "error")
            return render_template("auth/cadastro.html", form_data=form_data, tipo=tipo, current_step=current_step)

        if senha != confirm_senha:
            flash("As senhas não conferem.", "error")
            return render_template("auth/cadastro.html", form_data=form_data, tipo=tipo, current_step=current_step)

        if query_user_by_email(email):
            flash("Este e-mail já está em uso. Faça login ou use outro e-mail.", "error")
            return render_template("auth/cadastro.html", form_data=form_data, tipo=tipo, current_step=current_step)

        if tipo == "cliente":
            if not estado or not cidade or not telefone:
                current_step = 3
                flash("Preencha estado, cidade e telefone para finalizar seu cadastro.", "error")
                return render_template("auth/cadastro.html", form_data=form_data, tipo=tipo, current_step=current_step)
            approval_status = "Ativo"
            cpf = None
            cnpj = None
            documento = None
            documento_empresa = None
        elif tipo == "profissional":
            if not estado or not cidade or not telefone or not especialidade or not bio or not cpf:
                current_step = 3
                flash("Preencha todos os dados profissionais obrigatórios.", "error")
                return render_template("auth/cadastro.html", form_data=form_data, tipo=tipo, current_step=current_step)
            approval_status = "Pendente"
            empresa_nome = None
            cnpj = None
            documento_empresa = None
        else:
            if not empresa_nome or not estado or not cidade or not telefone or not cnpj:
                current_step = 3
                flash("Preencha todos os dados da empresa obrigatórios.", "error")
                return render_template("auth/cadastro.html", form_data=form_data, tipo=tipo, current_step=current_step)
            approval_status = "Pendente"
            cpf = None
            documento = None

        if foto_perfil_file and foto_perfil_file.filename != "" and not allowed_file(foto_perfil_file.filename):
            current_step = 3
            flash("Envie a foto de perfil em PDF, JPG ou PNG.", "error")
            return render_template("auth/cadastro.html", form_data=form_data, tipo=tipo, current_step=current_step)
        if logo_empresa_file and logo_empresa_file.filename != "" and not allowed_file(logo_empresa_file.filename):
            current_step = 3
            flash("Envie o logo da empresa em PDF, JPG ou PNG.", "error")
            return render_template("auth/cadastro.html", form_data=form_data, tipo=tipo, current_step=current_step)

        if documento:
            documento_filename = save_uploaded_file(documento)
        else:
            documento_filename = None
        if documento_empresa:
            documento_empresa_filename = save_uploaded_file(documento_empresa)
        else:
            documento_empresa_filename = None
        if foto_perfil_file:
            foto_perfil = save_uploaded_file(foto_perfil_file)
        else:
            foto_perfil = None
        if logo_empresa_file:
            logo_empresa = save_uploaded_file(logo_empresa_file)
        else:
            logo_empresa = None

        senha_segura = generate_password_hash(senha)
        db = get_db()
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, telefone, cidade, tipo, bio, especialidade, empresa_nome, estado, bairro, cpf, documento, foto_perfil, cnpj, documento_empresa, logo_empresa, approval_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                nome,
                email,
                senha_segura,
                telefone,
                cidade,
                tipo,
                bio,
                especialidade,
                empresa_nome,
                estado,
                bairro,
                cpf,
                documento_filename,
                foto_perfil,
                cnpj,
                documento_empresa_filename,
                logo_empresa,
                approval_status,
            ),
        )
        db.commit()

        if tipo == "cliente":
            user_id = db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()["id"]
            session.clear()
            session["user_id"] = user_id
            session["user_name"] = nome
            session["user_type"] = tipo
            session["approval_status"] = approval_status
            online_users.add(user_id)
            db.execute("UPDATE usuarios SET status_online = 'online', ultimo_acesso = datetime('now') WHERE id = ?", (user_id,))
            db.commit()
            flash("Cadastro concluído com sucesso! Bem-vindo ao Zenvix Connect.", "success")
            return redirect(url_for("dashboard"))

        flash("Seu cadastro foi enviado com sucesso. Aguarde aprovação para acessar o dashboard.", "success")
        return redirect(url_for("login"))

    return render_template("auth/cadastro.html", form_data={}, tipo="cliente", current_step=1)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not validate_csrf_token():
            flash("Token de segurança inválido. Tente novamente.", "error")
            return render_template("auth/login.html")

        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not email or not senha:
            flash("Informe e-mail e senha para acessar.", "error")
            return render_template("auth/login.html")

        user = query_user_by_email(email)
        if not user or not check_password_hash(user["senha"], senha):
            flash("E-mail ou senha inválidos.", "error")
            return render_template("auth/login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["nome"]
        session["user_type"] = user["tipo"]
        session["approval_status"] = user["approval_status"] or "Ativo"
        online_users.add(user["id"])
        db = get_db()
        db.execute(
            "UPDATE usuarios SET status_online = 'online', ultimo_acesso = datetime('now') WHERE id = ?",
            (user["id"],),
        )
        db.commit()
        flash(f"Bem-vindo(a), {user['nome']}!", "success")

        if user["tipo"] == ADMIN_USER_TYPE:
            return redirect(url_for("admin_panel"))

        if user["tipo"] in ("profissional", "empresa") and user["approval_status"] == "Pendente":
            flash("Conta pendente. Aguarde aprovação para acessar todas as funcionalidades.", "info")

        if user["tipo"] == "cliente":
            return redirect(url_for("dashboard_cliente"))
        if user["tipo"] == "profissional":
            return redirect(url_for("dashboard_profissional"))
        if user["tipo"] == "empresa":
            return redirect(url_for("dashboard_empresa"))

        return redirect(url_for("dashboard"))

    return render_template("auth/login.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Informe seu e-mail para receber as instruções.", "error")
            return render_template("forgot_password.html")

        query_user_by_email(email)
        flash("Se o e-mail estiver cadastrado, enviaremos instruções de recuperação em breve.", "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")

@app.route("/logout")
def logout():
    if session.get("user_id"):
        user_id = session["user_id"]
        online_users.discard(user_id)
        db = get_db()
        db.execute("UPDATE usuarios SET status_online = 'offline' WHERE id = ?", (user_id,))
        db.commit()
    session.clear()
    flash("Você saiu da sessão.", "success")
    return redirect(url_for("home"))

@app.route("/presenca/heartbeat", methods=["POST"])
def presence_heartbeat():
    if not session.get("user_id"):
        return {"authenticated": False}, 401
    db = get_db()
    db.execute(
        "UPDATE usuarios SET status_online = 'online', ultimo_acesso = datetime('now') WHERE id = ?",
        (session["user_id"],),
    )
    db.commit()
    return {"authenticated": True, "online": True}

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Faça login para acessar seu painel.", "error")
        return redirect(url_for("login"))

    user_type = session["user_type"]
    if user_type == "cliente":
        return redirect(url_for("dashboard_cliente"))
    if user_type == "profissional":
        return redirect(url_for("dashboard_profissional"))
    if user_type == "empresa":
        return redirect(url_for("dashboard_empresa"))
    if user_type == ADMIN_USER_TYPE:
        return redirect(url_for("admin_panel"))

    return redirect(url_for("home"))

@app.route("/admin")
def admin_panel():
    if "user_id" not in session or session.get("user_type") != ADMIN_USER_TYPE:
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for("login"))

    pending_users = get_pending_users()
    metrics = get_system_metrics()
    all_users = get_all_users()
    categories = get_categories()
    return render_template(
        "admin/dashboard.html",
        pending_users=pending_users,
        metrics=metrics,
        all_users=all_users,
        categories=categories,
    )

@app.route("/admin/documento/<int:user_id>/<document_type>")
def admin_view_document(user_id, document_type):
    if "user_id" not in session or session.get("user_type") != ADMIN_USER_TYPE:
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for("login"))

    field = {"profissional": "documento", "empresa": "documento_empresa"}.get(document_type)
    user = get_user_by_id(user_id)
    filename = user[field] if user and field else None
    if not filename:
        flash("Nenhum documento foi enviado para este cadastro.", "info")
        return redirect(url_for("admin_panel"))

    return send_from_directory(UPLOAD_FOLDER, os.path.basename(filename), as_attachment=False)

@app.route("/admin/aprovar-usuario/<int:user_id>", methods=["POST"])
def admin_approve_user(user_id):
    if not validate_csrf_token():
        flash("Token de segurança inválido. Tente novamente.", "error")
        return redirect(url_for("admin_panel"))

    if "user_id" not in session or session.get("user_type") != ADMIN_USER_TYPE:
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if not user or user["tipo"] not in ("profissional", "empresa"):
        flash("Usuário inválido.", "error")
        return redirect(url_for("admin_panel"))

    db = get_db()
    db.execute("UPDATE usuarios SET approval_status = 'Ativo' WHERE id = ?", (user_id,))
    db.commit()
    flash("Usuário aprovado com sucesso.", "success")
    return redirect(url_for("admin_panel"))

@app.route("/dashboard-cliente")
def dashboard_cliente():
    if "user_id" not in session:
        flash("Faça login para acessar seu painel.", "error")
        return redirect(url_for("login"))
    if session.get("user_type") != "cliente":
        flash("Acesso restrito ao painel de cliente.", "error")
        return redirect(url_for("dashboard"))

    user_id = session["user_id"]
    user = get_user_by_id(user_id)
    services = get_services_for_user(user_id, "cliente")

    pending_requests = [service for service in services if service["status"] == "Pendente"]
    active_services = [service for service in services if service["status"] in ("Aceito", "Em andamento")]
    history_services = [service for service in services if service["status"] == "Concluído"]
    for service in history_services:
        service["reviewed"] = user_has_reviewed_service(service["id"])

    favorites = get_favorite_providers(user_id)
    review_count = get_user_review_count(user_id)
    online_providers = get_online_providers()
    online_professionals = [provider for provider in online_providers if provider["tipo"] == "profissional"][:3]
    online_companies = [provider for provider in online_providers if provider["tipo"] == "empresa"][:3]

    return render_template(
        "cliente/dashboard.html",
        user=user,
        total_services=len(services),
        in_progress_services=len(active_services),
        completed_services=len(history_services),
        review_count=review_count,
        pending_requests=pending_requests,
        active_services=active_services,
        history_services=history_services,
        favorites=favorites,
        online_professionals=online_professionals,
        online_companies=online_companies,
    )

@app.route("/dashboard-profissional")
def dashboard_profissional():
    if "user_id" not in session:
        flash("Faça login para acessar seu painel.", "error")
        return redirect(url_for("login"))
    if session.get("user_type") != "profissional":
        flash("Acesso restrito ao painel de profissional.", "error")
        return redirect(url_for("dashboard"))

    user_id = session["user_id"]
    user = get_user_by_id(user_id)
    services = get_services_for_user(user_id, "profissional")
    pending_requests = [service for service in services if service["status"] == "Pendente"]
    accepted_services = [service for service in services if service["status"] == "Aceito"]
    in_progress_services = [service for service in services if service["status"] == "Em andamento"]
    active_services = [service for service in services if service["status"] in ("Aceito", "Em andamento")]
    completed_services = [service for service in services if service["status"] == "Concluído"]
    rating, _ = get_provider_rating(user_id)
    availability = get_availability_for_user(user_id)
    earnings = sum(service["valor"] or 0 for service in completed_services if service["valor"])
    commission = round(earnings * 0.2, 2)

    return render_template(
        "profissional/dashboard.html",
        user=user,
        approval_status=user["approval_status"] or "Ativo",
        pending_requests=pending_requests,
        accepted_services=accepted_services,
        active_services=active_services,
        in_progress_services=in_progress_services,
        completed_services=completed_services,
        rating=rating,
        availability=availability,
        earnings=round(earnings, 2),
        commission=commission,
        online_now=True,
    )

@app.route("/dashboard-empresa")
def dashboard_empresa():
    if "user_id" not in session:
        flash("Faça login para acessar seu painel.", "error")
        return redirect(url_for("login"))
    if session.get("user_type") != "empresa":
        flash("Acesso restrito ao painel de empresa.", "error")
        return redirect(url_for("dashboard"))

    user_id = session["user_id"]
    user = get_user_by_id(user_id)
    services = get_services_for_user(user_id, "empresa")
    company_services = get_company_services(user_id)
    completed_services = sum(1 for service in services if service["status"] == "Concluído")
    in_progress_services = sum(1 for service in services if service["status"] == "Em andamento")
    total_requests = len(services)
    rating, _ = get_provider_rating(user_id)
    categories = get_categories()

    return render_template(
        "empresa/dashboard.html",
        user=user,
        approval_status=user["approval_status"] or "Ativo",
        company_services=company_services,
        company_requests=services,
        total_requests=total_requests,
        completed_services=completed_services,
        in_progress_services=in_progress_services,
        rating=rating,
        categories=categories,
        total_services=len(company_services),
        online_now=True,
    )

@app.route("/favorito/<int:provider_id>/toggle", methods=["POST"])
def toggle_favorite(provider_id):
    if not validate_csrf_token():
        flash("Token de segurança inválido. Tente novamente.", "error")
        return redirect(url_for("dashboard_cliente"))

    if "user_id" not in session or session.get("user_type") != "cliente":
        flash("Apenas clientes podem gerenciar favoritos.", "error")
        return redirect(url_for("dashboard_cliente"))

    client_id = session["user_id"]
    db = get_db()
    existing = db.execute(
        "SELECT id FROM favoritos WHERE cliente_id = ? AND profissional_id = ?",
        (client_id, provider_id),
    ).fetchone()
    if existing:
        db.execute("DELETE FROM favoritos WHERE id = ?", (existing["id"],))
        flash("Profissional removido dos favoritos.", "success")
    else:
        db.execute(
            "INSERT INTO favoritos (cliente_id, profissional_id) VALUES (?, ?)",
            (client_id, provider_id),
        )
        flash("Profissional adicionado aos favoritos.", "success")
    db.commit()
    return redirect(url_for("dashboard_cliente"))

@app.route("/servico/<int:service_id>/chat", methods=["GET", "POST"])
def servico_chat(service_id):
    if "user_id" not in session:
        flash("Faça login para acessar o chat.", "error")
        return redirect(url_for("login"))

    service = get_service_by_id(service_id)
    if not service:
        flash("Serviço não encontrado.", "error")
        return redirect(url_for("dashboard"))

    user_id = session["user_id"]
    if user_id not in (service["cliente_id"], service["profissional_id"]) and session.get("user_type") != ADMIN_USER_TYPE:
        flash("Sem permissão para acessar este chat.", "error")
        return redirect(url_for("dashboard"))

    client_user = get_user_by_id(service["cliente_id"])
    professional_user = get_user_by_id(service["profissional_id"])
    client_phone = client_user["telefone"] if client_user else None
    professional_phone = professional_user["telefone"] if professional_user else None

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Token de segurança inválido. Tente novamente.", "error")
            return redirect(url_for("servico_chat", service_id=service_id))

        mensagem = request.form.get("mensagem", "").strip()
        if mensagem:
            db = get_db()
            db.execute(
                "INSERT INTO mensagens (servico_id, remetente_id, mensagem, criado_em) VALUES (?, ?, ?, datetime('now'))",
                (service_id, user_id, mensagem),
            )
            db.commit()

            sender = get_user_by_id(user_id)
            payload = {
                "service_id": service_id,
                "remetente_id": user_id,
                "usuario": sender["nome"] if sender else "Usuário",
                "telefone": sender["telefone"] if sender else None,
                "mensagem": mensagem,
                "criado_em": "Agora",
            }

            socketio.emit("nova_mensagem", payload, room=f"service_{service_id}")

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": True, "payload": payload})

            return redirect(url_for("servico_chat", service_id=service_id))

    messages = get_messages_for_service(service_id)
    return render_template(
        "chat.html",
        service=service,
        messages=messages,
        client_phone=client_phone,
        professional_phone=professional_phone,
    )

@app.route("/admin/remover-usuario/<int:user_id>", methods=["POST"])
def admin_remove_user(user_id):
    if not validate_csrf_token():
        flash("Token de segurança inválido. Tente novamente.", "error")
        return redirect(url_for("admin_panel"))

    if "user_id" not in session or session.get("user_type") != ADMIN_USER_TYPE:
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for("login"))

    if user_id == session["user_id"]:
        flash("Você não pode remover seu próprio usuário.", "error")
        return redirect(url_for("admin_panel"))

    user = get_user_by_id(user_id)
    if not user:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for("admin_panel"))

    if user["tipo"] == ADMIN_USER_TYPE:
        flash("Não é permitido remover outro administrador.", "error")
        return redirect(url_for("admin_panel"))

    db = get_db()
    db.execute(
        "UPDATE usuarios SET approval_status = 'Removado', status_online = 'offline' WHERE id = ?",
        (user_id,),
    )
    db.commit()
    flash("Usuário removido com sucesso.", "success")
    return redirect(url_for("admin_panel"))

@app.route("/disponibilidade/adicionar", methods=["POST"])
def add_availability():
    if not validate_csrf_token():
        flash("Token de segurança inválido. Tente novamente.", "error")
        return redirect(url_for("dashboard_profissional"))

    if "user_id" not in session or session.get("user_type") != "profissional":
        flash("Apenas profissionais podem cadastrar disponibilidade.", "error")
        return redirect(url_for("dashboard_profissional"))

    dia_semana = request.form.get("dia_semana", "").strip()
    horario_inicio = request.form.get("horario_inicio", "").strip()
    horario_fim = request.form.get("horario_fim", "").strip()

    if not dia_semana or not horario_inicio or not horario_fim:
        flash("Preencha todos os campos da disponibilidade.", "error")
        return redirect(url_for("dashboard_profissional"))

    db = get_db()
    db.execute(
        "INSERT INTO disponibilidade (profissional_id, dia_semana, horario_inicio, horario_fim) VALUES (?, ?, ?, ?)",
        (session["user_id"], dia_semana, horario_inicio, horario_fim),
    )
    db.commit()
    flash("Disponibilidade adicionada com sucesso.", "success")
    return redirect(url_for("dashboard_profissional"))

@app.route("/disponibilidade/<int:availability_id>/remover", methods=["POST"])
def remove_availability(availability_id):
    if not validate_csrf_token():
        flash("Token de segurança inválido. Tente novamente.", "error")
        return redirect(url_for("dashboard_profissional"))

    if "user_id" not in session or session.get("user_type") != "profissional":
        flash("Apenas profissionais podem remover disponibilidade.", "error")
        return redirect(url_for("dashboard_profissional"))

    db = get_db()
    db.execute("DELETE FROM disponibilidade WHERE id = ? AND profissional_id = ?", (availability_id, session["user_id"]))
    db.commit()
    flash("Disponibilidade removida.", "success")
    return redirect(url_for("dashboard_profissional"))

@app.route("/empresa/servico/adicionar", methods=["POST"])
def add_company_service():
    if not validate_csrf_token():
        flash("Token de segurança inválido. Tente novamente.", "error")
        return redirect(url_for("dashboard_empresa"))

    if "user_id" not in session or session.get("user_type") != "empresa":
        flash("Apenas empresas podem cadastrar serviços.", "error")
        return redirect(url_for("dashboard_empresa"))

    titulo = request.form.get("titulo", "").strip()
    descricao = request.form.get("descricao", "").strip()
    valor = request.form.get("valor", "").strip()

    if not titulo or not descricao:
        flash("Preencha título e descrição do serviço.", "error")
        return redirect(url_for("dashboard_empresa"))

    try:
        valor_real = float(valor) if valor else None
    except ValueError:
        flash("Valor inválido.", "error")
        return redirect(url_for("dashboard_empresa"))

    db = get_db()
    db.execute(
        "INSERT INTO servicos_empresa (empresa_id, titulo, descricao, valor) VALUES (?, ?, ?, ?)",
        (session["user_id"], titulo, descricao, valor_real),
    )
    db.commit()
    flash("Serviço cadastrado com sucesso.", "success")
    return redirect(url_for("dashboard_empresa"))

@app.route("/empresa/servico/<int:service_id>/remover", methods=["POST"])
def remove_company_service(service_id):
    if not validate_csrf_token():
        flash("Token de segurança inválido. Tente novamente.", "error")
        return redirect(url_for("dashboard_empresa"))

    if "user_id" not in session or session.get("user_type") != "empresa":
        flash("Apenas empresas podem remover serviços.", "error")
        return redirect(url_for("dashboard_empresa"))

    db = get_db()
    db.execute("DELETE FROM servicos_empresa WHERE id = ? AND empresa_id = ?", (service_id, session["user_id"]))
    db.commit()
    flash("Serviço removido.", "success")
    return redirect(url_for("dashboard_empresa"))

@app.route("/admin/recusar-usuario/<int:user_id>", methods=["POST"])
def admin_reject_user(user_id):
    if not validate_csrf_token():
        flash("Token de segurança inválido. Tente novamente.", "error")
        return redirect(url_for("admin_panel"))

    if "user_id" not in session or session.get("user_type") != ADMIN_USER_TYPE:
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for("login"))

    motivo = request.form.get("motivo", "").strip()
    db = get_db()
    db.execute(
        "UPDATE usuarios SET approval_status = 'Recusado', rejection_reason = ? WHERE id = ?",
        (motivo or "Requisição recusada.", user_id),
    )
    db.commit()
    flash("Usuário recusado com sucesso.", "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/categorias", methods=["POST"])
def admin_add_category():
    if not validate_csrf_token():
        flash("Token de segurança inválido. Tente novamente.", "error")
        return redirect(url_for("admin_panel"))

    if "user_id" not in session or session.get("user_type") != ADMIN_USER_TYPE:
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for("login"))

    nome = request.form.get("categoria_nome", "").strip()
    if not nome:
        flash("Informe o nome da categoria.", "error")
        return redirect(url_for("admin_panel"))

    db = get_db()
    try:
        db.execute("INSERT INTO categorias (nome) VALUES (?)", (nome,))
        db.commit()
        flash("Categoria adicionada com sucesso.", "success")
    except sqlite3.IntegrityError:
        flash("Esta categoria já existe.", "error")
    return redirect(url_for("admin_panel"))

@app.route("/servico/<int:service_id>/recusar", methods=["POST"])
def recusar_servico(service_id):
    if not validate_csrf_token():
        flash("Token de segurança inválido. Tente novamente.", "error")
        return redirect(url_for("dashboard_profissional"))

    if "user_id" not in session or session.get("user_type") not in ("profissional", "empresa"):
        flash("Apenas prestadores podem recusar serviços.", "error")
        return redirect(url_for("dashboard_profissional"))

    service = get_service_by_id(service_id)
    if not service or service["profissional_id"] != session["user_id"]:
        flash("Serviço não encontrado ou sem permissão.", "error")
        return redirect(url_for("dashboard_profissional"))

    db = get_db()
    db.execute("UPDATE servicos SET status = 'Recusado' WHERE id = ?", (service_id,))
    db.commit()
    flash("Serviço recusado.", "success")
    return redirect(url_for("dashboard_profissional"))

@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if "user_id" not in session:
        flash("Faça login para editar seu perfil.", "error")
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])
    if request.method == "POST":
        if not validate_csrf_token():
            flash("Token de segurança inválido. Tente novamente.", "error")
            return render_template("perfil.html", user=user)

        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("Informe seu nome para atualizar o perfil.", "error")
            return render_template("perfil.html", user=user)

        telefone = request.form.get("telefone", "").strip()
        cidade = request.form.get("cidade", "").strip()
        bio = request.form.get("bio", "").strip()
        especialidade = request.form.get("especialidade", "").strip()
        empresa_nome = request.form.get("empresa_nome", "").strip()
        db = get_db()
        db.execute(
            """UPDATE usuarios SET nome = ?, telefone = ?, cidade = ?, bio = ?, especialidade = ?, empresa_nome = ?
            WHERE id = ?""",
            (nome, telefone, cidade, bio, especialidade, empresa_nome, user["id"]),
        )
        db.commit()
        session["user_name"] = nome
        flash("Perfil atualizado com sucesso.", "success")
        return redirect(url_for("perfil"))

    return render_template("perfil.html", user=user)

@app.route("/perfil/alterar-senha", methods=["GET", "POST"])
def alterar_senha():
    if "user_id" not in session:
        flash("Faça login para alterar a senha.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Token de segurança inválido. Tente novamente.", "error")
            return render_template("alterar_senha.html")

        senha_atual = request.form.get("senha_atual", "")
        nova_senha = request.form.get("nova_senha", "")
        confirm_nova_senha = request.form.get("confirm_nova_senha", "")

        user = get_user_by_id(session["user_id"])
        if not check_password_hash(user["senha"], senha_atual):
            flash("Senha atual incorreta.", "error")
            return render_template("alterar_senha.html")

        if nova_senha != confirm_nova_senha or not nova_senha:
            flash("As novas senhas devem coincidir.", "error")
            return render_template("alterar_senha.html")

        db = get_db()
        db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (generate_password_hash(nova_senha), session["user_id"]))
        db.commit()
        flash("Senha atualizada com sucesso.", "success")
        return redirect(url_for("perfil"))

    return render_template("alterar_senha.html")

@app.route("/perfil/excluir-conta", methods=["GET", "POST"])
def excluir_conta():
    if "user_id" not in session:
        flash("Faça login para solicitar exclusão.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Token de segurança inválido. Tente novamente.", "error")
            return render_template("excluir_conta.html")

        db = get_db()
        db.execute("UPDATE usuarios SET deletion_requested = 1 WHERE id = ?", (session["user_id"],))
        db.commit()
        flash("Solicitação de exclusão registrada. Entraremos em contato em breve.", "success")
        return redirect(url_for("dashboard_cliente" if session.get("user_type") == "cliente" else "dashboard"))

    return render_template("excluir_conta.html")

@app.route("/profissionais")
def profissionais():
    search = request.args.get("q", "").strip()
    category = request.args.get("categoria", "").strip()
    city = request.args.get("cidade", "").strip()
    online_only = request.args.get("online") == "1"
    min_rating = request.args.get("avaliacao", "").strip()

    providers = []
    favorite_ids = set()
    if session.get("user_type") == "cliente":
        db = get_db()
        rows = db.execute(
            "SELECT profissional_id FROM favoritos WHERE cliente_id = ?",
            (session["user_id"],),
        ).fetchall()
        favorite_ids = {row["profissional_id"] for row in rows}

    try:
        minimum_rating = float(min_rating) if min_rating else None
    except ValueError:
        minimum_rating = None

    for provider in get_providers(search=search, category=category, city=city, online_only=online_only):
        provider_data = enrich_provider(provider)
        provider_data["recommendation_score"] = get_provider_recommendation_score(provider_data, requested_category=category)
        if minimum_rating and (provider_data["rating"] is None or provider_data["rating"] < minimum_rating):
            continue
        provider_data["is_favorite"] = provider["id"] in favorite_ids
        provider_data["online"] = bool(provider_data.get("online") or provider["id"] in online_users)
        providers.append(provider_data)

    providers.sort(key=lambda item: item["recommendation_score"], reverse=True)

    return render_template(
        "profissionais.html",
        providers=providers,
        search=search,
        category=category,
        city=city,
        online_only=online_only,
        min_rating=min_rating,
    )

def render_public_provider_profile(provider_id, expected_type):
    provider = get_user_by_id(provider_id)
    if not provider or provider["tipo"] != expected_type or not is_provider_active(provider):
        flash("Perfil não encontrado ou indisponível.", "error")
        return redirect(url_for("profissionais"))
    provider_data = enrich_provider(provider)
    company_services = get_company_services(provider_id) if expected_type == "empresa" else []
    provider_data["online"] = bool(provider_data.get("online") or provider_id in online_users)
    return render_template(
        "public/perfil_prestador.html",
        provider=provider_data,
        prestador=provider_data,
        company_services=company_services,
        online_users=online_users,
    )

@app.route("/profissional/<int:provider_id>")
def perfil_publico_profissional(provider_id):
    return render_public_provider_profile(provider_id, "profissional")

@app.route("/empresa/<int:provider_id>")
def perfil_publico_empresa(provider_id):
    return render_public_provider_profile(provider_id, "empresa")

@app.route("/solicitar-servico/<int:provider_id>", methods=["GET", "POST"])
def solicitar_servico(provider_id):
    if "user_id" not in session:
        flash("Faça login para solicitar um serviço.", "error")
        return redirect(url_for("login"))

    if session.get("user_type") != "cliente":
        flash("Apenas clientes podem solicitar serviços.", "error")
        return redirect(url_for("profissionais"))

    provider = get_user_by_id(provider_id)
    if not provider or provider["tipo"] == "cliente":
        flash("Profissional ou empresa não encontrado(a).", "error")
        return redirect(url_for("profissionais"))
    if provider["approval_status"] != "Ativo":
        flash("Este profissional ainda não está disponível para solicitações.", "error")
        return redirect(url_for("profissionais"))

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Token de segurança inválido. Tente novamente.", "error")
            return render_template("solicitar_servico.html", provider=provider)

        categoria = request.form.get("categoria", "").strip()
        descricao = request.form.get("descricao", "").strip()
        valor = request.form.get("valor", "").strip()

        if not categoria or not descricao:
            flash("Informe categoria e descrição do serviço.", "error")
            return render_template("solicitar_servico.html", provider=provider)

        try:
            valor_real = float(valor) if valor else None
        except ValueError:
            flash("Digite um valor válido para o serviço.", "error")
            return render_template("solicitar_servico.html", provider=provider)

        db = get_db()
        cursor = db.execute(
            "INSERT INTO servicos (cliente_id, profissional_id, categoria, descricao, status, valor, data_solicitacao) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
            (session["user_id"], provider_id, categoria, descricao, "Pendente", valor_real),
        )
        service_id = cursor.lastrowid

        admin = db.execute("SELECT id, nome FROM usuarios WHERE tipo = ? LIMIT 1", (ADMIN_USER_TYPE,)).fetchone()
        sender_id = admin["id"] if admin else session["user_id"]
        sender_name = admin["nome"] if admin else session.get("user_name", "Usuário")

        db.execute(
            "INSERT INTO mensagens (servico_id, remetente_id, mensagem, criado_em) VALUES (?, ?, ?, datetime('now'))",
            (service_id, sender_id, "Solicitação criada com sucesso."),
        )
        db.commit()

        payload = {
            "service_id": service_id,
            "remetente_id": sender_id,
            "usuario": sender_name,
            "mensagem": "Solicitação criada com sucesso.",
            "criado_em": "Agora",
        }
        socketio.emit("nova_mensagem", payload, room=f"service_{service_id}")

        flash("Solicitação enviada com sucesso.", "success")
        return redirect(url_for("servico_chat", service_id=service_id))

    return render_template("solicitar_servico.html", provider=provider)

@app.route("/meus-servicos")
def meus_servicos():
    if "user_id" not in session:
        flash("Faça login para ver seus serviços.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user_type = session["user_type"]
    user = get_user_by_id(user_id)
    provider_active = True
    if user_type in ("profissional", "empresa"):
        provider_active = is_provider_active(user)

    services = []
    for service in get_services_for_user(user_id, user_type):
        service_data = dict(service)
        if user_type == "cliente":
            service_data["partner_name"] = service["profissional_nome"]
            service_data["partner_role"] = service["profissional_tipo"]
        else:
            service_data["partner_name"] = service["cliente_nome"]
            service_data["partner_role"] = service["cliente_tipo"]

        service_data["reviewed"] = user_has_reviewed_service(service["id"])
        service_data["can_review"] = (
            user_type == "cliente"
            and service["status"] == "Concluído"
            and not service_data["reviewed"]
        )
        services.append(service_data)

    return render_template(
        "meus_servicos.html",
        services=services,
        user_type=user_type,
        provider_active=provider_active,
    )

@app.route("/servico/<int:service_id>/atualizar-status", methods=["POST"])
def atualizar_status_servico(service_id):
    if not validate_csrf_token():
        flash("Token de segurança inválido. Tente novamente.", "error")
        return redirect(url_for("meus_servicos"))

    if "user_id" not in session:
        flash("Faça login para atualizar o serviço.", "error")
        return redirect(url_for("login"))

    if session.get("user_type") not in ("profissional", "empresa"):
        flash("Apenas prestadores podem atualizar o status do serviço.", "error")
        return redirect(url_for("meus_servicos"))

    user = get_user_by_id(session["user_id"])
    if not is_provider_active(user):
        flash("Seu perfil está pendente de aprovação. Atualização de serviços não está disponível.", "error")
        return redirect(url_for("meus_servicos"))

    service = get_service_by_id(service_id)
    if not service or service["profissional_id"] != session["user_id"]:
        flash("Serviço não encontrado ou sem permissão.", "error")
        return redirect(url_for("meus_servicos"))

    new_status = request.form.get("new_status", "").strip()
    if new_status not in ("Aceito", "Em andamento", "Concluído"):
        flash("Status inválido.", "error")
        return redirect(url_for("meus_servicos"))

    current_status = service["status"] or "Pendente"
    if current_status == "Pendente" and new_status != "Aceito":
        flash("O serviço deve ser aceito primeiro.", "error")
        return redirect(url_for("meus_servicos"))
    if current_status == "Aceito" and new_status != "Em andamento":
        flash("O serviço deve ser iniciado antes de ficar em andamento.", "error")
        return redirect(url_for("meus_servicos"))
    if current_status == "Em andamento" and new_status != "Concluído":
        flash("O serviço deve ser concluído após estar em andamento.", "error")
        return redirect(url_for("meus_servicos"))
    if current_status == "Concluído":
        flash("O serviço já está concluído.", "info")
        return redirect(url_for("meus_servicos"))

    db = get_db()
    db.execute("UPDATE servicos SET status = ? WHERE id = ?", (new_status, service_id))
    db.commit()
    flash(f"Status do serviço atualizado para {new_status}.", "success")
    return redirect(url_for("meus_servicos"))

@app.route("/avaliar/<int:service_id>", methods=["GET", "POST"])
def avaliar(service_id):
    if "user_id" not in session:
        flash("Faça login para avaliar um serviço.", "error")
        return redirect(url_for("login"))

    service = get_service_by_id(service_id)
    if not service or service["cliente_id"] != session["user_id"]:
        flash("Serviço não encontrado ou sem permissão.", "error")
        return redirect(url_for("meus_servicos"))

    if service["status"] != "Concluído":
        flash("Somente serviços concluídos podem ser avaliados.", "error")
        return redirect(url_for("meus_servicos"))

    if user_has_reviewed_service(service_id):
        flash("Este serviço já foi avaliado.", "info")
        return redirect(url_for("meus_servicos"))

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Token de segurança inválido. Tente novamente.", "error")
            return render_template("avaliar.html", service=service)

        nota = request.form.get("nota", "")
        comentario = request.form.get("comentario", "").strip()

        try:
            nota_int = int(nota)
        except ValueError:
            nota_int = 0

        if nota_int < 1 or nota_int > 5:
            flash("Escolha uma nota entre 1 e 5.", "error")
            return render_template("avaliar.html", service=service)

        db = get_db()
        db.execute(
            "INSERT INTO avaliacoes (cliente_id, profissional_id, nota, comentario, servico_id) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], service["profissional_id"], nota_int, comentario, service_id),
        )
        db.commit()
        flash("Avaliação registrada. Obrigado pelo feedback!", "success")
        return redirect(url_for("meus_servicos"))

    return render_template("avaliar.html", service=service)

@socketio.on("connect")
def handle_connect(auth=None):
    if session.get("user_id"):
        user = get_user_by_id(session["user_id"])
        if user:
            online_users.add(user["id"])
            db = get_db()
            db.execute("UPDATE usuarios SET status_online = 'online', ultimo_acesso = datetime('now') WHERE id = ?", (user["id"],))
            db.commit()
            join_room("global")
            join_room(f"user_{user['id']}")
            socketio.emit("usuario_online", {"id": user["id"], "nome": user["nome"], "tipo": user["tipo"]}, room="global")

@socketio.on("join_conversation")
def handle_join_conversation(payload):
    conversation_id = payload.get("conversation_id") if payload else None
    user_id = session.get("user_id")

    if not user_id or not conversation_id:
        return

    db = get_db()
    participant = db.execute(
        "SELECT 1 FROM conversa_participantes WHERE conversa_id = ? AND usuario_id = ?",
        (conversation_id, user_id),
    ).fetchone()
    if participant:
        join_room(f"conversation_{conversation_id}")

@socketio.on("disconnect")
def handle_disconnect():
    user_id = session.get("user_id")
    if user_id:
        online_users.discard(user_id)
        db = get_db()
        db.execute("UPDATE usuarios SET status_online = 'offline', ultimo_acesso = datetime('now') WHERE id = ?", (user_id,))
        db.commit()
        socketio.emit("usuario_offline", {"id": user_id}, room="global")

@socketio.on("join_service")
def handle_join_service(payload):
    service_id = payload.get("service_id") if payload else None
    user_id = session.get("user_id")

    if not user_id or not service_id:
        return

    service = get_service_by_id(service_id)
    if not service:
        return

    # Allow only if the user is participant (cliente or profissional) or is admin/company
    if (
        user_id == service["cliente_id"]
        or user_id == service["profissional_id"]
        or session.get("user_type") in (ADMIN_USER_TYPE, "empresa")
    ):
        join_room(f"service_{service_id}")

@socketio.on("mensagem_lida")
def handle_mensagem_lida(payload):
    if session.get("user_id"):
        socketio.emit("mensagem_lida", payload, room="global")

if __name__ == "__main__":
    threading.Timer(1.0, lambda: open_browser(PORT)).start()
    try:
        socketio.run(app, debug=DEBUG, use_reloader=False, host="0.0.0.0", port=PORT)
    except OSError as exc:
        print(f"Erro ao iniciar o servidor: {exc}")
        if "address already in use" in str(exc).lower():
            print(
                f"Porta {PORT} já está em uso. Use outra porta definindo a variável de ambiente PORT ou encerrando o processo que ocupa essa porta."
            )
        raise
