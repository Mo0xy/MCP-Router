# MCP-Router Project

MCP API Project is a FastAPI-based API that implements the Model Context Protocol (MCP), standardizing interactions between applications and AI models.
It acts as a universal bridge to models available on OpenRouter, handling chat and document requests without requiring specific integrations for each model.
⚠️ **Important Note**: The `mcp_server.py` file included in the project is provided **for example/testing purposes only**.
For real use, this file should be **replaced or extended** with a **custom MCP server** according to your needs and application logic.

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Mo0xy/MCP-Router.git
cd MCP-Router
```

### 2. Environment setup

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
# MODEL=anthropic/claude-3-sonnet-20240229
# OPENROUTER_API_KEY=your_key_here
```

### 3. Start with Docker

```bash
# Create logs directory
mkdir logs

# Build and start
docker-compose up --build -d

# Check if it works
curl http://localhost:8000/health
```

## 📚 API Endpoints

* **GET /** → Redirects to Swagger documentation
* **GET /health** → Health check
* **POST /chat** → AI chat via MCP
* **POST /chat\_alternative** → Alternative endpoint

### Usage example:

```bash
curl -X POST "http://localhost:8000/chat?prompt=Hello"
```

## 🔧 Local Development

### Local venv setup (optional)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Local run

```bash
uvicorn api.v1.mcpApi:app --reload
```

## 📁 Project Structure

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
├── mcp_server.py          # ⚠️ Example/test MCP server → replace with your own
├── main.py                # CLI entry point
├── requirements.txt       # Dependencies
├── Dockerfile             # Production container
├── docker-compose.yml     # Container orchestration
└── .env.example           # Environment template
```

## 🔄 Customizing the MCP Server

The included `mcp_server.py` file is intended only as a **reference base**.
For real use, you need to implement a custom MCP server that handles your logic, resources, and interactions.
You can:

* Modify `mcp_server.py` directly
* Or create a new module/server and replace the example file

This way, the API can interface with your specific logic.

## 🛠️ Troubleshooting

### Container does not start

```bash
# See logs
docker-compose logs -f

# Rebuild without cache
docker-compose build --no-cache
```

### API does not respond

```bash
# Check health
curl http://localhost:8000/health

# Check application logs
cat logs/error_log.txt
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

