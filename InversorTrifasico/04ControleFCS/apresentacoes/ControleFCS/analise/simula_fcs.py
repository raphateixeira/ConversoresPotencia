"""FCS-MPC de corrente (firmware VSI04ControleFCS): figuras e simulacao do ensaio.

Planta: carga RL em estrela (R = 25,3 Ohm, L = 9,8 mH, neutro isolado), em alfa-beta,
simulada com passo fino (Ts/20) para mostrar a ondulacao. Temporizacao do firmware:
corrente lida no zero do contador (k), estado novo aplicado do topo (k + 1/2) ao topo
seguinte; predicao com compensacao do atraso e custo |i* - i(k+3/2)|^2 + lambda n.
Referencias e gravacao iguais as do VSI03 (degraus em d e q). PI simulado (simula_pi)
para comparar.

Gera em ../imgs: fcs_vetores.png, fcs_temporizacao.png, fcs_simulacao.png,
fcs_degrau.png, fcs_lambda.png; imprime os numeros dos slides.
Uso: python3 simula_fcs.py
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[3] / "03ControlePI/apresentacoes/ControlePIDados" / "analise"))
import simula_pi as SP                                    # noqa: E402

IMGS = AQUI.parent / "imgs"
TS, F, N = 50e-6, 60.0, 2044
R, L, VDC = 25.3, 9.8e-3, 20.0
SUB = 20                                                   # passos finos por periodo
AZUL, VERM, VERDE, CINZA, AMAR = "#1F5FBF", "#D62828", "#2A9D3A", "#6C757D", "#E8C547"
plt.rcParams.update({"font.size": 20, "axes.labelsize": 21, "axes.titlesize": 21,
                     "xtick.labelsize": 18, "ytick.labelsize": 18, "legend.fontsize": 18})


def vetor(e, vdc=None):
    vdc = VDC if vdc is None else vdc
    sa, sb, sc = (e >> 2) & 1, (e >> 1) & 1, e & 1
    return np.array([2 / 3 * vdc * (sa - (sb + sc) / 2), vdc / np.sqrt(3) * (sb - sc)])


def simula(lam=0.0, ruido=0.0085, periodos=2, semente=0, Rm=R, Lm=L, media=1):
    """Retorna o ultimo periodo (amostras no zero) e a corrente fina em alfa-beta."""
    rng = np.random.default_rng(semente)
    a, b = np.exp(-Rm * TS / Lm), (1 - np.exp(-Rm * TS / Lm)) / Rm
    ah, bh = np.exp(-Rm * TS / 2 / Lm), (1 - np.exp(-Rm * TS / 2 / Lm)) / Rm
    h = TS / SUB
    af, bf = np.exp(-R * h / L), (1 - np.exp(-R * h / L)) / R      # planta "real" no passo fino
    rd1, rq1 = SP.referencias()
    M = N * periodos
    rd, rq = np.tile(rd1, periodos), np.tile(rq1, periodos)
    w = 2 * np.pi * F
    i = np.zeros(2)
    estado, v_vig, v_novo = 0, np.zeros(2), np.zeros(2)
    out = {k: np.zeros(M) for k in ("id", "iq", "vd", "vq", "ia", "ib", "est")}
    fina = np.zeros((M * SUB, 2))
    com = 0
    for k in range(M):
        th = w * k * TS
        # medida no zero (com ruido e quantizacao do ADC)
        im = i + ruido * rng.standard_normal(2)
        im = np.round(im / 7.32e-3) * 7.32e-3 if ruido > 0 else im
        c, s = np.cos(th), np.sin(th)
        out["id"][k] = im[0] * c + im[1] * s
        out["iq"][k] = -im[0] * s + im[1] * c
        out["ia"][k], out["ib"][k] = i
        # predicao
        i2 = ah * im + bh * v_vig
        t3 = th + 1.5 * w * TS
        ref = np.array([rd[k] * np.cos(t3) - rq[k] * np.sin(t3), rd[k] * np.sin(t3) + rq[k] * np.cos(t3)])
        gmin, melhor = 1e30, estado
        for e in range(8):
            p = a * i2 + b * vetor(e)
            n = bin(e ^ estado).count("1")
            g = np.sum((ref - p) ** 2) + (lam + 1e-9) * n
            if g < gmin:
                gmin, melhor = g, e
        com += bin(melhor ^ estado).count("1")
        estado = melhor
        v_novo = vetor(estado)
        c1, s1 = np.cos(th + w * TS), np.sin(th + w * TS)
        out["vd"][k], out["vq"][k] = v_novo[0] * c1 + v_novo[1] * s1, -v_novo[0] * s1 + v_novo[1] * c1
        out["est"][k] = estado
        # planta: meio periodo com o vetor em vigor, meio com o novo (troca no topo)
        for j in range(SUB):
            v = v_vig if j < SUB // 2 else v_novo
            i = af * i + bf * v
            fina[k * SUB + j] = i
        v_vig = v_novo
    j = slice(M - N, M)
    r = {k: v[j] for k, v in out.items()}
    if media > 1:                       # media sincrona dos ultimos "media" periodos (como o firmware)
        for k in ("id", "iq", "vd", "vq"):
            r[k] = out[k][M - media * N:].reshape(media, N).mean(axis=0)
    r.update(idref=rd[j], iqref=rq[j], fina=fina[(M - N) * SUB:], fsw=com / 6 / (M * TS))
    return r


def erro_rms(x):
    k = np.r_[300:1190, 1300:2040]          # fora dos transitorios
    return np.sqrt(np.mean((x["idref"][k] - x["id"][k]) ** 2 + (x["iqref"][k] - x["iq"][k]) ** 2)) * 1e3


def fig_vetores():
    fig, ax = plt.subplots(figsize=(8.5, 8))
    hexv = [vetor(e) for e in (4, 6, 2, 3, 1, 5, 4)]
    ax.plot([v[0] for v in hexv], [v[1] for v in hexv], color=CINZA, lw=1.5)
    for e in range(8):
        v = vetor(e)
        nome = f"{e >> 2 & 1}{e >> 1 & 1}{e & 1}"
        if e in (0, 7):
            continue
        ax.annotate("", xy=v, xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", lw=3, color=AZUL, mutation_scale=22))
        ax.text(v[0] * 1.17, v[1] * 1.17, nome, ha="center", va="center", fontsize=22, fontweight="bold")
    ax.plot(0, 0, "o", color=VERM, ms=14)
    ax.text(1.2, -1.6, "000, 111\n(vetor nulo)", fontsize=18, color=VERM)
    ax.set_aspect("equal"); ax.set_xlim(-17, 17); ax.set_ylim(-17, 17)
    ax.set_xlabel("$v_α$ [V]"); ax.set_ylabel("$v_β$ [V]")
    ax.set_title(f"estados $S_aS_bS_c$, $V_{{dc}}$ = {VDC:.0f} V")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(IMGS / "fcs_vetores.png", dpi=110); plt.close(fig)


def fig_temporizacao():
    fig, ax = plt.subplots(figsize=(16, 5.6))
    t = np.linspace(-0.25, 3.25, 1400)
    ax.plot(t, 1 - np.abs(((t + 1) % 1) - 0.5) * 2, color="k", lw=1.5)
    for kk, nm in zip(range(4), ("k−1", "k", "k+1", "k+2")):
        ax.axvline(kk, color=CINZA, ls=":", lw=1)
        ax.plot(kk, 0, "o", color=AZUL, ms=13)
        ax.text(kk, -0.22, nm, ha="center", va="top", fontsize=20, fontweight="bold")
    for x0 in (0.5, 1.5, 2.5):
        ax.plot(x0, 1, "D", color=VERM, ms=12)
    ax.axvspan(0.5, 1.5, ymin=0.78, ymax=0.9, color=CINZA, alpha=0.35)
    ax.axvspan(1.5, 2.5, ymin=0.78, ymax=0.9, color=VERM, alpha=0.35)
    ax.text(1.0, 1.42, "vetor em vigor", ha="center", fontsize=17)
    ax.text(2.0, 1.42, "vetor escolhido em k", ha="center", fontsize=17, color=VERM)
    ax.text(1.0, 0.35, "mede i(k)\nescolhe o estado", ha="center", fontsize=16, color=AZUL)
    ax.annotate("", xy=(1.5, 0.15), xytext=(1.0, 0.15), arrowprops=dict(arrowstyle="-|>", lw=2.5, color=VERDE))
    ax.annotate("", xy=(2.5, 0.15), xytext=(1.5, 0.15), arrowprops=dict(arrowstyle="-|>", lw=2.5, color=VERM))
    ax.text(1.25, 0.02, "i(k+½)", ha="center", va="top", fontsize=16, color=VERDE)
    ax.text(2.0, 0.02, "i(k+3/2): custo", ha="center", va="top", fontsize=16, color=VERM)
    ax.plot([], [], "o", color=AZUL, ms=11, label="zero: lê a corrente")
    ax.plot([], [], "D", color=VERM, ms=11, label="topo: as chaves mudam")
    ax.legend(frameon=False, loc="upper left", ncol=2, bbox_to_anchor=(0, 1.32))
    ax.set_ylim(-0.4, 1.6); ax.set_xlim(-0.25, 3.25); ax.axis("off")
    fig.tight_layout(); fig.savefig(IMGS / "fcs_temporizacao.png", dpi=110); plt.close(fig)


def fig_simulacao(x, pi):
    t = np.arange(N) * TS * 1e3
    fig, axs = plt.subplots(1, 2, figsize=(17, 7.2))
    for e, cor in (("d", AZUL), ("q", VERM)):
        axs[0].plot(t, x["v" + e], color=cor, lw=0.6, alpha=0.6, label=f"$v_{e}$ (vetor)")
        axs[0].plot(t, np.convolve(x["v" + e], np.ones(40) / 40, mode="same"), color=cor, lw=3, label=f"$v_{e}$ média 2 ms")
        axs[1].plot(t, x["i" + e] * 1e3, color=cor, lw=1.2, label=f"$i_{e}$ FCS")
        axs[1].plot(t, pi["i" + e] * 1e3, color="k" if e == "d" else CINZA, lw=2, ls="--", label=f"$i_{e}$ PI")
    axs[0].set_ylabel("tensão [V]"); axs[1].set_ylabel("corrente [mA]")
    axs[0].set_ylim(-16, 20)
    for ax in axs:
        ax.set_xlabel("tempo [ms]"); ax.grid(alpha=0.3); ax.margins(x=0)
        ax.legend(frameon=False, loc="upper right", ncol=2, fontsize=15)
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "fcs_simulacao.png", dpi=110); plt.close(fig)


def fig_degrau(x, pi):
    k = SP.REF["d_liga"]
    j = slice(k - 20, k + 100)
    tt = (np.arange(N)[j] - k) * TS * 1e3
    fig, axs = plt.subplots(1, 2, figsize=(17, 6.8))
    tf = (np.arange((k - 20) * SUB, (k + 100) * SUB) / SUB - k) * TS * 1e3
    th = 2 * np.pi * F * (np.arange((k - 20) * SUB, (k + 100) * SUB) / SUB + (2 - 1) * N) * TS
    ia, ib = x["fina"][(k - 20) * SUB:(k + 100) * SUB].T
    idf, iqf = ia * np.cos(th) + ib * np.sin(th), -ia * np.sin(th) + ib * np.cos(th)
    axs[0].step(tt, x["est"][j], where="post", color=CINZA, lw=2)
    axs[0].set_yticks(range(8)); axs[0].set_yticklabels([f"{e >> 2 & 1}{e >> 1 & 1}{e & 1}" for e in range(8)])
    axs[0].set_ylabel("estado $S_aS_bS_c$"); axs[0].set_title("estados escolhidos")
    ax = axs[1]
    ax.step(tt, x["idref"][j] * 1e3, "k:", where="post", lw=1.8)
    ax.plot(tf, idf * 1e3, color=AZUL, lw=1.2, alpha=0.6, label="$i_d$ FCS (contínua)")
    ax.plot(tt, x["id"][j] * 1e3, "o", color=AZUL, ms=5, label="$i_d$ FCS (amostrada)")
    ax.plot(tt, pi["id"][j] * 1e3, "k--", lw=2.2, label="$i_d$ PI")
    ax.plot(tf, iqf * 1e3, color=VERM, lw=1.2, alpha=0.6)
    ax.plot(tt, x["iq"][j] * 1e3, "o", color=VERM, ms=5, label="$i_q$ FCS")
    ax.set_ylabel("corrente [mA]"); ax.set_title("degrau em $i_d$: FCS × PI")
    ax.legend(frameon=False, loc="center right", fontsize=15)
    for ax in axs:
        ax.set_xlabel("tempo desde o degrau [ms]"); ax.grid(alpha=0.3)
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "fcs_degrau.png", dpi=110); plt.close(fig)


def fig_lambda():
    lams = [0, 2e-5, 5e-5, 1e-4, 2e-4, 5e-4]
    fs, er = [], []
    for lam in lams:
        x = simula(lam, ruido=0.0, periodos=2)
        fs.append(x["fsw"]); er.append(erro_rms(x))
    print("lambda | fsw [Hz] | erro rms [mA]")
    for l_, f_, e_ in zip(lams, fs, er):
        print(f"  {l_:.0e} | {f_:6.0f} | {e_:5.1f}")
    fig, ax = plt.subplots(figsize=(12, 6.4))
    ax.plot(np.array(fs) / 1e3, er, "o-", color=AZUL, lw=3, ms=11)
    for l_, f_, e_ in zip(lams, fs, er):
        if l_ not in (0, 2e-4, 5e-4):
            continue
        ax.annotate(f"λ = {l_:.0e}".replace("0e+00", "0"), (f_ / 1e3, e_), textcoords="offset points",
                    xytext=(-40, 14), fontsize=18)
    ax.set_xlabel("frequência média de chaveamento [kHz]"); ax.set_ylabel("erro rms de corrente [mA]")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(IMGS / "fcs_lambda.png", dpi=110); plt.close(fig)


def main():
    fig_vetores()
    fig_temporizacao()
    x = simula(0.0, ruido=0.0085)
    xs = simula(0.0, ruido=0.0)
    pi = SP.simula(300.0, True, ruido=0.0)
    print(f"FCS lambda 0: fsw {xs['fsw']:.0f} Hz, erro rms {erro_rms(xs):.1f} mA (sem ruido), "
          f"{erro_rms(x):.1f} mA (com ruido de medida)")
    print(f"PI 300 Hz: erro rms {erro_rms(pi):.1f} mA (sem ruido)")
    fig_simulacao(x, pi)
    fig_degrau(xs, pi)
    fig_lambda()


if __name__ == "__main__":
    main()
