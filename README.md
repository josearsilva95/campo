# Controle de Viagem

SaaS para gestão de equipes técnicas externas — controle de viagens, gastos, ponto de horas e prestação de contas.

## Stack

- **Backend:** Python 3.12+ com Flask
- **Banco:** Supabase (PostgreSQL)
- **Storage:** Supabase Storage (fotos de notas fiscais)
- **PDF:** WeasyPrint
- **Frontend:** Tailwind CSS (CDN) + Tabler Icons + JavaScript vanilla
- **WhatsApp:** Evolution API

---

## Pré-requisitos

- Python 3.12+
- Conta no [Supabase](https://supabase.com)
- (Opcional) Instância da [Evolution API](https://doc.evolution-api.com) para WhatsApp

---

## Setup Local

### 1. Clone e entre no diretório

```bash
git clone <repo>
cd controle_viagem
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

> **Windows + WeasyPrint:** instale o GTK runtime em https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

### 4. Configure o Supabase

1. Crie um projeto em [supabase.com](https://supabase.com)
2. Vá em **SQL Editor** e execute o conteúdo de `supabase_schema.sql`
3. Vá em **Storage → New Bucket**, crie o bucket `notas` com acesso público
4. Copie a **URL do projeto** e a **anon key** em **Settings → API**

### 5. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com suas credenciais:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SECRET_KEY=gere-uma-chave-aleatoria-longa
FLASK_ENV=development
URL_SISTEMA=http://localhost:5000
```

### 6. Crie os usuários iniciais

```bash
python seed.py
```

Credenciais geradas:

| Perfil    | E-mail                | Senha       |
|-----------|-----------------------|-------------|
| ADM       | admin@empresa.com     | admin123    |
| Técnico   | joao@empresa.com      | tecnico123  |
| Técnico   | pedro@empresa.com     | tecnico123  |
| Técnico   | carlos@empresa.com    | tecnico123  |

### 7. Execute a aplicação

```bash
flask run
# ou:
python app.py
```

Acesse: [http://localhost:5000](http://localhost:5000)

---

## Configurar WhatsApp (Evolution API)

Preencha no `.env`:

```env
EVOLUTION_API_URL=http://seu-servidor:8080
EVOLUTION_INSTANCE=nome-da-instancia
EVOLUTION_API_KEY=sua-api-key
```

As notificações são enviadas automaticamente ao:
- Criar uma viagem (responsável e técnicos)
- Adicionar uma parada
- Aprovar encerramento

Se não configurado, o sistema funciona normalmente sem enviar WhatsApp.

---

## Deploy no Railway / Render

### Railway

1. Crie um novo projeto e conecte o repositório
2. Configure as variáveis de ambiente no painel do Railway
3. O `Procfile` já contém: `web: gunicorn app:app`
4. Deploy automático ao fazer push

### Render

1. Novo Web Service → conecte o repositório
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app:app`
4. Configure as variáveis de ambiente

---

## Estrutura de Arquivos

```
controle_viagem/
├── app.py                    # Entrada da aplicação Flask
├── config.py                 # Configurações (env vars)
├── seed.py                   # Dados iniciais
├── supabase_schema.sql       # Schema do banco de dados
├── Procfile                  # Deploy Railway/Render
├── requirements.txt
├── .env.example
├── routes/
│   ├── auth.py               # Login / logout
│   ├── adm.py                # Rotas do ADM
│   ├── tecnico.py            # Rotas do técnico
│   ├── relatorio.py          # PDFs
│   └── whatsapp.py           # Funções de notificação
├── models/
│   ├── __init__.py           # Cliente Supabase
│   ├── usuario.py
│   ├── viagem.py
│   ├── gasto.py
│   ├── ponto.py
│   ├── parada.py
│   └── checklist.py
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── adm/
│   ├── tecnico/
│   └── relatorios/
└── static/
    ├── css/main.css
    └── js/main.js
```

---

## Perfis e Permissões

| Ação                            | ADM | Técnico (Responsável) | Técnico (Membro) |
|---------------------------------|-----|-----------------------|------------------|
| Ver todas as viagens            | ✅  | ❌                    | ❌               |
| Criar / editar viagem           | ✅  | ❌                    | ❌               |
| Lançar gastos                   | ❌  | ✅                    | ❌               |
| Registrar ponto                 | ❌  | ✅                    | ✅               |
| Checklist saída / retorno       | ❌  | ✅                    | ❌               |
| Solicitar encerramento          | ❌  | ✅                    | ❌               |
| Aprovar encerramento            | ✅  | ❌                    | ❌               |
| Adicionar paradas               | ✅  | ❌                    | ❌               |
| Gerar PDF                       | ✅  | ✅                    | ✅               |

---

## Fluxo de Status da Viagem

```
ativa → encerramento_pendente → encerrada
         (técnico solicita)    (ADM aprova)
```

O ADM também pode encerrar diretamente sem passar pelo técnico.
