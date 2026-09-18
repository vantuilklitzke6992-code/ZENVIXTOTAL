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
        db.execute("DELETE FROM servicos")
        db.execute("DELETE FROM avaliacoes")
        db.execute("DELETE FROM mensagens")
        db.execute("DELETE FROM usuarios WHERE email LIKE 'flow_%@test.com'")
        db.commit()


def _make_users_and_service(status="Em andamento", client_flag=0, professional_flag=0):
    with app.app_context():
        db = get_db()
        unique = uuid.uuid4().hex[:8]
        client_email = f"flow_client_{unique}@test.com"
        professional_email = f"flow_prof_{unique}@test.com"
        other_email = f"flow_other_{unique}@test.com"
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Cliente Flow",
                client_email,
                "x",
                "cliente",
                "Ativo",
                "123",
                "Cidade",
                "Estado",
            ),
        )
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Profissional Flow",
                professional_email,
                "x",
                "profissional",
                "Ativo",
                "456",
                "Cidade",
                "Estado",
            ),
        )
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, approval_status, telefone, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Outro Flow",
                other_email,
                "x",
                "cliente",
                "Ativo",
                "789",
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
        other_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", (other_email,)
        ).fetchone()[0]
        cursor = db.execute(
            "INSERT INTO servicos (cliente_id, profissional_id, categoria, descricao, status, valor, data_solicitacao, cliente_confirmou_conclusao, profissional_confirmou_conclusao) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?, ?)",
            (
                client_id,
                professional_id,
                "Teste",
                "Descrição",
                status,
                100.0,
                client_flag,
                professional_flag,
            ),
        )
        service_id = cursor.lastrowid
        db.commit()
        return client_id, professional_id, other_id, service_id


def _set_session(client, user_id, user_type):
    with client.session_transaction() as session:
        session["_csrf_token"] = "test-token"
        session["user_id"] = user_id
        session["user_type"] = user_type
        session["user_name"] = "Usuário teste"


def test_cliente_confirma_sozinho():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/confirmar-conclusao",
            data={"_csrf_token": "test-token"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT cliente_confirmou_conclusao, profissional_confirmou_conclusao, status FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert row[0] == 1 and row[1] == 0
            assert row[2] == "Aguardando confirmação"


def test_profissional_confirma_sozinho():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, professional_id, "profissional")
        response = client.post(
            f"/servico/{service_id}/confirmar-conclusao",
            data={"_csrf_token": "test-token"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT cliente_confirmou_conclusao, profissional_confirmou_conclusao, status FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert row[0] == 0 and row[1] == 1
            assert row[2] == "Aguardando confirmação"


def test_ambos_confirmam_concluem_servico():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        client.post(
            f"/servico/{service_id}/confirmar-conclusao",
            data={"_csrf_token": "test-token"},
        )
        _set_session(client, professional_id, "profissional")
        response = client.post(
            f"/servico/{service_id}/confirmar-conclusao",
            data={"_csrf_token": "test-token"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT cliente_confirmou_conclusao, profissional_confirmou_conclusao, status, data_conclusao FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert row[0] == 1 and row[1] == 1
            assert row[2] == "Concluído"
            assert row[3] is not None


def test_cliente_nao_altera_flag_profissional():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        client.post(
            f"/servico/{service_id}/confirmar-conclusao",
            data={"_csrf_token": "test-token"},
        )
        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT cliente_confirmou_conclusao, profissional_confirmou_conclusao FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert row[0] == 1 and row[1] == 0


def test_profissional_nao_altera_flag_cliente():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, professional_id, "profissional")
        client.post(
            f"/servico/{service_id}/confirmar-conclusao",
            data={"_csrf_token": "test-token"},
        )
        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT cliente_confirmou_conclusao, profissional_confirmou_conclusao FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert row[0] == 0 and row[1] == 1


def test_cancelamento_sem_motivo_falha():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/cancelar",
            data={"_csrf_token": "test-token", "motivo_cancelamento": ""},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT status, motivo_cancelamento, data_cancelamento FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert row[0] == "Em andamento"
            assert row[1] is None
            assert row[2] is None


def test_cancelamento_com_motivo_sucesso():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/cancelar",
            data={
                "_csrf_token": "test-token",
                "motivo_cancelamento": "Cliente desistiu",
            },
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT status, motivo_cancelamento, data_cancelamento FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert row[0] == "Cancelado"
            assert row[1] == "Cliente desistiu"
            assert row[2] is not None


def test_nao_conclui_servico_cancelado():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Cancelado"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/confirmar-conclusao",
            data={"_csrf_token": "test-token"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT status, cliente_confirmou_conclusao, profissional_confirmou_conclusao FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert row[0] == "Cancelado"
            assert row[1] == 0 and row[2] == 0


def test_nao_cancela_servico_concluido():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Concluído", client_flag=1, professional_flag=1
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/cancelar",
            data={
                "_csrf_token": "test-token",
                "motivo_cancelamento": "Cliente desistiu",
            },
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT status, motivo_cancelamento FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert row[0] == "Concluído"
            assert row[1] is None


def test_usuario_que_nao_pertence_ao_servico_nao_altera():
    client_id, professional_id, other_id, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, other_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/atualizar-status",
            data={"_csrf_token": "test-token", "new_status": "Em andamento"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT status FROM servicos WHERE id = ?", (service_id,)
            ).fetchone()
            assert row[0] == "Em andamento"


def test_cliente_cria_proposta():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "550"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT * FROM servico_propostas_valor WHERE servico_id = ? ORDER BY id DESC",
                (service_id,),
            ).fetchone()
            assert proposal is not None
            assert proposal["estado"] == "Pendente"
            assert proposal["valor_anterior"] == 100.0
            assert proposal["valor_proposto"] == 550.0


def test_profissional_aceita_proposta():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "550"},
        )
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT id FROM servico_propostas_valor WHERE servico_id = ? ORDER BY id DESC",
                (service_id,),
            ).fetchone()
        _set_session(client, professional_id, "profissional")
        response = client.post(
            f"/servico/{service_id}/proposta-valor/{proposal['id']}/aceitar",
            data={"_csrf_token": "test-token"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            proposal_row = db.execute(
                "SELECT estado FROM servico_propostas_valor WHERE id = ?",
                (proposal["id"],),
            ).fetchone()
            service_row = db.execute(
                "SELECT valor, valor_historico FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert proposal_row["estado"] == "Aceita"
            assert service_row["valor"] == 550.0
            assert service_row["valor_historico"] is not None


def test_valor_muda_somente_apos_aceite():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "550"},
        )
        with app.app_context():
            db = get_db()
            service_row = db.execute(
                "SELECT valor FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert service_row["valor"] == 100.0


def test_profissional_recusa_proposta():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "550"},
        )
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT id FROM servico_propostas_valor WHERE servico_id = ? ORDER BY id DESC",
                (service_id,),
            ).fetchone()
        _set_session(client, professional_id, "profissional")
        response = client.post(
            f"/servico/{service_id}/proposta-valor/{proposal['id']}/recusar",
            data={"_csrf_token": "test-token"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            proposal_row = db.execute(
                "SELECT estado FROM servico_propostas_valor WHERE id = ?",
                (proposal["id"],),
            ).fetchone()
            service_row = db.execute(
                "SELECT valor FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert proposal_row["estado"] == "Recusada"
            assert service_row["valor"] == 100.0


def test_profissional_cria_proposta():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, professional_id, "profissional")
        response = client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "600"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT * FROM servico_propostas_valor WHERE servico_id = ? ORDER BY id DESC",
                (service_id,),
            ).fetchone()
            assert proposal is not None
            assert proposal["proponente_id"] == professional_id


def test_cliente_aceita_proposta_do_profissional():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, professional_id, "profissional")
        client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "600"},
        )
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT id FROM servico_propostas_valor WHERE servico_id = ? ORDER BY id DESC",
                (service_id,),
            ).fetchone()
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/proposta-valor/{proposal['id']}/aceitar",
            data={"_csrf_token": "test-token"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            service_row = db.execute(
                "SELECT valor FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert service_row["valor"] == 600.0


def test_cliente_recusa_proposta_do_profissional():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, professional_id, "profissional")
        client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "600"},
        )
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT id FROM servico_propostas_valor WHERE servico_id = ? ORDER BY id DESC",
                (service_id,),
            ).fetchone()
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/proposta-valor/{proposal['id']}/recusar",
            data={"_csrf_token": "test-token"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            proposal_row = db.execute(
                "SELECT estado FROM servico_propostas_valor WHERE id = ?",
                (proposal["id"],),
            ).fetchone()
            assert proposal_row["estado"] == "Recusada"


def test_criador_nao_pode_aceitar_propria_proposta():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "550"},
        )
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT id FROM servico_propostas_valor WHERE servico_id = ? ORDER BY id DESC",
                (service_id,),
            ).fetchone()
        response = client.post(
            f"/servico/{service_id}/proposta-valor/{proposal['id']}/aceitar",
            data={"_csrf_token": "test-token"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            proposal_row = db.execute(
                "SELECT estado FROM servico_propostas_valor WHERE id = ?",
                (proposal["id"],),
            ).fetchone()
            assert proposal_row["estado"] == "Pendente"


def test_usuario_externo_nao_pode_aceitar_proposta():
    client_id, professional_id, other_id, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "550"},
        )
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT id FROM servico_propostas_valor WHERE servico_id = ? ORDER BY id DESC",
                (service_id,),
            ).fetchone()
        _set_session(client, other_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/proposta-valor/{proposal['id']}/aceitar",
            data={"_csrf_token": "test-token"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            proposal_row = db.execute(
                "SELECT estado FROM servico_propostas_valor WHERE id = ?",
                (proposal["id"],),
            ).fetchone()
            assert proposal_row["estado"] == "Pendente"


def test_nao_permite_segunda_proposta_while_pendente():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response1 = client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "550"},
        )
        response2 = client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "600"},
        )
        assert response1.status_code == 302
        assert response2.status_code == 302
        with app.app_context():
            db = get_db()
            proposals = db.execute(
                "SELECT id FROM servico_propostas_valor WHERE servico_id = ? ORDER BY id",
                (service_id,),
            ).fetchall()
            assert len(proposals) == 1


def test_nao_cria_proposta_em_servico_concluido():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Concluído", client_flag=1, professional_flag=1
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "550"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT * FROM servico_propostas_valor WHERE servico_id = ?",
                (service_id,),
            ).fetchone()
            assert proposal is None


def test_nao_cria_proposta_em_servico_cancelado():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Cancelado"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "550"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT * FROM servico_propostas_valor WHERE servico_id = ?",
                (service_id,),
            ).fetchone()
            assert proposal is None


def test_valor_invalido_rejeita_proposta():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        response = client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "-10"},
        )
        assert response.status_code == 302
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT * FROM servico_propostas_valor WHERE servico_id = ?",
                (service_id,),
            ).fetchone()
            assert proposal is None


def test_historico_de_valor_persiste():
    client_id, professional_id, _, service_id = _make_users_and_service(
        status="Em andamento"
    )
    with app.test_client() as client:
        _set_session(client, client_id, "cliente")
        client.post(
            f"/servico/{service_id}/propor-valor",
            data={"_csrf_token": "test-token", "valor": "550"},
        )
        with app.app_context():
            db = get_db()
            proposal = db.execute(
                "SELECT id FROM servico_propostas_valor WHERE servico_id = ? ORDER BY id DESC",
                (service_id,),
            ).fetchone()
        _set_session(client, professional_id, "profissional")
        client.post(
            f"/servico/{service_id}/proposta-valor/{proposal['id']}/aceitar",
            data={"_csrf_token": "test-token"},
        )
        with app.app_context():
            db = get_db()
            service_row = db.execute(
                "SELECT valor, valor_historico FROM servicos WHERE id = ?",
                (service_id,),
            ).fetchone()
            assert service_row["valor"] == 550.0
            assert (
                service_row["valor_historico"] is not None
                and "100.0" in service_row["valor_historico"]
            )
