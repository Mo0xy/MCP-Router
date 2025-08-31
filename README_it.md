# MCP-Router

MCP-Router è un’API FastAPI che implementa il Model Context Protocol (MCP), standardizzando le interazioni tra applicazioni e modelli AI.
Funziona come un ponte universale verso i modelli disponibili su OpenRouter, gestendo richieste di chat e documenti senza richiedere integrazioni specifiche per ciascun modello.

⚠️ **Nota importante**: il file `mcp_server.py` incluso nel progetto è fornito **solo come esempio/test**.
In un utilizzo reale, questo file dovrebbe essere **sostituito o esteso** con un **server MCP personalizzato**, in base alle proprie esigenze e logica applicativa.

---

## 🚀 Quick Start

Esistono due modi principali per eseguire MCP-Router: **API Mode** e **CLI Mode**.

---

### 🔹 1. Clone del repository

```bash
git clone https://github.com/tuo-username/MCP-Router.git
cd MCP-Router
```

### 🔹 2. Configurazione ambiente

```bash
# Copia il file di esempio
cp .env.example .env

# Modifica .env con le tue credenziali
# MODEL=anthropic/claude-3-sonnet-20240229
# OPENROUTER_API_KEY=your_key_here
```

---

### 🔹 3A. Avvio in modalità API

```bash
# Crea directory logs
mkdir logs

# Avvio con Docker
docker-compose up --build -d

# Verifica che funzioni
curl http://localhost:8000/health
```

### 🔹 3B. Avvio in modalità CLI

> Puoi eseguire MCP-Router direttamente senza usare Docker o FastAPI, tramite il CLI integrato.

```bash
uv run main.py
```

> In questa modalità tutte le funzionalità MCP sono accessibili direttamente dal terminale.

---

## 📚 Endpoints API

*(Solo per modalità API)*

* **GET /** → Redirect a documentazione Swagger
* **GET /health** → Health check
* **POST /chat** → Chat con AI tramite MCP
* **POST /chat\_alternative** → Endpoint alternativo

### Esempio utilizzo API:

```bash
curl -X POST "http://localhost:8000/chat?prompt=Hello"
```

> Per la modalità CLI (`uv run main.py`), non sono necessari endpoint HTTP: tutte le funzionalità sono accessibili direttamente dal terminale.

---

## 🔧 Sviluppo Locale

### Setup venv locale (opzionale)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Run locale API

```bash
uvicorn api.v1.mcpApi:app --reload
```

### Run locale CLI

```bash
uv run main.py
```

---

## 📁 Struttura Progetto

```
MCP-Router/
├── api/v1/
│   ├── mcpApi.py          # FastAPI app
│   └── mcp_run.py         # MCP runner functions
├── core/
│   ├── cli_chat.py        # Chat logic
│   ├── openrouter.py      # OpenRouter client
│   └── cli.py             # CLI interface
├── mcp_client.py          # MCP client
├── mcp_server.py          # ⚠️ MCP server di esempio/test → sostituire con uno personalizzato
├── main.py                # CLI entry point → eseguibile con `uv run main.py`
├── requirements.txt       # Dependencies
├── Dockerfile             # Production container
├── docker-compose.yml     # Container orchestration
└── .env.example           # Environment template
```

---

## 🔄 Personalizzazione del Server MCP

Il file `mcp_server.py` incluso è pensato solo come **base di riferimento**.
Per un utilizzo reale, è necessario implementare un server MCP personalizzato che gestisca le tue logiche, risorse e interazioni.

Puoi:

* Modificare direttamente `mcp_server.py`
* Oppure creare un nuovo modulo/server e sostituirlo al file di esempio

> ⚠️ Ricorda: se non vuoi usare l’API, puoi sempre eseguire `uv run main.py` in modalità CLI per sfruttare le funzionalità MCP senza server.

---

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

---

## 🤝 Contributing

1. Fork del repository
2. Crea feature branch
3. Commit delle modifiche
4. Push al branch
5. Crea Pull Request
