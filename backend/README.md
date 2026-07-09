# PriStilo Backend

MVP da vitrine virtual com catalogo, personal stylist, cadastro de produtos e finalizacao por WhatsApp.

## Rodar local

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Defina `ADMIN_PASSWORD` no `.env` para acessar `/admin` e cadastrar produtos.

API:

- `GET /health`
- `GET /api/v1/products`
- `POST /api/v1/products`
- `POST /api/v1/stylist/recommendations`
- `POST /api/v1/stylist/chat`
- `POST /api/v1/whatsapp/checkout`
- `POST /api/v1/uploads/products`

Vitrine:

- `/`
- `/admin`

## IA gratuita

Por padrao, o chatbot usa recomendacao deterministica baseada no catalogo.
Para usar LLM local sem custo por token:

```powershell
ollama pull llama3.2
```

Depois ajuste no `.env`:

```env
ENABLE_OLLAMA=true
OLLAMA_MODEL=llama3.2
```

## PostgreSQL

Em producao, configure:

```env
DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/fthec_style
```

## Deploy no Render

O projeto inclui um `render.yaml` na raiz do repositorio para criar:

- Web Service Python com FastAPI.
- Render Postgres para produtos, clientes e pedidos.
- Disco persistente para imagens enviadas no painel admin.

Se configurar manualmente no Render:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

Variaveis obrigatorias:

```env
DATABASE_URL=<Internal Database URL do Render Postgres>
SEED_DEMO_DATA=false
CONSULTANT_WHATSAPP_NUMBER=5511997727075
PUBLIC_STORE_URL=<URL publica do Render>
UPLOAD_ROOT=/var/data/uploads
ADMIN_PASSWORD=<senha forte>
ADMIN_SESSION_SECRET=<segredo forte>
ENABLE_OLLAMA=false
```

Para manter as imagens cadastradas depois de redeploy/restart, anexe um disco
persistente no Web Service com mount path:

```text
/var/data/uploads
```
