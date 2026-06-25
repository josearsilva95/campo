from datetime import datetime, date
from models import supabase

CAMPOS_PONTO = ["entrada1", "saida1", "entrada2", "saida2", "entrada3", "saida3"]
_PARES = [("entrada1", "saida1"), ("entrada2", "saida2"), ("entrada3", "saida3")]


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


def calcular_horas_total(dados: dict) -> float | None:
    total = 0.0
    any_pair = False
    for e, s in _PARES:
        t_e = _parse_time(dados.get(e))
        t_s = _parse_time(dados.get(s))
        if t_e and t_s:
            dt_e = datetime.combine(date.today(), t_e)
            dt_s = datetime.combine(date.today(), t_s)
            diff = dt_s - dt_e
            if diff.total_seconds() > 0:
                total += diff.total_seconds() / 3600
                any_pair = True
    return round(total, 2) if any_pair else None


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


def registrar_ponto(viagem_id: str, usuario_id: str, data_str: str, campos: dict,
                    lat: float = None, lon: float = None):
    existente = buscar_ponto(viagem_id, usuario_id, data_str)

    if existente:
        # Dia fechado — sem mais edições
        if existente.get("fechado"):
            return existente

        campos_validos = {k: v for k, v in campos.items() if k in CAMPOS_PONTO}
        if not campos_validos:
            return existente

        if lat is not None and lon is not None and existente.get("lat") is None:
            campos_validos["lat"] = lat
            campos_validos["lon"] = lon

        merged = dict(existente)
        merged.update(campos_validos)
        total = calcular_horas_total(merged)
        if total is not None:
            campos_validos["total_horas"] = total

        res = (
            supabase.table("pontos")
            .update(campos_validos)
            .eq("id", existente["id"])
            .execute()
        )
        return res.data[0] if res.data else None
    else:
        dados = {
            "viagem_id": viagem_id,
            "usuario_id": usuario_id,
            "data": data_str,
            **{k: v for k, v in campos.items() if k in CAMPOS_PONTO},
        }
        if lat is not None and lon is not None:
            dados["lat"] = lat
            dados["lon"] = lon
        total = calcular_horas_total(dados)
        if total is not None:
            dados["total_horas"] = total
        res = supabase.table("pontos").insert(dados).execute()
        return res.data[0] if res.data else None


def fechar_dia(viagem_id: str, usuario_id: str, data_str: str):
    existente = buscar_ponto(viagem_id, usuario_id, data_str)
    if not existente or existente.get("fechado"):
        return existente
    res = (
        supabase.table("pontos")
        .update({"fechado": True})
        .eq("id", existente["id"])
        .execute()
    )
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


def historico_pontos_usuario(viagem_id: str, usuario_id: str):
    res = (
        supabase.table("pontos")
        .select("*")
        .eq("viagem_id", viagem_id)
        .eq("usuario_id", usuario_id)
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
