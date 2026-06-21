import os
import requests
from flask import Blueprint

whatsapp_bp = Blueprint("whatsapp", __name__)


def enviar_whatsapp(telefone: str, mensagem: str):
    url_base = os.getenv("EVOLUTION_API_URL", "")
    instance = os.getenv("EVOLUTION_INSTANCE", "")
    api_key = os.getenv("EVOLUTION_API_KEY", "")

    if not url_base or not instance or not api_key:
        print("[whatsapp] Evolution API não configurada, pulando envio.")
        return

    numero = "".join(filter(str.isdigit, telefone))
    if not numero.startswith("55"):
        numero = "55" + numero

    url = f"{url_base}/message/sendText/{instance}"
    headers = {"apikey": api_key, "Content-Type": "application/json"}
    payload = {"number": numero, "text": mensagem}
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        print(f"[whatsapp] erro ao enviar: {e}")


def msg_escalar_tecnico(nome: str, obra: str, data_saida: str, carro: str, placa: str, funcao: str, valor_caixa: float) -> str:
    url = os.getenv("URL_SISTEMA", "http://localhost:5000")
    return (
        f"👷 Olá, {nome}!\n\n"
        f"Você foi escalado para uma nova viagem:\n\n"
        f"📍 Obra: {obra}\n"
        f"📅 Saída: {data_saida}\n"
        f"🚗 Veículo: {carro} · {placa}\n"
        f"👤 Função: {funcao}\n"
        f"💰 Caixa: R$ {valor_caixa:.2f}\n\n"
        f"Acesse o sistema para ver os detalhes:\n"
        f"🔗 {url}\n\n"
        f"Controle de Viagem"
    )


def msg_nova_parada(obra: str, local: str, tipo: str, instrucoes: str) -> str:
    return (
        f"📌 Nova parada adicionada à viagem!\n\n"
        f"🏗️ Obra: {obra}\n"
        f"📍 Local: {local}\n"
        f"🔖 Tipo: {tipo}\n"
        f"📋 Instruções: {instrucoes or 'Sem instruções adicionais'}\n\n"
        f"Acesse o sistema para ver a rota atualizada.\n\nControle de Viagem"
    )


def msg_encerramento_aprovado(obra: str, data_retorno: str) -> str:
    return (
        f"✅ Encerramento aprovado!\n\n"
        f"🏗️ Obra: {obra}\n"
        f"📅 Data de retorno: {data_retorno}\n\n"
        f"Sua prestação de contas foi aceita pelo gestor.\n\nControle de Viagem"
    )
