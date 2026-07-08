"""
Servidor de teste: mesma app ASGI servida simultaneamente sobre
HTTP/1.1 + HTTP/2 (TCP) e HTTP/3 (QUIC/UDP), com o mesmo certificado.

Isso garante que a ÚNICA variável entre os testes seja o protocolo.

Rodar:
    python server.py --port 8443 --payload 1024

Requer certificado self-signed (veja README.md).
"""
import argparse
import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config

# Tamanho do corpo da resposta (bytes). Pode ser sobrescrito por ?size=N.
DEFAULT_PAYLOAD = 1024


def make_app(default_payload: int):
    async def app(scope, receive, send):
        assert scope["type"] == "http"

        # permite ?size=N para variar o payload por requisição
        size = default_payload
        qs = scope.get("query_string", b"").decode()
        for part in qs.split("&"):
            if part.startswith("size="):
                try:
                    size = int(part.split("=", 1)[1])
                except ValueError:
                    pass

        body = b"x" * size
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"application/octet-stream"),
                (b"content-length", str(len(body)).encode()),
            ],
        })
        await send({"type": "http.response.body", "body": body})

    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--payload", type=int, default=DEFAULT_PAYLOAD)
    parser.add_argument("--cert", default="cert.pem")
    parser.add_argument("--key", default="key.pem")
    args = parser.parse_args()

    config = Config()
    # Bind TCP -> HTTP/1.1 e HTTP/2
    config.bind = [f"{args.host}:{args.port}"]
    # Bind UDP/QUIC -> HTTP/3 (mesma porta)
    config.quic_bind = [f"{args.host}:{args.port}"]
    config.certfile = args.cert
    config.keyfile = args.key
    # ALPN: ordem de preferência do servidor
    config.alpn_protocols = ["h3", "h2", "http/1.1"]

    print(f"HTTP/1.1+HTTP/2 (TCP) e HTTP/3 (QUIC) em :{args.port}, payload={args.payload}B")
    asyncio.run(serve(make_app(args.payload), config))


if __name__ == "__main__":
    main()
