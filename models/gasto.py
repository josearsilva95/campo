import io
from models import supabase
from PIL import Image


BUCKET = "notas"
MAX_PX = 1200


def resumo_anual(ano: int):
    res = (
        supabase.table("gastos")
        .select("valor, categoria, created_at, viagem:viagens(id, obra, status, data_saida)")
        .execute()
    )
    gastos = res.data or []

    por_categoria: dict[str, float] = {}
    por_mes: dict[int, float] = {}
    por_viagem: dict[str, dict] = {}
    total_geral = 0.0

    for g in gastos:
        data = g.get("created_at", "")[:10]
        if not data.startswith(str(ano)):
            continue
        valor = float(g["valor"])
        mes = int(data[5:7])
        cat = g["categoria"]
        viagem = g.get("viagem") or {}
        vid = viagem.get("id", "")

        total_geral += valor
        por_categoria[cat] = por_categoria.get(cat, 0) + valor
        por_mes[mes] = por_mes.get(mes, 0) + valor

        if vid not in por_viagem:
            por_viagem[vid] = {
                "obra": viagem.get("obra", "—"),
                "status": viagem.get("status", ""),
                "data_saida": viagem.get("data_saida", ""),
                "total": 0.0,
            }
        por_viagem[vid]["total"] += valor

    meses_labels = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    por_mes_lista = [round(por_mes.get(m, 0), 2) for m in range(1, 13)]

    return {
        "total_geral": round(total_geral, 2),
        "por_categoria": {k: round(v, 2) for k, v in sorted(por_categoria.items(), key=lambda x: -x[1])},
        "por_mes": por_mes_lista,
        "meses_labels": meses_labels,
        "por_viagem": sorted(por_viagem.values(), key=lambda x: -x["total"]),
    }


def listar_todos_gastos_com_foto():
    res = (
        supabase.table("gastos")
        .select("*, viagem:viagens(id, obra, status)")
        .not_.is_("foto_url", "null")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def listar_gastos(viagem_id: str):
    res = (
        supabase.table("gastos")
        .select("*")
        .eq("viagem_id", viagem_id)
        .order("created_at", desc=False)
        .execute()
    )
    return res.data or []


def total_gastos(viagem_id: str) -> float:
    res = supabase.table("gastos").select("valor").eq("viagem_id", viagem_id).execute()
    return sum(float(g["valor"]) for g in (res.data or []))


def gastos_por_categoria(viagem_id: str) -> dict:
    gastos = listar_gastos(viagem_id)
    resumo: dict[str, float] = {}
    for g in gastos:
        cat = g["categoria"]
        resumo[cat] = resumo.get(cat, 0) + float(g["valor"])
    return resumo


def lancar_gasto(viagem_id: str, categoria: str, descricao: str, valor: float, foto_url: str = None):
    dados = {
        "viagem_id": viagem_id,
        "categoria": categoria,
        "descricao": descricao,
        "valor": valor,
        "foto_url": foto_url,
    }
    res = supabase.table("gastos").insert(dados).execute()
    return res.data[0] if res.data else None


def deletar_gasto(gasto_id: str):
    supabase.table("gastos").delete().eq("id", gasto_id).execute()


def upload_foto(file_bytes: bytes, filename: str) -> str | None:
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.thumbnail((MAX_PX, MAX_PX), Image.LANCZOS)
        buf = io.BytesIO()
        fmt = img.format or "JPEG"
        if fmt not in ("JPEG", "PNG", "WEBP"):
            fmt = "JPEG"
        img.save(buf, format=fmt)
        buf.seek(0)
        compressed = buf.read()

        content_type = "image/jpeg" if fmt == "JPEG" else f"image/{fmt.lower()}"
        res = supabase.storage.from_(BUCKET).upload(
            filename,
            compressed,
            {"content-type": content_type, "upsert": "true"},
        )
        public_url = supabase.storage.from_(BUCKET).get_public_url(filename)
        return public_url
    except Exception as e:
        print(f"[upload_foto] erro: {e}")
        return None
