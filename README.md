# Benchmark HTTP/1.1 vs HTTP/3 (QUIC) em Python — com Docker

Compara latência e desempenho dos dois protocolos servindo a **mesma app**
sobre TCP (HTTP/1.1) e QUIC (HTTP/3). Servidor e cliente rodam em contêineres
separados numa rede bridge, então o `tc netem` afeta as medições de verdade.

## Arquivos

- `server.py` — app ASGI servida em HTTP/1.1+HTTP/2 (TCP) e HTTP/3 (QUIC).
- `bench.py` — harness de medição (modos warm / cold / concurrent, percentis).
- `Dockerfile` — imagem com aioquic, httpx, hypercorn, tc e cert self-signed.
- `docker-compose.yml` — serviços `server` e `client` na rede `benchnet`.
- `entrypoint.sh` — aplica `tc netem` na interface antes de rodar.
- `plot.py` — análise com Pandas: gera os gráficos e a tabela `resumo.csv`.
- `Makefile` — atalhos.

## Requisitos

Docker + docker compose. O `netem` depende do módulo `sch_netem` no host;
carregue-o uma vez antes de começar:

```bash
sudo modprobe sch_netem
```

No Linux funciona direto. No Docker Desktop (Mac/Windows) o `netem` roda na
VM LinuxKit; se o `tc` falhar, rode sem NETEM primeiro para validar o resto.

## 1. Build

```bash
make build          # ou: docker compose build
```

## 2. Subir o servidor

Rede perfeita (baseline):
```bash
make up
```

Com latência + perda (recomendado — é onde o HTTP/3 se diferencia):
```bash
make NETEM="delay 25ms loss 1%" up
```

> O NETEM é aplicado no egress de CADA contêiner. Como servidor e cliente
> usam o mesmo valor, o atraso soma nas duas direções: `delay 25ms` ≈ 50ms
> de RTT. Perfis para testar: `delay 5ms` (LAN), `delay 25ms loss 1%` (bom),
> `delay 100ms loss 5%` (ruim).

## 3. Rodar os benchmarks

Um comando por cenário (roda os dois protocolos):
```bash
make warm         # conexao quente: overhead por requisicao / multiplexing
make cold         # conexao fria: handshake QUIC 1-RTT vs TCP+TLS
make concurrent   # lote paralelo na mesma conexao: head-of-line blocking
make all          # os tres acima
```

Repita com o servidor sob perfis de NETEM diferentes para ver a diferença.
Lembre de derrubar e subir de novo o servidor ao trocar o NETEM:
```bash
make down
make NETEM="delay 100ms loss 5%" up
make all
```

Chamada manual (fora do Makefile):
```bash
docker compose run --rm client \
  python bench.py --proto h3 --host server --port 8443 -n 1000 --mode warm --insecure
```

Payload grande (teste de throughput): suba com `make NETEM="..." PAYLOAD=1048576 up`.

## 4. Gerar os gráficos (Pandas + matplotlib)

Para salvar os resultados e produzir os gráficos, use `make bench` (grava em
`results/results.jsonl`) e depois `make plot`:

```bash
export NETEM="delay 25ms loss 1%"
make down && make up && make bench

export NETEM="delay 100ms loss 5%"
make down && make up && make bench

make plot
```

Saem em `results/`: `warm_latency.png`, `cold_latency.png`, `throughput.png`
e a tabela consolidada `resumo.csv`. O `make clean-results` limpa tudo.

## 5. Como interpretar

- **cold**: espere o HTTP/3 ganhar (handshake em menos RTTs).
- **warm**: em rede boa pode empatar ou o HTTP/1.1 ganhar (overhead do
  Python puro da aioquic); sob perda o HTTP/3 estabiliza melhor a cauda.
- **concurrent**: aqui o HTTP/1.1 mais sofre sob perda — um pacote perdido
  bloqueia todo o pipeline TCP; o QUIC isola por stream.
- Olhe **p95/p99**, não só a média. A vantagem do QUIC vive na cauda.

## Ressalvas

- A aioquic é Python puro em espaço de usuário: mede a diferença de
  *protocolo*, não o teto de uma stack QUIC em C. Para números de produção,
  cruze com `h2load` (nghttp3) ou um servidor como Caddy/nginx-quic.
- O cliente HTTP/3 segue o padrão canônico da aioquic; confirme os nomes de
  eventos/API na versão instalada.
- `--insecure` ignora a validação do certificado (só para o self-signed local).

## Sem Docker (bare metal)

```bash
pip install -r requirements.txt
openssl req -x509 -newkey rsa:2048 -nodes -days 365 -keyout key.pem -out cert.pem -subj "/CN=localhost"
# aplique netem no loopback: sudo tc qdisc add dev lo root netem delay 25ms loss 1%
python server.py --port 8443 --payload 1024
python bench.py --proto h3 --host localhost --port 8443 -n 1000 --mode warm --insecure
```
