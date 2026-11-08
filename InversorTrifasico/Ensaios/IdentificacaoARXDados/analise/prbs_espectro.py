"""Figuras sobre a PRBS como aproximacao do ruido branco.

1. ../imgs/prbs_branco.png: ruido branco x PRBS (1 amostra por bit) x PRBS (4 amostras por bit):
   sinal, autocorrelacao e espectro estimado (Welch), mesma amplitude (desvio de 3 V).
2. ../imgs/prbs_bits.png: por que 4 amostras por bit: espectro para 1, 2, 4, 8 amostras/bit com o
   polo da carga, e a variacao de corrente que um bit produz na carga.
3. ../imgs/prbs_corr.png: resposta ao impulso pela correlacao (supoe entrada branca) x minimos quadrados.
Uso: python3 prbs_espectro.py
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch
import identifica as I
from identifica import IMGS, TS, COR_A, COR_B, COR_C, COR_CINZA, COR_AMARELO

plt.rcParams.update({"font.size": 18, "axes.labelsize": 19, "axes.titlesize": 20,
                     "xtick.labelsize": 16, "ytick.labelsize": 16, "legend.fontsize": 17})
N, DV = 2044, 3.0
FS = 1 / TS


def xcorr(a, b):
    """Correlacao circular (registro = periodo), normalizada por N."""
    return np.real(np.fft.ifft(np.conj(np.fft.fft(a)) * np.fft.fft(b))) / len(a)


def sinais():
    rng = np.random.default_rng(3)
    p = I.prbs(4)
    return {"ruído branco": DV * rng.standard_normal(N),
            "PRBS, 1 amostra/bit": DV * np.tile(p, 4)[:N],
            "PRBS, 4 amostras/bit": DV * np.repeat(p, 4)}


def fig_branco():
    s = sinais()
    cores = (COR_CINZA, COR_C, COR_A)
    fig, axs = plt.subplots(3, 3, figsize=(17, 8.6))
    k = np.arange(60)
    lag = np.arange(-10, 11)
    for c, (nome, x), cor in zip(range(3), s.items(), cores):
        ax = axs[0, c]
        ax.step(k * TS * 1e3, x[k], where="post", color=cor, lw=2)
        ax.set_title(nome, color=cor, fontweight="bold")
        ax.set_ylim(-9, 9)
        ax = axs[1, c]
        r = xcorr(x, x)
        ml, sl, bl = ax.stem(lag, r[lag] / r[0], linefmt=cor, markerfmt="o", basefmt=" ")
        plt.setp(ml, color=cor, markersize=7); plt.setp(sl, linewidth=2.5)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_ylim(-0.3, 1.1)
        ax = axs[2, c]
        f, P = welch(x, fs=FS, nperseg=256)
        ax.plot(f / 1e3, 10 * np.log10(P), color=cor, lw=2.5)
        ax.set_ylim(-60, -20)
        ax.set_xlim(0, 10)
    axs[0, 0].set_ylabel("sinal [V]")
    axs[1, 0].set_ylabel("autocorrelação")
    axs[2, 0].set_ylabel("espectro [dB/Hz]")
    for ax in axs[0]:
        ax.set_xlabel("tempo [ms]")
    for ax in axs[1]:
        ax.set_xlabel("deslocamento τ [amostras]")
    for ax in axs[2]:
        ax.set_xlabel("frequência [kHz]")
    for ax in axs.flat:
        ax.grid(alpha=0.3)
    fig.tight_layout(h_pad=1.2, w_pad=2)
    fig.savefig(IMGS / "prbs_branco.png", dpi=110)
    plt.close(fig)


def fig_bits(R=25.0, L=10e-3):
    p = I.prbs(4)
    a = np.exp(-R * TS / L)
    b = (1 - a) / R
    fig, axs = plt.subplots(1, 2, figsize=(16, 6.4), gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axs[0]
    cores = {1: COR_C, 2: COR_AMARELO, 4: COR_A, 8: COR_B}
    f = np.logspace(np.log10(40), 4, 600)
    for nb, cor in cores.items():
        # envoltoria do espectro da PRBS: sigma^2 Nb Ts sinc^2(f Nb Ts)  (mesma potencia total)
        P = DV**2 * nb * TS * np.sinc(f * nb * TS) ** 2
        ax.semilogx(f, 10 * np.log10(P + 1e-12), color=cor, lw=3.5 if nb == 4 else 2.2,
                    label=f"{nb} amostra{'s' if nb > 1 else ''}/bit")
    fc = R / (2 * np.pi * L)
    ax.axvline(fc, color="k", ls="--", lw=1.8)
    ax.text(fc * 1.08, -52, f"polo da carga\n{fc:.0f} Hz", fontsize=16, va="bottom")
    ax.set_xlim(40, 1e4); ax.set_ylim(-55, -18)
    ax.set_xlabel("frequência [Hz]"); ax.set_ylabel("espectro da tensão [dB/Hz]")
    ax.legend(frameon=False, loc="lower left")
    ax.grid(alpha=0.3, which="both")
    ax.set_title("espectro (envoltória sinc²)")
    ax = axs[1]
    nbs = np.array([1, 2, 4, 8])
    di = b * DV * (1 - a ** nbs) / (1 - a) * 1e3
    ax.bar(np.arange(4), di, color=[cores[n] for n in nbs], width=0.6)
    for xx, v, n in zip(np.arange(4), di, nbs):
        ax.text(xx, v + 2, f"{v:.0f} mA\n{511 * n * TS * 1e3:.0f} ms", ha="center", va="bottom", fontsize=15)
    ax.axhline(9, color=COR_CINZA, ls=":", lw=2)
    ax.text(-0.4, 106, "····  ruído medido (1 período) ≈ 9 mA", ha="left", va="center", fontsize=15, color=COR_CINZA)
    ax.set_xticks(np.arange(4)); ax.set_xticklabels([str(n) for n in nbs])
    ax.set_xlabel("amostras por bit"); ax.set_ylabel("Δi num bit de 3 V [mA]")
    ax.set_ylim(0, 115)
    ax.set_title("resposta da corrente e período")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout(w_pad=3)
    fig.savefig(IMGS / "prbs_bits.png", dpi=110)
    plt.close(fig)


def fig_corr(n=16, R=25.0, L=10e-3):
    """Esquerda: entrada branca (PRBS 1 amostra/bit, simulacao RL): R_vi/sigma^2 = h.
    Direita: dados reais (4 amostras/bit): R_vi/sigma^2 = h * triangulo (borrado); h por minimos quadrados."""
    k = np.arange(n)
    a = np.exp(-R * TS / L)
    h_nom = np.where(k >= 2, (1 - a) / R * a ** np.clip(k - 2, 0, None), 0.0)
    rng = np.random.default_rng(1)
    v = DV * np.tile(I.prbs(4), 4)[:N]
    hl = np.where(np.arange(60) >= 2, (1 - a) / R * a ** np.clip(np.arange(60) - 2, 0, None), 0.0)
    i_sim = np.real(np.fft.ifft(np.fft.fft(v) * np.fft.fft(hl, N))) + 0.002 * rng.standard_normal(N)
    r1 = xcorr(v, i_sim) / xcorr(v, v)[0]
    s = I.carrega()
    y, u = I.desvios(s)
    h = I.fir(y, u)["d"][0]
    ruu = xcorr(u["d"], u["d"])
    ryu = xcorr(u["d"], y["d"]) / ruu[0]
    tri = ruu / ruu[0]
    borr = np.array([sum(h[j] * tri[(t - j) % N] for j in range(len(h))) for t in k])
    fig = plt.figure(figsize=(18, 6.6))
    g = fig.add_gridspec(1, 3, width_ratios=[0.75, 1, 1], wspace=0.25)
    at = fig.add_subplot(g[0])
    axs = [fig.add_subplot(g[1]), None]
    axs[1] = fig.add_subplot(g[2], sharey=axs[0])
    lag = np.arange(-6, 7)
    ml, sl, bl = at.stem(lag, tri[lag], linefmt=COR_A, markerfmt="o", basefmt=" ")
    plt.setp(ml, color=COR_A, markersize=10); plt.setp(sl, linewidth=3)
    for t_, v_ in zip(lag, tri[lag]):
        if v_ > 0.1:
            at.text(t_, v_ + 0.04, f"{v_:.2f}".replace(".", ","), ha="center", va="bottom", fontsize=13)
    at.axhline(0, color="k", lw=0.8)
    at.set_ylim(-0.1, 1.2)
    at.set_xlabel("deslocamento τ [amostras]")
    at.set_ylabel("$R_{vv}(τ)/σ^2$")
    at.set_title("autocorrelação da entrada")
    at.grid(alpha=0.3)
    ax = axs[0]
    ml, sl, bl = ax.stem(k, h_nom * 1e3, linefmt=COR_A, markerfmt="o", basefmt=" ", label="$h$ (modelo RL)")
    plt.setp(ml, color=COR_A, markersize=10); plt.setp(sl, linewidth=3)
    ax.plot(k, r1[:n] * 1e3, "s", color=COR_CINZA, ms=12, mfc="none", mew=2.5, label="$R_{vi}/σ^2$")
    ax.set_title("entrada branca (simulação)")
    ax = axs[1]
    ml, sl, bl = ax.stem(k, h[:n] * 1e3, linefmt=COR_A, markerfmt="o", basefmt=" ", label="$h$ (mínimos quadrados)")
    plt.setp(ml, color=COR_A, markersize=10); plt.setp(sl, linewidth=3)
    ax.plot(k, ryu[:n] * 1e3, "s", color=COR_CINZA, ms=12, mfc="none", mew=2.5, label="$R_{vi}/σ^2$ (dados)")
    ax.plot(k, borr * 1e3, "--", color=COR_B, lw=2.5, label="$h$ ∗ triângulo")
    ax.set_title("nossos dados (4 amostras/bit)")
    for ax in axs:
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xticks(k[::2])
        ax.set_xlabel("atraso τ [amostras]")
        ax.legend(frameon=False, loc="upper right")
        ax.grid(alpha=0.3)
    axs[0].set_ylabel("$v_d \\to i_d$ [mA/V]")
    axs[0].set_ylim(-0.8, 19)
    fig.subplots_adjust(left=0.05, right=0.99, top=0.9, bottom=0.14)
    fig.savefig(IMGS / "prbs_corr.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    fig_branco()
    fig_bits()
    fig_corr()
