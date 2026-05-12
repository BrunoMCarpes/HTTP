import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse

# Aplicação simples que servirá para medir o tempo de resposta e vazão
app = Starlette()

@app.route("/teste")
async def teste_rota(request):
    # Simulando um payload/arquivo de tamanho moderado (ex: 1MB de dados)
    payload = "A" * 1024 * 1024 
    return PlainTextResponse(payload)

async def main():
    config = Config()
    # Bind para HTTP/1.1 (TCP)
    config.bind = ["0.0.0.0:8080"]
    
    # Bind para HTTP/3 QUIC (UDP) - Usa aioquic internamente
    config.quic_bind = ["0.0.0.0:4433"] 
    
    # Certificados são obrigatórios no QUIC
    config.certfile = "cert.pem" 
    config.keyfile = "key.pem"
    
    print("Servidor rodando...")
    print("HTTP/1.1 escutando em TCP 8080")
    print("HTTP/3 escutando em UDP 4433")
    
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())