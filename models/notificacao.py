from models import supabase


def criar_notificacao(usuario_id: str, tipo: str, mensagem: str, viagem_id: str = None):
    try:
        supabase.table("notificacoes").insert({
            "usuario_id": usuario_id,
            "tipo": tipo,
            "mensagem": mensagem,
            "viagem_id": viagem_id,
            "lida": False,
        }).execute()
    except Exception:
        pass


def buscar_nao_lidas(usuario_id: str):
    try:
        res = (
            supabase.table("notificacoes")
            .select("*")
            .eq("usuario_id", usuario_id)
            .eq("lida", False)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def marcar_lida(notificacao_id: str):
    try:
        supabase.table("notificacoes").update({"lida": True}).eq("id", notificacao_id).execute()
    except Exception:
        pass


def marcar_todas_lidas(usuario_id: str):
    try:
        supabase.table("notificacoes").update({"lida": True}).eq("usuario_id", usuario_id).execute()
    except Exception:
        pass
