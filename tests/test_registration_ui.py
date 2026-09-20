import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.app_init import app
from utils.db import get_db


def setup_module():
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM categorias")
        db.commit()


def test_cadastro_renders_estado_cidade_e_especialidade_em_selects():
    with app.test_client() as client:
        response = client.get("/cadastro")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'id="estado"' in html
        assert 'id="cidade"' in html
        assert 'id="especialidade"' in html
        assert "<select" in html
        assert "Nenhuma categoria disponível" in html


def test_cadastro_ignora_categoria_vazia_sem_quebrar_a_pagina():
    with app.test_client() as client:
        response = client.get("/cadastro")
        assert response.status_code == 200
        assert b"Nenhuma categoria dispon\xc3\xadvel" in response.data
