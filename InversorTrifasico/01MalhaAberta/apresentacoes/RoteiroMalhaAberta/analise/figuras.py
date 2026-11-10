"""Figuras e numeros da apresentacao "Roteiro do inversor em malha aberta" (VSI01).

Gera em ../imgs/:
  modos01.png         o que o osciloscopio mostra nos modos 0 e 1
  modo2.png           modo 2: razoes ciclicas e o PWM da fase A em 5 ms/div
  anim_modo2.gif      modo 2: as tres razoes ciclicas girando
  etapaB.png          simulacao com a carga RL a 20 V (modo 2, amplitude 0,4)
  rc_esquema.png      ligacao do filtro RC (etapas A e B)
  rc_etapaA.png       saida do RC na LaunchPad (0 a 3,3 V)
  rc_etapaB.png       saidas do RC nos bornes do inversor (0 a 20 V)

O PWM (contador, saidas com tempo morto), a carga e as cores vem de
00Bancada/apresentacoes/BancadaInversor/analise/figuras_placa.py.
Uso: python3 figuras.py   (precisa de numpy, matplotlib e Pillow)
Os numeros impressos no fim sao os valores esperados na bancada (slides).
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Rectangle, Circle

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[3] / "00Bancada/apresentacoes/BancadaInversor/analise"))
from figuras_placa import (contador, saidas, F_PWM, TOPO, VDC, R, L,  # noqa: E402
                           COR_A, COR_B, COR_C, COR_ACENTO, COR_AMARELO, COR_CINZA)

IMGS = AQUI.parent / "imgs"
IMGS.mkdir(exist_ok=True)
AMPLITUDE = 0.4            # amplitude da razao ciclica no modo 2 (padrao do main.c)


def salva(fig, nome):
    fig.savefig(IMGS / nome, dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("gravado", nome)


def figura_modos01():
    t = np.linspace(0, 2 / F_PWM, 4000)
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)
    for ax, razoes, tit in [(axs[0], (0.5, 0.5, 0.5), "modo 0: 50 % nas três fases"),
                            (axs[1], (0.25, 0.5, 0.75), "modo 1: 25 %, 50 % e 75 %")]:
        for k, (d, cor, nome) in enumerate(zip(razoes, (COR_A, COR_B, COR_C), "ABC")):
            a, _ = saidas(t, d)
            ax.plot(t * 1e6, a * 3.3 + (2 - k) * 4.5, color=cor, lw=2.2, drawstyle="steps-post")
            ax.text(-3, (2 - k) * 4.5 + 1.6, f"{nome}\n{d:.0%}".replace("%", " %"),
                    color=cor, ha="right", va="center", fontsize=14)
        ax.set_title(tit); ax.set_yticks([]); ax.set_xlabel("tempo [µs] (10 µs/div)")
        ax.set_xlim(0, 100)
    salva(fig, "modos01.png")


def figura_modo2():
    amplitude, f = AMPLITUDE, 60.0
    t = np.arange(0, 2 / f, 1 / (F_PWM * 200))
    ang = 2 * np.pi * f * np.floor(t * F_PWM) / F_PWM
    fig, axs = plt.subplots(2, 1, figsize=(12, 6.2), sharex=True)
    for k, (cor, nome) in enumerate(zip((COR_A, COR_B, COR_C), "ABC")):
        d = 0.5 + amplitude * np.sin(ang - k * 2 * np.pi / 3)
        axs[0].plot(t * 1e3, d, color=cor, lw=2.5, label=f"fase {nome}")
    axs[0].set_ylabel("razão cíclica"); axs[0].set_ylim(0, 1)
    axs[0].legend(ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.22))
    dA = 0.5 + amplitude * np.sin(ang)
    cnt = contador(t)
    pwmA = (cnt < dA * TOPO).astype(float)
    axs[1].fill_between(t * 1e3, 0, pwmA, step="post", color=COR_A, lw=0)
    axs[1].plot(t * 1e3, dA, color=COR_AMARELO, lw=3, label="média do pulso = razão cíclica")
    axs[1].set_ylabel("J4-40"); axs[1].set_yticks([0, 1])
    axs[1].set_xlabel("tempo [ms] (5 ms/div): 60 Hz, amplitude 0,4")
    axs[1].legend(frameon=False, loc="lower right", fontsize=13)
    salva(fig, "modo2.png")


def animacao_modo2():
    amplitude = AMPLITUDE
    angs = np.linspace(0, 2 * np.pi, 49)[:-1]
    x = np.linspace(0, 2 * np.pi, 300)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1, 1.6]})
    cores = (COR_A, COR_B, COR_C)
    barras = ax1.bar(["A", "B", "C"], [0.5] * 3, color=cores)
    ax1.set_ylim(0, 1); ax1.axhline(0.5, color=COR_CINZA, ls="--", lw=1)
    ax1.set_ylabel("razão cíclica"); ax1.set_title("as três fases agora")
    for k, cor in enumerate(cores):
        ax2.plot(np.degrees(x), 0.5 + amplitude * np.sin(x - k * 2 * np.pi / 3), color=cor, lw=2.5)
    cursor = ax2.axvline(0, color="k", lw=1.5)
    ax2.set_xlim(0, 360); ax2.set_ylim(0, 1); ax2.set_xticks([0, 120, 240, 360])
    ax2.set_xlabel("ângulo [graus] (um ciclo = 1/60 s)"); ax2.set_title("120° entre as fases")
    fig.tight_layout()

    def quadro(i):
        a = angs[i]
        for k, br in enumerate(barras):
            br.set_height(0.5 + amplitude * np.sin(a - k * 2 * np.pi / 3))
        cursor.set_xdata([np.degrees(a)] * 2)
        return (*barras, cursor)

    anim = FuncAnimation(fig, quadro, frames=len(angs), interval=80)
    anim.save(IMGS / "anim_modo2.gif", writer=PillowWriter(fps=12), dpi=75)
    plt.close(fig)
    print("gravado anim_modo2.gif")


def simula_carga(amplitude=AMPLITUDE, f=60.0, ciclos=3, dt=0.2e-6):
    n = int(ciclos / f / dt)
    t = np.arange(n) * dt
    amostra = np.floor(t * F_PWM)                       # razao ciclica muda a cada periodo
    ang = 2 * np.pi * f * amostra / F_PWM
    cnt = contador(t)
    v_terminal = np.zeros((3, n))
    for k in range(3):
        d = 0.5 + amplitude * np.sin(ang - k * 2 * np.pi / 3)
        v_terminal[k] = VDC * (cnt < d * TOPO)          # tensao do terminal em relacao ao GND
    v_neutro = v_terminal.mean(axis=0)                  # carga equilibrada em estrela
    v_fase = v_terminal - v_neutro
    a = np.exp(-dt * R / L)
    i = np.zeros((3, n))
    for j in range(1, n):
        i[:, j] = i[:, j - 1] * a + v_fase[:, j - 1] / R * (1 - a)
    # tensao em J3-24: divisor 100k/4,22k com 33 nF (constante de tempo de Thevenin)
    tau_f = (100e3 * 4.22e3 / 104.22e3) * 33e-9
    af = np.exp(-dt / tau_f)
    vf = np.zeros(n)
    for j in range(1, n):
        vf[j] = vf[j - 1] * af + v_terminal[0, j - 1] / 24.7 * (1 - af)
    return t, v_terminal, i, vf


def figura_etapaB():
    t, vt, i, vf = simula_carga()
    m = t >= 1 / 60                                     # descarta o primeiro ciclo (transitorio)
    tm = (t[m] - t[m][0]) * 1e3
    fig, axs = plt.subplots(3, 1, figsize=(12, 7.6), sharex=True)
    axs[0].fill_between(tm, 0, vt[0, m], step="post", color=COR_A, lw=0)
    axs[0].set_ylabel("VA × GND\n[V]"); axs[0].set_yticks([0, VDC])
    axs[1].plot(tm, vf[m], color=COR_A, lw=1.5)
    axs[1].set_ylabel("J3-24\n[V]")
    for k, (cor, nome) in enumerate(zip((COR_A, COR_B, COR_C), "ABC")):
        axs[2].plot(tm, i[k, m], color=cor, lw=2, label=f"$i_{nome}$")
    axs[2].set_ylabel("corrente\n[A]"); axs[2].legend(ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.97))
    axs[2].set_xlabel("tempo [ms] (5 ms/div)")
    sec = axs[2].secondary_yaxis("right", functions=(lambda x: 1.65 - 0.1 * x,
                                                     lambda v: (1.65 - v) / 0.1))
    sec.set_ylabel("J3-27 [V]")
    salva(fig, "etapaB.png")
    pico = i[0, m].max()
    print(f"simulacao: pico de iA = {pico:.3f} A; J3-27 entre {1.65 - 0.1 * pico:.3f} "
          f"e {1.65 + 0.1 * pico:.3f} V; J3-24 entre {vf[m].min():.3f} e {vf[m].max():.3f} V")


# ---------------------------------------------------------------------------
# Filtro RC para ver a senoide (R = 10 kOhm, C = 100 nF: corte em 159 Hz)
R_FILTRO, C_FILTRO = 10e3, 100e-9


def desenha_rc(ax, x, y_topo, rotulo, cor):
    """Um filtro RC: resistor horizontal saindo de (x, y_topo), capacitor e
    simbolo de terra embaixo (cada RC com o seu proprio terra)."""
    ax.plot([x, x + 0.4], [y_topo, y_topo], color=cor, lw=2)
    ax.add_patch(Rectangle((x + 0.4, y_topo - 0.15), 1.0, 0.3, fc="white", ec=cor, lw=2))
    ax.text(x + 0.9, y_topo + 0.28, "10 kΩ", ha="center", fontsize=12)
    ax.plot([x + 1.4, x + 2.2], [y_topo, y_topo], color=cor, lw=2)
    ax.add_patch(Circle((x + 2.2, y_topo), 0.07, color=cor))
    ax.plot([x + 2.2, x + 2.2], [y_topo, y_topo - 0.4], color=cor, lw=2)
    ax.plot([x + 1.95, x + 2.45], [y_topo - 0.4, y_topo - 0.4], color=cor, lw=3)
    ax.plot([x + 1.95, x + 2.45], [y_topo - 0.58, y_topo - 0.58], color=cor, lw=3)
    ax.text(x + 2.6, y_topo - 0.49, "100 nF", va="center", fontsize=12)
    ax.plot([x + 2.2, x + 2.2], [y_topo - 0.58, y_topo - 0.85], color="k", lw=2)
    for j, meia in enumerate((0.25, 0.16, 0.07)):          # simbolo de terra
        yy = y_topo - 0.85 - 0.08 * j
        ax.plot([x + 2.2 - meia, x + 2.2 + meia], [yy, yy], color="k", lw=2)
    if rotulo:
        ax.annotate(rotulo, xy=(x + 2.2, y_topo), xytext=(x + 2.7, y_topo + 0.3), fontsize=12,
                    color=cor, weight="bold", arrowprops=dict(arrowstyle="->", color=cor))


def figura_rc_esquema():
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.4))
    paineis = [("Etapa A: na LaunchPad (0 a 3,3 V)",
                [("J4-40 (A)", COR_A, 3.6, "ponta CH1"), ("J4-38 (B)", COR_B, 1.9, "ponta CH2")],
                "terra = J2-20 (GND): garras de terra aqui", "k"),
               ("Etapa B: nos bornes do inversor (0 a 20 V), sem a carga RL",
                [("VA", COR_A, 4.1, "ponta CH1"), ("VB", COR_B, 2.6, "ponta CH2"),
                 ("VC", COR_C, 1.1, "")],
                "terra = borne GND: garras de terra só aqui", COR_B)]
    for ax, (tit, linhas, nota, cor_nota) in zip(axs, paineis):
        ax.set_xlim(0, 7); ax.set_ylim(-0.5, 4.8); ax.axis("off")
        ax.set_title(tit, fontsize=15)
        for pino, cor, yt, rot in linhas:
            ax.text(0.1, yt, pino, va="center", fontsize=13, color=cor, weight="bold")
            desenha_rc(ax, 1.4, yt, rot, cor)
        ax.text(0.1, -0.3, nota, fontsize=13, color=cor_nota, weight="bold")
    salva(fig, "rc_esquema.png")


def simula_rc(vpico, amplitude=AMPLITUDE, f=60.0, ciclos=3, dt=0.2e-6):
    """Saida do RC para as tres fases (pulsos de 0 a vpico, modo 2)."""
    n = int(ciclos / f / dt)
    t = np.arange(n) * dt
    ang = 2 * np.pi * f * np.floor(t * F_PWM) / F_PWM
    cnt = contador(t)
    a = np.exp(-dt / (R_FILTRO * C_FILTRO))
    pulsos = np.zeros((3, n)); vc = np.zeros((3, n))
    for k in range(3):
        d = 0.5 + amplitude * np.sin(ang - k * 2 * np.pi / 3)
        pulsos[k] = vpico * (cnt < d * TOPO)
    vc[:, 0] = vpico / 2
    for j in range(1, n):
        vc[:, j] = vc[:, j - 1] * a + pulsos[:, j - 1] * (1 - a)
    return t, pulsos, vc


def figura_rc_simulacao():
    for vpico, nome, tit in [(3.3, "rc_etapaA.png", "Etapa A: J4-40 e saída do RC (amplitude 0,4, 60 Hz)"),
                             (VDC, "rc_etapaB.png", "Etapa B: saídas dos três RC e a diferença A − B")]:
        t, p, vc = simula_rc(vpico)
        m = t >= 1 / 60
        tm = (t[m] - t[m][0]) * 1e3
        if vpico < 5:
            fig, axs = plt.subplots(2, 1, figsize=(12, 6.2), sharex=True)
            axs[0].fill_between(tm, 0, p[0, m], step="post", color=COR_A, lw=0)
            axs[0].set_ylabel("J4-40 [V]"); axs[0].set_yticks([0, 3.3])
            axs[1].plot(tm, vc[0, m], color=COR_A, lw=1.5, label="CH1: depois do RC (fase A)")
            axs[1].plot(tm, vc[1, m], color=COR_B, lw=1.5, label="CH2: depois do RC (fase B)")
            axs[1].set_ylabel("[V]"); axs[1].legend(frameon=False, ncol=2, loc="upper center",
                                                    bbox_to_anchor=(0.5, 1.2))
            print(f"RC etapa A: {vc[0, m].min():.2f} a {vc[0, m].max():.2f} V")
        else:
            fig, axs = plt.subplots(2, 1, figsize=(12, 6.2), sharex=True)
            for k, (cor, nome_f) in enumerate(zip((COR_A, COR_B, COR_C), "ABC")):
                axs[0].plot(tm, vc[k, m], color=cor, lw=1.5, label=f"V{nome_f} depois do RC")
            axs[0].set_ylabel("[V]"); axs[0].legend(frameon=False, ncol=3, loc="upper center",
                                                    bbox_to_anchor=(0.5, 1.25))
            dif = vc[0, m] - vc[1, m]
            axs[1].plot(tm, dif, color=COR_ACENTO, lw=1.5)
            axs[1].set_ylabel("A − B [V]")
            print(f"RC etapa B: VA {vc[0, m].min():.2f} a {vc[0, m].max():.2f} V; "
                  f"A-B {dif.min():.2f} a {dif.max():.2f} V")
        axs[1].set_xlabel("tempo [ms] (5 ms/div)")
        fig.suptitle(tit, fontsize=15, y=1.02)
        salva(fig, nome)


def numeros_esperados():
    z = np.hypot(R, 2 * np.pi * 60 * L)
    phi = np.degrees(np.arctan2(2 * np.pi * 60 * L, R))
    print(f"\nvalores esperados ({VDC:.0f} V, carga {R:.0f} ohm + {L * 1e3:.0f} mH):")
    vf = 0.25 * VDC                                  # modo 1: medias 25/50/75 % -> fases -vf, 0, +vf
    i1 = vf / R
    print(f"  modo 1: medias {0.25 * VDC:.0f}, {0.5 * VDC:.0f}, {0.75 * VDC:.0f} V; fases -{vf:.0f}, 0, +{vf:.0f} V"
          f" -> iA = {-i1:.3f} A, iC = {i1:.3f} A; J3-27 = {1.65 + 0.1 * i1:.3f} V;"
          f" potencia = {2 * i1 ** 2 * R:.2f} W -> fonte {2 * i1 ** 2 * R / VDC:.2f} A")
    for a in (0.25, 0.4, 0.45):
        vp = a * VDC
        ip = vp / z
        p = 1.5 * vp * ip * np.cos(np.radians(phi))
        print(f"  modo 2, amplitude {a}: fase {vp:.1f} V de pico, |Z| = {z:.2f}, i = {ip:.3f} A de pico"
              f" ({phi:.1f} graus); potencia {p:.2f} W -> fonte {p / VDC:.3f} A;"
              f" J3-27 = 1,65 +- {0.1 * ip:.3f} V; J3-24 = {(0.5 - a) * VDC / 24.7:.2f} a {(0.5 + a) * VDC / 24.7:.2f} V")


if __name__ == "__main__":
    figura_modos01()
    figura_modo2()
    animacao_modo2()
    figura_etapaB()
    figura_rc_esquema()
    figura_rc_simulacao()
    numeros_esperados()
