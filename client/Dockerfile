FROM python:3.10-slim

# Instalar o tc (iproute2) e ferramentas de rede para o cliente
RUN apt-get update && \
    apt-get install -y iproute2 curl iputils-ping && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY client/ .

# O docker-compose vai sobrescrever esse comando com tail -f /dev/null
CMD ["bash"]