import os
import re
import sqlite3
from flask import g

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def add_column_if_missing(table, column_name, column_type_def):
    db = get_db()
    columns = [
        row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()
    ]
    if column_name not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type_def}")


def normalize_usuarios_schema():
    db = get_db()
    rows = db.execute("PRAGMA table_info(usuarios)").fetchall()
    existing_columns = [row["name"] for row in rows]
    expected_columns = [
        "id",
        "nome",
        "email",
        "senha",
        "telefone",
        "cidade",
        "tipo",
        "bio",
        "especialidade",
        "empresa_nome",
        "estado",
        "bairro",
        "cpf",
        "documento",
        "foto_perfil",
        "cnpj",
        "documento_empresa",
        "logo_empresa",
        "approval_status",
        "deletion_requested",
        "rejection_reason",
        "status_online",
        "ultimo_acesso",
    ]

    invalid_columns = [
        col for col in existing_columns if col and col not in expected_columns
    ]
    if not invalid_columns:
        return

    valid_columns = [col for col in expected_columns if col in existing_columns]
    columns_to_copy = ", ".join(valid_columns)

    db.execute("ALTER TABLE usuarios RENAME TO usuarios_old")
    db.execute("""
        CREATE TABLE usuarios (
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
            approval_status TEXT,
            deletion_requested INTEGER DEFAULT 0,
            rejection_reason TEXT,
            status_online TEXT DEFAULT 'offline',
            ultimo_acesso TEXT
        )
        """)
    if columns_to_copy:
        db.execute(
            f"INSERT INTO usuarios ({columns_to_copy}) SELECT {columns_to_copy} FROM usuarios_old"
        )
    db.execute("DROP TABLE usuarios_old")


def repair_usuarios_foreign_keys():
    db = get_db()
    tables = db.execute(
        "SELECT name, sql FROM sqlite_master "
        "WHERE type = 'table' AND sql IS NOT NULL AND sql LIKE '%usuarios_old%'"
    ).fetchall()
    if not tables:
        return

    foreign_keys_enabled = db.execute("PRAGMA foreign_keys").fetchone()[0]
    legacy_alter_table = db.execute("PRAGMA legacy_alter_table").fetchone()[0]
    db.commit()
    db.execute("PRAGMA foreign_keys = OFF")
    db.execute("PRAGMA legacy_alter_table = ON")

    try:
        db.execute("BEGIN")
        for table in tables:
            table_name = table["name"]
            temporary_name = f"__fk_repair_{table_name}"
            table_sql = re.sub(
                r"usuarios_old", "usuarios", table["sql"], flags=re.IGNORECASE
            )
            objects = db.execute(
                "SELECT type, name, sql FROM sqlite_master "
                "WHERE tbl_name = ? AND type IN ('index', 'trigger') "
                "AND sql IS NOT NULL",
                (table_name,),
            ).fetchall()
            columns = [
                row["name"] for row in db.execute(f'PRAGMA table_info("{table_name}")')
            ]
            quoted_columns = ", ".join(f'"{column}"' for column in columns)

            for obj in objects:
                db.execute(f'DROP {obj["type"].upper()} "{obj["name"]}"')
            db.execute(f'ALTER TABLE "{table_name}" RENAME TO "{temporary_name}"')
            db.execute(table_sql)
            db.execute(
                f'INSERT INTO "{table_name}" ({quoted_columns}) '
                f'SELECT {quoted_columns} FROM "{temporary_name}"'
            )
            db.execute(f'DROP TABLE "{temporary_name}"')
            for obj in objects:
                db.execute(
                    re.sub(
                        rf"(?i)\b{re.escape(temporary_name)}\b",
                        table_name,
                        obj["sql"],
                    )
                )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.execute(f"PRAGMA legacy_alter_table = {legacy_alter_table}")
        db.execute(f"PRAGMA foreign_keys = {foreign_keys_enabled}")


def init_db():
    db = get_db()
    db.execute("""
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
        """)
    db.execute("""
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
        """)
    db.execute("""
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
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS favoritos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            profissional_id INTEGER,
            FOREIGN KEY(cliente_id) REFERENCES usuarios(id),
            FOREIGN KEY(profissional_id) REFERENCES usuarios(id)
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            servico_id INTEGER,
            remetente_id INTEGER,
            mensagem TEXT,
            criado_em TEXT,
            FOREIGN KEY(servico_id) REFERENCES servicos(id),
            FOREIGN KEY(remetente_id) REFERENCES usuarios(id)
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS servico_propostas_valor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            servico_id INTEGER NOT NULL,
            valor_anterior REAL NOT NULL,
            valor_proposto REAL NOT NULL,
            proponente_id INTEGER NOT NULL,
            estado TEXT DEFAULT 'Pendente',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            respondido_em TEXT,
            FOREIGN KEY(servico_id) REFERENCES servicos(id),
            FOREIGN KEY(proponente_id) REFERENCES usuarios(id)
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS disponibilidade (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profissional_id INTEGER,
            dia_semana TEXT,
            horario_inicio TEXT,
            horario_fim TEXT,
            FOREIGN KEY(profissional_id) REFERENCES usuarios(id)
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS servicos_empresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            titulo TEXT,
            descricao TEXT,
            valor REAL,
            FOREIGN KEY(empresa_id) REFERENCES usuarios(id)
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS conversas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS conversa_participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversa_id INTEGER,
            usuario_id INTEGER,
            FOREIGN KEY(conversa_id) REFERENCES conversas(id),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
        """)
    db.execute("""
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
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS bloqueios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bloqueador_id INTEGER NOT NULL,
            bloqueado_id INTEGER NOT NULL,
            motivo TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            removido_em TEXT,
            ativo INTEGER DEFAULT 1,
            FOREIGN KEY(bloqueador_id) REFERENCES usuarios(id),
            FOREIGN KEY(bloqueado_id) REFERENCES usuarios(id)
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS denuncias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            denunciante_id INTEGER NOT NULL,
            denunciado_id INTEGER,
            servico_id INTEGER,
            conversa_id INTEGER,
            descricao TEXT NOT NULL,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Aberta',
            dados_investigacao TEXT,
            FOREIGN KEY(denunciante_id) REFERENCES usuarios(id),
            FOREIGN KEY(denunciado_id) REFERENCES usuarios(id),
            FOREIGN KEY(servico_id) REFERENCES servicos(id),
            FOREIGN KEY(conversa_id) REFERENCES conversas(id)
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS mensagem_historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tabela_origem TEXT NOT NULL,
            mensagem_id INTEGER NOT NULL,
            mensagem_original TEXT,
            mensagem_anterior TEXT,
            alterado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            usuario_id INTEGER,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS convites_empresa_profissional (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            profissional_id INTEGER NOT NULL,
            estado TEXT DEFAULT 'Pendente',
            mensagem TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TEXT,
            resposta_em TEXT,
            historico TEXT,
            FOREIGN KEY(empresa_id) REFERENCES usuarios(id),
            FOREIGN KEY(profissional_id) REFERENCES usuarios(id)
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS vinculos_empresa_profissional (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            profissional_id INTEGER NOT NULL,
            iniciado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            encerrado_em TEXT,
            status TEXT DEFAULT 'Ativo',
            observacao TEXT,
            FOREIGN KEY(empresa_id) REFERENCES usuarios(id),
            FOREIGN KEY(profissional_id) REFERENCES usuarios(id)
        )
        """)
    normalize_usuarios_schema()
    repair_usuarios_foreign_keys()
    add_column_if_missing("usuarios", "bio", "TEXT")
    add_column_if_missing("usuarios", "especialidade", "TEXT")
    add_column_if_missing("usuarios", "empresa_nome", "TEXT")
    add_column_if_missing("usuarios", "estado", "TEXT")
    add_column_if_missing("usuarios", "bairro", "TEXT")
    add_column_if_missing("usuarios", "cpf", "TEXT")
    add_column_if_missing("usuarios", "documento", "TEXT")
    add_column_if_missing("usuarios", "foto_perfil", "TEXT")
    add_column_if_missing("usuarios", "cnpj", "TEXT")
    add_column_if_missing("usuarios", "documento_empresa", "TEXT")
    add_column_if_missing("usuarios", "logo_empresa", "TEXT")
    add_column_if_missing("usuarios", "approval_status", "TEXT")
    add_column_if_missing("usuarios", "status_online", "TEXT DEFAULT 'offline'")
    add_column_if_missing("usuarios", "ultimo_acesso", "TEXT")
    add_column_if_missing("usuarios", "deletion_requested", "INTEGER DEFAULT 0")
    add_column_if_missing("usuarios", "rejection_reason", "TEXT")
    add_column_if_missing("servicos", "status", "TEXT")
    add_column_if_missing("servicos", "valor", "REAL")
    add_column_if_missing("servicos", "data_solicitacao", "TEXT")
    add_column_if_missing("servicos", "motivo_cancelamento", "TEXT")
    add_column_if_missing(
        "servicos", "cliente_confirmou_conclusao", "INTEGER DEFAULT 0"
    )
    add_column_if_missing(
        "servicos", "profissional_confirmou_conclusao", "INTEGER DEFAULT 0"
    )
    add_column_if_missing("servicos", "data_cancelamento", "TEXT")
    add_column_if_missing("servicos", "data_conclusao", "TEXT")
    add_column_if_missing("servicos", "valor_historico", "TEXT")
    add_column_if_missing("avaliacoes", "servico_id", "INTEGER")
    add_column_if_missing("avaliacoes", "criado_em", "TEXT")
    add_column_if_missing("avaliacoes", "editado_em", "TEXT")
    add_column_if_missing("avaliacoes", "edicoes", "INTEGER DEFAULT 0")
    add_column_if_missing("avaliacoes", "resposta_publica", "TEXT")
    add_column_if_missing("mensagens", "apagado", "INTEGER DEFAULT 0")
    add_column_if_missing("mensagens", "apagado_em", "TEXT")
    add_column_if_missing("mensagens", "editado_em", "TEXT")
    add_column_if_missing("conversa_mensagens", "apagado", "INTEGER DEFAULT 0")
    add_column_if_missing("conversa_mensagens", "apagado_em", "TEXT")
    add_column_if_missing("conversa_mensagens", "editado_em", "TEXT")
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_bloqueios_bloqueador ON bloqueios(bloqueador_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_bloqueios_bloqueado ON bloqueios(bloqueado_id)"
    )
    db.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_bloqueios_ativo_unique ON bloqueios(bloqueador_id, bloqueado_id) WHERE ativo = 1"
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_denuncias_status ON denuncias(status)")
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_denuncias_servico ON denuncias(servico_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_denuncias_conversa ON denuncias(conversa_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_mensagem_historico_mensagem ON mensagem_historico(tabela_origem, mensagem_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_convites_empresa_profissional_estado ON convites_empresa_profissional(empresa_id, profissional_id, estado)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_vinculos_empresa_profissional_status ON vinculos_empresa_profissional(empresa_id, profissional_id, status)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_servico_propostas_valor_servico ON servico_propostas_valor(servico_id, estado)"
    )
    db.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_servicos_sync_status_after_confirmation_update
        AFTER UPDATE OF cliente_confirmou_conclusao, profissional_confirmou_conclusao ON servicos
        WHEN NEW.cliente_confirmou_conclusao <> OLD.cliente_confirmou_conclusao OR NEW.profissional_confirmou_conclusao <> OLD.profissional_confirmou_conclusao
        BEGIN
            UPDATE servicos
            SET status = CASE
                WHEN NEW.status = 'Cancelado' THEN 'Cancelado'
                WHEN NEW.status = 'Concluído' THEN 'Concluído'
                WHEN NEW.cliente_confirmou_conclusao = 1 AND NEW.profissional_confirmou_conclusao = 1 THEN 'Concluído'
                WHEN NEW.cliente_confirmou_conclusao = 1 OR NEW.profissional_confirmou_conclusao = 1 THEN 'Aguardando confirmação'
                ELSE NEW.status
            END,
            data_conclusao = CASE
                WHEN NEW.cliente_confirmou_conclusao = 1 AND NEW.profissional_confirmou_conclusao = 1 THEN datetime('now')
                ELSE NULL
            END
            WHERE id = NEW.id;
        END;
        """)
    db.commit()
