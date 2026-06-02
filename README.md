# ngo-service (Python / Flask)

Serviço responsável pelo **cadastro e listagem de ONGs parceiras** da plataforma SolidaryTech.

## 🧱 Stack

| Item | Valor |
|---|---|
| Linguagem | Python 3.11 |
| Framework | Flask + Gunicorn |
| Banco de Dados | PostgreSQL 15 |
| Porta | `8081` |

## 📦 Pré-requisitos (execução isolada)

- Python 3.11+
- PostgreSQL 15 (local ou container)
- `pip install -r requirements.txt`

## 🔐 Variáveis de Ambiente

| Variável | Obrigatória | Descrição | Exemplo |
|---|---|---|---|
| `DATABASE_URL` | ✅ | String de conexão PostgreSQL | `postgresql://user:pass@localhost:5432/ngo_db` |
| `PORT` | ❌ | Porta HTTP (padrão `8081`) | `8081` |

## 🚀 Executando localmente (sem Docker)

```bash
# 1. Criar o banco e tabela
psql -U postgres -c "CREATE DATABASE ngo_db;"
psql -U postgres -d ngo_db -f db/init.sql

# 2. Definir variáveis
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ngo_db"
export PORT=8081

# 3. Instalar dependências e rodar
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:8081 app:app
```

> **Recomendado:** use o `docker-compose` da raiz do projeto, que orquestra esse
> serviço junto com o PostgreSQL, o LocalStack e os demais microsserviços.

## 🔌 Endpoints

### `GET /health`

Verifica saúde do serviço.

```bash
curl http://localhost:8081/health
# → {"status":"ok","service":"ngo-service"}
```

### `GET /ngos`

Lista todas as ONGs cadastradas (ordenadas por `id DESC`).

```bash
curl http://localhost:8081/ngos
```

**Resposta (200):**
```json
[
  {
    "id": 2,
    "name": "Educa Mais",
    "email": "info@educamais.org",
    "cause": "Educação",
    "city": "São Paulo",
    "created_at": "2026-05-27T15:20:11Z"
  }
]
```

### `POST /ngos`

Cadastra uma nova ONG.

**Request:**
```bash
curl -X POST http://localhost:8081/ngos \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Anjos de Patas",
    "email": "contato@anjosdepatas.org",
    "cause": "Proteção Animal",
    "city": "Osasco"
  }'
```

**Resposta (201):** objeto criado.
**Erros possíveis:**
- `400` — campos obrigatórios ausentes
- `409` — e-mail já cadastrado (constraint `UNIQUE`)
- `500` — erro interno

## 🐳 Imagem Docker

```bash
docker build -t solidary/ngo-service:local .
docker run --rm -p 8081:8081 \
  -e DATABASE_URL="postgresql://user:pass@host.docker.internal:5432/ngo_db" \
  solidary/ngo-service:local
```

A imagem segue boas práticas:
- Multi-stage build (final < 100 MB)
- Usuário não-root (UID 1001)
- `HEALTHCHECK` embutido
- Gunicorn com 4 workers e timeout 60s
