from models import supabase
from werkzeug.security import generate_password_hash, check_password_hash


def buscar_por_email(email: str):
    res = supabase.table("usuarios").select("*").eq("email", email).eq("ativo", True).execute()
    return res.data[0] if res.data else None


def buscar_por_id(usuario_id: str):
    res = supabase.table("usuarios").select("*").eq("id", usuario_id).execute()
    return res.data[0] if res.data else None


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return check_password_hash(senha_hash, senha)


def listar_tecnicos():
    res = (
        supabase.table("usuarios")
        .select("*")
        .eq("perfil", "tecnico")
        .eq("ativo", True)
        .order("nome")
        .execute()
    )
    return res.data or []


def listar_todos():
    res = supabase.table("usuarios").select("*").order("nome").execute()
    return res.data or []


def criar_usuario(nome: str, email: str, senha: str, perfil: str = "tecnico", telefone: str = None):
    dados = {
        "nome": nome,
        "email": email,
        "senha_hash": generate_password_hash(senha),
        "perfil": perfil,
        "telefone": telefone,
        "ativo": True,
    }
    res = supabase.table("usuarios").insert(dados).execute()
    return res.data[0] if res.data else None


def atualizar_usuario(usuario_id: str, dados: dict):
    res = (
        supabase.table("usuarios")
        .update(dados)
        .eq("id", usuario_id)
        .execute()
    )
    return res.data[0] if res.data else None


def redefinir_senha(usuario_id: str, nova_senha: str):
    res = (
        supabase.table("usuarios")
        .update({"senha_hash": generate_password_hash(nova_senha)})
        .eq("id", usuario_id)
        .execute()
    )
    return res.data[0] if res.data else None


def desativar_usuario(usuario_id: str):
    res = (
        supabase.table("usuarios")
        .update({"ativo": False})
        .eq("id", usuario_id)
        .execute()
    )
    return res.data[0] if res.data else None
