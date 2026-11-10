"""Figuras da apresentacao "O codigo do VSI01MalhaAberta, parte por parte".

Gera em ../imgs/:
  fluxo.png         main (configura uma vez, depois laco infinito) e a interrupcao
                    chamada a cada 50 us
  linha_tempo.png   dois periodos do PWM: contador, CMPA, saidas A e B, interrupcao,
                    conversoes do ADC no zero e no topo, troca do CMPA (sombra)
  media_zero.png    a media movel do zero do sensor de corrente (PESO_ZERO)

Uso: python3 figuras.py
"""

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

AQUI = Path(__file__).resolve().parent
IMGS = AQUI.parent / "imgs"
IMGS.mkdir(exist_ok=True)

COR_A, COR_B, COR_C = "#1B365D", "#B23A48", "#2E7D32"
COR_ACENTO, COR_AMARELO, COR_CINZA = "#4A6FA5", "#E8C547", "#6C757D"
plt.rcParams.update({"font.size": 15, "axes.titlesize": 16, "axes.labelsize": 15,
                     "font.family": "sans-serif", "axes.spines.top": False,
                     "axes.spines.right": False})

TOPO = 2500


def caixa(ax, x, y, w, h, texto, cor, tam=14, cor_texto="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=cor, ec="none"))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", color=cor_texto,
            fontsize=tam, linespacing=1.3)


def seta(ax, x0, y0, x1, y1, cor=COR_CINZA):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=cor, lw=2))


def fluxo():
    fig, ax = plt.subplots(figsize=(14, 7.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7.4)
    ax.axis("off")

    # main
    ax.text(3.2, 7.05, "main(): roda uma vez", ha="center", fontsize=17, color=COR_A, weight="bold")
    passos = ["Device_init(), Interrupt_init...\nrelógio de 200 MHz",
              "ConfiguraPinos()\ninversor desligado",
              "ConfiguraModuloPWM() × 3\ncontadores parados",
              "ConfiguraADC()",
              "registra a interrupção\nliga os contadores, EINT"]
    y = 6.0
    for i, p in enumerate(passos):
        caixa(ax, 0.6, y, 5.2, 0.8, p, COR_A, tam=13)
        if i < len(passos) - 1:
            seta(ax, 3.2, y, 3.2, y - 0.3)
        y -= 1.1
    seta(ax, 3.2, y + 1.1, 3.2, y + 0.75)
    caixa(ax, 0.6, y - 0.05, 5.2, 0.8, "for (;;) laço infinito:\nescreve o pino de habilitação",
          COR_ACENTO, tam=13)
    ax.annotate("", xy=(0.55, y + 0.55), xytext=(0.55, y + 0.15),
                arrowprops=dict(arrowstyle="-|>", color=COR_ACENTO, lw=2,
                                connectionstyle="arc3,rad=-1.6"))

    # interrupcao
    ax.text(10.4, 7.05, "AtualizaPWM(): a cada 50 µs", ha="center", fontsize=17, color=COR_B,
            weight="bold")
    passos = ["avança o ângulo\ncalcula as 3 razões cíclicas",
              "EscreveRazao() × 3\nCMPA dos três braços",
              "LeMedidas()\nlê o ADC, converte, grava",
              "limpa a marca e confirma (ACK)\nvolta para o laço"]
    y = 6.0
    for i, p in enumerate(passos):
        caixa(ax, 7.8, y, 5.2, 0.8, p, COR_B, tam=13)
        if i < len(passos) - 1:
            seta(ax, 10.4, y, 10.4, y - 0.3)
        y -= 1.1
    ax.text(10.4, 1.15, "o PWM do braço A chama\nesta função quando o contador passa por zero",
            ha="center", fontsize=13, color=COR_CINZA)
    ax.annotate("", xy=(7.75, 6.4), xytext=(5.85, 0.95),
                arrowprops=dict(arrowstyle="-|>", color=COR_CINZA, lw=1.5, ls="--",
                                connectionstyle="arc3,rad=-0.25"))
    ax.text(6.9, 3.3, "interrompe\no laço", ha="center", fontsize=12, color=COR_CINZA)
    fig.tight_layout()
    fig.savefig(IMGS / "fluxo.png", dpi=110)
    plt.close(fig)


def linha_tempo():
    # dois periodos de 50 us, razao da fase A = 0,3 no 1o e 0,6 no 2o
    t = np.linspace(0, 100, 4001)                        # us
    fase = (t % 50) / 50
    cont = np.where(fase < 0.5, fase * 2 * TOPO, (1 - fase) * 2 * TOPO)
    cmpa = np.where(t < 50, 0.3 * TOPO, 0.6 * TOPO)
    saida_a = (cont < cmpa).astype(float)

    fig, axs = plt.subplots(3, 1, figsize=(14, 7.6), sharex=True,
                            gridspec_kw={"height_ratios": [3, 1, 1]})
    ax = axs[0]
    ax.plot(t, cont, color=COR_A, lw=2, label="contador (TBCTR)")
    ax.plot(t, cmpa, color=COR_B, lw=2, ls="--", label="CMPA da fase A")
    ax.set_ylim(-300, 3300)
    ax.set_yticks([0, 750, 1500, 2500])
    ax.set_yticklabels(["0", "750", "1500", "TOPO = 2500"])
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    for tz in (0, 50, 100):
        ax.axvline(tz, color=COR_CINZA, lw=0.8)
    for tt in (25, 75):
        ax.axvline(tt, color=COR_C, lw=0.8, ls=":")
    # marcas
    for tz in (0, 50):
        ax.annotate("interrupção\nSOCA: v, i, Vdc", xy=(tz, 0), xytext=(tz + 9, 120),
                    color=COR_A, fontsize=12,
                    arrowprops=dict(arrowstyle="-|>", color=COR_A))
    for tt in (25, 75):
        ax.annotate("SOCB: i no topo", xy=(tt, TOPO), xytext=(tt + 1.5, 2950), color=COR_C,
                    fontsize=12, arrowprops=dict(arrowstyle="-|>", color=COR_C))
    ax.annotate("a interrupção de t = 0 escreve 0,6·TOPO;\nvale só a partir do zero seguinte (sombra)",
                xy=(50, 1500), xytext=(53, 1700), color=COR_B, fontsize=12,
                bbox=dict(fc="white", ec="none", alpha=0.9),
                arrowprops=dict(arrowstyle="-|>", color=COR_B))
    ax.set_ylabel("contagens")

    axs[1].fill_between(t, 0, saida_a, color=COR_A, alpha=0.8, step="mid")
    axs[1].set_yticks([])
    axs[1].set_ylabel("EPWM1A\n(cima)", rotation=0, ha="right", va="center")
    axs[2].fill_between(t, 0, 1 - saida_a, color=COR_B, alpha=0.8, step="mid")
    axs[2].set_yticks([])
    axs[2].set_ylabel("EPWM1B\n(baixo)", rotation=0, ha="right", va="center")
    axs[2].set_xlabel("tempo [µs]   (tempo morto de 0,1 µs: pequeno demais para aparecer)")
    axs[2].set_xticks([0, 25, 50, 75, 100])
    for a in axs[1:]:
        for tz in (0, 50, 100):
            a.axvline(tz, color=COR_CINZA, lw=0.8)
        for tt in (25, 75):
            a.axvline(tt, color=COR_C, lw=0.8, ls=":")
    fig.tight_layout()
    fig.savefig(IMGS / "linha_tempo.png", dpi=110)
    plt.close(fig)


def media_zero():
    rng = np.random.default_rng(1)
    n = 4000
    leitura = 2262 + rng.normal(0, 2.0, n)              # contagens com ruido
    zero = np.empty(n)
    z = 2253.0
    for k in range(n):
        z += 0.001 * (leitura[k] - z)
        zero[k] = z
    t = np.arange(n) * 50e-3                             # ms
    fig, ax = plt.subplots(figsize=(13, 4.6))
    ax.plot(t, leitura, ".", color=COR_CINZA, ms=2, label="leitura do ADC (corrente nula)")
    ax.plot(t, zero, color=COR_B, lw=2.5, label="offsetCorrente")
    ax.axvline(50, color=COR_A, lw=1, ls="--")
    ax.text(52, 2254, "50 ms: 63 % do caminho", color=COR_A, fontsize=13)
    ax.set_xlabel("tempo depois de ligar a placa [ms]")
    ax.set_ylabel("contagens")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "media_zero.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    fluxo()
    linha_tempo()
    media_zero()
