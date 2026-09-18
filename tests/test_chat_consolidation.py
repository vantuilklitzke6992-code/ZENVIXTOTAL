import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as app_module
from utils.app_init import app
from utils.db import get_db


def setup_module():
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM mensagens")
        db.execute("DELETE FROM servicos")
        db.execute("DELETE FROM conversas")
        db.execute("DELETE FROM conversa_participantes")
        db.execute("DELETE FROM conversa_mensagens")
        db.execute("DELETE FROM usuarios WHERE email LIKE 'chat_%@test.com'")
        db.commit()


def _make_service_and_users(status="Em andamento"):
    with app.app_context():
        db = get_db()
        suffix = uuid.uuid4().hex[:8]
        client_email = f"chat_client_{suffix}@test.com"
        professional_email = f"chat_prof_{suffix}@test.com"
        third_email = f"chat_third_{suffix}@test.com"
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Cliente Chat",
                client_email,
                "x",
                "cliente",
                "Ativo",
                "100",
                "Cidade",
                "Estado",
            ),
        )
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Profissional Chat",
                professional_email,
                "x",
                "profissional",
                "Ativo",
                "200",
                "Cidade",
                "Estado",
            ),
        )
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Terceiro Chat",
                third_email,
                "x",
                "cliente",
                "Ativo",
                "300",
                "Cidade",
                "Estado",
            ),
        )
        db.commit()
        client_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (client_email,)
        ).fetchone()[0]
        professional_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (professional_email,)
        ).fetchone()[0]
        third_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (third_email,)
        ).fetchone()[0]
        cursor = db.execute(
            "INSERT INTO servicos (cliente_id, profissional_id, categoria, descricao, status, valor, data_solicitacao, cliente_confirmou_conclusao, profissional_confirmou_conclusao) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 0, 0)",
            (client_id, professional_id, "Teste", "Descrição", status, 100.0),
        )
        service_id = cursor.lastrowid
        db.commit()
        return client_id, professional_id, third_id, service_id


def _set_session(client, user_id, user_type):
    with client.session_transaction() as session:
        session["_csrf_token"] = "test-token"
        session["user_id"] = user_id
        session["user_type"] = user_type
        session["user_name"] = "Usuário teste"


def test_user_can_access_service_chat_only_for_participants():
    client_id, professional_id, third_id, service_id = _make_service_and_users()

    with app.app_context():
        assert app_module.user_can_access_service_chat(client_id, service_id) is True
        assert (
            app_module.user_can_access_service_chat(professional_id, service_id) is True
        )
        assert app_module.user_can_access_service_chat(third_id, service_id) is False


def test_service_chat_route_denies_third_party():
    client_id, professional_id, third_id, service_id = _make_service_and_users()
    with app.test_client() as client:
        _set_session(client, third_id, "cliente")
        response = client.get(f"/servico/{service_id}/chat")
        assert response.status_code == 302


def test_service_chat_renders_malicious_message_as_text():
    client_id, professional_id, _, service_id = _make_service_and_users()
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/chat",
            data={
                "_csrf_token": "test-token",
                "mensagem": "<script>alert('xss')</script>",
            },
        )
        assert response.status_code == 302
        response = client.get(f"/servico/{service_id}/chat")
        assert response.status_code == 200
        assert b"&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in response.data


def test_chat_privado_cria_conversa_e_salva_mensagem():
    with app.app_context():
        db = get_db()
        suffix = uuid.uuid4().hex[:8]
        user_email = f"private_user_{suffix}@test.com"
        partner_email = f"private_partner_{suffix}@test.com"
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Usuário Privado",
                user_email,
                "x",
                "cliente",
                "Ativo",
                "400",
                "Cidade",
                "Estado",
            ),
        )
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Parceiro Privado",
                partner_email,
                "x",
                "profissional",
                "Ativo",
                "500",
                "Cidade",
                "Estado",
            ),
        )
        db.commit()
        user_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (user_email,)
        ).fetchone()[0]
        partner_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (partner_email,)
        ).fetchone()[0]

    with app.test_client() as client:
        _set_session(client, user_id, "cliente")
        response = client.get(f"/conversar/{partner_id}")
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            conversation = db.execute(
                "SELECT id FROM conversas ORDER BY id DESC LIMIT 1"
            ).fetchone()
            assert conversation is not None
            message_count = db.execute(
                "SELECT COUNT(*) AS total FROM conversa_mensagens"
            ).fetchone()["total"]
            assert message_count == 0


def test_conversa_privada_oferece_botoes_de_transicao_para_servico():
    with app.app_context():
        db = get_db()
        suffix = uuid.uuid4().hex[:8]
        user_email = f"chat_transition_user_{suffix}@test.com"
        provider_email = f"chat_transition_provider_{suffix}@test.com"
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Usuário Transição",
                user_email,
                "x",
                "cliente",
                "Ativo",
                "600",
                "Cidade",
                "Estado",
            ),
        )
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Prestador Transição",
                provider_email,
                "x",
                "profissional",
                "Ativo",
                "700",
                "Cidade",
                "Estado",
            ),
        )
        db.commit()
        user_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (user_email,)
        ).fetchone()[0]
        provider_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (provider_email,)
        ).fetchone()[0]
        conversation_id = db.execute(
            "INSERT INTO conversas (criado_em) VALUES (datetime('now'))"
        ).lastrowid
        db.execute(
            "INSERT INTO conversa_participantes (conversa_id, usuario_id) VALUES (?, ?)",
            (conversation_id, user_id),
        )
        db.execute(
            "INSERT INTO conversa_participantes (conversa_id, usuario_id) VALUES (?, ?)",
            (conversation_id, provider_id),
        )
        db.commit()

    with app.test_client() as client:
        _set_session(client, user_id, "cliente")
        response = client.get(f"/conversa/{conversation_id}")
        assert response.status_code == 200
        assert b"Solicitar servi\xc3\xa7o" in response.data


def test_solicitar_servico_via_conversa_cria_servico_e_redireciona_para_chat():
    with app.app_context():
        db = get_db()
        suffix = uuid.uuid4().hex[:8]
        user_email = f"chat_request_user_{suffix}@test.com"
        provider_email = f"chat_request_provider_{suffix}@test.com"
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Cliente de Solicitação",
                user_email,
                "x",
                "cliente",
                "Ativo",
                "800",
                "Cidade",
                "Estado",
            ),
        )
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Prestador Solicitação",
                provider_email,
                "x",
                "profissional",
                "Ativo",
                "900",
                "Cidade",
                "Estado",
            ),
        )
        db.commit()
        user_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (user_email,)
        ).fetchone()[0]
        provider_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (provider_email,)
        ).fetchone()[0]
        conversation_id = db.execute(
            "INSERT INTO conversas (criado_em) VALUES (datetime('now'))"
        ).lastrowid
        db.execute(
            "INSERT INTO conversa_participantes (conversa_id, usuario_id) VALUES (?, ?)",
            (conversation_id, user_id),
        )
        db.execute(
            "INSERT INTO conversa_participantes (conversa_id, usuario_id) VALUES (?, ?)",
            (conversation_id, provider_id),
        )
        db.commit()

    with app.test_client() as client:
        _set_session(client, user_id, "cliente")
        response = client.post(
            f"/solicitar-servico/{provider_id}?conversation_id={conversation_id}",
            data={
                "_csrf_token": "test-token",
                "categoria": "Limpeza",
                "descricao": "Quero contratar",
                "valor": "150",
            },
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            service = db.execute(
                "SELECT id, cliente_id, profissional_id FROM servicos ORDER BY id DESC LIMIT 1"
            ).fetchone()
            assert service is not None
            assert service["cliente_id"] == user_id
            assert service["profissional_id"] == provider_id


def test_conversa_privada_exibe_identidade_visual_de_pre_contratacao():
    with app.app_context():
        db = get_db()
        suffix = uuid.uuid4().hex[:8]
        user_email = f"ux_private_user_{suffix}@test.com"
        provider_email = f"ux_private_provider_{suffix}@test.com"
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Usuário UX",
                user_email,
                "x",
                "cliente",
                "Ativo",
                "1000",
                "Cidade",
                "Estado",
            ),
        )
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Prestador UX",
                provider_email,
                "x",
                "profissional",
                "Ativo",
                "1100",
                "Cidade",
                "Estado",
            ),
        )
        db.commit()
        user_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (user_email,)
        ).fetchone()[0]
        provider_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (provider_email,)
        ).fetchone()[0]
        conversation_id = db.execute(
            "INSERT INTO conversas (criado_em) VALUES (datetime('now'))"
        ).lastrowid
        db.execute(
            "INSERT INTO conversa_participantes (conversa_id, usuario_id) VALUES (?, ?)",
            (conversation_id, user_id),
        )
        db.execute(
            "INSERT INTO conversa_participantes (conversa_id, usuario_id) VALUES (?, ?)",
            (conversation_id, provider_id),
        )
        db.commit()

    with app.test_client() as client:
        _set_session(client, user_id, "cliente")
        response = client.get(f"/conversa/{conversation_id}")
        assert response.status_code == 200
        assert b"Pronto para contratar" in response.data


def test_chat_de_servico_exibe_identidade_visual_do_servico():
    client_id, professional_id, _, service_id = _make_service_and_users()
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response = client.get(f"/servico/{service_id}/chat")
        assert response.status_code == 200
        assert b"Detalhes do servi\xc3\xa7o" in response.data
