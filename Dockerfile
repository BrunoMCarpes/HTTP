FROM python:3.12-slim

# iproute2 -> comando `tc` (netem);  openssl -> gerar certificado self-signed
RUN apt-get update && apt-get install -y --no-install-recommends \
        iproute2 openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Certificado self-signed compartilhado (mesma imagem -> servidor e cliente
# enxergam o mesmo cert). O cliente usa --insecure, então só o servidor o usa.
RUN openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
        -keyout key.pem -out cert.pem -subj "/CN=server"

COPY server.py bench.py plot.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
