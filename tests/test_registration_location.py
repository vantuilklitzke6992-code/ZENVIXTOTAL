from io import BytesIO
from uuid import uuid4

import pytest

import app as app_module
import routes.auth as auth_routes
from utils.db import get_db


@pytest.mark.parametrize("account_type", ["cliente", "profissional", "empresa"])
def test_registration_rejects_city_outside_initial_launch(account_type):
    email = f"{account_type}_{uuid4().hex}@test.com"

    with app_module.app.test_client() as client:
        with client.session_transaction() as session:
            session["_csrf_token"] = "registration-location-test"

        response = client.post(
            "/cadastro",
            data={
                "_csrf_token": "registration-location-test",
                "tipo": account_type,
                "nome": "Cadastro de teste",
                "email": email,
                "senha": "test-password",
                "confirm_senha": "test-password",
                "cidade": "Vitória",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"apenas em S\xc3\xa3o Gabriel da Palha" in response.data

    with app_module.app.app_context():
        row = get_db().execute(
            "SELECT id FROM usuarios WHERE email = ?",
            (email,),
        ).fetchone()
    assert row is None


@pytest.mark.parametrize("account_type", ["cliente", "profissional", "empresa"])
def test_registration_stores_canonical_initial_city(
    account_type,
    monkeypatch,
):
    email = f"{account_type}_{uuid4().hex}@test.com"
    monkeypatch.setattr(
        auth_routes,
        "save_uploaded_file",
        lambda file_storage, file_validator=auth_routes.allowed_file: (
            "test-document.pdf" if file_storage else None
        ),
    )
    form_data = {
        "_csrf_token": "registration-location-test",
        "tipo": account_type,
        "nome": "Cadastro de teste",
        "email": email,
        "senha": "test-password",
        "confirm_senha": "test-password",
        "telefone": "2799999999",
        "estado": "Espírito Santo",
        "cidade": "São Gabriel da Palha",
    }

    if account_type == "profissional":
        form_data.update(
            {"especialidade": "Pedreiro", "bio": "Descrição de teste", "cpf": "12345678901"}
        )
        form_data["documento"] = (BytesIO(b"document"), "documento.pdf")
    elif account_type == "empresa":
        form_data.update(
            {"empresa_nome": "Empresa de teste", "cnpj": "12345678000199"}
        )
        form_data["documento_empresa"] = (BytesIO(b"document"), "documento.pdf")

    with app_module.app.test_client() as client:
        with client.session_transaction() as session:
            session["_csrf_token"] = "registration-location-test"

        response = client.post("/cadastro", data=form_data)

    assert response.status_code == 302

    with app_module.app.app_context():
        db = get_db()
        try:
            row = db.execute(
                "SELECT cidade FROM usuarios WHERE email = ?",
                (email,),
            ).fetchone()
            assert row is not None
            assert row["cidade"] == "São Gabriel da Palha"
        finally:
            db.execute("DELETE FROM usuarios WHERE email = ?", (email,))
            db.commit()
