# MCP API Project

MCP API Project è un’API FastAPI che implementa il Model Context Protocol (MCP), standardizzando le interazioni tra applicazioni e modelli AI.
Funziona come un ponte universale verso i modelli disponibili su OpenRouter, gestendo richieste di chat e documenti senza richiedere integrazioni specifiche per ciascun modello.
⚠️ **Nota importante**: il file `mcp_server.py` incluso nel progetto è fornito **solo come esempio/test**.
In un utilizzo reale, questo file dovrebbe essere **sostituito o esteso** con un **server MCP personalizzato**, in base alle proprie esigenze e logica applicativa.

## 🚀 Quick Start

### 1. Clone del repository

```bash
git clone https://github.com/tuo-username/mcp-api.git
cd mcp-api
```

### 2. Configurazione ambiente

```bash
# Copia il file di esempio
cp .env.example .env

# Modifica .env con le tue credenziali
# MODEL=anthropic/claude-3-sonnet-20240229
# OPENROUTER_API_KEY=your_key_here
```

### 3. Avvio con Docker

```bash
# Crea directory logs
mkdir logs

# Build e avvio
docker-compose up --build -d

# Verifica che funzioni
curl http://localhost:8000/health
```

## 📚 Endpoints API

* **GET /** → Redirect a documentazione Swagger
* **GET /health** → Health check
* **POST /chat** → Chat con AI tramite MCP
* **POST /chat\_alternative** → Endpoint alternativo

### Esempio utilizzo:

```bash
curl -X POST "http://localhost:8000/chat?prompt=Hello"
```

## 🔧 Sviluppo Locale

### Setup venv locale (opzionale)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Run locale

```bash
uvicorn api.v1.mcpApi:app --reload
```

## 📁 Struttura Progetto

```
MCP_v2/
├── api/v1/
│   ├── mcpApi.py          # FastAPI app
│   └── mcp_run.py         # MCP runner functions
├── core/
│   ├── cli_chat.py        # Chat logic
│   ├── openrouter.py      # OpenRouter client
│   └── cli.py             # CLI interface
├── mcp_client.py          # MCP client
├── mcp_server.py          # ⚠️ MCP server di esempio/test → sostituire con uno personalizzato
├── main.py                # CLI entry point
├── requirements.txt       # Dependencies
├── Dockerfile             # Production container
├── docker-compose.yml     # Container orchestration
└── .env.example           # Environment template
```

## 🔄 Personalizzazione del Server MCP

Il file `mcp_server.py` incluso è pensato solo come **base di riferimento**.
Per un utilizzo reale, è necessario implementare un server MCP personalizzato che gestisca le tue logiche, risorse e interazioni.
Puoi:

* Modificare direttamente `mcp_server.py`
* Oppure creare un nuovo modulo/server e sostituirlo al file di esempio

In questo modo l’API potrà interfacciarsi con la tua logica specifica.

## 🛠️ Troubleshooting

### Container non si avvia

```bash
# Vedi i logs
docker-compose logs -f

# Rebuilda senza cache
docker-compose build --no-cache
```

### API non risponde

```bash
# Verifica health
curl http://localhost:8000/health

# Verifica logs applicazione
cat logs/error_log.txt
```

## 🤝 Contributing

1. Fork del repository
2. Crea feature branch
3. Commit delle modifiche
4. Push al branch
5. Crea Pull Request
