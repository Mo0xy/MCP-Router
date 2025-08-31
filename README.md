# MCP-Router

MCP-Router is a FastAPI API that implements the Model Context Protocol (MCP), standardizing interactions between applications and AI models.
It acts as a universal bridge to models available on OpenRouter, handling chat and document requests without requiring specific integrations for each model.

⚠️ **Important Note**: The `mcp_server.py` file included in the project is provided **for example/testing purposes only**.
For real use, this file should be **replaced or extended** with a **custom MCP server** according to your needs and application logic.

---

## 🚀 Quick Start

There are two main ways to run MCP-Router: **API Mode** and **CLI Mode**.

---

### 🔹 1. Clone the repository

```bash
git clone https://github.com/your-username/MCP-Router.git
cd MCP-Router
```

### 🔹 2. Environment setup

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
# MODEL=anthropic/claude-3-sonnet-20240229
# OPENROUTER_API_KEY=your_key_here
```

---

### 🔹 3A. Start in API mode

```bash
# Create logs directory
mkdir logs

# Start with Docker
docker-compose up --build -d

# Check if it's working
curl http://localhost:8000/health
```

### 🔹 3B. Start in CLI mode

> You can run MCP-Router directly without using Docker or FastAPI, via the integrated CLI.

```bash
uv run main.py
```

> In this mode, all MCP features are accessible directly from the terminal.

---

## 📚 API Endpoints

*(API mode only)*

* **GET /** → Redirects to Swagger documentation
* **GET /health** → Health check
* **POST /chat** → Chat with AI via MCP
* **POST /chat\_alternative** → Alternative endpoint

### API usage example:

```bash
curl -X POST "http://localhost:8000/chat?prompt=Hello"
```

> For CLI mode (`uv run main.py`), HTTP endpoints are not needed: all features are accessible directly from the terminal.

---

## 🔧 Local Development

### Local venv setup (optional)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Run local API

```bash
uvicorn api.v1.mcpApi:app --reload
```

### Run local CLI

```bash
uv run main.py
```

---

## 📁 Project Structure

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
├── mcp_server.py          # ⚠️ Example/test MCP server → replace with your own
├── main.py                # CLI entry point → run with `uv run main.py`
├── requirements.txt       # Dependencies
├── Dockerfile             # Production container
├── docker-compose.yml     # Container orchestration
└── .env.example           # Environment template
```

---

## 🔄 Customizing the MCP Server

The included `mcp_server.py` file is intended only as a **reference base**.
For real use, you need to implement a custom MCP server that handles your logic, resources, and interactions.

You can:

* Modify `mcp_server.py` directly
* Or create a new module/server and replace the example file

> ⚠️ Reminder: if you don't want to use the API, you can always run `uv run main.py` in CLI mode to use MCP features without a server.

---

## 🛠️ Troubleshooting

### Container won't start

```bash
# View logs
docker-compose logs -f

# Rebuild without cache
docker-compose build --no-cache
```

### API not responding

```bash
# Check health
curl http://localhost:8000/health

# Check application logs
cat logs/error_log.txt
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

