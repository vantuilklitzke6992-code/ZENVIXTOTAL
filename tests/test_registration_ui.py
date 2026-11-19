import re
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
        city_field = re.search(r'<input[^>]*id="cidade"[^>]*>', html)
        assert city_field is not None
        assert 'value="São Gabriel da Palha"' in city_field.group()
        assert "readonly" in city_field.group()
        assert '<select class="form-control" id="cidade"' not in html
        assert 'id="especialidade"' in html
        assert "<select" in html
        assert "Nenhuma categoria disponível" in html


def test_home_header_has_single_about_link_and_preserves_contact_information():
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        header = html.split("</header>", 1)[0]

        assert header.count('href="/#sobre-o-zenvix"') == 1
        assert "Sobre o Zenvix" in header
        assert 'href="/#como-funciona"' not in header
        assert 'href="/#contato"' not in header
        assert 'id="sobre-o-zenvix"' in html
        assert 'id="contato"' in html
        assert 'href="mailto:ismaelklitzke07@gmail.com"' in html


def test_login_and_registration_password_fields_have_visibility_controls():
    with app.test_client() as client:
        login_html = client.get("/login").get_data(as_text=True)
        registration_html = client.get("/cadastro").get_data(as_text=True)

    assert 'id="senha" name="senha" type="password"' in login_html
    assert 'data-password-toggle="senha"' in login_html
    assert 'id="senha" name="senha"' in registration_html
    assert 'type="password"' in registration_html
    assert 'data-password-toggle="senha"' in registration_html
    assert 'data-password-toggle="confirm_senha"' in registration_html


def test_cadastro_ignora_categoria_vazia_sem_quebrar_a_pagina():
    with app.test_client() as client:
        response = client.get("/cadastro")
        assert response.status_code == 200
        assert b"Nenhuma categoria dispon\xc3\xadvel" in response.data
