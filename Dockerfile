FROM python:3.12.10

WORKDIR /app

COPY requirements.txt .

RUN apt-get update

#&& apt-get install -y curl build-essential pkg-config libssl-dev


RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Avvia l'app
CMD ["uvicorn", "api.v1.mcpApi:app", "--host", "0.0.0.0", "--port", "8000"]
