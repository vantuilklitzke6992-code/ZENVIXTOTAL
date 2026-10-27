import sqlite3

import pytest

from utils.app_init import app
from utils.db import get_db, init_db


CANONICAL_CATEGORIES = (
    "Alvenaria e construção",
    "Instalações elétricas",
    "Instalações hidráulicas",
    "Pintura",
    "Acabamentos e revestimentos",
    "Reformas e ampliações",
)


def test_init_db_creates_provider_category_relation_and_seeds_categories():
    with app.app_context():
        db = get_db()
        init_db()
        init_db()

        tables = {
            row["name"]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "usuario_categorias" in tables

        category_rows = db.execute(
            "SELECT nome FROM categorias WHERE nome IN (?, ?, ?, ?, ?, ?)",
            CANONICAL_CATEGORIES,
        ).fetchall()
        assert {row["nome"] for row in category_rows} == set(CANONICAL_CATEGORIES)
        assert len(category_rows) == len(CANONICAL_CATEGORIES)

        foreign_keys = db.execute(
            "PRAGMA foreign_key_list(usuario_categorias)"
        ).fetchall()
        assert {(row["table"], row["from"], row["to"]) for row in foreign_keys} == {
            ("usuarios", "usuario_id", "id"),
            ("categorias", "categoria_id", "id"),
        }


def test_provider_can_have_multiple_categories_without_duplicate_or_orphan_links():
    with app.app_context():
        db = get_db()

        db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo, especialidade) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Teste Fase 3.1", "fase3-1@example.test", "hash", "profissional", "Pedreiro"),
        )
        user_id = db.execute(
            "SELECT id FROM usuarios WHERE email = ?", ("fase3-1@example.test",)
        ).fetchone()["id"]
        category_ids = [
            db.execute("SELECT id FROM categorias WHERE nome = ?", (category,)).fetchone()["id"]
            for category in CANONICAL_CATEGORIES[:2]
        ]
        db.commit()
        # SQLite declares these foreign keys but enforces them only when enabled
        # on the current connection. Keep the project's global behavior intact.
        db.execute("PRAGMA foreign_keys = ON")
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1

        try:
            db.executemany(
                "INSERT INTO usuario_categorias (usuario_id, categoria_id) VALUES (?, ?)",
                [(user_id, category_id) for category_id in category_ids],
            )
            db.commit()

            with pytest.raises(sqlite3.IntegrityError):
                db.execute(
                    "INSERT INTO usuario_categorias (usuario_id, categoria_id) VALUES (?, ?)",
                    (user_id, category_ids[0]),
                )

            with pytest.raises(sqlite3.IntegrityError):
                db.execute(
                    "INSERT INTO usuario_categorias (usuario_id, categoria_id) VALUES (?, ?)",
                    (-1, category_ids[0]),
                )

            with pytest.raises(sqlite3.IntegrityError):
                db.execute(
                    "INSERT INTO usuario_categorias (usuario_id, categoria_id) VALUES (?, ?)",
                    (user_id, -1),
                )

            db.execute(
                "INSERT INTO servicos (profissional_id, categoria) VALUES (?, ?)",
                (user_id, "Categoria independente da solicitação"),
            )
            db.commit()

            stored_specialty = db.execute(
                "SELECT especialidade FROM usuarios WHERE id = ?", (user_id,)
            ).fetchone()["especialidade"]
            assert stored_specialty == "Pedreiro"

            linked_categories = db.execute(
                "SELECT COUNT(*) AS total FROM usuario_categorias WHERE usuario_id = ?",
                (user_id,),
            ).fetchone()["total"]
            assert linked_categories == 2

            service_category = db.execute(
                "SELECT categoria FROM servicos WHERE profissional_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()["categoria"]
            assert service_category == "Categoria independente da solicitação"
        finally:
            db.execute("DELETE FROM servicos WHERE profissional_id = ?", (user_id,))
            db.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
            db.commit()
            db.execute("PRAGMA foreign_keys = OFF")
