"""Figuras dos referenciais (slides de modelagem).

1. ../imgs/referenciais.gif: animacao abc -> alfa-beta -> dq (um ciclo de 60 Hz):
   sinais abc, alfa-beta e dq no tempo e o vetor girando no plano, com os eixos d e q girando junto.
2. ../imgs/firmware_dq.png (diagrama) e firmware_dq_sinais.png: como o firmware VSI02 cria as tensoes (dados gravados, Dados01A):
   angulo theta(k), v_d e v_q = constante + PRBS, Park inversa -> v_A, v_B, v_C, razoes ciclicas.
Uso: python3 referenciais.py
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import identifica as I
from identifica import IMGS, TS, COR_A, COR_B, COR_C, COR_CINZA

plt.rcParams.update({"font.size": 17, "axes.labelsize": 18, "axes.titlesize": 18,
                     "xtick.labelsize": 14, "ytick.labelsize": 14, "legend.fontsize": 16})
ABC = (COR_A, COR_B, COR_C)
F = 60.0
PHI = np.radians(30)            # o vetor adiantado 30 graus do eixo d: d e q nao nulos


def animacao(nquadros=48):
    T = 1 / F
    t = np.linspace(0, T, 400)
    th = 2 * np.pi * F * t
    abc = [np.cos(th + PHI - k * 2 * np.pi / 3) for k in range(3)]
    al = (2 * abc[0] - abc[1] - abc[2]) / 3
    be = (abc[1] - abc[2]) / np.sqrt(3)
    d = al * np.cos(th) + be * np.sin(th)
    q = -al * np.sin(th) + be * np.cos(th)
    tm = t * 1e3
    fig = plt.figure(figsize=(12, 7.2))
    g = fig.add_gridspec(3, 2, width_ratios=[1.15, 1], wspace=0.08, hspace=0.12)
    a1, a2, a3 = fig.add_subplot(g[0, 0]), fig.add_subplot(g[1, 0]), fig.add_subplot(g[2, 0])
    ap = fig.add_subplot(g[:, 1])
    for ax, ys, nomes, cores, tit in ((a1, abc, ("$v_A$", "$v_B$", "$v_C$"), ABC, "abc"),
                                      (a2, (al, be), (r"$v_\alpha$", r"$v_\beta$"), (COR_A, COR_B), "αβ"),
                                      (a3, (d, q), ("$v_d$", "$v_q$"), (COR_A, COR_B), "dq")):
        for y, n, c in zip(ys, nomes, cores):
            ax.plot(tm, y, color=c, lw=3.2, label=n)
        ax.set_xlim(0, tm[-1]); ax.set_ylim(-1.2, 1.9); ax.set_yticks([-1, 0, 1])
        ax.set_ylabel(tit, fontsize=21)
        ax.tick_params(labelsize=17)
        ax.legend(frameon=False, loc="upper center", ncol=3, fontsize=20, handlelength=1.2,
                  borderaxespad=0.1, columnspacing=1.2)
        ax.grid(alpha=0.3)
    a3.set_xlabel("tempo [ms]", fontsize=20)
    a1.tick_params(labelbottom=False); a2.tick_params(labelbottom=False)
    cur = [ax.axvline(0, color="k", lw=1.5) for ax in (a1, a2, a3)]
    ap.set_aspect("equal"); ap.set_xlim(-1.4, 1.4); ap.set_ylim(-1.4, 1.4); ap.axis("off")
    ap.add_patch(plt.Circle((0, 0), 1, fill=False, color=COR_CINZA, lw=1))
    ap.annotate("", xy=(1.3, 0), xytext=(-1.3, 0), arrowprops=dict(arrowstyle="-|>", lw=3, color=COR_CINZA, mutation_scale=22))
    ap.annotate("", xy=(0, 1.3), xytext=(0, -1.3), arrowprops=dict(arrowstyle="-|>", lw=3, color=COR_CINZA, mutation_scale=22))
    for k, (c, n) in enumerate(zip(ABC, "ABC")):
        ang = k * 2 * np.pi / 3
        ap.plot([0, 1.25 * np.cos(ang)], [0, 1.25 * np.sin(ang)], color=c, lw=1.2, alpha=0.6)
        ap.text(1.36 * np.cos(ang), 1.36 * np.sin(ang), n, color=c, ha="center", va="center", fontsize=22)
    ap.text(1.2, -0.28, "α", fontsize=26, color=COR_CINZA, fontweight="bold"); ap.text(0.1, 1.2, "β", fontsize=26, color=COR_CINZA, fontweight="bold")
    ap.set_title("plano αβ: eixos dq girando", fontsize=21)
    eixo_d, = ap.plot([], [], color=COR_A, lw=2.5, ls="--")
    eixo_q, = ap.plot([], [], color=COR_B, lw=2.5, ls="--")
    td = ap.text(0, 0, "d", color=COR_A, fontsize=26, fontweight="bold")
    tq = ap.text(0, 0, "q", color=COR_B, fontsize=26, fontweight="bold")
    seta = ap.annotate("", xy=(1, 0), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", lw=3, color="k", mutation_scale=25))
    proj_d, = ap.plot([], [], color=COR_A, lw=6, alpha=0.5)
    proj_q, = ap.plot([], [], color=COR_B, lw=6, alpha=0.5)
    idx = np.linspace(0, len(t) - 1, nquadros).astype(int)

    def quadro(n):
        i = idx[n]
        for c in cur:
            c.set_xdata([tm[i], tm[i]])
        ct, st = np.cos(th[i]), np.sin(th[i])
        eixo_d.set_data([-1.2 * ct, 1.2 * ct], [-1.2 * st, 1.2 * st])
        eixo_q.set_data([1.2 * st, -1.2 * st], [-1.2 * ct, 1.2 * ct])
        td.set_position((1.22 * ct, 1.22 * st)); tq.set_position((-1.22 * st, 1.22 * ct))
        seta.xy = (al[i], be[i])
        proj_d.set_data([0, d[i] * ct], [0, d[i] * st])
        proj_q.set_data([0, -q[i] * st], [0, q[i] * ct])
        return cur + [eixo_d, eixo_q, td, tq, seta, proj_d, proj_q]

    fig.subplots_adjust(left=0.08, right=0.99, top=0.93, bottom=0.1)
    an = FuncAnimation(fig, quadro, frames=nquadros, blit=False)
    an.save(IMGS / "referenciais.gif", writer=PillowWriter(fps=12), dpi=85)
    plt.close(fig)


def firmware(t_ms=20.0):
    s = I.carrega()
    t = np.arange(s["N"]) * TS * 1e3
    j = t <= t_ms
    th, vd, vq, vdc = s["th"], s["vd"], s["vq"], s["vdc"]
    vabc = [vd * np.cos(th - k * 2 * np.pi / 3) - vq * np.sin(th - k * 2 * np.pi / 3) for k in range(3)]
    fig, axs = plt.subplots(2, 2, figsize=(16, 8.4), sharex=True)
    ax = axs[0, 0]
    ax.plot(t[j], th[j], color="k", lw=2.5)
    ax.set_ylabel("θ [rad]"); ax.set_title("1. ângulo: θ(k) = θ(k−1) + ωT$_s$")
    ax = axs[0, 1]
    ax.step(t[j], vd[j], where="post", color=COR_A, lw=2.5, label="$v_d$ = 5 + 3·PRBS")
    ax.step(t[j], vq[j], where="post", color=COR_B, lw=2.5, label="$v_q$ = 0 + 3·PRBS")
    ax.set_ylabel("[V]"); ax.set_title("2. tensões em dq: constante + PRBS")
    ax.legend(frameon=False, loc="upper right", ncol=2, framealpha=0.9)
    ax = axs[1, 0]
    for k, (c, n) in enumerate(zip(ABC, ("$v_A$", "$v_B$", "$v_C$"))):
        ax.plot(t[j], vabc[k][j], color=c, lw=2, label=n)
    ax.set_ylabel("[V]"); ax.set_title("3. Park inversa: $v_A = v_d\\cos θ - v_q\\sin θ$, ...")
    ax.legend(frameon=False, loc="upper right", ncol=3, framealpha=0.9)
    ax = axs[1, 1]
    for k, (c, n) in enumerate(zip(ABC, ("$d_A$", "$d_B$", "$d_C$"))):
        ax.plot(t[j], 0.5 + vabc[k][j] / vdc[j], color=c, lw=2, label=n)
    ax.set_ylabel("razão cíclica"); ax.set_title("4. PWM: $d = 0{,}5 + v/V_{dc}$")
    ax.legend(frameon=False, loc="upper right", ncol=3, framealpha=0.9)
    for ax in axs.flat:
        ax.grid(alpha=0.3); ax.margins(x=0, y=0.3)
    for ax in axs[1]:
        ax.set_xlabel("tempo [ms]")
    fig.tight_layout(h_pad=2, w_pad=3)
    fig.savefig(IMGS / "firmware_dq_sinais.png", dpi=110)
    plt.close(fig)


def firmware_diagrama():
    """Diagrama do firmware VSI02: referencial dq criado pelo angulo theta, PRBS em v_d e v_q."""
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(16, 6.4))
    ax.set_xlim(0, 16); ax.set_ylim(0, 6.4); ax.axis("off")
    W, H = 2.9, 1.4

    def caixa(x, y, txt, cor):
        ax.add_patch(FancyBboxPatch((x, y - H / 2), W, H, boxstyle="round,pad=0.04", fc="white", ec=cor, lw=3))
        ax.text(x + W / 2, y, txt, ha="center", va="center", fontsize=19)

    def seta(x0, y0, x1, y1, txt=None, dy=0.12, cor="k"):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", lw=2.2, color=cor, mutation_scale=24))
        if txt:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, txt, ha="center", va="bottom", fontsize=19)

    yt, yb, ym = 5.0, 1.2, 3.1
    ax.axvspan(0, 7.45, color=COR_A, alpha=0.06)
    ax.text(0.15, 6.2, "referencial dq (constantes)", fontsize=18, color=COR_A, va="top")
    ax.text(15.85, 6.2, "abc (60 Hz)", fontsize=18, color=COR_C, va="top", ha="right")
    caixa(0.2, yt, "$v_d = 5 + 3\\,$PRBS\n$v_q = 0 + 3\\,$PRBS", COR_A)
    seta(3.1, yt, 4.4, yt)
    caixa(4.4, yt, "Park inversa\n(θ)", COR_A)
    seta(7.3, yt, 8.5, yt, "$v_{ABC}$")
    caixa(8.5, yt, "$d = 0{,}5 + v/V_{dc}$\nPWM", COR_CINZA)
    seta(11.4, yt, 12.6, yt)
    caixa(12.6, yt, "inversor +\ncarga RL", COR_C)
    seta(14.05, yt - H / 2, 14.05, yb + H / 2)
    caixa(12.6, yb, "ADC\n$i_A, i_B, i_C$", COR_CINZA)
    seta(12.6, yb, 7.3, yb, "$i_{ABC}$")
    caixa(4.4, yb, "Park\n(θ)", COR_A)
    seta(4.4, yb, 3.1, yb)
    caixa(0.2, yb, "$i_d, i_q$\n(gravados)", COR_A)
    ax.add_patch(FancyBboxPatch((8.6, ym - 0.55), 2.7, 1.1, boxstyle="round,pad=0.04", fc="white", ec="k", lw=2))
    ax.text(9.95, ym, "θ(k) = θ(k−1) + ωT$_s$", ha="center", va="center", fontsize=17)
    ax.plot([8.6, 5.85], [ym, ym], color="k", lw=2.2)
    seta(5.85, ym, 5.85, yt - H / 2)
    seta(5.85, ym, 5.85, yb + H / 2)
    fig.tight_layout()
    fig.savefig(IMGS / "firmware_dq.png", dpi=110)
    plt.close(fig)


def dq_constante(vd0=5.0, vq0=0.0, t_ms=25.0, R=25.0, L=10e-3):
    """v_d, v_q constantes -> senoides em abc; correntes do modelo RL (partindo de zero)."""
    import scipy.linalg as la
    w = 2 * np.pi * F
    A = np.array([[-R / L, w], [-w, -R / L]])
    Phi = la.expm(A * TS)
    Gam = np.linalg.solve(A, (Phi - np.eye(2)) / L)
    n = int(t_ms * 1e-3 / TS)
    t = np.arange(n) * TS * 1e3
    th = w * np.arange(n) * TS
    v = np.array([vd0, vq0])
    i = np.zeros((n, 2))
    for k in range(1, n):
        i[k] = Phi @ i[k - 1] + Gam @ v
    def abc(xd, xq):
        return [xd * np.cos(th - k * 2 * np.pi / 3) - xq * np.sin(th - k * 2 * np.pi / 3) for k in range(3)]
    vabc = abc(vd0, vq0)
    iabc = abc(i[:, 0], i[:, 1])
    fig, axs = plt.subplots(2, 2, figsize=(16, 8), sharex=True)
    axs[0, 0].plot(t, np.full(n, vd0), color=COR_A, lw=3, label="$v_d$")
    axs[0, 0].plot(t, np.full(n, vq0), color=COR_B, lw=3, label="$v_q$")
    axs[0, 0].set_ylabel("tensão dq [V]")
    for k, (c, nm) in enumerate(zip(ABC, ("$v_A$", "$v_B$", "$v_C$"))):
        axs[1, 0].plot(t, vabc[k], color=c, lw=2.5, label=nm)
    axs[1, 0].set_ylabel("tensão de fase [V]")
    axs[0, 1].plot(t, i[:, 0] * 1e3, color=COR_A, lw=3, label="$i_d$")
    axs[0, 1].plot(t, i[:, 1] * 1e3, color=COR_B, lw=3, label="$i_q$")
    axs[0, 1].set_ylabel("corrente dq [mA]")
    for k, (c, nm) in enumerate(zip(ABC, ("$i_A$", "$i_B$", "$i_C$"))):
        axs[1, 1].plot(t, iabc[k] * 1e3, color=c, lw=2.5, label=nm)
    axs[1, 1].set_ylabel("corrente de fase [mA]")
    for ax, nc in zip(axs.flat, (2, 2, 3, 3)):
        ax.margins(x=0, y=0.25)
        ax.legend(frameon=False, loc="upper right", ncol=nc, fontsize=19)
        ax.grid(alpha=0.3)
        ax.tick_params(labelsize=17)
        ax.yaxis.label.set_size(20)
    for ax in axs[1]:
        ax.set_xlabel("tempo [ms]", fontsize=20)
    fig.tight_layout(w_pad=4)
    fig.savefig(IMGS / "dq_constante.png", dpi=110)
    plt.close(fig)
    print(f"regime: id {i[-1, 0] * 1e3:.0f} mA, iq {i[-1, 1] * 1e3:.0f} mA, pico de fase {np.hypot(*i[-1]) * 1e3:.0f} mA")


def atraso_pwm():
    """Diagrama de tempo: por que a razao calculada em k so aparece na corrente lida em k+2."""
    fig, axs = plt.subplots(3, 1, figsize=(16, 8.2), sharex=True, gridspec_kw={"height_ratios": [1, 0.9, 1.1]})
    t = np.linspace(-0.25, 3.25, 1400)
    tri = np.abs(((t + 1) % 1) - 0.5) * 2          # portadora up-down: zero (vale) em t inteiro
    for ax in axs:
        for kk in range(4):
            ax.axvline(kk, color=COR_CINZA, lw=1, ls=":")
    # 1. portadora e comparacao
    ax = axs[0]
    ax.plot(t, 1 - tri, color="k", lw=2)
    dcmp = np.where(t < 1, 0.35, np.where(t < 2, 0.35, 0.7))
    ax.plot(t, dcmp, color=COR_B, lw=2.5, label="razão")
    ax.set_ylim(-0.75, 1.35); ax.set_yticks([])
    ax.set_ylabel("contador\ndo PWM", fontsize=18)
    for kk, nm in zip(range(4), ("k−1", "k", "k+1", "k+2")):
        ax.plot(kk, 0, "o", color=COR_A, ms=12)
        ax.text(kk, 1.15, nm, ha="center", fontsize=20, fontweight="bold")
    ax.text(1.0, -0.12, "lê i(k) e calcula d(k)", fontsize=16, color=COR_A, va="top", ha="center")
    ax.annotate("a nova razão só vale no próximo período", xy=(2, 0.68), xytext=(2.05, -0.55), fontsize=16, color=COR_B,
                arrowprops=dict(arrowstyle="-|>", color=COR_B, lw=2))
    # 2. tensao media aplicada
    ax = axs[1]
    ax.step([0, 1, 2, 3], [0.35, 0.35, 0.7, 0.7], where="post", color="k", lw=2.5)
    ax.fill_between([2, 3], 0, 0.7, color=COR_B, alpha=0.2)
    ax.text(2.5, 0.35, "d(k) aplicada", ha="center", va="center", fontsize=18, color=COR_B)
    ax.text(1.5, 0.15, "ainda d(k−1)", ha="center", va="center", fontsize=16, color=COR_CINZA)
    ax.set_ylim(0, 0.9); ax.set_yticks([])
    ax.set_ylabel("tensão\nmédia", fontsize=18)
    # 3. corrente
    ax = axs[2]
    tt = np.linspace(0, 3, 300)
    i = np.where(tt < 2, 0.45, 0.45 + 0.45 * (1 - np.exp(-(tt - 2) / 0.6)))
    ax.plot(tt, i, color=COR_A, lw=2.5)
    for kk in range(4):
        ax.plot(kk, np.interp(kk, tt, i), "o", color=COR_A, ms=12)
    ax.annotate("1ª leitura que vê d(k)", xy=(3, np.interp(3, tt, i)), xytext=(1.6, 1.0), fontsize=17,
                color=COR_A, arrowprops=dict(arrowstyle="-|>", color=COR_A, lw=2))
    ax.set_ylim(-0.05, 1.15); ax.set_yticks([])
    ax.set_ylabel("corrente", fontsize=18)
    # chaves dos dois atrasos
    for x0, x1, txt, cor in ((1, 2, "1º atraso: PWM\n(atualiza no início do período)", COR_B), (2, 3, "2º atraso: a tensão age no\nperíodo; lida só no fim", COR_C)):
        ax.annotate("", xy=(x1, 0.02), xytext=(x0, 0.02), arrowprops=dict(arrowstyle="<->", color=cor, lw=2.5))
        ax.text((x0 + x1) / 2, 0.06, txt, ha="center", va="bottom", fontsize=15, color=cor)
    ax.set_xticks([0, 1, 2, 3]); ax.set_xticklabels(["k−1", "k", "k+1", "k+2"], fontsize=18)
    ax.set_xlim(-0.25, 3.25)
    for a_ in axs:
        for sp in ("left", "top", "right"):
            a_.spines[sp].set_visible(False)
    fig.tight_layout(h_pad=0.5)
    fig.savefig(IMGS / "atraso_pwm.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    animacao()
    firmware()
    firmware_diagrama()
    dq_constante()
    atraso_pwm()
