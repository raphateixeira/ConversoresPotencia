"""Modelos SISO por eixo (busca ampla) e projeto inicial de PI, em simulacao.

1. Busca SISO: y(k) = a1 y(k-1) + ... + a_na y(k-na) + b1 u(k-nk) + ... + b_nb u(k-nk-nb+1),
   na, nb, nk = 1 a 3, estimada por minimos quadrados (identifica.METODO); validacao cruzada nas duas metades.
2. PI por eixo sobre o modelo SISO 1,2,2 (LS): R e L equivalentes; zero do PI
   cancela o polo da carga (kp = 2 pi fc L, ki = 2 pi fc R).
3. Malha fechada simulada sobre o modelo MIMO 1,2,2 (LS), que tem o acoplamento:
   PI por eixo sozinho e com desacoplamento (v_d -= (c_d/b_d) i_q, v_q -= (c_q/b_q) i_d).

Usa identifica.py; gera ../imgs/siso_busca.png e ../imgs/pi_*.png; imprime os numeros.
Uso: python3 siso_pi.py
"""

import numpy as np
import matplotlib.pyplot as plt
import identifica as I
from identifica import IMGS, TS, EIXOS, COR_A, COR_B, COR_C, COR_CINZA, COR_AMARELO

plt.rcParams.update({"font.size": 20, "axes.labelsize": 21, "axes.titlesize": 21,
                     "xtick.labelsize": 18, "ytick.labelsize": 18, "legend.fontsize": 19})

FC = (300.0, 500.0, 1000.0)      # bandas testadas [Hz]
DEGRAU = {"d": 0.10, "q": -0.05}  # degraus de referencia diferentes em d e q [A]


def busca_siso(y, u, N):
    meio = N // 2
    res = []
    for na in (1, 2, 3):
        for nb in (1, 2, 3):
            for nk in (1, 2, 3):
                e = dict(na=na, nb=nb, nk=nk, cy=False, cu=False)
                f1 = I.ajuste(I.estima(e, y, u, 0, meio, I.METODO), e, y, u, meio, N)
                f2 = I.ajuste(I.estima(e, y, u, meio, N, I.METODO), e, y, u, 0, meio)
                th = I.estima(e, y, u, 0, N, I.METODO)
                fis = {o: I.fisicos(th[o], e) for o in EIXOS}
                res.append(dict(nome=f"{na},{nb},{nk}", e=e, fit={o: (f1[o] + f2[o]) / 2 for o in EIXOS},
                                fis=fis, n=na + nb))
    return res


def malha_fechada(thp, ganhos, desacopla, n=600, k_d=40, k_q=300):
    """Planta = MIMO 1,2,2 identificado (desvios em torno do ponto de operacao)."""
    a = {o: thp[o][0] for o in EIXOS}
    b = {o: thp[o][1:3] for o in EIXOS}
    e_ = {o: thp[o][3:5] for o in EIXOS}
    c = {o: thp[o][5] for o in EIXOS}
    outro = {"d": "q", "q": "d"}
    i = {o: np.zeros(n) for o in EIXOS}
    v = {o: np.zeros(n) for o in EIXOS}
    r = {"d": np.where(np.arange(n) >= k_d, DEGRAU["d"], 0.0), "q": np.where(np.arange(n) >= k_q, DEGRAU["q"], 0.0)}
    integ = {o: 0.0 for o in EIXOS}
    for k in range(3, n):
        for o in EIXOS:
            p = outro[o]
            i[o][k] = (a[o] * i[o][k - 1] + b[o][0] * v[o][k - 2] + b[o][1] * v[o][k - 3]
                       + e_[o][0] * v[p][k - 2] + e_[o][1] * v[p][k - 3] + c[o] * i[p][k - 1])
        for o in EIXOS:
            kp, ki = ganhos[o]
            err = r[o][k] - i[o][k]
            integ[o] += err
            v[o][k] = kp * err + ki * TS * integ[o]
            if desacopla:
                v[o][k] -= c[o] / b[o].sum() * i[outro[o]][k]
    return r, i, v


def fig_diagrama():
    """Diagrama de blocos da malha de corrente do eixo d (o eixo q e simetrico)."""
    from matplotlib.patches import FancyBboxPatch, Circle
    fig, ax = plt.subplots(figsize=(16, 5.6))
    ax.set_xlim(0, 16); ax.set_ylim(0, 5.6); ax.axis("off")
    W, H, y = 2.6, 1.5, 2.6

    def caixa(x, txt, nome, cor, nome_acima=True):
        ax.add_patch(FancyBboxPatch((x, y - H / 2), W, H, boxstyle="round,pad=0.04", fc="white", ec=cor, lw=3))
        ax.text(x + W / 2, y, txt, ha="center", va="center", fontsize=24)
        yy = y + H / 2 + 0.15 if nome_acima else y - H / 2 - 0.15
        ax.text(x + W / 2, yy, nome, ha="center", va="bottom" if nome_acima else "top", fontsize=21,
                color=cor, fontweight="bold")

    def soma(x):
        ax.add_patch(Circle((x, y), 0.33, fc="white", ec="k", lw=2))

    def seta(x0, y0, x1, y1, txt=None, dy=0.15):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", lw=2.2, color="k", mutation_scale=24))
        if txt:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, txt, ha="center", va="bottom", fontsize=22)

    seta(0.1, y, 1.17, y, "$i_d^*$")
    soma(1.5); ax.text(0.95, y + 0.3, "+", fontsize=22); ax.text(1.62, y - 1.05, "−", fontsize=24)
    seta(1.83, y, 2.6, y, "$e$")
    caixa(2.6, "$K\\,\\dfrac{z - z_0}{z - 1}$", "PI", COR_A)
    seta(5.2, y, 6.07, y)
    soma(6.4); ax.text(6.55, y + 0.38, "−", fontsize=24)
    seta(6.4, y + 2.2, 6.4, y + 0.33)
    ax.text(6.4, y + 2.25, "desacoplamento $(\\hat c/\\hat b)\\,i_q$", ha="center", va="bottom", fontsize=19, color=COR_B)
    seta(6.73, y, 7.6, y, "$v_d$")
    caixa(7.6, "$z^{-2}$", "PWM", COR_CINZA)
    seta(10.2, y, 11.0, y)
    caixa(11.0, "$\\dfrac{b_1 z + b_2}{z - a}$", "carga RL", COR_C, nome_acima=False)
    seta(12.3, y + 2.2, 12.3, y + H / 2 + 0.05)
    ax.text(12.3, y + 2.25, "acoplamento $c\\,i_q$", ha="center", va="bottom", fontsize=19, color=COR_B)
    seta(13.6, y, 15.9, y, "$i_d$")
    ax.plot([14.8, 14.8, 1.5], [y, 0.35, 0.35], color="k", lw=2.2)
    seta(1.5, 0.35, 1.5, y - 0.33)
    ax.text(8.0, 0.45, "corrente medida (ADC + Park)", ha="center", va="bottom", fontsize=18, color=COR_CINZA)
    fig.tight_layout()
    fig.savefig(IMGS / "pi_diagrama.png", dpi=110)
    plt.close(fig)


def fig_planoz(th_d, RL_d):
    """Polos e zeros no plano z: planta SISO 1,2,2 (eixo d), PI e malha fechada para cada banda."""
    a, b1, b2 = th_d
    R, L = RL_d
    fig, axs = plt.subplots(1, 2, figsize=(15, 8.6), gridspec_kw={"width_ratios": [1, 1.25]})
    marcas = {300.0: ("^", COR_C), 500.0: ("D", COR_B), 1000.0: ("s", COR_AMARELO)}
    for ax, lim in zip(axs, (None, (0.55, 1.05, -0.25, 0.25))):
        th = np.linspace(0, 2 * np.pi, 400)
        ax.plot(np.cos(th), np.sin(th), color=COR_CINZA, lw=1.5)
        ax.axhline(0, color=COR_CINZA, lw=0.8); ax.axvline(0, color=COR_CINZA, lw=0.8)
        ax.plot([a], [0], "x", color=COR_A, ms=16, mew=3, label="polo da carga $a$")
        ax.plot([1], [0], "x", color="k", ms=16, mew=3, label="polo do PI ($z = 1$)")
        ax.plot([0], [0], "x", color=COR_CINZA, ms=16, mew=3, label="atraso ($z = 0$, duplo)")
        ax.plot([-b2 / b1], [0], "o", color=COR_A, ms=12, mfc="none", mew=2.5, label="zero da planta")
        for fc, (mk, cor) in marcas.items():
            kp, ki = 2 * np.pi * fc * L, 2 * np.pi * fc * R
            K = kp + ki * TS
            z0 = kp / K
            # 1 + C G = 0:  z^2 (z - 1)(z - a) + K (z - z0)(b1 z + b2) = 0
            den = np.polyadd(np.polymul([1, 0, 0], np.polymul([1, -1], [1, -a])),
                             K * np.polymul([1, -z0], [b1, b2]))
            p = np.roots(den)
            ax.plot(p.real, p.imag, mk, color=cor, ms=11, label=f"malha fechada, {fc:.0f} Hz")
            if fc == 500.0:
                ax.plot([z0], [0], "o", color=COR_B, ms=16, mfc="none", mew=3, label="zero do PI $z_0$")
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)
        ax.set_xlabel("Re z"); 
        if lim:
            ax.set_xlim(lim[0], lim[1]); ax.set_ylim(lim[2], lim[3])
            ax.set_title("zoom perto de z = 1")
        else:
            ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15)
            ax.set_ylabel("Im z")
            ax.set_title("círculo unitário")
    h, l = axs[1].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, loc="lower center", ncol=4, fontsize=17)
    fig.tight_layout(rect=(0, 0.13, 1, 1))
    fig.savefig(IMGS / "pi_planoz.png", dpi=110)
    plt.close(fig)
    print(f"zero do PI z0 = {2 * np.pi * 500 * L / (2 * np.pi * 500 * L + 2 * np.pi * 500 * R * TS):.4f}, polo a = {a:.4f}")


def main():
    s = I.carrega()
    N = s["N"]
    y, u = I.desvios(s)

    # 1. busca SISO
    res = busca_siso(y, u, N)
    res.sort(key=lambda r: -np.mean(list(r["fit"].values())))
    print("SISO na,nb,nk (LS): ajuste d/q | polo d/q | R d/q | L d/q")
    for r in res[:10]:
        f, fi = r["fit"], r["fis"]
        print(f"  {r['nome']}  {f['d']:5.1f}/{f['q']:5.1f} | {fi['d'][0]:.4f}/{fi['q'][0]:.4f} | "
              f"{fi['d'][2]:.1f}/{fi['q'][2]:.1f} | {fi['d'][3] * 1e3:.2f}/{fi['q'][3] * 1e3:.2f}")
    print("  ... pior:", res[-1]["nome"], {o: round(res[-1]["fit"][o], 1) for o in EIXOS})
    fig, ax = plt.subplots(figsize=(14, 5.5))
    nomes = [r["nome"] for r in res]
    x = np.arange(len(res))
    ax.bar(x - 0.2, [r["fit"]["d"] for r in res], width=0.4, color=COR_A, label="eixo d")
    ax.bar(x + 0.2, [r["fit"]["q"] for r in res], width=0.4, color=COR_C, label="eixo q")
    ax.set_xticks(x)
    ax.set_xticklabels(nomes, rotation=60)
    ax.set_xlabel("estrutura SISO na, nb, nk (ordenadas pelo FIT)")
    ax.set_ylabel("FIT na validação [%]")
    ax.set_ylim(40, 100)
    ax.legend(frameon=False, loc="upper right", ncol=2)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(IMGS / "siso_busca.png", dpi=110)
    plt.close(fig)

    # 2. PI por eixo sobre SISO 1,2,2 (LS)
    e = dict(na=1, nb=2, nk=2, cy=False, cu=False)
    th = I.estima(e, y, u, 0, N, I.METODO)
    RL = {o: (I.fisicos(th[o], e)[2], I.fisicos(th[o], e)[3]) for o in EIXOS}
    em = dict(I.ESTRUTURAS)["MIMO 1,2,2"]
    thp = I.estima(em, y, u, 0, N, I.METODO)
    print("R, L por eixo (SISO 1,2,2):", {o: (round(RL[o][0], 2), round(RL[o][1] * 1e3, 2)) for o in EIXOS})
    print("desacoplamento [ohm]:", {o: round(thp[o][5] / thp[o][1:3].sum(), 2) for o in EIXOS},
          " (wL =", round(2 * np.pi * 60 * RL["d"][1], 2), ")")
    fig_diagrama()
    fig_planoz(th["d"], RL["d"])
    td = 2.33 * TS                                   # atraso efetivo (2 amostras + fracao)
    t = np.arange(600) * TS * 1e3
    fig, axs = plt.subplots(1, len(FC), figsize=(16, 6.2), sharey=True)
    for ax, fc in zip(axs, FC):
        g = {o: (2 * np.pi * fc * RL[o][1], 2 * np.pi * fc * RL[o][0]) for o in EIXOS}
        pm = 90 - np.degrees(2 * np.pi * fc * td)
        r, i, v = malha_fechada(thp, g, desacopla=True)
        k = slice(40, 290)
        D = DEGRAU["d"]
        sobre = (i["d"][k].max() - D) / D * 100
        t5 = np.argmax(np.abs(i["d"][40:290] - D) < 0.02 * D) * TS * 1e3
        print(f"fc {fc:.0f} Hz: kp {g['d'][0]:.2f}/{g['q'][0]:.2f}, ki {g['d'][1]:.0f}/{g['q'][1]:.0f}; "
              f"MF ~{pm:.0f} graus; sobressinal {sobre:.0f} %, entra em 2 % em {t5:.2f} ms; "
              f"vd max {np.abs(v['d']).max():.2f} V")
        ax.plot(t, r["d"], color=COR_A, ls="--", lw=1.5)
        ax.plot(t, r["q"], color=COR_C, ls="--", lw=1.5)
        ax.plot(t, i["d"], color=COR_A, lw=2.5, label="$i_d$")
        ax.plot(t, i["q"], color=COR_C, lw=2.5, label="$i_q$")
        ax.set_title(f"$f_c$ = {fc:.0f} Hz (MF ≈ {pm:.0f}°)")
        ax.set_xlabel("tempo [ms]")
        ax.grid(alpha=0.3)
    axs[0].set_ylabel("desvio de corrente [A]")
    axs[0].legend(frameon=False, loc="center right")
    fig.tight_layout()
    fig.savefig(IMGS / "pi_banda.png", dpi=110)
    plt.close(fig)

    # 3. com e sem desacoplamento (fc = 500 Hz)
    g = {o: (2 * np.pi * 500 * RL[o][1], 2 * np.pi * 500 * RL[o][0]) for o in EIXOS}
    fig, axs = plt.subplots(1, 2, figsize=(16, 6.2), sharey=True)
    for ax, des, tit in ((axs[0], False, "PI por eixo, sem desacoplamento"),
                         (axs[1], True, "PI por eixo + desacoplamento")):
        r, i, v = malha_fechada(thp, g, desacopla=des)
        ax.plot(t, r["d"], color=COR_A, ls="--", lw=1.5)
        ax.plot(t, r["q"], color=COR_C, ls="--", lw=1.5)
        ax.plot(t, i["d"], color=COR_A, lw=2.5, label="$i_d$")
        ax.plot(t, i["q"], color=COR_C, lw=2.5, label="$i_q$")
        ax.set_title(tit)
        ax.set_xlabel("tempo [ms]")
        ax.grid(alpha=0.3)
        print(f"{tit}: maior desvio de iq no degrau de id {np.abs(i['q'][40:290]).max() * 1e3:.1f} mA; "
              f"de id no degrau de iq {np.abs(i['d'][300:] - DEGRAU['d']).max() * 1e3:.1f} mA")
    axs[0].set_ylabel("desvio de corrente [A]")
    axs[0].legend(frameon=False, loc="center right")
    fig.tight_layout()
    fig.savefig(IMGS / "pi_desacopla.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    main()
