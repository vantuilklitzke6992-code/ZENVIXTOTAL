from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from utils.db import get_db
from utils.security import validate_csrf_token
from utils.presence import online_users
import os

auth_bp = Blueprint("auth", __name__)


def _registration_error_redirect(form_data, tipo, current_step):
    session["cadastro_form_data"] = form_data
    session["cadastro_tipo"] = tipo
    session["cadastro_current_step"] = current_step
    return redirect(url_for("auth.cadastro"))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {
        "png",
        "jpg",
        "jpeg",
        "pdf",
    }


def save_uploaded_file(file_storage):
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        return None
    filename = secure_filename(file_storage.filename)
    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    if not upload_folder:
        return None
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file_storage.save(filepath)
    return filename


@auth_bp.route("/cadastro", methods=["GET", "POST"], endpoint="cadastro")
def cadastro():
    if request.method == "POST":
        if not validate_csrf_token():
            flash("Token de segurança inválido. Tente novamente.", "error")
            return redirect(url_for("auth.cadastro"))

        tipo = request.form.get("tipo", "cliente")
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirm_senha = request.form.get("confirm_senha", "")
        telefone = request.form.get("telefone", "").strip()
        estado = request.form.get("estado", "").strip()
        cidade = request.form.get("cidade", "").strip()
        bairro = request.form.get("bairro", "").strip()
        bio = request.form.get("bio", "").strip()
        especialidade = request.form.get("especialidade", "").strip()
        cpf = request.form.get("cpf", "").strip()
        empresa_nome = request.form.get("empresa_nome", "").strip()
        cnpj = request.form.get("cnpj", "").strip()

        documento = request.files.get("documento")
        documento_empresa = request.files.get("documento_empresa")
        foto_perfil_file = request.files.get("foto_perfil")
        logo_empresa_file = request.files.get("logo_empresa")

        form_data = {
            "tipo": tipo,
            "nome": nome,
            "email": email,
            "telefone": telefone,
            "estado": estado,
            "cidade": cidade,
            "bairro": bairro,
            "bio": bio,
            "especialidade": especialidade,
            "cpf": cpf,
            "empresa_nome": empresa_nome,
            "cnpj": cnpj,
        }
        current_step = 2

        if not nome or not email or not senha or not confirm_senha:
            flash("Preencha os dados obrigatórios da conta.", "error")
            return _registration_error_redirect(form_data, tipo, current_step)

        if "@" not in email or "." not in email:
            flash("Informe um e-mail válido.", "error")
            return _registration_error_redirect(form_data, tipo, current_step)

        if senha != confirm_senha:
            flash("As senhas não conferem.", "error")
            return _registration_error_redirect(form_data, tipo, current_step)

        db = get_db()
        existing = db.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            flash(
                "Este e-mail já está em uso. Faça login ou use outro e-mail.", "error"
            )
            return _registration_error_redirect(form_data, tipo, current_step)

        if tipo == "cliente":
            if not estado or not cidade or not telefone:
                current_step = 3
                flash(
                    "Preencha estado, cidade e telefone para finalizar seu cadastro.",
                    "error",
                )
                return _registration_error_redirect(form_data, tipo, current_step)
            approval_status = "Ativo"
            cpf = None
            cnpj = None
            documento = None
            documento_empresa = None
        elif tipo == "profissional":
            if (
                not estado
                or not cidade
                or not telefone
                or not especialidade
                or not bio
                or not cpf
            ):
                current_step = 3
                flash("Preencha todos os dados profissionais obrigatórios.", "error")
                return _registration_error_redirect(form_data, tipo, current_step)
            approval_status = "Pendente"
            empresa_nome = None
            cnpj = None
            documento_empresa = None
        else:
            if not empresa_nome or not estado or not cidade or not telefone or not cnpj:
                current_step = 3
                flash("Preencha todos os dados da empresa obrigatórios.", "error")
                return _registration_error_redirect(form_data, tipo, current_step)
            approval_status = "Pendente"
            cpf = None
            documento = None

        if documento and documento.filename and not allowed_file(documento.filename):
            current_step = 3
            flash("Envie o documento em PDF, JPG ou PNG.", "error")
            return _registration_error_redirect(form_data, tipo, current_step)
        if (
            documento_empresa
            and documento_empresa.filename
            and not allowed_file(documento_empresa.filename)
        ):
            current_step = 3
            flash("Envie o documento da empresa em PDF, JPG ou PNG.", "error")
            return _registration_error_redirect(form_data, tipo, current_step)
        if (
            foto_perfil_file
            and foto_perfil_file.filename
            and not allowed_file(foto_perfil_file.filename)
        ):
            current_step = 3
            flash("Envie a foto de perfil em PDF, JPG ou PNG.", "error")
            return _registration_error_redirect(form_data, tipo, current_step)
        if (
            logo_empresa_file
            and logo_empresa_file.filename
            and not allowed_file(logo_empresa_file.filename)
        ):
            current_step = 3
            flash("Envie o logo da empresa em PDF, JPG ou PNG.", "error")
            return _registration_error_redirect(form_data, tipo, current_step)

        documento_filename = save_uploaded_file(documento)
        documento_empresa_filename = save_uploaded_file(documento_empresa)
        foto_perfil = save_uploaded_file(foto_perfil_file)
        logo_empresa = save_uploaded_file(logo_empresa_file)

        senha_segura = generate_password_hash(senha)
        db.execute(
            "INSERT INTO usuarios (nome, email, senha, telefone, cidade, tipo, bio, especialidade, empresa_nome, estado, bairro, cpf, documento, foto_perfil, cnpj, documento_empresa, logo_empresa, approval_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                nome,
                email,
                senha_segura,
                telefone,
                cidade,
                tipo,
                bio,
                especialidade,
                empresa_nome,
                estado,
                bairro,
                cpf,
                documento_filename,
                foto_perfil,
                cnpj,
                documento_empresa_filename,
                logo_empresa,
                approval_status,
            ),
        )
        db.commit()

        if tipo == "cliente":
            user_id = db.execute(
                "SELECT id FROM usuarios WHERE email = ?", (email,)
            ).fetchone()["id"]
            session.clear()
            session["user_id"] = user_id
            session["user_name"] = nome
            session["user_type"] = tipo
            session["approval_status"] = approval_status
            online_users.add(user_id)
            db.execute(
                'UPDATE usuarios SET status_online = "online", ultimo_acesso = datetime("now") WHERE id = ?',
                (user_id,),
            )
            db.commit()
            flash(
                "Cadastro concluído com sucesso! Bem-vindo ao Zenvix Connect.",
                "success",
            )
            return redirect(url_for("dashboard"))

        flash(
            "Seu cadastro foi enviado com sucesso. Aguarde aprovação para acessar o dashboard.",
            "success",
        )
        return redirect(url_for("auth.login"))

    form_data = session.pop("cadastro_form_data", {})
    tipo = session.pop("cadastro_tipo", "cliente")
    current_step = session.pop("cadastro_current_step", 1)
    return render_template(
        "auth/cadastro.html", form_data=form_data, tipo=tipo, current_step=current_step
    )


@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if request.method == "POST":
        if not validate_csrf_token():
            flash("Token de segurança inválido. Tente novamente.", "error")
            return redirect(url_for("auth.login"))

        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not email or not senha:
            flash("Informe e-mail e senha para acessar.", "error")
            return redirect(url_for("auth.login"))

        db = get_db()
        user = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        if not user or not check_password_hash(user["senha"], senha):
            flash("E-mail ou senha inválidos.", "error")
            return redirect(url_for("auth.login"))

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["nome"]
        session["user_type"] = user["tipo"]
        session["approval_status"] = user["approval_status"] or "Ativo"
        online_users.add(user["id"])
        db.execute(
            'UPDATE usuarios SET status_online = "online", ultimo_acesso = datetime("now") WHERE id = ?',
            (user["id"],),
        )
        db.commit()
        flash(f'Bem-vindo(a), {user["nome"]}!', "success")

        if user["tipo"] == "admin":
            return redirect(url_for("admin_panel"))
        if user["tipo"] == "cliente":
            return redirect(url_for("dashboard_cliente"))
        if user["tipo"] == "profissional":
            return redirect(url_for("dashboard_profissional"))
        if user["tipo"] == "empresa":
            return redirect(url_for("dashboard_empresa"))

        return redirect(url_for("public.home"))

    return render_template("auth/login.html")
