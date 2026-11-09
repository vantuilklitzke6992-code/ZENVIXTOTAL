import uuid

import app as app_module
import utils.db as db_module
from services import provider_service
from utils.db import get_db


def test_development_uses_sqlite_unless_postgres_is_explicit(monkeypatch):
    monkeypatch.setattr(db_module, "FORCE_SQLITE", False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.delenv("DATABASE_BACKEND", raising=False)

    monkeypatch.setenv("APP_ENV", "development")
    assert not db_module.using_postgres()

    monkeypatch.setenv("APP_ENV", "production")
    assert db_module.using_postgres()

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_BACKEND", "postgres")
    assert db_module.using_postgres()

    monkeypatch.setenv("DATABASE_BACKEND", "sqlite")
    assert not db_module.using_postgres()

    monkeypatch.setattr(db_module, "FORCE_SQLITE", True)
    monkeypatch.setenv("DATABASE_BACKEND", "postgres")
    assert not db_module.using_postgres()


def test_static_requests_do_not_open_a_database_connection(monkeypatch):
    def fail_if_database_is_opened():
        raise AssertionError("Static requests must not access the database.")

    monkeypatch.setattr(app_module, "get_db", fail_if_database_is_opened)

    response = app_module.app.test_client().get("/static/css/style.css")

    assert response.status_code == 200


def test_provider_enrichment_uses_one_aggregate_query():
    with app_module.app.app_context():
        db = get_db()
        token = uuid.uuid4().hex

        provider_service.get_providers()
        db.execute("SAVEPOINT provider_performance_test")
        try:
            db.execute(
                """
                INSERT INTO usuarios (
                    nome, email, senha, tipo, approval_status
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Cliente de teste",
                    f"client_{token}@test.com",
                    "x",
                    "cliente",
                    "Ativo",
                ),
            )
            client_id = db.execute(
                "SELECT id FROM usuarios WHERE email = ?",
                (f"client_{token}@test.com",),
            ).fetchone()["id"]
            db.execute(
                """
                INSERT INTO usuarios (
                    nome, email, senha, tipo, approval_status, especialidade
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    f"Profissional {token}",
                    f"provider_{token}@test.com",
                    "x",
                    "profissional",
                    "Ativo",
                    "Pintura",
                ),
            )
            provider_id = db.execute(
                "SELECT id FROM usuarios WHERE email = ?",
                (f"provider_{token}@test.com",),
            ).fetchone()["id"]
            service_id = db.execute(
                """
                INSERT INTO servicos (cliente_id, profissional_id, status)
                VALUES (?, ?, 'Concluído')
                """,
                (client_id, provider_id),
            ).lastrowid
            db.execute(
                """
                INSERT INTO avaliacoes (
                    cliente_id, profissional_id, nota, servico_id
                )
                VALUES (?, ?, 5, ?)
                """,
                (client_id, provider_id, service_id),
            )
            db.execute(
                "INSERT INTO disponibilidade (profissional_id) VALUES (?)",
                (provider_id,),
            )

            statements = []
            db.set_trace_callback(statements.append)
            providers = provider_service.get_providers(
                search=f"Profissional {token}"
            )
            enriched = [
                provider_service.enrich_provider(row)
                for row in providers
            ]
            db.set_trace_callback(None)

            assert len(enriched) == 1
            assert enriched[0]["rating"] == 5.0
            assert enriched[0]["rating_count"] == 1
            assert enriched[0]["completed_services"] == 1
            assert enriched[0]["availability_count"] == 1
            assert sum(
                statement.lstrip().upper().startswith("SELECT")
                for statement in statements
            ) == 1
            assert not any(
                statement.lstrip().upper().startswith("UPDATE")
                for statement in statements
            )
        finally:
            db.set_trace_callback(None)
            db.execute("ROLLBACK TO provider_performance_test")
            db.execute("RELEASE provider_performance_test")
