from models import supabase


CAMPOS_BOOL = ["pneus", "combustivel", "oleo", "agua", "lanternas", "macaco", "extintor", "documentos"]


def buscar_checklist(viagem_id: str, tipo: str):
    res = (
        supabase.table("checklists")
        .select("*")
        .eq("viagem_id", viagem_id)
        .eq("tipo", tipo)
        .execute()
    )
    return res.data[0] if res.data else None


def salvar_checklist(viagem_id: str, tipo: str, dados: dict):
    existente = buscar_checklist(viagem_id, tipo)
    if existente:
        res = (
            supabase.table("checklists")
            .update(dados)
            .eq("id", existente["id"])
            .execute()
        )
    else:
        payload = {"viagem_id": viagem_id, "tipo": tipo, **dados}
        res = supabase.table("checklists").insert(payload).execute()
    return res.data[0] if res.data else None
