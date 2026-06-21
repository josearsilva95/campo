from datetime import datetime, date
from models import supabase


def _parse_time(t_str: str):
    if not t_str:
        return None
    try:
        return datetime.strptime(t_str, "%H:%M").time()
    except ValueError:
        try:
            return datetime.strptime(t_str, "%H:%M:%S").time()
        except ValueError:
            return None


def calcular_horas(saida_hotel: str, chegada_hotel: str) -> float | None:
    t_saida = _parse_time(saida_hotel)
    t_chegada = _parse_time(chegada_hotel)
    if not t_saida or not t_chegada:
        return None
    dt_saida = datetime.combine(date.today(), t_saida)
    dt_chegada = datetime.combine(date.today(), t_chegada)
    diff = dt_chegada - dt_saida
    if diff.total_seconds() < 0:
        return None
    return round(diff.total_seconds() / 3600, 2)


def buscar_ponto(viagem_id: str, usuario_id: str, data_str: str):
    res = (
        supabase.table("pontos")
        .select("*")
        .eq("viagem_id", viagem_id)
        .eq("usuario_id", usuario_id)
        .eq("data", data_str)
        .execute()
    )
    return res.data[0] if res.data else None


def registrar_ponto(viagem_id: str, usuario_id: str, data_str: str, campos: dict):
    existente = buscar_ponto(viagem_id, usuario_id, data_str)

    if campos.get("chegada_hotel") and campos.get("saida_hotel"):
        saida = campos.get("saida_hotel") or (existente or {}).get("saida_hotel")
        campos["total_horas"] = calcular_horas(saida, campos["chegada_hotel"])
    elif existente and existente.get("saida_hotel") and campos.get("chegada_hotel"):
        campos["total_horas"] = calcular_horas(existente["saida_hotel"], campos["chegada_hotel"])

    if existente:
        res = (
            supabase.table("pontos")
            .update(campos)
            .eq("id", existente["id"])
            .execute()
        )
        return res.data[0] if res.data else None
    else:
        dados = {"viagem_id": viagem_id, "usuario_id": usuario_id, "data": data_str, **campos}
        res = supabase.table("pontos").insert(dados).execute()
        return res.data[0] if res.data else None


def historico_pontos(viagem_id: str):
    res = (
        supabase.table("pontos")
        .select("*, usuario:usuarios(id, nome)")
        .eq("viagem_id", viagem_id)
        .order("data")
        .execute()
    )
    return res.data or []


def total_horas_viagem(viagem_id: str, usuario_id: str) -> float:
    res = (
        supabase.table("pontos")
        .select("total_horas")
        .eq("viagem_id", viagem_id)
        .eq("usuario_id", usuario_id)
        .execute()
    )
    return sum(float(p["total_horas"] or 0) for p in (res.data or []))


def resumo_horas_viagem(viagem_id: str) -> list:
    pontos = historico_pontos(viagem_id)
    resumo: dict[str, dict] = {}
    for p in pontos:
        uid = p["usuario_id"]
        nome = (p.get("usuario") or {}).get("nome", uid)
        if uid not in resumo:
            resumo[uid] = {"nome": nome, "dias": 0, "total_horas": 0.0, "horas_extras": 0.0}
        resumo[uid]["dias"] += 1
        horas = float(p.get("total_horas") or 0)
        resumo[uid]["total_horas"] += horas
        extras = horas - 8.0
        if extras > 0:
            resumo[uid]["horas_extras"] += extras
    for v in resumo.values():
        v["total_horas"] = round(v["total_horas"], 2)
        v["horas_extras"] = round(v["horas_extras"], 2)
    return list(resumo.values())
