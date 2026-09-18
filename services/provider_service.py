from utils.db import get_db


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


def get_provider_rating(provider_id):
    db = get_db()
    row = db.execute(
        "SELECT AVG(nota) AS avg_rating, COUNT(*) AS total FROM avaliacoes WHERE profissional_id = ?",
        (provider_id,),
    ).fetchone()
    avg_rating = row["avg_rating"]
    return (round(avg_rating, 1), row["total"]) if avg_rating is not None else (None, row["total"])


def get_availability_for_user(user_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM disponibilidade WHERE profissional_id = ? ORDER BY id DESC",
        (user_id,),
    ).fetchall()


def get_online_providers(limit=None):
    providers = [enrich_provider(provider) for provider in get_providers(online_only=True)]
    return providers[:limit] if limit else providers


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
