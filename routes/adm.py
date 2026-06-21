import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from models import viagem as vm
from models import usuario as um
from models.gasto import listar_gastos, gastos_por_categoria
from models.parada import adicionar_parada, listar_paradas, marcar_notificado
from models.checklist import buscar_checklist
from routes.whatsapp import (
    enviar_whatsapp,
    msg_escalar_tecnico,
    msg_nova_parada,
    msg_encerramento_aprovado,
)

adm_bp = Blueprint("adm", __name__, url_prefix="/adm")


def requer_adm(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("auth.login"))
        if session.get("perfil") != "adm":
            flash("Acesso restrito ao administrador.", "error")
            return redirect(url_for("tecnico.dashboard"))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ────────────────────────────────────────────────
@adm_bp.route("/dashboard")
@requer_adm
def dashboard():
    viagens = vm.listar_viagens()
    ativas = [v for v in viagens if v["status"] == "ativa"]
    pendentes = [v for v in viagens if v["status"] == "encerramento_pendente"]
    encerradas = [v for v in viagens if v["status"] == "encerrada"]
    return render_template(
        "adm/dashboard.html",
        viagens=viagens,
        ativas=ativas,
        pendentes=pendentes,
        encerradas=encerradas,
    )


# ── Nova viagem ──────────────────────────────────────────────
@adm_bp.route("/nova-viagem", methods=["GET", "POST"])
@requer_adm
def nova_viagem():
    tecnicos = um.listar_tecnicos()

    if request.method == "POST":
        dados = {
            "obra": request.form.get("obra", "").strip(),
            "data_saida": request.form.get("data_saida"),
            "data_retorno_prevista": request.form.get("data_retorno_prevista") or None,
            "carro": request.form.get("carro", "").strip(),
            "placa": request.form.get("placa", "").strip().upper(),
            "responsavel_id": request.form.get("responsavel_id"),
            "caixa_valor": float(request.form.get("caixa_valor", 0) or 0),
            "caixa_transferido": 0,
            "observacoes": request.form.get("observacoes", "").strip() or None,
            "status": "ativa",
        }

        membros_ids = request.form.getlist("membros")

        viagem = vm.criar_viagem(dados)
        if not viagem:
            flash("Erro ao criar viagem.", "error")
            return render_template("adm/nova_viagem.html", tecnicos=tecnicos)

        viagem_id = viagem["id"]

        # Adiciona responsável como membro também
        vm.adicionar_tecnico_viagem(viagem_id, dados["responsavel_id"])
        for mid in membros_ids:
            if mid != dados["responsavel_id"]:
                vm.adicionar_tecnico_viagem(viagem_id, mid)

        # WhatsApp — responsável
        responsavel = um.buscar_por_id(dados["responsavel_id"])
        if responsavel and responsavel.get("telefone"):
            mensagem = msg_escalar_tecnico(
                nome=responsavel["nome"],
                obra=dados["obra"],
                data_saida=dados["data_saida"],
                carro=dados["carro"],
                placa=dados["placa"],
                funcao="Responsável",
                valor_caixa=dados["caixa_valor"],
            )
            enviar_whatsapp(responsavel["telefone"], mensagem)

        # WhatsApp — membros
        for mid in membros_ids:
            if mid != dados["responsavel_id"]:
                tecnico = um.buscar_por_id(mid)
                if tecnico and tecnico.get("telefone"):
                    mensagem = msg_escalar_tecnico(
                        nome=tecnico["nome"],
                        obra=dados["obra"],
                        data_saida=dados["data_saida"],
                        carro=dados["carro"],
                        placa=dados["placa"],
                        funcao="Técnico",
                        valor_caixa=dados["caixa_valor"],
                    )
                    enviar_whatsapp(tecnico["telefone"], mensagem)

        flash("Viagem criada com sucesso!", "success")
        return redirect(url_for("adm.viagem_detalhe", id=viagem_id))

    return render_template("adm/nova_viagem.html", tecnicos=tecnicos)


# ── Editar viagem ────────────────────────────────────────────
@adm_bp.route("/viagem/<id>/editar", methods=["GET", "POST"])
@requer_adm
def editar_viagem(id):
    viagem = vm.buscar_viagem(id)
    if not viagem:
        flash("Viagem não encontrada.", "error")
        return redirect(url_for("adm.dashboard"))

    tecnicos = um.listar_tecnicos()
    membros_atuais = vm.listar_tecnicos_viagem(id)
    membros_ids = [m["usuario_id"] for m in membros_atuais]

    if request.method == "POST":
        dados = {
            "obra": request.form.get("obra", "").strip(),
            "data_saida": request.form.get("data_saida"),
            "data_retorno_prevista": request.form.get("data_retorno_prevista") or None,
            "carro": request.form.get("carro", "").strip(),
            "placa": request.form.get("placa", "").strip().upper(),
            "responsavel_id": request.form.get("responsavel_id"),
            "caixa_valor": float(request.form.get("caixa_valor", 0) or 0),
            "observacoes": request.form.get("observacoes", "").strip() or None,
        }

        novos_membros = request.form.getlist("membros")

        vm.atualizar_viagem(id, dados)
        vm.remover_tecnicos_viagem(id)
        vm.adicionar_tecnico_viagem(id, dados["responsavel_id"])
        for mid in novos_membros:
            if mid != dados["responsavel_id"]:
                vm.adicionar_tecnico_viagem(id, mid)

        flash("Viagem atualizada com sucesso!", "success")
        return redirect(url_for("adm.viagem_detalhe", id=id))

    return render_template(
        "adm/editar_viagem.html",
        viagem=viagem,
        tecnicos=tecnicos,
        membros_ids=membros_ids,
    )


# ── Detalhe da viagem ────────────────────────────────────────
@adm_bp.route("/viagem/<id>")
@requer_adm
def viagem_detalhe(id):
    viagem = vm.buscar_viagem(id)
    if not viagem:
        flash("Viagem não encontrada.", "error")
        return redirect(url_for("adm.dashboard"))

    gastos = listar_gastos(id)
    por_categoria = gastos_por_categoria(id)
    equipe = vm.listar_tecnicos_viagem(id)
    paradas = listar_paradas(id)
    checklist_saida = buscar_checklist(id, "saida")
    checklist_retorno = buscar_checklist(id, "retorno")

    return render_template(
        "adm/viagem_detalhe.html",
        viagem=viagem,
        gastos=gastos,
        por_categoria=por_categoria,
        equipe=equipe,
        paradas=paradas,
        checklist_saida=checklist_saida,
        checklist_retorno=checklist_retorno,
    )


# ── Adicionar parada ─────────────────────────────────────────
@adm_bp.route("/viagem/<id>/parada", methods=["POST"])
@requer_adm
def add_parada(id):
    viagem = vm.buscar_viagem(id)
    if not viagem:
        flash("Viagem não encontrada.", "error")
        return redirect(url_for("adm.dashboard"))

    local = request.form.get("local", "").strip()
    tipo = request.form.get("tipo", "outro")
    instrucoes = request.form.get("instrucoes", "").strip() or None

    if not local:
        flash("Informe o local da parada.", "error")
        return redirect(url_for("adm.viagem_detalhe", id=id))

    parada = adicionar_parada(id, local, tipo, instrucoes)

    # Notificar responsável
    responsavel = um.buscar_por_id(viagem["responsavel_id"])
    if responsavel and responsavel.get("telefone"):
        mensagem = msg_nova_parada(viagem["obra"], local, tipo, instrucoes)
        enviar_whatsapp(responsavel["telefone"], mensagem)
        if parada:
            marcar_notificado(parada["id"])

    flash("Parada adicionada e responsável notificado.", "success")
    return redirect(url_for("adm.viagem_detalhe", id=id))


# ── Revisar encerramento ─────────────────────────────────────
@adm_bp.route("/viagem/<id>/encerramento")
@requer_adm
def revisar_encerramento(id):
    viagem = vm.buscar_viagem(id)
    if not viagem:
        flash("Viagem não encontrada.", "error")
        return redirect(url_for("adm.dashboard"))

    gastos = listar_gastos(id)
    por_categoria = gastos_por_categoria(id)
    equipe = vm.listar_tecnicos_viagem(id)
    viagens_ativas = vm.listar_viagens_ativas_exceto(id)

    return render_template(
        "adm/revisar_encerramento.html",
        viagem=viagem,
        gastos=gastos,
        por_categoria=por_categoria,
        equipe=equipe,
        viagens_ativas=viagens_ativas,
    )


# ── Aprovar encerramento ─────────────────────────────────────
@adm_bp.route("/viagem/<id>/aprovar-encerramento", methods=["POST"])
@requer_adm
def aprovar_encerramento(id):
    viagem = vm.buscar_viagem(id)
    if not viagem:
        flash("Viagem não encontrada.", "error")
        return redirect(url_for("adm.dashboard"))

    data_retorno_real = request.form.get("data_retorno_real", viagem.get("data_retorno_real", ""))
    acao = request.form.get("acao", "devolver")
    saldo_devolvido = float(request.form.get("saldo_devolvido", 0) or 0)
    viagem_destino_id = request.form.get("viagem_destino_id") or None
    valor_transferir = float(request.form.get("valor_transferir", 0) or 0)

    if acao == "transferir" and viagem_destino_id and valor_transferir > 0:
        vm.aprovar_encerramento(
            id,
            data_retorno_real,
            viagem_destino_id=viagem_destino_id,
            valor_transferir=valor_transferir,
        )
    else:
        vm.aprovar_encerramento(id, data_retorno_real, saldo_devolvido=saldo_devolvido)

    # WhatsApp — responsável
    responsavel = um.buscar_por_id(viagem["responsavel_id"])
    if responsavel and responsavel.get("telefone"):
        mensagem = msg_encerramento_aprovado(viagem["obra"], data_retorno_real)
        enviar_whatsapp(responsavel["telefone"], mensagem)

    flash("Encerramento aprovado com sucesso!", "success")
    return redirect(url_for("adm.dashboard"))


# ── Excluir viagem ───────────────────────────────────────────
@adm_bp.route("/viagem/<id>/excluir", methods=["POST"])
@requer_adm
def excluir_viagem(id):
    viagem = vm.buscar_viagem(id)
    if not viagem:
        flash("Viagem não encontrada.", "error")
        return redirect(url_for("adm.dashboard"))
    vm.excluir_viagem(id)
    flash(f"Viagem '{viagem['obra']}' excluída com sucesso.", "success")
    return redirect(url_for("adm.dashboard"))


# ── Encerramento direto pelo ADM ─────────────────────────────
@adm_bp.route("/viagem/<id>/encerrar", methods=["POST"])
@requer_adm
def encerrar_direto(id):
    viagem = vm.buscar_viagem(id)
    if not viagem:
        flash("Viagem não encontrada.", "error")
        return redirect(url_for("adm.dashboard"))

    data_retorno_real = request.form.get("data_retorno_real", "")
    saldo_devolvido = float(request.form.get("saldo_devolvido", 0) or 0)

    vm.aprovar_encerramento(id, data_retorno_real, saldo_devolvido=saldo_devolvido)
    flash("Viagem encerrada.", "success")
    return redirect(url_for("adm.dashboard"))


# ── Funcionários ─────────────────────────────────────────────
@adm_bp.route("/funcionarios")
@requer_adm
def funcionarios():
    todos = um.listar_todos()
    return render_template("adm/funcionarios.html", funcionarios=todos)


@adm_bp.route("/funcionarios/novo", methods=["POST"])
@requer_adm
def novo_funcionario():
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")
    perfil = request.form.get("perfil", "tecnico")
    telefone = request.form.get("telefone", "").strip() or None

    if not nome or not email or not senha:
        flash("Preencha todos os campos obrigatórios.", "error")
        return redirect(url_for("adm.funcionarios"))

    usuario = um.criar_usuario(nome, email, senha, perfil, telefone)
    if not usuario:
        flash("Erro ao criar funcionário.", "error")
    else:
        flash(f"Funcionário {nome} criado com sucesso!", "success")

    return redirect(url_for("adm.funcionarios"))


@adm_bp.route("/funcionarios/<id>/editar", methods=["POST"])
@requer_adm
def editar_funcionario(id):
    dados = {}
    if request.form.get("nome"):
        dados["nome"] = request.form.get("nome").strip()
    if request.form.get("email"):
        dados["email"] = request.form.get("email").strip().lower()
    if request.form.get("telefone") is not None:
        dados["telefone"] = request.form.get("telefone").strip() or None
    if request.form.get("perfil"):
        dados["perfil"] = request.form.get("perfil")

    um.atualizar_usuario(id, dados)
    flash("Funcionário atualizado.", "success")
    return redirect(url_for("adm.funcionarios"))


@adm_bp.route("/funcionarios/<id>/senha", methods=["POST"])
@requer_adm
def redefinir_senha(id):
    nova = request.form.get("nova_senha", "")
    if len(nova) < 6:
        flash("A senha deve ter ao menos 6 caracteres.", "error")
        return redirect(url_for("adm.funcionarios"))
    um.redefinir_senha(id, nova)
    flash("Senha redefinida.", "success")
    return redirect(url_for("adm.funcionarios"))


@adm_bp.route("/funcionarios/<id>/excluir", methods=["POST"])
@requer_adm
def excluir_funcionario(id):
    um.excluir_usuario(id)
    flash("Funcionário excluído.", "success")
    return redirect(url_for("adm.funcionarios"))
