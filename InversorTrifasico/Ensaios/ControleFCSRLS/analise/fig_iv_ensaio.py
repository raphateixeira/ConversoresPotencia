"""Cenario 2 (RLS) x cenario 4 (variavel instrumental por predicao): ensaio e simulacao.
Gera ../imgs/rls_ens_iv.png e, com Tempos04, ../imgs/rls_tempos_ensaio.png."""
import numpy as np, matplotlib.pyplot as plt
import analisa_rls as A, simula_rls as S
from analisa_rls import t, IMGS, AZUL, VERM

def RL(d):
    R = 19.85 * (1 - np.sqrt(d[0])) / d[1]
    return R, -R * 50e-6 / np.log(d[0])

d2 = A.le('../../../Dados3FRL/DadosRLS02.csv', 8); d4 = A.le('../../../Dados3FRL/DadosRLS04.csv', 8)
sr = S.simula(35, 14e-3, True, metodo="RLS", periodos=1); sp = S.simula(35, 14e-3, True, metodo="PIV", periodos=1)
fig, axs = plt.subplots(1, 2, figsize=(17, 7))
for d, s, cor, nome in ((d2, sr, VERM, "RLS"), (d4, sp, AZUL, "var. instrumental por predição")):
    R, L = RL(d)
    axs[0].plot(t, R, color=cor, lw=2.6, label=nome + " (ensaio)"); axs[1].plot(t, L * 1e3, color=cor, lw=2.6, label=nome + " (ensaio)")
    axs[0].plot(t, s['R'], color=cor, lw=1.6, ls="--", alpha=0.8, label=nome + " (simulação)")
    axs[1].plot(t, s['L'] * 1e3, color=cor, lw=1.6, ls="--", alpha=0.8, label=nome + " (simulação)")
axs[0].axhline(25.3, color="k", ls=":", lw=2, label="referência"); axs[1].axhline(9.8, color="k", ls=":", lw=2, label="referência")
axs[0].set_ylabel("R estimado [Ω]"); axs[1].set_ylabel("L estimado [mH]"); axs[0].set_ylim(18, 40); axs[1].set_ylim(6, 15)
for ax in axs:
    ax.set_xlabel("tempo desde o recomeço [ms]"); ax.grid(alpha=0.3); ax.set_xlim(0, 60)
h, l = axs[1].get_legend_handles_labels(); fig.legend(h, l, frameon=False, loc="lower center", ncol=3, fontsize=15)
fig.tight_layout(w_pad=3, rect=(0, 0.12, 1, 1)); fig.savefig(IMGS / "rls_ens_iv.png", dpi=110); plt.close(fig)
A.tempos('../../../Dados3FRL/Tempos04.csv')
