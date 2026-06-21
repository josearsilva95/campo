from models import supabase


def criar_notificacao(usuario_id: str, tipo: str, mensagem: str, viagem_id: str = None):
    supabase.table("notificacoes").insert({
        "usuario_id": usuario_id,
        "tipo": tipo,
        "mensagem": mensagem,
        "viagem_id": viagem_id,
        "lida": False,
    }).execute()


def buscar_nao_lidas(usuario_id: str):
    res = (
        supabase.table("notificacoes")
        .select("*")
        .eq("usuario_id", usuario_id)
        .eq("lida", False)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def marcar_lida(notificacao_id: str):
    supabase.table("notificacoes").update({"lida": True}).eq("id", notificacao_id).execute()


def marcar_todas_lidas(usuario_id: str):
    supabase.table("notificacoes").update({"lida": True}).eq("usuario_id", usuario_id).execute()
