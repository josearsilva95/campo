from models import supabase
from models.gasto import total_gastos


def listar_viagens():
    res = (
        supabase.table("viagens")
        .select("*, responsavel:usuarios!viagens_responsavel_id_fkey(id, nome, email, telefone)")
        .order("created_at", desc=True)
        .execute()
    )
    viagens = res.data or []
    for v in viagens:
        v["total_gastos"] = total_gastos(v["id"])
        caixa = float(v.get("caixa_valor") or 0)
        transferido = float(v.get("caixa_transferido") or 0)
        v["saldo_disponivel"] = caixa + transferido - v["total_gastos"]
    return viagens


def buscar_viagem(viagem_id: str):
    res = (
        supabase.table("viagens")
        .select("*, responsavel:usuarios!viagens_responsavel_id_fkey(id, nome, email, telefone)")
        .eq("id", viagem_id)
        .execute()
    )
    if not res.data:
        return None
    v = res.data[0]
    v["total_gastos"] = total_gastos(v["id"])
    caixa = float(v.get("caixa_valor") or 0)
    transferido = float(v.get("caixa_transferido") or 0)
    v["saldo_disponivel"] = caixa + transferido - v["total_gastos"]
    return v


def criar_viagem(dados: dict):
    res = supabase.table("viagens").insert(dados).execute()
    return res.data[0] if res.data else None


def atualizar_viagem(viagem_id: str, dados: dict):
    res = (
        supabase.table("viagens")
        .update(dados)
        .eq("id", viagem_id)
        .execute()
    )
    return res.data[0] if res.data else None


def adicionar_tecnico_viagem(viagem_id: str, usuario_id: str):
    existente = (
        supabase.table("tecnicos_viagem")
        .select("id")
        .eq("viagem_id", viagem_id)
        .eq("usuario_id", usuario_id)
        .execute()
    )
    if existente.data:
        return existente.data[0]
    res = supabase.table("tecnicos_viagem").insert(
        {"viagem_id": viagem_id, "usuario_id": usuario_id}
    ).execute()
    return res.data[0] if res.data else None


def remover_tecnicos_viagem(viagem_id: str):
    supabase.table("tecnicos_viagem").delete().eq("viagem_id", viagem_id).execute()


def listar_tecnicos_viagem(viagem_id: str):
    res = (
        supabase.table("tecnicos_viagem")
        .select("*, usuario:usuarios(id, nome, email, telefone)")
        .eq("viagem_id", viagem_id)
        .execute()
    )
    return res.data or []


def viagens_do_responsavel(usuario_id: str):
    res = (
        supabase.table("viagens")
        .select("*, responsavel:usuarios!viagens_responsavel_id_fkey(id, nome)")
        .eq("responsavel_id", usuario_id)
        .neq("status", "encerrada")
        .order("created_at", desc=True)
        .execute()
    )
    viagens = res.data or []
    for v in viagens:
        v["total_gastos"] = total_gastos(v["id"])
        caixa = float(v.get("caixa_valor") or 0)
        transferido = float(v.get("caixa_transferido") or 0)
        v["saldo_disponivel"] = caixa + transferido - v["total_gastos"]
    return viagens


def viagens_do_tecnico(usuario_id: str):
    res = (
        supabase.table("tecnicos_viagem")
        .select("viagem_id")
        .eq("usuario_id", usuario_id)
        .execute()
    )
    ids = [r["viagem_id"] for r in (res.data or [])]
    if not ids:
        return []
    res2 = (
        supabase.table("viagens")
        .select("*, responsavel:usuarios!viagens_responsavel_id_fkey(id, nome)")
        .in_("id", ids)
        .neq("status", "encerrada")
        .order("created_at", desc=True)
        .execute()
    )
    viagens = res2.data or []
    for v in viagens:
        v["total_gastos"] = total_gastos(v["id"])
        caixa = float(v.get("caixa_valor") or 0)
        transferido = float(v.get("caixa_transferido") or 0)
        v["saldo_disponivel"] = caixa + transferido - v["total_gastos"]
    return viagens


def todas_viagens_do_tecnico(usuario_id: str):
    """Retorna viagens onde é responsável OU membro."""
    como_responsavel = viagens_do_responsavel(usuario_id)
    como_membro = viagens_do_tecnico(usuario_id)
    ids_vistos = {v["id"] for v in como_responsavel}
    combined = list(como_responsavel)
    for v in como_membro:
        if v["id"] not in ids_vistos:
            combined.append(v)
    return combined


def solicitar_encerramento(viagem_id: str, data_retorno_real: str):
    res = (
        supabase.table("viagens")
        .update({"status": "encerramento_pendente", "data_retorno_real": data_retorno_real})
        .eq("id", viagem_id)
        .execute()
    )
    return res.data[0] if res.data else None


def aprovar_encerramento(
    viagem_id: str,
    data_retorno_real: str,
    saldo_devolvido: float = None,
    viagem_destino_id: str = None,
    valor_transferir: float = None,
):
    update_data = {
        "status": "encerrada",
        "data_retorno_real": data_retorno_real,
    }

    if viagem_destino_id and valor_transferir:
        destino = buscar_viagem(viagem_destino_id)
        if destino:
            atual_transferido = float(destino.get("caixa_transferido") or 0)
            supabase.table("viagens").update(
                {"caixa_transferido": atual_transferido + valor_transferir}
            ).eq("id", viagem_destino_id).execute()
        update_data["saldo_devolvido"] = 0
    else:
        update_data["saldo_devolvido"] = saldo_devolvido or 0

    res = (
        supabase.table("viagens")
        .update(update_data)
        .eq("id", viagem_id)
        .execute()
    )
    return res.data[0] if res.data else None


def excluir_viagem(viagem_id: str):
    supabase.table("gastos").delete().eq("viagem_id", viagem_id).execute()
    supabase.table("registros_hora").delete().eq("viagem_id", viagem_id).execute()
    supabase.table("paradas").delete().eq("viagem_id", viagem_id).execute()
    supabase.table("checklist").delete().eq("viagem_id", viagem_id).execute()
    supabase.table("tecnicos_viagem").delete().eq("viagem_id", viagem_id).execute()
    supabase.table("viagens").delete().eq("id", viagem_id).execute()


def listar_viagens_ativas_exceto(viagem_id: str):
    res = (
        supabase.table("viagens")
        .select("id, obra")
        .eq("status", "ativa")
        .neq("id", viagem_id)
        .execute()
    )
    return res.data or []
