from models import supabase


def adicionar_parada(viagem_id: str, local: str, tipo: str, instrucoes: str = None):
    dados = {
        "viagem_id": viagem_id,
        "local": local,
        "tipo": tipo,
        "instrucoes": instrucoes,
        "notificado": False,
    }
    res = supabase.table("paradas").insert(dados).execute()
    return res.data[0] if res.data else None


def listar_paradas(viagem_id: str):
    res = (
        supabase.table("paradas")
        .select("*")
        .eq("viagem_id", viagem_id)
        .order("created_at")
        .execute()
    )
    return res.data or []


def marcar_notificado(parada_id: str):
    supabase.table("paradas").update({"notificado": True}).eq("id", parada_id).execute()
