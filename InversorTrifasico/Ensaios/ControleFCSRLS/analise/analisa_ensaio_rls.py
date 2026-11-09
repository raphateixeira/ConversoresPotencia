"""Ensaio do VSI05MPCAdaptativoRLS: os quatro cenarios, comparados a simulacao e ao FCS fixo.

Dados (Dados3FRL): DadosRLS01 (modelo errado fixo, media 16), DadosRLS02 (convergencia, cru),
DadosRLS03 (adaptativo, media 16), DadosRLS04 (variavel instrumental), Tempos02 (tempos);
ControleFCS02 (FCS do VSI04 com o modelo certo, media 16) como referencia.
Gera em ../imgs: rls_ens_convergencia.png, rls_ens_correntes.png (e rls_tempos_ensaio.png
via analisa_rls); imprime os numeros.
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "ControlePIDados" / "analise"))
import simula_pi as SP                                    # noqa: E402
import analisa_rls as A                                   # noqa: E402
import simula_rls as SR                                   # noqa: E402

D = AQUI.parents[2] / "Dados3FRL"
IMGS = AQUI.parent / "imgs"
N, TS, VDC = SP.N, SP.TS, 19.85
AZUL, VERM, CINZA = "#1F5FBF", "#D62828", "#6C757D"
plt.rcParams.update({"font.size": 20, "axes.labelsize": 21, "axes.titlesize": 21,
                     "xtick.labelsize": 18, "ytick.labelsize": 18, "legend.fontsize": 16})
t = np.arange(N) * TS * 1e3
REG = np.r_[300:690, 900:1190, 1300:1690, 1800:2040]
rd, rq = SP.referencias()


def RL(d):
    th1, th3 = d[0], d[1]
    R = VDC * (1 - np.sqrt(th1)) / th3
    return R, -R * TS / np.log(th1)


def main():
    c = {k: A.le(D / f"DadosRLS0{k}.csv", 8) for k in (1, 2, 3, 4)}
    ref = SP.le_dados_pi(D / "ControleFCS02.csv")
    print("cenário | erro médio d / q [mA] | rms [mA] | R, L (últimos 20 ms)")
    for k, d in c.items():
        R, L = RL(d)
        print(f"  {k}: {(rd - d[2])[REG].mean() * 1e3:+6.1f} / {(rq - d[3])[REG].mean() * 1e3:+5.1f} | "
              f"{np.sqrt(np.mean((rd - d[2])[REG] ** 2 + (rq - d[3])[REG] ** 2)) * 1e3:6.1f} | {R[-400:].mean():5.1f} Ω, {L[-400:].mean() * 1e3:5.2f} mH")
    print(f"  FCS fixo certo (VSI04): {(rd - ref['id'])[REG].mean() * 1e3:+6.1f} / {(rq - ref['iq'])[REG].mean() * 1e3:+5.1f}")

    # convergencia: ensaio (cenario 2) x simulacao (RLS a partir de 35 Ohm; 14 mH)
    R2, L2 = RL(c[2])
    sim = SR.simula(35.0, 14e-3, True, metodo="RLS", periodos=1)
    fig, axs = plt.subplots(1, 2, figsize=(17, 6.8))
    for ax, med, simv, real, nome, lim in ((axs[0], R2, sim["R"], 25.3, "R [Ω]", (18, 40)),
                                           (axs[1], L2 * 1e3, sim["L"] * 1e3, 9.8, "L [mH]", (6, 15))):
        ax.plot(t, simv, color=CINZA, lw=2.2, ls="--", label="simulação")
        ax.plot(t, med, color=AZUL, lw=2.6, label="ensaio")
        ax.axhline(real, color="k", ls=":", lw=2, label="referência")
        ax.set_ylabel(nome + " estimado"); ax.set_ylim(*lim); ax.set_xlim(0, 60)
        ax.set_xlabel("tempo desde o recomeço do RLS [ms]"); ax.grid(alpha=0.3)
    axs[0].legend(frameon=False, loc="upper right")
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "rls_ens_convergencia.png", dpi=110); plt.close(fig)

    # correntes medias: modelo errado (1) x adaptativo (3) x modelo certo (VSI04)
    fig, axs = plt.subplots(2, 1, figsize=(17, 8.6), sharex=True)
    for ax, e, r, cor in ((axs[0], 2, rd, AZUL), (axs[1], 3, rq, VERM)):
        nome = "d" if e == 2 else "q"
        ax.step(t, r * 1e3, where="post", color="#C8A400", lw=2, label="referência")
        ax.plot(t, c[1][e] * 1e3, color="k", lw=1.6, ls="--", label="modelo errado fixo (cenário 1)")
        ax.plot(t, c[3][e] * 1e3, color=cor, lw=1.8, label="adaptativo RLS (cenário 3)")
        ax.plot(t, ref["i" + nome] * 1e3, color=CINZA, lw=1.4, ls=":", label="modelo certo fixo (VSI04)")
        ax.set_ylabel(f"$i_{nome}$ [mA]"); ax.grid(alpha=0.3); ax.margins(x=0)
    axs[0].legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 1), ncol=4, borderaxespad=0, fontsize=15)
    axs[1].set_xlabel("tempo [ms]")
    fig.tight_layout(h_pad=1.2); fig.savefig(IMGS / "rls_ens_correntes.png", dpi=110); plt.close(fig)

    A.tempos(D / "Tempos02.csv")


if __name__ == "__main__":
    main()
