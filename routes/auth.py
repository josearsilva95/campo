from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.usuario import buscar_por_email, verificar_senha

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    return redirect(url_for("auth.splash"))


@auth_bp.route("/splash")
def splash():
    if session.get("usuario_id"):
        return _redirecionar_perfil(session.get("perfil"))
    return render_template("splash.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("usuario_id"):
        return _redirecionar_perfil(session.get("perfil"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        try:
            usuario = buscar_por_email(email)
        except Exception as e:
            flash(f"Erro de conexão com banco de dados: {e}", "error")
            return render_template("login.html")

        if usuario and verificar_senha(senha, usuario["senha_hash"]):
            session["usuario_id"] = usuario["id"]
            session["nome"] = usuario["nome"]
            session["perfil"] = usuario["perfil"]
            session["telefone"] = usuario.get("telefone", "")
            return _redirecionar_perfil(usuario["perfil"])

        flash("E-mail ou senha incorretos.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


def _redirecionar_perfil(perfil: str):
    if perfil == "adm":
        return redirect(url_for("adm.dashboard"))
    return redirect(url_for("tecnico.dashboard"))
