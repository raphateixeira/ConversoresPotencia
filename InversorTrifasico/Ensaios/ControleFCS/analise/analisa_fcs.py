"""Analise do ensaio do FCS-MPC (VSI04ControleFCS) e comparacao com o PI (VSI03).

Dados (Dados3F: idRef iqRef id iq vd vq iA iB):
  ControleFCS01.csv  FCS, periodosMedia = 1  (registro cru: ondulacao e chaveamento)
  ControleFCS02.csv  FCS, periodosMedia = 16 (resposta media)
  DadosControlePI01.csv  PI 300 Hz, periodosMedia = 16
Estados das chaves reconstruidos do registro cru: angulo da Park (correntes ABC x dq) e vetor
aplicado (vd, vq) -> estado; daí as comutacoes e a frequencia media de chaveamento.
Gera em ../imgs: fcs_cru.png, fcs_cru_zoom.png, fcs_media_pi.png, fcs_degraus_pi.png,
fcs_fases_pi.png; imprime os numeros dos slides.
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "ControlePIDados" / "analise"))
import simula_pi as SP                                    # noqa: E402
import simula_fcs as SF                                   # noqa: E402

DADOS = AQUI.parents[2] / "Dados3FRL"
IMGS = AQUI.parent / "imgs"
N, TS, REF = SP.N, SP.TS, SP.REF
W = 2 * np.pi * 60.0
AZUL, VERM, VERDE, CINZA = "#1F5FBF", "#D62828", "#2A9D3A", "#6C757D"
plt.rcParams.update({"font.size": 20, "axes.labelsize": 21, "axes.titlesize": 21,
                     "xtick.labelsize": 18, "ytick.labelsize": 18, "legend.fontsize": 17})
t = np.arange(N) * TS * 1e3
suav = lambda v, n=7: np.convolve(np.pad(v, (n // 2, n - 1 - n // 2), mode="edge"), np.ones(n) / n, mode="valid")
TRANS = np.r_[0:N]
REG = np.r_[300:690, 900:1190, 1300:1690, 1800:2040]       # regime (fora dos degraus)


def estados(x):
    """Angulo da Park e estado das chaves a partir do registro cru."""
    ia, ib = x["iA"], x["iB"]; ic = -ia - ib
    al = (2 * ia - ib - ic) / 3; be = (ib - ic) / np.sqrt(3)
    th = np.angle((al + 1j * be) / (x["id"] + 1j * x["iq"]))        # angulo de cada amostra
    th0 = np.angle(np.mean(np.exp(1j * (th - W * np.arange(N) * TS))))
    thk = th0 + W * np.arange(N) * TS
    v = (x["vd"] + 1j * x["vq"]) * np.exp(1j * (thk + W * TS))      # vetor em alfa-beta
    vet = np.array([complex(*SF.vetor(e, 19.85)) for e in range(8)])
    est = np.argmin(np.abs(v[:, None] - vet[None, :]), axis=1)
    nulo = np.abs(v) < 3
    # estado nulo: 000 ou 111 (o mais perto do anterior, como o firmware)
    for k in np.flatnonzero(nulo):
        ant = est[k - 1] if k else 0
        est[k] = 0 if bin(ant).count("1") <= 1 else 7
    com = np.array([bin(a ^ b).count("1") for a, b in zip(est[:-1], est[1:])])
    return est, com, th0


def degrau(x, eixo, k0, de, para, n=300):
    y = x["i" + eixo][k0 - 3:k0 + n + 3]
    zs = (np.convolve(y, np.ones(7) / 7, mode="valid") - de) / (para - de)
    z = (y[3:-3] - de) / (para - de)
    t10 = np.argmax(suav(z, 3) >= 0.1); t90 = np.argmax(suav(z, 3) >= 0.9)
    fora = np.flatnonzero(np.abs(zs - 1) > 0.05)
    return (t90 - t10) * TS * 1e3, max(0, (zs.max() - 1) * 100), ((fora[-1] + 1) if fora.size else 0) * TS * 1e3


def erro(x, k=REG):
    return np.sqrt(np.mean((x["idref"][k] - x["id"][k]) ** 2 + (x["iqref"][k] - x["iq"][k]) ** 2)) * 1e3


def main():
    cru = SP.le_dados_pi(DADOS / "ControleFCS01.csv")
    med = SP.le_dados_pi(DADOS / "ControleFCS02.csv")
    pi = SP.le_dados_pi(DADOS / "DadosControlePI01.csv")
    sim = SF.simula(0.0, ruido=0.0085)
    simm = SF.simula(0.0, ruido=0.0085, periodos=17, media=16)       # FCS simulado, media de 16
    simpi = SP.simula(300.0, True, ruido=0.0)                          # PI simulado
    est, com, th0 = estados(cru)
    fig_chaveamento(est)
    fsw = com.sum() / 6 / (N * TS)

    print(f"FCS cru: erro rms em regime {erro(cru):.1f} mA (simulado {erro(sim):.1f}); "
          f"fsw {fsw:.0f} Hz (simulado {sim['fsw']:.0f}); estados nulos {np.mean(np.isin(est, (0, 7))) * 100:.0f} %")
    print(f"FCS média 16: erro rms {erro(med):.1f} mA; PI média 16: {erro(pi):.1f} mA")
    for nome, x in (("FCS média", med), ("PI", pi)):
        sd = degrau(x, "d", REF["d_liga"], REF["d0"], REF["d0"] + REF["dd"])
        sq = degrau(x, "q", REF["q_liga"], REF["q0"], REF["q0"] + REF["dq"])
        e_d = (x["idref"][REG] - x["id"][REG]).mean() * 1e3
        e_q = (x["iqref"][REG] - x["iq"][REG]).mean() * 1e3
        itq = np.abs(suav(x["iq"])[REF["d_liga"]:REF["d_liga"] + 200] - REF["q0"]).max() * 1e3
        itd = np.abs(suav(x["id"])[REF["q_liga"]:REF["q_liga"] + 200] - REF["d0"] - REF["dd"]).max() * 1e3
        print(f"  {nome:9s} subida d {sd[0]:.2f} ms, sobre {sd[1]:.0f} %, acomoda {sd[2]:.2f} ms | subida q {sq[0]:.2f} ms | "
              f"erro médio d {e_d:+.1f} q {e_q:+.1f} mA | interf. {itq:.1f} / {itd:.1f} mA | desvio em regime "
              f"{np.std(x['id'][900:1190] - suav(x['id'])[900:1190]) * 1e3:.1f} mA")
    for k0, nome in ((150, "0,15/0"), (1000, "0,25/-0,05")):
        print(f"  tensão média {nome}: FCS vd {med['vd'][k0:k0+40].mean():.2f} vq {med['vq'][k0:k0+40].mean():.2f} | "
              f"PI vd {pi['vd'][k0:k0+40].mean():.2f} vq {pi['vq'][k0:k0+40].mean():.2f}")
    def desvio_fase(x):
        """iA, iB menos a senoide de referencia (i* em dq, angulo reconstruido), em regime."""
        _, _, t0 = estados(x)
        th = t0 + W * np.arange(N) * TS
        rA = x["idref"] * np.cos(th) - x["iqref"] * np.sin(th)
        rB = x["idref"] * np.cos(th - 2 * np.pi / 3) - x["iqref"] * np.sin(th - 2 * np.pi / 3)
        return np.sqrt(np.mean(np.r_[(x["iA"] - rA)[REG], (x["iB"] - rB)[REG]] ** 2)) * 1e3
    print(f"  fases: desvio rms em relação à senoide de referência: FCS {desvio_fase(cru):.1f} mA, PI {desvio_fase(pi):.1f} mA")

    # ---- registro cru
    fig, axs = plt.subplots(1, 2, figsize=(17, 7.2))
    for e, cor in (("d", AZUL), ("q", VERM)):
        axs[0].plot(t, cru["v" + e], color=cor, lw=0.5, alpha=0.45)
        axs[0].plot(t, suav(cru["v" + e], 40), color=cor, lw=3, label=f"$v_{e}$ (média 2 ms)")
        axs[1].plot(t, cru["i" + e] * 1e3, color=cor, lw=1.2, label=f"$i_{e}$")
        axs[1].step(t, cru["i" + e + "ref"] * 1e3, where="post", color="k" if e == "d" else CINZA, ls=":", lw=2, label=f"$i_{e}^*$")
    axs[0].set_ylabel("tensão [V]"); axs[1].set_ylabel("corrente [mA]"); axs[0].set_ylim(-15, 19)
    for ax in axs:
        ax.set_xlabel("tempo [ms]"); ax.grid(alpha=0.3); ax.margins(x=0)
        ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 1), ncol=4, borderaxespad=0, columnspacing=0.8)
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "fcs_cru.png", dpi=110); plt.close(fig)

    # ---- zoom cru: estados + correntes medida x simulada
    k = REF["d_liga"]; j = slice(k - 20, k + 80); tt = (np.arange(N)[j] - k) * TS * 1e3
    fig, axs = plt.subplots(1, 2, figsize=(17, 7))
    axs[0].step(tt, est[j], where="post", color=VERM, lw=2.2, label="medido")
    axs[0].step(tt, sim["est"][j], where="post", color=CINZA, lw=1.5, ls="--", label="simulado (outra sequência)")
    axs[0].set_yticks(range(8)); axs[0].set_yticklabels([f"{e >> 2 & 1}{e >> 1 & 1}{e & 1}" for e in range(8)])
    axs[0].set_ylabel("estado $S_aS_bS_c$")
    for e, cor in (("d", AZUL), ("q", VERM)):
        axs[1].plot(tt, cru["i" + e][j] * 1e3, "o-", color=cor, ms=5, lw=1.2, label=f"$i_{e}$ medida")
        axs[1].plot(tt, sim["i" + e][j] * 1e3, "--", color=cor, lw=1.8, alpha=0.8, label=f"$i_{e}$ simulada")
        axs[1].step(tt, cru["i" + e + "ref"][j] * 1e3, where="post", color="k", ls=":", lw=1.6)
    axs[1].set_ylabel("corrente [mA]")
    for ax in axs:
        ax.set_xlabel("tempo desde o degrau em $i_d$ [ms]"); ax.grid(alpha=0.3)
        ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 1), ncol=2, borderaxespad=0, fontsize=15)
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "fcs_cru_zoom.png", dpi=110); plt.close(fig)

    # ---- média: FCS x PI (cada grandeza no seu grafico; verde = FCS, cinza = PI)
    C_PI = "#1A1A1A"                                                       # PI em preto; FCS na cor do eixo
    fig, axs = plt.subplots(2, 2, figsize=(17, 8.6), sharex=True)
    for row, (e, C_FCS) in enumerate((("d", AZUL), ("q", VERM))):
        ax = axs[row, 0]
        ax.plot(t, suav(med["v" + e], 20), color=C_FCS, lw=2.8, label="FCS")
        ax.plot(t, pi["v" + e], color=C_PI, lw=2.2, ls="--", label="PI")
        ax.plot(t, suav(simm["v" + e], 20), color=C_FCS, lw=1.6, ls=":", alpha=0.9, label="FCS sim.")
        ax.plot(t, simpi["v" + e], color="#8A8A8A", lw=1.6, ls=":", label="PI sim.")
        ax.set_ylabel(f"$v_{e}$ [V]")
        ax = axs[row, 1]
        ax.plot(t, med["i" + e] * 1e3, color=C_FCS, lw=1.8, label="FCS")
        ax.plot(t, pi["i" + e] * 1e3, color=C_PI, lw=2.0, ls="--", label="PI")
        ax.plot(t, simm["i" + e] * 1e3, color=C_FCS, lw=1.4, ls=":", alpha=0.9, label="FCS sim.")
        ax.plot(t, simpi["i" + e] * 1e3, color="#8A8A8A", lw=1.6, ls=":", label="PI sim.")
        ax.step(t, med["i" + e + "ref"] * 1e3, where="post", color="#C8A400", ls="-", lw=1.5, label="ref.")
        ax.set_ylabel(f"$i_{e}$ [mA]")
    for ax in axs.flat:
        ax.grid(alpha=0.3); ax.margins(x=0)
    for ax in axs.flat:
        ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 1), ncol=5, borderaxespad=0, fontsize=15, columnspacing=0.7, handlelength=1.6)
    for ax in axs[1]:
        ax.set_xlabel("tempo [ms]")
    fig.tight_layout(w_pad=3, h_pad=1.2); fig.savefig(IMGS / "fcs_media_pi.png", dpi=110); plt.close(fig)

    # ---- degraus (média): FCS x PI, d e q juntos, desvios
    fig, axs = plt.subplots(2, 2, figsize=(17, 8.8), sharex=True)
    for row, (eixo, k) in enumerate((("d", REF["d_liga"]), ("q", REF["q_liga"]))):
        j = slice(k - 20, k + 100); tt = (np.arange(N)[j] - k) * TS * 1e3
        for e, cor in (("d", AZUL), ("q", VERM)):
            for x, ls, lab in ((med, "-", "FCS"), (pi, "--", "PI"), (simm, ":", "FCS sim."), (simpi, ":", "PI sim.")):
                corx = cor if lab.startswith("FCS") else ("#1A1A1A" if e == "d" else "#8A8A8A")
                b_v, b_i = x["v" + e][k - 40:k].mean(), x["i" + e][k - 40:k].mean()   # base: 2 ms antes
                vv = suav(x["v" + e], 5)[j] if lab.startswith("FCS") else x["v" + e][j]
                lw = 1.6 if "sim" in lab else 2.4
                axs[row, 0].plot(tt, vv - b_v, ls, color=corx, lw=lw, label=f"$v_{e}$ {lab}")
                axs[row, 1].plot(tt, (x["i" + e][j] - b_i) * 1e3, ls, color=corx, lw=lw, label=f"$i_{e}$ {lab}")
        r = med["i" + eixo + "ref"]
        axs[row, 1].step(tt, (r[j] - r[k - 5]) * 1e3, where="post", color="k", ls=":", lw=1.6)
        axs[row, 0].set_ylabel(f"Δv [V]\n(degrau em $i_{eixo}$)"); axs[row, 1].set_ylabel(f"Δi [mA]\n(degrau em $i_{eixo}$)")
    for ax in axs.flat:
        ax.grid(alpha=0.3)
    for ax in axs[0]:
        ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 1), ncol=4, borderaxespad=0, columnspacing=0.5, fontsize=13, handlelength=1.5)
    for ax in axs[1]:
        ax.set_xlabel("tempo desde o degrau [ms]")
    fig.tight_layout(w_pad=3, h_pad=1.5); fig.savefig(IMGS / "fcs_degraus_pi.png", dpi=110); plt.close(fig)

    # ---- correntes das fases: FCS cru x PI
    j = slice(0, 400); tt = t[j]
    fig, axs = plt.subplots(1, 2, figsize=(17, 6.6), sharey=True)
    for ax, x, tit in ((axs[0], cru, "FCS-MPC (registro cru)"), (axs[1], pi, "PI (último período)")):
        for c, cor in (("iA", AZUL), ("iB", VERM), ("iC", VERDE)):
            ax.plot(tt, x[c][j] * 1e3, color=cor, lw=1.6, label=f"$i_{c[1]}$")
        ax.set_title(tit); ax.set_xlabel("tempo [ms]"); ax.grid(alpha=0.3); ax.margins(x=0)
    axs[0].set_ylabel("corrente de fase [mA]")
    axs[1].legend(frameon=False, loc="lower right", ncol=3)
    fig.tight_layout(w_pad=2); fig.savefig(IMGS / "fcs_fases_pi.png", dpi=110); plt.close(fig)


def fig_chaveamento(est, k0=400, n=20):
    """Chave de cima da fase A em 1 ms: PWM (razao do PI) x FCS (estados reconstruidos)."""
    C_PI, C_FCS = "#1A1A1A", AZUL                                       # PI em preto, FCS em azul
    fig, axs = plt.subplots(2, 1, figsize=(17, 7.6), sharex=True)
    tf = np.linspace(0, n, n * 400, endpoint=False)
    d = 0.5 + 0.18 * np.sin(2 * np.pi * 60 * (k0 + tf) * TS)            # razao tipica do PI
    port = 1 - np.abs((tf % 1) - 0.5) * 2
    pwm = (port < d).astype(float)
    axs[0].fill_between(tf, 0, pwm, step=None, color=C_PI, alpha=0.25)
    axs[0].plot(tf, pwm, color=C_PI, lw=3)
    mud = np.flatnonzero(np.diff(pwm) != 0)
    axs[0].plot(tf[mud], np.full(mud.size, 0.5), "o", color="k", ms=9, label="comutação")
    sa = ((est[k0:k0 + n + 1] >> 2) & 1).astype(float)
    tt = np.r_[0.0, np.arange(n) + 0.5]                                 # muda no topo
    axs[1].fill_between(tt, 0, sa, step="post", color=C_FCS, alpha=0.35)
    axs[1].step(tt, sa, where="post", color=C_FCS, lw=3.5)
    mf = [tt[q + 1] for q in range(n) if sa[q + 1] != sa[q]]
    axs[1].plot(mf, np.full(len(mf), 0.5), "o", color="k", ms=9)
    for ax in axs:
        ax.plot(np.arange(n + 1), np.full(n + 1, -0.12), "^", color=CINZA, ms=11, clip_on=False,
                label="decisão (a cada 50 µs)" if ax is axs[0] else None)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["0", "1"]); ax.set_ylim(-0.2, 1.25)
        ax.grid(alpha=0.3, axis="x")
        ax.tick_params(labelsize=20)
    axs[0].set_title(f"PWM (PI): {mud.size} comutações em 1 ms → 20 kHz, fixo", loc="left", fontsize=23, color=C_PI)
    axs[1].set_title(f"FCS (medido): {len(mf)} comutações em 1 ms → muda só quando outro estado é melhor",
                     loc="left", fontsize=23, color=C_FCS)
    axs[0].set_ylabel("PI\n$S_a$", fontsize=26, color=C_PI, fontweight="bold")
    axs[1].set_ylabel("FCS\n$S_a$", fontsize=26, color=C_FCS, fontweight="bold")
    axs[1].set_xlabel("tempo [períodos de 50 µs]", fontsize=22)
    axs[1].set_xlim(0, n); axs[1].set_xticks(range(0, n + 1, 2))
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, frameon=False, fontsize=20)
    fig.tight_layout(h_pad=1.5, rect=(0, 0.07, 1, 1)); fig.savefig(IMGS / "fcs_chaveamento.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
