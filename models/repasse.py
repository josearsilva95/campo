from models import supabase


def registrar_repasse(viagem_id: str, valor: float, descricao: str):
    try:
        res = supabase.table("repasses").insert({
            "viagem_id": viagem_id,
            "valor": valor,
            "descricao": descricao,
        }).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def listar_repasses(viagem_id: str):
    try:
        res = (
            supabase.table("repasses")
            .select("*")
            .eq("viagem_id", viagem_id)
            .order("created_at")
            .execute()
        )
        return res.data or []
    except Exception:
        return []