from utils.db import get_db
from services.user_service import get_user_by_id


def get_chat_conversations_for_user(user_id, search=None):
    db = get_db()
    rows = db.execute(
        "SELECT conversa_id FROM conversa_participantes WHERE usuario_id = ? ORDER BY conversa_id DESC",
        (user_id,),
    ).fetchall()

    search_term = (search or "").strip().lower()
    conversations = []

    for row in rows:
        conversation_id = row["conversa_id"]
        participants = get_conversation_participants(conversation_id)
        if len(participants) < 2:
            continue

        other_user_id = next(
            (participant for participant in participants if participant != user_id),
            None,
        )
        if not other_user_id:
            continue

        partner = get_user_by_id(other_user_id)
        if not partner:
            continue

        partner_name = (partner["nome"] or "") + " " + (partner["empresa_nome"] or "")
        if search_term and search_term not in partner_name.lower():
            continue

        last_message = db.execute(
            "SELECT * FROM conversa_mensagens WHERE conversa_id = ? ORDER BY id DESC LIMIT 1",
            (conversation_id,),
        ).fetchone()
        unread_count = get_unread_conversation_count(conversation_id, user_id)
        conversations.append(
            {
                "conversation_id": conversation_id,
                "partner_id": partner["id"],
                "partner_name": partner["empresa_nome"] or partner["nome"] or "Usuário",
                "partner_photo": partner["foto_perfil"] or partner["logo_empresa"],
                "partner_type": partner["tipo"],
                "partner_status": partner["status_online"] or "offline",
                "last_message": (
                    last_message["mensagem"]
                    if last_message
                    else "Nenhuma mensagem ainda"
                ),
                "last_message_time": (
                    last_message["criado_em"] if last_message else None
                ),
                "unread_count": unread_count,
            }
        )

    conversations.sort(key=lambda item: item["last_message_time"] or "", reverse=True)
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


def get_conversation_participants(conversation_id):
    db = get_db()
    return [
        row["usuario_id"]
        for row in db.execute(
            "SELECT usuario_id FROM conversa_participantes WHERE conversa_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
    ]


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


def get_chat_contacts(user_id, search=None):
    db = get_db()
    search_term = (search or "").strip().lower()
    digits_search = get_user_by_id(0)  # placeholder not used
    query = "SELECT * FROM usuarios WHERE id != ? AND lower(coalesce(approval_status, '')) IN ('aprovado','ativo')"
    params = [user_id]

    rows = db.execute(query, tuple(params)).fetchall()
    contacts = []
    for row in rows:
        row_name = (row["nome"] or "").lower()
        row_company = (row["empresa_nome"] or "").lower()
        row_phone_digits = row["telefone"] or ""

        if search_term:
            if (
                search_term not in row_name
                and search_term not in row_company
                and (not digits_search or search_term not in row_phone_digits)
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
