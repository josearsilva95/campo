import uuid
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from models import viagem as vm
from models import usuario as um
from models.gasto import listar_gastos, lancar_gasto, deletar_gasto, upload_foto, gastos_por_categoria
from models.ponto import registrar_ponto, buscar_ponto, historico_pontos, total_horas_viagem
from models.parada import listar_paradas
from models.checklist import buscar_checklist, salvar_checklist, CAMPOS_BOOL
from models.notificacao import buscar_nao_lidas, marcar_todas_lidas, marcar_lida

tecnico_bp = Blueprint("tecnico", __name__, url_prefix="/tecnico")

CATEGORIAS = ["combustivel", "pedagio", "alimentacao", "hospedagem", "material", "outros"]


def requer_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def verificar_acesso_viagem(viagem_id: str, usuario_id: str):
    viagem = vm.buscar_viagem(viagem_id)
    if not viagem:
        return None, "Viagem não encontrada."

    membros = vm.listar_tecnicos_viagem(viagem_id)
    membros_ids = [m["usuario_id"] for m in membros]

    if usuario_id != viagem["responsavel_id"] and usuario_id not in membros_ids:
        return None, "Você não tem acesso a esta viagem."

    return viagem, None


# ── Dashboard ────────────────────────────────────────────────
@tecnico_bp.route("/dashboard")
@requer_login
def dashboard():
    uid = session["usuario_id"]
    viagens = vm.todas_viagens_do_tecnico(uid)
    notificacoes = buscar_nao_lidas(uid)
    return render_template("tecnico/dashboard.html", viagens=viagens, notificacoes=notificacoes)


@tecnico_bp.route("/notificacoes/marcar-lidas", methods=["POST"])
@requer_login
def marcar_notificacoes_lidas():
    marcar_todas_lidas(session["usuario_id"])
    return redirect(url_for("tecnico.dashboard"))


@tecnico_bp.route("/notificacoes/<nid>/lida", methods=["POST"])
@requer_login
def marcar_notificacao_lida(nid):
    marcar_lida(nid)
    return redirect(request.referrer or url_for("tecnico.dashboard"))


# ── Detalhe da viagem ────────────────────────────────────────
@tecnico_bp.route("/viagem/<id>")
@requer_login
def viagem_detalhe(id):
    uid = session["usuario_id"]
    viagem, erro = verificar_acesso_viagem(id, uid)
    if erro:
        flash(erro, "error")
        return redirect(url_for("tecnico.dashboard"))

    gastos = listar_gastos(id)
    por_categoria = gastos_por_categoria(id)
    equipe = vm.listar_tecnicos_viagem(id)
    paradas = listar_paradas(id)
    checklist_saida = buscar_checklist(id, "saida")
    checklist_retorno = buscar_checklist(id, "retorno")
    e_responsavel = uid == viagem["responsavel_id"]

    return render_template(
        "tecnico/viagem_detalhe.html",
        viagem=viagem,
        gastos=gastos,
        por_categoria=por_categoria,
        equipe=equipe,
        paradas=paradas,
        checklist_saida=checklist_saida,
        checklist_retorno=checklist_retorno,
        e_responsavel=e_responsavel,
    )


# ── Lançar gasto ─────────────────────────────────────────────
@tecnico_bp.route("/viagem/<id>/lancar", methods=["GET", "POST"])
@requer_login
def lancar(id):
    uid = session["usuario_id"]
    viagem, erro = verificar_acesso_viagem(id, uid)
    if erro:
        flash(erro, "error")
        return redirect(url_for("tecnico.dashboard"))

    if uid != viagem["responsavel_id"]:
        flash("Apenas o responsável pode lançar gastos.", "error")
        return redirect(url_for("tecnico.viagem_detalhe", id=id))

    if request.method == "POST":
        categoria = request.form.get("categoria", "outros")
        descricao = request.form.get("descricao", "").strip()
        valor_str = request.form.get("valor", "0").replace(",", ".")
        try:
            valor = float(valor_str)
        except ValueError:
            flash("Valor inválido.", "error")
            return render_template("tecnico/lancar_gasto.html", viagem=viagem, categorias=CATEGORIAS)

        foto_url = None
        foto = request.files.get("foto")
        if foto and foto.filename:
            ext = foto.filename.rsplit(".", 1)[-1].lower() if "." in foto.filename else "jpg"
            filename = f"{id}/{uuid.uuid4()}.{ext}"
            foto_url = upload_foto(foto.read(), filename)
            if not foto_url:
                flash("Gasto salvo, mas a foto não foi enviada. Verifique o bucket 'notas' no Supabase Storage.", "error")

        lancar_gasto(id, categoria, descricao, valor, foto_url)
        if foto_url:
            flash("Gasto lançado com foto!", "success")
        else:
            flash("Gasto lançado com sucesso!", "success")
        return redirect(url_for("tecnico.viagem_detalhe", id=id))

    return render_template("tecnico/lancar_gasto.html", viagem=viagem, categorias=CATEGORIAS)


# ── Deletar gasto ────────────────────────────────────────────
@tecnico_bp.route("/viagem/<id>/deletar-gasto/<gasto_id>", methods=["POST"])
@requer_login
def deletar_gasto_route(id, gasto_id):
    uid = session["usuario_id"]
    viagem, erro = verificar_acesso_viagem(id, uid)
    if erro:
        flash(erro, "error")
        return redirect(url_for("tecnico.dashboard"))

    if uid != viagem["responsavel_id"]:
        flash("Apenas o responsável pode remover gastos.", "error")
        return redirect(url_for("tecnico.viagem_detalhe", id=id))

    deletar_gasto(gasto_id)
    flash("Gasto removido.", "success")
    return redirect(url_for("tecnico.viagem_detalhe", id=id))


# ── Ponto ────────────────────────────────────────────────────
@tecnico_bp.route("/viagem/<id>/ponto", methods=["GET", "POST"])
@requer_login
def ponto(id):
    uid = session["usuario_id"]
    viagem, erro = verificar_acesso_viagem(id, uid)
    if erro:
        flash(erro, "error")
        return redirect(url_for("tecnico.dashboard"))

    hoje = date.today().isoformat()
    ponto_hoje = buscar_ponto(id, uid, hoje)

    if request.method == "POST":
        campo = request.form.get("campo")
        hora = request.form.get("hora")
        if campo and hora:
            registrar_ponto(id, uid, hoje, {campo: hora})
            flash("Ponto registrado!", "success")
            return redirect(url_for("tecnico.ponto", id=id))

    return render_template("tecnico/ponto.html", viagem=viagem, ponto=ponto_hoje, hoje=hoje)


# ── Histórico de pontos ──────────────────────────────────────
@tecnico_bp.route("/viagem/<id>/ponto/historico")
@requer_login
def ponto_historico(id):
    uid = session["usuario_id"]
    viagem, erro = verificar_acesso_viagem(id, uid)
    if erro:
        flash(erro, "error")
        return redirect(url_for("tecnico.dashboard"))

    pontos = historico_pontos(id)
    total = total_horas_viagem(id, uid)
    return render_template("tecnico/ponto_historico.html", viagem=viagem, pontos=pontos, total=total)


# ── Checklist ────────────────────────────────────────────────
@tecnico_bp.route("/viagem/<id>/checklist/<tipo>", methods=["GET", "POST"])
@requer_login
def checklist(id, tipo):
    if tipo not in ("saida", "retorno"):
        flash("Tipo inválido.", "error")
        return redirect(url_for("tecnico.viagem_detalhe", id=id))

    uid = session["usuario_id"]
    viagem, erro = verificar_acesso_viagem(id, uid)
    if erro:
        flash(erro, "error")
        return redirect(url_for("tecnico.dashboard"))

    if uid != viagem["responsavel_id"]:
        flash("Apenas o responsável preenche o checklist.", "error")
        return redirect(url_for("tecnico.viagem_detalhe", id=id))

    checklist_atual = buscar_checklist(id, tipo)

    if request.method == "POST":
        dados: dict = {campo: campo in request.form for campo in CAMPOS_BOOL}
        dados["km"] = request.form.get("km") or None
        dados["observacoes"] = request.form.get("observacoes", "").strip() or None
        salvar_checklist(id, tipo, dados)
        flash(f"Checklist de {tipo} salvo!", "success")
        return redirect(url_for("tecnico.viagem_detalhe", id=id))

    return render_template(
        "tecnico/checklist.html",
        viagem=viagem,
        tipo=tipo,
        checklist=checklist_atual,
        campos_bool=CAMPOS_BOOL,
    )


# ── Solicitar encerramento ───────────────────────────────────
@tecnico_bp.route("/viagem/<id>/encerrar", methods=["GET", "POST"])
@requer_login
def encerrar(id):
    uid = session["usuario_id"]
    viagem, erro = verificar_acesso_viagem(id, uid)
    if erro:
        flash(erro, "error")
        return redirect(url_for("tecnico.dashboard"))

    if uid != viagem["responsavel_id"]:
        flash("Apenas o responsável pode solicitar o encerramento.", "error")
        return redirect(url_for("tecnico.viagem_detalhe", id=id))

    if viagem["status"] != "ativa":
        flash("Esta viagem não pode ser encerrada no status atual.", "error")
        return redirect(url_for("tecnico.viagem_detalhe", id=id))

    gastos = listar_gastos(id)
    por_categoria = gastos_por_categoria(id)

    if request.method == "POST":
        data_retorno = request.form.get("data_retorno_real", date.today().isoformat())
        vm.solicitar_encerramento(id, data_retorno)
        flash("Solicitação de encerramento enviada ao ADM!", "success")
        return redirect(url_for("tecnico.dashboard"))

    return render_template(
        "tecnico/encerrar.html",
        viagem=viagem,
        gastos=gastos,
        por_categoria=por_categoria,
    )
