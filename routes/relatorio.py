from datetime import datetime
from flask import Blueprint, render_template, request, make_response, session, redirect, url_for, flash
from functools import wraps
from models import viagem as vm
from models.gasto import listar_gastos, gastos_por_categoria
from models.ponto import historico_pontos, resumo_horas_viagem
from models.parada import listar_paradas

relatorio_bp = Blueprint("relatorio", __name__, url_prefix="/relatorio")


def requer_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@relatorio_bp.route("/viagem/<id>/gastos")
@requer_login
def pdf_gastos(id):
    viagem = vm.buscar_viagem(id)
    if not viagem:
        flash("Viagem não encontrada.", "error")
        return redirect(url_for("auth.login"))

    gastos = listar_gastos(id)
    por_categoria = gastos_por_categoria(id)
    equipe = vm.listar_tecnicos_viagem(id)
    paradas = listar_paradas(id)

    return render_template(
        "relatorios/gastos_pdf.html",
        viagem=viagem,
        gastos=gastos,
        por_categoria=por_categoria,
        equipe=equipe,
        paradas=paradas,
        now=datetime.now,
    )


@relatorio_bp.route("/viagem/<id>/horas")
@requer_login
def pdf_horas(id):
    viagem = vm.buscar_viagem(id)
    if not viagem:
        flash("Viagem não encontrada.", "error")
        return redirect(url_for("auth.login"))

    pontos = historico_pontos(id)
    resumo = resumo_horas_viagem(id)
    equipe = vm.listar_tecnicos_viagem(id)

    return render_template(
        "relatorios/horas_pdf.html",
        viagem=viagem,
        pontos=pontos,
        resumo=resumo,
        equipe=equipe,
        now=datetime.now,
    )
