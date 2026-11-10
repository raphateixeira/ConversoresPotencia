"""Analise do ensaio do PI (VSI03ControlePI) com os dados medidos, comparados a simulacao.

Le ../../../dados/DadosControlePI01.csv (Dados3F: idRef iqRef id iq vd vq iA iB), simula
o mesmo ensaio (simula_pi.simula, 300 Hz com desacoplamento) e gera em ../imgs:
  pi_registro.png   referencias, correntes e tensoes medidas (registro inteiro)
  pi_comparacao.png medido x simulado (registro inteiro)
  pi_degrau_d.png   zoom no degrau de id (subida e descida)
  pi_degrau_q.png   zoom no degrau de iq
  pi_fases.png      correntes das fases
e imprime os numeros dos slides.
Uso: python3 analisa_pi.py [arquivo] [fc] [desacopla 0/1]
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
import simula_pi as S
from simula_pi import N, TS, REF, IMGS

AZUL, VERM, VERDE, CINZA, AMAR = "#1F5FBF", "#D62828", "#2A9D3A", "#6C757D", "#E8C547"
ARQ = sys.argv[1] if len(sys.argv) > 1 else str(S.AQUI.parents[2] / "dados" / "DadosControlePI01.csv")
FC = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
DES = (sys.argv[3] != "0") if len(sys.argv) > 3 else True
t = np.arange(N) * TS * 1e3


def degrau(x, eixo, k0, alvo_ini, alvo_fim, n=300):
    """subida 10-90 %; sobressinal e acomodacao (5 %) sobre a curva suavizada (media de 7
    amostras, 0,35 ms), para o ruido de ~2 mA nao contar como dinamica."""
    y = x["i" + eixo][k0 - 3:k0 + n + 3]
    D = alvo_fim - alvo_ini
    zs = (np.convolve(y, np.ones(7) / 7, mode="valid") - alvo_ini) / D
    z = (y[3:-3] - alvo_ini) / D
    t10 = np.argmax(z >= 0.1); t90 = np.argmax(z >= 0.9)
    sobre = max(0.0, (zs.max() - 1) * 100)
    fora = np.flatnonzero(np.abs(zs - 1) > 0.05)
    acom = (fora[-1] + 1) if fora.size else 0
    return (t90 - t10) * TS * 1e3, sobre, acom * TS * 1e3


def regime(x, eixo, a, b):
    e = x["i" + eixo + "ref"][a:b] - x["i" + eixo][a:b]
    return e.mean() * 1e3, e.std() * 1e3


def main():
    med = S.le_dados_pi(ARQ)
    sim = S.simula(FC, DES, ruido=0.0)
    simr = S.simula(FC, DES, ruido=0.0085 / 4, semente=2)   # ruido de 16 periodos (media)

    # ---- numeros
    print(f"fc {FC:.0f} Hz, desacoplamento {DES}: kp {sim['kp']:.1f}, ki {sim['ki']:.0f}")
    for nome, x in (("medido", med), ("simulado", sim)):
        sd = degrau(x, "d", REF["d_liga"], REF["d0"], REF["d0"] + REF["dd"])
        sdd = degrau(x, "d", REF["d_desl"], REF["d0"] + REF["dd"], REF["d0"])
        sq = degrau(x, "q", REF["q_liga"], REF["q0"], REF["q0"] + REF["dq"])
        suav = lambda v: np.convolve(v, np.ones(7) / 7, mode="same")
        itq = np.abs(suav(x["iq"])[REF["d_liga"]:REF["d_liga"] + 200] - REF["q0"]).max() * 1e3
        itd = np.abs(suav(x["id"])[REF["q_liga"]:REF["q_liga"] + 200] - (REF["d0"] + REF["dd"])).max() * 1e3
        print(f"  {nome:8s} degrau d: subida {sd[0]:.2f} ms, sobressinal {sd[1]:.0f} %, acomoda {sd[2]:.2f} ms | "
              f"descida {sdd[0]:.2f} ms | degrau q: subida {sq[0]:.2f} ms, sobre {sq[1]:.0f} %, acomoda {sq[2]:.2f} ms | "
              f"interf. iq no degrau d {itq:.1f} mA, id no degrau q {itd:.1f} mA")
    for eixo, (a, b) in (("d", (600, 1190)), ("q", (1100, 1690))):
        m, s = regime(med, eixo, a, b)
        print(f"  regime {eixo}: erro medio {m:.2f} mA, desvio {s:.2f} mA")
    for k0, nome in ((150, "0,15 A / 0"), (1000, "0,25 A / -0,05"), (1500, "0,15 / -0,05"), (1900, "0,15 / 0")):
        print(f"  tensoes em regime ({nome}): medido vd {med['vd'][k0:k0+40].mean():.2f} vq {med['vq'][k0:k0+40].mean():.2f} | "
              f"simulado vd {sim['vd'][k0]:.2f} vq {sim['vq'][k0]:.2f}")
    print(f"  |v| max medido {np.hypot(med['vd'], med['vq']).max():.2f} V; soma das fases rms {np.std(med['iA'] + med['iB'] + med['iC']) * 1e3:.2f} mA")
    print(f"  pico das fases {np.abs(np.vstack([med['iA'], med['iB'], med['iC']])).max():.3f} A")

    plt.rcParams.update({"font.size": 20, "axes.labelsize": 22, "axes.titlesize": 22,
                         "xtick.labelsize": 18, "ytick.labelsize": 18, "legend.fontsize": 19})

    def par(ax_v, ax_i, x, j, tt, estilo="-", ms=0, lw=2.6, sim=None, refs=True, desvio=None):
        """tensoes d e q num eixo, correntes d e q (e referencias) no outro."""
        for e, cor in (("d", AZUL), ("q", VERM)):
            base_v = 0.0 if desvio is None else x["v" + e][desvio]
            base_i = 0.0 if desvio is None else x["i" + e][desvio]
            if sim is not None:
                bs_v = 0.0 if desvio is None else sim["v" + e][desvio]
                bs_i = 0.0 if desvio is None else sim["i" + e][desvio]
                ax_v.plot(tt, sim["v" + e][j] - bs_v, color=cor, lw=1.8, ls="--", alpha=0.9)
                ax_i.plot(tt, (sim["i" + e][j] - bs_i) * 1e3, color=cor, lw=1.8, ls="--", alpha=0.9)
            ax_v.plot(tt, x["v" + e][j] - base_v, estilo, color=cor, lw=lw, ms=ms, label=f"$v_{e}$")
            ax_i.plot(tt, (x["i" + e][j] - base_i) * 1e3, estilo, color=cor, lw=lw, ms=ms, label=f"$i_{e}$")
            if refs:
                base_r = 0.0 if desvio is None else x["i" + e + "ref"][desvio]
                ax_i.step(tt, (x["i" + e + "ref"][j] - base_r) * 1e3, where="post", color="k" if e == "d" else CINZA,
                          lw=1.6, ls=":", label=f"$i_{e}^*$")

    def acabamento(axs, xlabel):
        for ax in axs.flat:
            ax.grid(alpha=0.3)
            nh = len(ax.get_legend_handles_labels()[0])
            ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 1.0), ncol=nh, borderaxespad=0,
                      handlelength=1.2, columnspacing=0.8, markerscale=3)
        for ax in axs[-1] if axs.ndim > 1 else axs:
            ax.set_xlabel(xlabel)

    # ---- registro medido: entradas a esquerda, respostas a direita
    fig, axs = plt.subplots(1, 2, figsize=(17, 7.2))
    par(axs[0], axs[1], med, slice(None), t, lw=1.8)
    axs[0].set_ylabel("tensão [V]"); axs[1].set_ylabel("corrente [mA]")
    for ax in axs:
        ax.margins(x=0)
    acabamento(axs, "tempo [ms]")
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "pi_registro.png", dpi=110); plt.close(fig)

    # ---- medido x simulado (tracejado = simulado)
    fig, axs = plt.subplots(1, 2, figsize=(17, 7.2))
    par(axs[0], axs[1], med, slice(None), t, estilo=".", ms=3, lw=0, sim=sim)
    axs[0].plot([], [], "k--", lw=1.8, label="simulado"); axs[1].plot([], [], "k--", lw=1.8, label="simulado")
    axs[0].set_ylabel("tensão [V]"); axs[1].set_ylabel("corrente [mA]")
    for ax in axs:
        ax.margins(x=0)
    acabamento(axs, "tempo [ms]")
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "pi_comparacao.png", dpi=110); plt.close(fig)

    # ---- zooms: linhas = inicio e fim do degrau; desvios em relacao ao valor antes do degrau
    for e, k1, k2, arq in (("d", REF["d_liga"], REF["d_desl"], "pi_degrau_d.png"),
                           ("q", REF["q_liga"], REF["q_desl"], "pi_degrau_q.png")):
        fig, axs = plt.subplots(2, 2, figsize=(17, 8.8), sharex=True)
        for row, k in enumerate((k1, k2)):
            j = slice(k - 20, k + 100)
            tt = (np.arange(N)[j] - k) * TS * 1e3
            par(axs[row, 0], axs[row, 1], med, j, tt, estilo="o-", ms=4, lw=1.2, sim=sim, desvio=k - 2)
            r = med["i" + e + "ref"]
            nome = "início" if row == 0 else "fim"
            axs[row, 0].set_ylabel(f"Δv [V]\n({nome})")
            axs[row, 1].set_ylabel(f"Δi [mA]\n({nome}: $i_{e}^*$ {r[k - 5] * 1e3:.0f}→{r[k + 5] * 1e3:.0f})")
        axs[0, 0].plot([], [], "k--", lw=1.8, label="simulado")
        acabamento(axs, "tempo desde o degrau [ms]")
        for ax in axs[1]:
            ax.get_legend().remove()
        fig.tight_layout(w_pad=3, h_pad=1.5); fig.savefig(IMGS / arq, dpi=110); plt.close(fig)

    # ---- fases
    fig, ax = plt.subplots(figsize=(17, 6.2))
    for c, cor, n in (("iA", AZUL, "$i_A$"), ("iB", VERM, "$i_B$"), ("iC", VERDE, "$i_C$")):
        ax.plot(t, med[c] * 1e3, color=cor, lw=1.6, label=n)
    for k in (REF["d_liga"], REF["q_liga"], REF["d_desl"], REF["q_desl"]):
        ax.axvline(k * TS * 1e3, color=CINZA, ls=":", lw=1.5)
    ax.set_xlabel("tempo [ms]"); ax.set_ylabel("corrente de fase [mA]")
    ax.legend(frameon=False, loc="upper right", ncol=3); ax.grid(alpha=0.3); ax.margins(x=0)
    fig.tight_layout(); fig.savefig(IMGS / "pi_fases.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
