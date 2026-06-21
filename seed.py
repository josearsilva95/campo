"""
Seed inicial — cria 1 ADM e 3 técnicos de exemplo no Supabase.
Execute: python seed.py
"""
from dotenv import load_dotenv
load_dotenv()

from models.usuario import criar_usuario

usuarios = [
    {"nome": "Admin Sistema",    "email": "admin@empresa.com",    "senha": "admin123",  "perfil": "adm",    "telefone": "5511999990000"},
    {"nome": "João Técnico",     "email": "joao@empresa.com",     "senha": "tecnico123","perfil": "tecnico","telefone": "5511999991111"},
    {"nome": "Pedro Eletricista","email": "pedro@empresa.com",    "senha": "tecnico123","perfil": "tecnico","telefone": "5511999992222"},
    {"nome": "Carlos Mecânico",  "email": "carlos@empresa.com",   "senha": "tecnico123","perfil": "tecnico","telefone": "5511999993333"},
]

for u in usuarios:
    resultado = criar_usuario(u["nome"], u["email"], u["senha"], u["perfil"], u.get("telefone"))
    if resultado:
        print(f"[OK] {u['nome']} criado ({u['email']})")
    else:
        print(f"[ERRO] {u['nome']} — pode já existir ou houve falha no Supabase.")

print("\nSeed concluído.")
print("\nCredenciais:")
print("  ADM:     admin@empresa.com / admin123")
print("  Técnico: joao@empresa.com  / tecnico123")
