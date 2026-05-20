import httpx
import time
import pandas as pd
import asyncio

def testar_http1():
    print("Iniciando teste HTTP/1.1 (TCP)...")
    resultados = []
    
    with httpx.Client(http1=True, http2=False, verify=False) as client:
        for i in range(5):  # 5 requisições de teste
            inicio = time.time()
            resposta = client.get("https://server:8080/teste")
            fim = time.time()
            
            latencia = (fim - inicio) * 1000  # ms
            resultados.append({
                "Protocolo": "HTTP/1.1", 
                "Iteracao": i+1, 
                "Latencia_ms": latencia, 
                "Status": resposta.status_code
            })
            print(f"Requisição {i+1} - Tempo: {latencia:.2f} ms")
            
    return resultados

# ==============================================================================
# --- ESQUELETO COMENTADO: IMPLEMENTAÇÃO FUTURA DO HTTP/3 (AIOQUIC) ---
#
# from aioquic.asyncio.client import connect
# from aioquic.quic.configuration import QuicConfiguration
#
# async def executar_requisicao_quic():
#     configuration = QuicConfiguration(is_client=True)
#     configuration.load_verify_locations("cert.pem") # Se necessário
#     async with connect("server", 4433, configuration=configuration) as client:
#         # Envio dos pacotes através de streams UDP assíncronas
#         pass
# ==============================================================================

def testar_http3():
    print("\nMapeando esqueleto estrutural do HTTP/3 (QUIC)...")
    resultados = []
    
    # Loop de mock: não faz requisições reais para não atrapalhar o script atual
    for i in range(5):
        latencia_placeholder = 0.0  # Zerado para indicar que é apenas estrutura por enquanto
        resultados.append({
            "Protocolo": "HTTP/3 (Esqueleto)", 
            "Iteracao": i+1, 
            "Latencia_ms": latencia_placeholder, 
            "Status": 200
        })
        print(f"[Esqueleto] Canal de dados do HTTP/3 preparado para iteração {i+1}")
        
    return resultados

def main():
    # 1. Coleta os dados reais do HTTP/1.1
    dados_http1 = testar_http1()
    
    # 2. Passa pela estrutura demarcada do HTTP/3
    dados_http3 = testar_http3()
    
    # Unifica ambos no dataframe para garantir que a pipeline do Pandas funcione
    df = pd.DataFrame(dados_http1 + dados_http3)
    
    print("\n--- Resumo Estatístico (Ambiente Prontificado) ---")
    print(df.groupby('Protocolo')['Latencia_ms'].describe())
    
    # Salvar resultados estruturados
    df.to_csv("resultados_teste.csv", index=False)
    print("\nResultados salvos em 'resultados_teste.csv'.")

if __name__ == "__main__":
    main()
