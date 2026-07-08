"""
Harness de medição: compara latência de HTTP/1.1 (httpx) vs HTTP/3 (aioquic).

Cenários suportados (--mode):
  warm   -> conexão reutilizada, mede latência por requisição (multiplexing/overhead)
  cold   -> conexão nova a cada requisição (inclui handshake TCP+TLS vs QUIC)
  concurrent -> N requisições em paralelo na MESMA conexão (head-of-line blocking)

Uso:
    python bench.py --proto h11 --host localhost --port 8443 -n 1000 --mode warm
    python bench.py --proto h3  --host localhost --port 8443 -n 1000 --mode warm

Dica: rode SEMPRE sob `tc netem` (latência/perda). Em loopback perfeito
o resultado é enganoso — veja README.md.

NOTA: este é um scaffold. O cliente HTTP/3 segue o padrão canônico da
aioquic (subclasse de QuicConnectionProtocol + H3Connection). Valide contra
sua versão da aioquic antes de tirar conclusões.
"""
import argparse
import asyncio
import json
import os
import ssl
import statistics
import time
from collections import deque

# ---- HTTP/1.1 (e H2) via httpx -------------------------------------------
import httpx

# ---- HTTP/3 via aioquic ---------------------------------------------------
from aioquic.asyncio.client import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import DataReceived, HeadersReceived
from aioquic.quic.configuration import QuicConfiguration


# ==========================================================================
# Cliente HTTP/3
# ==========================================================================
class H3Client(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._http = H3Connection(self._quic)
        self._events: dict[int, deque] = {}
        self._waiters: dict[int, asyncio.Future] = {}

    async def get(self, authority: str, path: str) -> bytes:
        stream_id = self._quic.get_next_available_stream_id()
        self._http.send_headers(
            stream_id,
            [
                (b":method", b"GET"),
                (b":scheme", b"https"),
                (b":authority", authority.encode()),
                (b":path", path.encode()),
            ],
            end_stream=True,
        )
        waiter = self._loop.create_future()
        self._events[stream_id] = deque()
        self._waiters[stream_id] = waiter
        self.transmit()
        return await asyncio.shield(waiter)

    def _on_http_event(self, event) -> None:
        if isinstance(event, (HeadersReceived, DataReceived)):
            sid = event.stream_id
            if sid in self._events:
                self._events[sid].append(event)
                if getattr(event, "stream_ended", False):
                    body = b"".join(
                        e.data for e in self._events.pop(sid)
                        if isinstance(e, DataReceived)
                    )
                    self._waiters.pop(sid).set_result(body)

    def quic_event_received(self, event) -> None:
        for http_event in self._http.handle_event(event):
            self._on_http_event(http_event)


def _quic_config(insecure: bool) -> QuicConfiguration:
    config = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN)
    if insecure:
        config.verify_mode = ssl.CERT_NONE
    return config


async def bench_h3(host, port, path, n, mode, insecure):
    authority = f"{host}:{port}"
    lats = []

    if mode == "cold":
        # conexão nova por requisição -> mede handshake QUIC + 1a resposta.
        # IMPORTANTE: o cronômetro para DENTRO do bloco, antes do teardown,
        # porque o fechamento da conexão na aioquic tem uma espera fixa que
        # nao faz parte do custo de estabelecer a conexao.
        for _ in range(n):
            t0 = time.perf_counter()
            async with connect(host, port,
                               configuration=_quic_config(insecure),
                               create_protocol=H3Client) as client:
                await client.get(authority, path)
                lats.append(time.perf_counter() - t0)
        return lats

    # warm / concurrent -> uma conexão reutilizada
    async with connect(host, port,
                       configuration=_quic_config(insecure),
                       create_protocol=H3Client) as client:
        await client.get(authority, path)  # warm-up

        if mode == "concurrent":
            t0 = time.perf_counter()
            await asyncio.gather(*[client.get(authority, path) for _ in range(n)])
            # latência "wall clock" do lote inteiro
            lats.append(time.perf_counter() - t0)
        else:  # warm
            for _ in range(n):
                t0 = time.perf_counter()
                await client.get(authority, path)
                lats.append(time.perf_counter() - t0)
    return lats


# ==========================================================================
# Cliente HTTP/1.1
# ==========================================================================
async def bench_h11(host, port, path, n, mode, insecure):
    url = f"https://{host}:{port}{path}"
    verify = not insecure
    lats = []

    if mode == "cold":
        # client novo por requisição -> força TCP+TLS a cada vez.
        # cronômetro para antes do teardown, para ser simétrico com o H3.
        for _ in range(n):
            t0 = time.perf_counter()
            async with httpx.AsyncClient(http1=True, http2=False,
                                         verify=verify) as c:
                await c.get(url)
                lats.append(time.perf_counter() - t0)
        return lats

    async with httpx.AsyncClient(http1=True, http2=False, verify=verify) as c:
        await c.get(url)  # warm-up

        if mode == "concurrent":
            t0 = time.perf_counter()
            await asyncio.gather(*[c.get(url) for _ in range(n)])
            lats.append(time.perf_counter() - t0)
        else:  # warm
            for _ in range(n):
                t0 = time.perf_counter()
                await c.get(url)
                lats.append(time.perf_counter() - t0)
    return lats


# ==========================================================================
# Relatório
# ==========================================================================
def _pct(ms, p):
    if len(ms) == 1:
        return ms[0]
    k = (len(ms) - 1) * p
    f = int(k)
    c = min(f + 1, len(ms) - 1)
    return ms[f] + (ms[c] - ms[f]) * (k - f)


def compute_record(proto, mode, lats, netem, n):
    """Monta um dicionário com as estatísticas, serializável em JSON."""
    ms = sorted(x * 1000 for x in lats)
    rec = {"proto": proto, "mode": mode, "netem": netem, "n": n}
    if mode == "concurrent":
        rec["batch_ms"] = round(ms[0], 3)
    else:
        rec["mean"] = round(statistics.mean(ms), 3)
        rec["p50"] = round(_pct(ms, 0.50), 3)
        rec["p95"] = round(_pct(ms, 0.95), 3)
        rec["p99"] = round(_pct(ms, 0.99), 3)
        rec["max"] = round(ms[-1], 3)
    return rec


def print_record(rec):
    print(f"\n=== {rec['proto'].upper()} | mode={rec['mode']} "
          f"| netem='{rec['netem']}' ===")
    if rec["mode"] == "concurrent":
        print(f"tempo total do lote: {rec['batch_ms']:.2f} ms")
    else:
        print(f"média : {rec['mean']:.3f} ms")
        print(f"p50   : {rec['p50']:.3f} ms")
        print(f"p95   : {rec['p95']:.3f} ms")
        print(f"p99   : {rec['p99']:.3f} ms")
        print(f"máx   : {rec['max']:.3f} ms")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proto", choices=["h11", "h3"], required=True)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--path", default="/")
    parser.add_argument("-n", type=int, default=1000)
    parser.add_argument("--mode", choices=["warm", "cold", "concurrent"],
                        default="warm")
    parser.add_argument("--insecure", action="store_true",
                        help="não valida o certificado (para self-signed local)")
    parser.add_argument("--out", default=None,
                        help="acrescenta o resultado (JSON) a este arquivo")
    args = parser.parse_args()

    fn = bench_h3 if args.proto == "h3" else bench_h11
    lats = await fn(args.host, args.port, args.path, args.n, args.mode,
                    args.insecure)

    netem = os.environ.get("NETEM") or "sem-netem"
    rec = compute_record(args.proto, args.mode, lats, netem, args.n)
    print_record(rec)

    if args.out:
        with open(args.out, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f">> salvo em {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
