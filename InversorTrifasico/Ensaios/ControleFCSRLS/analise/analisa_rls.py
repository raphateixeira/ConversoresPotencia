"""Ensaio do VSI05MPCAdaptativoRLS: parametros estimados e tempo de calculo.

Uso: python3 analisa_rls.py Dados3F.csv [Tempos.csv]
  Dados3F (8 x 2044): th1 th3 id iq vd vq iA iB  -> ../imgs/rls_parametros_ensaio.png
  Tempos  (4 x 2044): medidas RLS FCS total [us] -> ../imgs/rls_tempos_ensaio.png
Imprime R e L estimados (inicio e fim), erro medio de corrente e os tempos (media,
media movel, maximo, folga ate o topo do contador = 25 us).
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "ControlePIDados" / "analise"))
import simula_pi as SP                                    # noqa: E402

IMGS = AQUI.parent / "imgs"
N, TS, VDC = SP.N, SP.TS, 19.85
AZUL, VERM, VERDE, CINZA = "#1F5FBF", "#D62828", "#2A9D3A", "#6C757D"
plt.rcParams.update({"font.size": 20, "axes.labelsize": 21, "axes.titlesize": 21,
                     "xtick.labelsize": 18, "ytick.labelsize": 18, "legend.fontsize": 17})
t = np.arange(N) * TS * 1e3


def le(arquivo, linhas):
    vals = []
    for l in open(arquivo):
        p = l.strip().split(",")
        try:
            vals.append(float(p[-1] if p[-1] else p[0]))
        except ValueError:
            continue
    x = np.array(vals)[:linhas * N]
    return x.reshape(linhas, N)


def media_movel(x, n=200):
    return np.convolve(np.pad(x, (n // 2, n - 1 - n // 2), mode="edge"), np.ones(n) / n, mode="valid")


def parametros(arq):
    th1, th3, id_, iq, vd, vq, ia, ib = le(arq, 8)
    ok = (th1 > 0) & (th1 < 1) & (th3 > 0)
    R = np.full(N, np.nan); Lh = np.full(N, np.nan)
    R[ok] = VDC * (1 - np.sqrt(th1[ok])) / th3[ok]
    Lh[ok] = -R[ok] * TS / np.log(th1[ok])
    rd, rq = SP.referencias()
    reg = np.r_[300:690, 900:1190, 1300:1690, 1800:2040]
    print(f"R estimado: início {np.nanmean(R[:20]):.1f} Ω, fim {np.nanmean(R[-400:]):.1f} Ω; "
          f"L: início {np.nanmean(Lh[:20]) * 1e3:.2f} mH, fim {np.nanmean(Lh[-400:]) * 1e3:.2f} mH")
    print(f"erro médio em regime: d {(rd - id_)[reg].mean() * 1e3:+.1f} mA, q {(rq - iq)[reg].mean() * 1e3:+.1f} mA")
    fig, axs = plt.subplots(2, 2, figsize=(17, 8.6), sharex=True)
    axs[0, 0].plot(t, th1, color=AZUL, lw=2); axs[0, 0].set_ylabel("$θ_1$")
    axs[1, 0].plot(t, th3, color=VERM, lw=2); axs[1, 0].set_ylabel("$θ_3$")
    axs[0, 1].plot(t, R, color=AZUL, lw=2, label="estimado"); axs[0, 1].axhline(25.3, color="k", ls=":", lw=2, label="regime do PI")
    axs[0, 1].set_ylabel("R [Ω]")
    axs[1, 1].plot(t, Lh * 1e3, color=VERM, lw=2, label="estimado"); axs[1, 1].axhline(9.8, color="k", ls=":", lw=2, label="identificado")
    axs[1, 1].set_ylabel("L [mH]")
    for ax in axs.flat:
        ax.grid(alpha=0.3); ax.margins(x=0)
    for ax in axs[:, 1]:
        ax.legend(frameon=False, loc="upper right")
    for ax in axs[1]:
        ax.set_xlabel("tempo [ms]")
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "rls_parametros_ensaio.png", dpi=110); plt.close(fig)


def tempos(arq):
    med, rls, fcs, tot = le(arq, 4)
    print("tempo [µs]: média | máximo | média móvel (10 ms) mín–máx")
    for nome, x in (("medidas", med), ("RLS", rls), ("FCS", fcs), ("interrupção", tot)):
        mm = media_movel(x)
        print(f"  {nome:12s} {x.mean():6.2f} | {x.max():6.2f} | {mm.min():.2f}–{mm.max():.2f}")
    decisao = med + fcs                      # o RLS roda depois da decisao
    print(f"  decisão (medidas + FCS, sem a latência): pior {decisao.max():.2f} µs de 25 µs; "
          f"ocupação média da interrupção {tot.mean() / 50 * 100:.0f} %")
    fig, axs = plt.subplots(1, 2, figsize=(17, 7), gridspec_kw={"width_ratios": [1.6, 1]})
    ax = axs[0]
    for x, cor, nome in ((med, CINZA, "medidas"), (rls, VERM, "RLS"), (fcs, AZUL, "FCS"), (tot, "k", "interrupção")):
        ax.plot(t, x, color=cor, lw=0.6, alpha=0.35)
        ax.plot(t, media_movel(x), color=cor, lw=3, label=nome)
    ax.axhline(25, color=VERDE, ls="--", lw=2.5, label="prazo da decisão (topo)")
    ax.axhline(50, color=VERDE, ls=":", lw=2.5, label="período de amostragem")
    ax.set_xlabel("tempo [ms]"); ax.set_ylabel("tempo de cálculo [µs]\n(média móvel de 10 ms)"); ax.set_ylim(0, 55)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), fontsize=14, ncol=3); ax.grid(alpha=0.3); ax.margins(x=0)
    ax = axs[1]
    ax.barh(["medidas", "RLS", "FCS", "resto"], [med.mean(), rls.mean(), fcs.mean(), tot.mean() - med.mean() - rls.mean() - fcs.mean()],
            color=[CINZA, VERM, AZUL, "#BBBBBB"])
    ax.set_xlabel("tempo médio [µs]"); ax.grid(alpha=0.3, axis="x"); ax.set_title("onde vai o tempo")
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "rls_tempos_ensaio.png", dpi=110, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
    else:
        parametros(sys.argv[1])
        if len(sys.argv) > 2:
            tempos(sys.argv[2])
