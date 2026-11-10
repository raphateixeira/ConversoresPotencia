"""Figuras e numeros da apresentacao "Bancada e modelo do inversor".

Carga RL em estrela (25 Ohm, 10 mH), 60 Hz, barramento de 20 V, PWM de 20 kHz.
Gera em ../imgs: fonte_trifasica.png, fasores_carga.png, estados_inversor.png,
limites_carga.png, discreto_dq.png; imprime os numeros dos slides.
Uso: python3 figuras.py
"""
from pathlib import Path
import numpy as np
import scipy.linalg as la
import matplotlib.pyplot as plt

IMGS = Path(__file__).resolve().parent.parent / "imgs"
R, L, F, VDC, FSW = 25.0, 10e-3, 60.0, 20.0, 20e3
TS = 1 / FSW
W = 2 * np.pi * F
AZUL, VERM, VERDE, CINZA, AMAR = "#1F5FBF", "#D62828", "#2A9D3A", "#6C757D", "#C8A400"
ABC = (AZUL, VERM, VERDE)
plt.rcParams.update({"font.size": 20, "axes.labelsize": 21, "axes.titlesize": 21,
                     "xtick.labelsize": 18, "ytick.labelsize": 18, "legend.fontsize": 18})


def numeros():
    XL = W * L; Z = np.hypot(R, XL); phi = np.degrees(np.arctan2(XL, R))
    tau = L / R; fp = R / Z
    vmax = 0.45 * VDC                     # pico de fase (razao 5-95 %)
    ipico = vmax / Z
    P = 1.5 * ipico ** 2 * R; Q = 1.5 * ipico ** 2 * XL
    rip = VDC / (4 * L * FSW)             # ondulacao pico a pico maxima do PWM (razao 50 %)
    A = np.array([[-R / L, W], [-W, -R / L]])
    Phi = la.expm(A * TS); Gam = np.linalg.solve(A, (Phi - np.eye(2)) / L)
    print(f"XL = {XL:.2f} Ω, |Z| = {Z:.2f} Ω, φ = {phi:.1f}°, FP = {fp:.3f}, τ = {tau * 1e3:.2f} ms "
          f"({tau / TS:.1f} amostras), polo = {1 / (2 * np.pi * tau):.0f} Hz")
    print(f"Vdc {VDC:.0f} V: |v| máx {vmax:.1f} V, I pico {ipico * 1e3:.0f} mA, P {P:.2f} W, Q {Q:.2f} var; "
          f"ondulação PWM ≤ {rip * 1e3:.0f} mA p-p; resolução ADC 7,32 mA → {ipico / 7.32e-3:.0f} contagens no pico")
    print("Φ =", np.round(Phi, 4).tolist(), " Γ =", np.round(Gam, 5).tolist())
    print(f"ωL = {XL:.2f} Ω; acoplamento c = {Phi[0, 1]:.4f}")
    old = dict(R=4.7, L=6.8e-3)
    Zo = np.hypot(old["R"], W * old["L"])
    print(f"carga antiga 4,7 Ω/6,8 mH: |Z| {Zo:.2f} Ω, a 20 V I pico {vmax / Zo:.2f} A, τ {old['L'] / old['R'] * 1e3:.2f} ms")


def fig_fonte():
    t = np.linspace(0, 1 / F * 1.25, 600)
    fig = plt.figure(figsize=(17, 6.6))
    g = fig.add_gridspec(1, 2, width_ratios=[1.8, 1])
    ax = fig.add_subplot(g[0])
    for k, (c, n) in enumerate(zip(ABC, "ABC")):
        ax.plot(t * 1e3, 9 * np.cos(W * t - k * 2 * np.pi / 3), color=c, lw=3, label=f"$v_{n}$")
    ax.plot(t * 1e3, sum(9 * np.cos(W * t - k * 2 * np.pi / 3) for k in range(3)), color="k", lw=2, ls="--",
            label="$v_A+v_B+v_C$")
    ax.set_xlabel("tempo [ms]"); ax.set_ylabel("tensão de fase [V]"); ax.grid(alpha=0.3); ax.margins(x=0)
    ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 1), ncol=4, borderaxespad=0)
    ax = fig.add_subplot(g[1])
    for k, (c, n) in enumerate(zip(ABC, "ABC")):
        a = -k * 2 * np.pi / 3
        ax.annotate("", xy=(np.cos(a), np.sin(a)), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", lw=3.5, color=c, mutation_scale=26))
        ax.text(1.18 * np.cos(a), 1.18 * np.sin(a), f"$\\dot V_{n}$", color=c, fontsize=24, ha="center", va="center")
    ax.annotate("", xy=(0.45 * np.cos(-2.1), 0.45 * np.sin(-2.1)), xytext=(0.45, 0),
                arrowprops=dict(arrowstyle="-|>", lw=1.5, color=CINZA, connectionstyle="arc3,rad=-0.35"))
    ax.text(0.33, -0.42, "120°", fontsize=18, color=CINZA)
    ax.set_aspect("equal"); ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.4, 1.4); ax.axis("off")
    ax.set_title("fasores (giram a ω)")
    fig.tight_layout(w_pad=2); fig.savefig(IMGS / "fonte_trifasica.png", dpi=110); plt.close(fig)


def fig_fasores():
    XL = W * L; Z = R + 1j * XL; V = 7.07
    I = V / Z
    fig, ax = plt.subplots(figsize=(10, 7))
    esc = 25
    for z, cor, nome, xy in ((V, "k", "$\\dot V$", (0, 0)), (I * R, AZUL, "$R\\,\\dot I$", (0, 0)),
                             (I * 1j * XL, VERM, "$j\\omega L\\,\\dot I$", (np.real(I * R), np.imag(I * R)))):
        ax.annotate("", xy=(xy[0] + z.real, xy[1] + z.imag), xytext=xy, arrowprops=dict(arrowstyle="-|>", lw=3.2, color=cor, mutation_scale=24))
        off = (2.6, 0.12) if cor == "k" else ((0, -0.45) if cor == AZUL else (0.15, -0.1))
        ax.text(xy[0] + z.real * 0.55 + off[0], xy[1] + z.imag * 0.55 + off[1], nome, color=cor, fontsize=22)
    ax.text(0.3, 0.7, f"$\\dot V$ adiantada de φ = {np.degrees(np.angle(Z)):.1f}° sobre $\\dot I$", fontsize=20)
    ax.text(0.6, -1.5, f"$\\dot I$ está na direção de $R\\,\\dot I$ ($|\\dot I|$ = {abs(I) * 1e3:.0f} mA rms para 7,07 V rms)", fontsize=17, color=AZUL)
    ax.set_aspect("equal"); ax.set_xlim(-0.5, 8.6); ax.set_ylim(-1.75, 1.2); ax.grid(alpha=0.3)
    ax.set_xlabel("real [V]"); ax.set_ylabel("imaginário [V]")
    fig.tight_layout(); fig.savefig(IMGS / "fasores_carga.png", dpi=110, bbox_inches="tight"); plt.close(fig)


def fig_estados():
    """Os 8 estados: tensoes de polo e de fase (neutro isolado), em unidades de Vdc."""
    fig, ax = plt.subplots(figsize=(17, 5.6))
    est = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1), (1, 0, 1), (1, 1, 1)]
    for k, s in enumerate(est):
        s = np.array(s, float); vf = s - s.mean()
        for f, c in enumerate(ABC):
            ax.bar(k + (f - 1) * 0.25, vf[f], width=0.24, color=c, label="ABC"[f] if k == 0 else None)
        ax.text(k, 0.78, "".join(str(int(x)) for x in s), ha="center", fontsize=20, fontweight="bold")
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(range(8)); ax.set_xticklabels([f"estado {k}" for k in range(8)], fontsize=15)
    ax.set_ylabel("tensão de fase / $V_{dc}$"); ax.set_ylim(-0.8, 0.95); ax.set_yticks([-2 / 3, -1 / 3, 0, 1 / 3, 2 / 3])
    ax.set_yticklabels(["−2/3", "−1/3", "0", "1/3", "2/3"]); ax.grid(alpha=0.3, axis="y")
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, ["fase A", "fase B", "fase C"], frameon=False, loc="lower center", ncol=3)
    fig.tight_layout(rect=(0, 0.1, 1, 1)); fig.savefig(IMGS / "estados_inversor.png", dpi=110); plt.close(fig)


def fig_limites():
    vdc = np.linspace(5, 60, 200)
    fig, axs = plt.subplots(1, 2, figsize=(17, 6.6))
    for (Rc, Lc), cor, nome in (((25.0, 10e-3), AZUL, "25 Ω; 10 mH (atual)"), ((4.7, 6.8e-3), CINZA, "4,7 Ω; 6,8 mH (projeto antigo)")):
        Z = np.hypot(Rc, W * Lc)
        axs[0].plot(vdc, 0.45 * vdc / Z, color=cor, lw=3, label=nome)
        axs[1].plot(vdc, vdc / (4 * Lc * FSW) * 1e3, color=cor, lw=3, label=nome)
    axs[0].axhline(0.5, color=VERM, ls="--", lw=2, label="limite da fonte (0,5 A)")
    axs[0].axhline(9.9, color="k", ls=":", lw=2, label="limite do inversor (7 A rms)")
    axs[0].axvline(20, color=AMAR, lw=2.5, label="ensaios (20 V)")
    axs[0].set_yscale("log"); axs[0].set_ylabel("corrente de pico máxima [A]"); axs[0].set_ylim(0.05, 40)
    axs[1].axvline(20, color=AMAR, lw=2.5); axs[1].set_ylabel("ondulação do PWM, pico a pico [mA]")
    axs[1].axhline(7.32, color=VERDE, ls="--", lw=2, label="1 contagem do ADC")
    for ax in axs:
        ax.set_xlabel("$V_{dc}$ [V]"); ax.grid(alpha=0.3, which="both"); ax.legend(frameon=False, fontsize=14, loc="upper left", ncol=2)
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "limites_carga.png", dpi=110); plt.close(fig)


def fig_discreto():
    """Degrau de vd = 3 V: modelo continuo x discreto (ZOH) x discreto com atraso de 2 amostras."""
    A = np.array([[-R / L, W], [-W, -R / L]]); B = np.eye(2) / L
    Phi = la.expm(A * TS); Gam = np.linalg.solve(A, (Phi - np.eye(2)) @ B)
    n = 60; v = np.array([3.0, 0.0])
    tc = np.linspace(0, n * TS, 1200)
    ic = np.array([np.linalg.solve(A, (la.expm(A * t) - np.eye(2)) @ B @ v) for t in tc])
    i = np.zeros((n, 2)); ia = np.zeros((n, 2))
    for k in range(1, n):
        i[k] = Phi @ i[k - 1] + Gam @ v
        ia[k] = Phi @ ia[k - 1] + (Gam @ v if k >= 2 else 0)
    k = np.arange(n) * TS * 1e3
    fig, axs = plt.subplots(1, 2, figsize=(17, 6.4), sharex=True)
    for ax, j, nome in ((axs[0], 0, "$i_d$"), (axs[1], 1, "$i_q$")):
        ax.plot(tc * 1e3, ic[:, j] * 1e3, color="k", lw=2, label="contínuo")
        ax.plot(k, i[:, j] * 1e3, "o", color=AZUL, ms=7, label="discreto (ZOH): 1 amostra")
        ax.plot(k, ia[:, j] * 1e3, "s", color=VERM, ms=6, mfc="none", mew=2, label="+ atraso do PWM: 2 amostras")
        ax.set_ylabel(nome + " [mA]"); ax.set_xlabel("tempo [ms]"); ax.grid(alpha=0.3)
    axs[0].legend(frameon=False, loc="lower right", fontsize=16)
    axs[0].set_title("degrau de 3 V em $v_d$"); axs[1].set_title("o acoplamento ωL aparece em $i_q$")
    for ax in axs:
        ax.set_xlim(-0.02, 0.6)
    axs[0].set_ylim(-5, 95); axs[1].set_ylim(-8.5, 0.5)
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "discreto_dq.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    numeros(); fig_fonte(); fig_fasores(); fig_estados(); fig_limites(); fig_discreto()
