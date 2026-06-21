import io
from models import supabase
from PIL import Image


BUCKET = "notas"
MAX_PX = 1200


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
