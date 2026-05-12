FROM python:3.10-slim

# Instalar dependências de sistema para compilar o aioquic e usar o tc
RUN apt-get update && \
    apt-get install -y libssl-dev python3-dev build-essential iproute2 openssl curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar dependências e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Gerar certificado Self-Signed (Obrigatório para HTTP/3 e QUIC)
RUN openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"

# Copiar o restante do código
COPY server/ .

CMD ["python", "main.py"]