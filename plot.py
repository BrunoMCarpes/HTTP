"""
Análise e geração de gráficos: HTTP/1.1 vs HTTP/3, usando Pandas + matplotlib.

Lê os resultados salvos por bench.py (results/results.jsonl) e produz, na
pasta results/:
  - warm_latency.png      latência por requisição (p50/p95/p99), por perfil
  - cold_latency.png      latência de handshake (conexão nova), por perfil
  - throughput.png        vazão sob concorrência (requisições por segundo)
  - resumo.csv            tabela consolidada de todas as métricas

Rodadas repetidas do mesmo cenário são agregadas pela média (Pandas).
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RESULTS = os.environ.get("RESULTS", "results/results.jsonl")
OUTDIR = os.path.dirname(RESULTS) or "."

C = {"h11": "#4C72B0", "h3": "#DD8452"}      # azul / laranja
LABEL = {"h11": "HTTP/1.1", "h3": "HTTP/3"}


def load_df():
    if not os.path.exists(RESULTS):
        raise SystemExit(f"nao encontrei {RESULTS}. Rode `make bench` primeiro.")
    df = pd.read_json(RESULTS, lines=True)
    # concorrencia: deriva vazao (requisicoes por segundo) a partir do lote
    if "batch_ms" in df.columns:
        df["req_s"] = np.where(df["mode"] == "concurrent",
                               df["n"] / (df["batch_ms"] / 1000.0), np.nan)
    return df


def profile_order(profiles):
    return sorted(profiles, key=lambda s: (s != "sem-netem", s))


def plot_latency(df, mode, fname, title):
    sub = df[df["mode"] == mode]
    if sub.empty:
        return
    metrics = ["p50", "p95", "p99"]
    # media entre rodadas repetidas
    piv = (sub.groupby(["netem", "proto"])[metrics].mean())
    profiles = profile_order(piv.index.get_level_values("netem").unique())

    fig, axes = plt.subplots(1, len(profiles), figsize=(5.2 * len(profiles), 4.2),
                             squeeze=False)
    for ax, netem in zip(axes[0], profiles):
        x = np.arange(len(metrics))
        w = 0.38
        for i, proto in enumerate(["h11", "h3"]):
            if (netem, proto) in piv.index:
                vals = [piv.loc[(netem, proto), m] for m in metrics]
                bars = ax.bar(x + (i - 0.5) * w, vals, w,
                              label=LABEL[proto], color=C[proto])
                ax.bar_label(bars, fmt="%.0f", fontsize=8)
        ax.set_title(f"netem: {netem}", fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels([m.upper() for m in metrics])
        ax.set_ylabel("latência (ms)")
        ax.grid(axis="y", alpha=0.3)
    axes[0][0].legend()
    fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.tight_layout()
    out = os.path.join(OUTDIR, fname)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f">> gerado: {out}")


def plot_throughput(df, fname, title):
    sub = df[df["mode"] == "concurrent"]
    if sub.empty:
        return
    piv = sub.groupby(["netem", "proto"])["req_s"].mean()
    profiles = profile_order(piv.index.get_level_values("netem").unique())

    fig, ax = plt.subplots(figsize=(1.9 * len(profiles) + 3, 4.4))
    x = np.arange(len(profiles))
    w = 0.38
    for i, proto in enumerate(["h11", "h3"]):
        vals = [piv.get((p, proto), np.nan) for p in profiles]
        bars = ax.bar(x + (i - 0.5) * w, vals, w, label=LABEL[proto], color=C[proto])
        ax.bar_label(bars, fmt="%.1f", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(profiles, fontsize=9)
    ax.set_ylabel("vazão (requisições por segundo)")
    ax.set_xlabel("perfil de rede (netem)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend()
    fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.tight_layout()
    out = os.path.join(OUTDIR, fname)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f">> gerado: {out}")


def export_summary(df, fname):
    cols = [c for c in ["mean", "p50", "p95", "p99", "max", "batch_ms", "req_s"]
            if c in df.columns]
    resumo = (df.groupby(["netem", "mode", "proto"])[cols]
                .mean().round(2).reset_index())
    out = os.path.join(OUTDIR, fname)
    resumo.to_csv(out, index=False)
    print(f">> gerado: {out}")
    return resumo


def main():
    df = load_df()
    plot_latency(df, "warm", "warm_latency.png",
                 "Latência por requisição — conexão reaproveitada (warm)")
    plot_latency(df, "cold", "cold_latency.png",
                 "Latência de handshake — conexão nova (cold)")
    plot_throughput(df, "throughput.png",
                    "Vazão sob concorrência — 500 requisições em paralelo")
    export_summary(df, "resumo.csv")
    print(">> pronto. Veja os arquivos na pasta results/")


if __name__ == "__main__":
    main()
