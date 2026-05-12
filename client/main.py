import httpx
import time
import pandas as pd

def testar_http1():
    print("Iniciando teste HTTP/1.1 (TCP)...")
    resultados =[]
    
    # HTTPX configurado para HTTP/1.1
    # verify=False porque usamos certificado self-signed no servidor
    with httpx.Client(http1=True, http2=False, verify=False) as client:
        for i in range(5): # 5 requisições de teste
            inicio = time.time()
            resposta = client.get("http://server:8080/teste")
            fim = time.time()
            
            latencia = (fim - inicio) * 1000 # ms
            resultados.append({"Protocolo": "HTTP/1.1", "Iteracao": i+1, "Latencia_ms": latencia, "Status": resposta.status_code})
            print(f"Requisição {i+1} - Tempo: {latencia:.2f} ms")
            
    return resultados

# Para HTTP/3 via aioquic puro do lado do cliente, o ideal na sua arquitetura 
# é rodar scripts chamando a API do aioquic. Como protótipo de hoje, 
# vamos garantir que o HTTP/1.1 funcione e salvar os dados no Pandas.

def main():
    dados = testar_http1()
    
    # Tratamento estatístico inicial com Pandas como proposto no PDF
    df = pd.DataFrame(dados)
    print("\n--- Resumo Estatístico ---")
    print(df.groupby('Protocolo')['Latencia_ms'].describe())
    
    # Salvar resultados
    df.to_csv("resultados_teste.csv", index=False)
    print("Resultados salvos em 'resultados_teste.csv'.")

if __name__ == "__main__":
    main()