from utils.db import get_db


def query_user_by_email(email):
    db = get_db()
    return db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()


def get_user_by_id(user_id):
    db = get_db()
    return db.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()


def get_all_users():
    db = get_db()
    return db.execute(
        "SELECT * FROM usuarios WHERE coalesce(approval_status, '') != 'Removado' ORDER BY tipo, nome"
    ).fetchall()


def normalize_phone(phone):
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if digits.startswith("55") and len(digits) > 11:
        digits = digits[2:]
    return digits


def get_user_by_phone(phone):
    normalized = normalize_phone(phone)
    if not normalized:
        return None

    db = get_db()
    rows = db.execute(
        "SELECT * FROM usuarios WHERE telefone IS NOT NULL AND telefone != ''"
    ).fetchall()
    for row in rows:
        database_phone = normalize_phone(row["telefone"])
        if database_phone == normalized:
            approval_status = (row["approval_status"] or "").strip().lower()
            if approval_status in {"aprovado", "ativo"}:
                return row
            return None
    return None


def get_chat_contacts(user_id, search=None):
    db = get_db()
    search_term = (search or "").strip().lower()
    digits_search = normalize_phone(search)
    query = (
        "SELECT * FROM usuarios WHERE id != ? AND lower(coalesce(approval_status, '')) "
        "IN ('aprovado','ativo')"
    )
    params = [user_id]

    rows = db.execute(query, tuple(params)).fetchall()
    contacts = []
    for row in rows:
        row_name = (row["nome"] or "").lower()
        row_company = (row["empresa_nome"] or "").lower()
        row_phone_digits = normalize_phone(row["telefone"] or "")

        if search_term:
            if (
                search_term not in row_name
                and search_term not in row_company
                and (not digits_search or digits_search not in row_phone_digits)
            ):
                continue

        contacts.append(
            {
                "id": row["id"],
                "nome": row["nome"],
                "empresa_nome": row["empresa_nome"],
                "foto_perfil": row["foto_perfil"],
                "logo_empresa": row["logo_empresa"],
                "tipo": row["tipo"],
                "status_online": row["status_online"] or "offline",
            }
        )
    return contacts
