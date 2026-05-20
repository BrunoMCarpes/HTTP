import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse

app = Starlette()

@app.route("/teste")
async def teste_rota(request):
    # Identifica a versão do protocolo dinamicamente
    versao_protocolo = request.scope.get('http_version', '1.1')
    
    # ==========================================================================
    # --- ESQUELETO COMENTADO: LÓGICA DE APLICAÇÃO PARA HTTP/3 ---
    #
    # if versao_protocolo == "3":
    #     # Ex: logs específicos de frames QUIC ou controle de vazão customizado
    #     print("[Servidor UDP] Processando fluxo nativo HTTP/3")
    # ==========================================================================
    
    # Servindo o payload padrão de 1MB
    payload = "A" * 1024 * 1024 
    return PlainTextResponse(payload)

async def main():
    config = Config()
    
    # Bind estável para HTTP/1.1 (TCP)
    config.bind = ["0.0.0.0:8080"]
    
    # Bind preparado para HTTP/3 QUIC (UDP) - Gerenciado internamente via aioquic
    config.quic_bind = ["0.0.0.0:4433"] 
    
    # Certificados TLS gerados na etapa anterior (obrigatórios para ambos)
    config.certfile = "cert.pem" 
    config.keyfile = "key.pem"
    
    print("--- Servidor Híbrido Prontificado ---")
    print("[TCP] HTTP/1.1 ativo e escutando na porta 8080")
    print("[UDP] HTTP/3 (QUIC) estruturado e aguardando conexões na porta 4433")
    
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())
