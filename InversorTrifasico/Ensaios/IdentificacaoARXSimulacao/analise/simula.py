"""Simulacao do ensaio VSI02IdentificacaoARX (PRBS em vd e vq) e identificacao ARX.

Reproduz a logica do firmware: PRBS de 9 bits (x^9+x^5+1 em d, x^9+x^4+1 em q),
amostrasPorBit = 4, vd = 5 +- 3 V, vq = 0 +- 3 V, Park inversa a 60 Hz,
razao = 0,5 + v/Vdc limitada a 5-95 % e arredondada para CMPA, atraso de um
periodo (a razao escrita em k vale entre k+1 e k+2), carga RL em estrela com
neutro isolado (25 Ohm, 10 mH, discretizada exatamente), corrente com ruido
branco e quantizacao do ADC (7,32 mA), Park das correntes com o angulo da amostra.

Modelo identificado (por eixo, com acoplamento):
  id(k) = a id(k-1) + b vd(k-2) + e vq(k-2) + c iq(k-1)
  iq(k) = a iq(k-1) + b vq(k-2) + e vd(k-2) - c id(k-1)
estimado por minimos quadrados (LS) e por variavel instrumental (IV).

Gera em ../imgs/ e imprime os numeros dos slides.
Uso: python3 simula.py
"""

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
IMGS = AQUI.parent / "imgs"
IMGS.mkdir(exist_ok=True)

COR_A, COR_B, COR_C = "#1B365D", "#B23A48", "#2E7D32"
COR_ACENTO, COR_AMARELO, COR_CINZA = "#4A6FA5", "#E8C547", "#6C757D"
plt.rcParams.update({"font.size": 15, "axes.titlesize": 16, "axes.labelsize": 15,
                     "font.family": "sans-serif", "axes.spines.top": False,
                     "axes.spines.right": False})

# Bancada e firmware
R, L = 25.0, 10e-3
TS, F, VDC = 50e-6, 60.0, 19.85
NB, VD0, VQ0, DV = 4, 5.0, 0.0, 3.0
TOPO = 2500
A_ADC = 3.0 / (4096 * 0.1)              # 7,32 mA por contagem
W = 2 * np.pi * F
N = 511 * NB                            # 2044 amostras


def prbs(tap, n=511, semente=0x1FF):
    r, saida = semente, []
    for _ in range(n):
        bit = ((r >> 8) ^ (r >> tap)) & 1
        r = ((r << 1) | bit) & 0x1FF
        saida.append(1.0 if r & 1 else -1.0)
    return np.array(saida)


BIT_D = np.repeat(prbs(4), NB)
BIT_Q = np.repeat(prbs(3), NB)


def ensaio(ruido, semente=0, eixo=0, dv=DV, vd0=VD0):
    """Um registro de N amostras em regime; devolve um dicionario de sinais."""
    vd = vd0 + dv * BIT_D * (eixo != 2)
    vq = VQ0 + dv * BIT_Q * (eixo != 1)
    th = (np.arange(1, N + 1) * W * TS) % (2 * np.pi)
    va = vd * np.cos(th) - vq * np.sin(th)
    vb = vd * np.sin(th) + vq * np.cos(th)
    v = np.vstack([va, -0.5 * va + np.sqrt(3) / 2 * vb, -0.5 * va - np.sqrt(3) / 2 * vb])
    d = np.floor(np.clip(0.5 + v / VDC, 0.05, 0.95) * TOPO) / TOPO
    vn = d * VDC
    vn = vn - vn.mean(axis=0)                        # neutro isolado
    a = np.exp(-R * TS / L)
    i = np.zeros((3, N + 2))
    for _ in range(4):                               # 4 periodos da PRBS: regime
        i0, i1 = i[:, N].copy(), i[:, N + 1].copy()
        i = np.zeros((3, N + 2))
        i[:, 0], i[:, 1] = i0, i1
        for k in range(N):
            i[:, k + 2] = a * i[:, k + 1] + (1 - a) / R * vn[:, k]
    rng = np.random.default_rng(semente)
    im = i[:, :N] + rng.normal(0, ruido, (3, N))
    im = np.round(im / A_ADC) * A_ADC                # quantizacao do ADC
    al = (2 * im[0] - im[1] - im[2]) / 3
    be = (im[1] - im[2]) / np.sqrt(3)
    return dict(vd=vd, vq=vq, th=th, d=d, i=im,
                id=al * np.cos(th) + be * np.sin(th), iq=-al * np.sin(th) + be * np.cos(th))


def ensaio_media(ruido, periodos, semente=0, vdc=VDC, vd0=VD0, dv=DV):
    """Logica do firmware com media sincrona: (periodos + 1) periodos seguidos da
    PRBS, angulo continuo, primeiro periodo descartado, media de id e iq."""
    P = periodos + 1
    vd = np.tile(vd0 + dv * BIT_D, P)
    vq = np.tile(VQ0 + dv * BIT_Q, P)
    M = P * N
    th = (np.arange(1, M + 1) * W * TS) % (2 * np.pi)
    va = vd * np.cos(th) - vq * np.sin(th)
    vb = vd * np.sin(th) + vq * np.cos(th)
    v = np.vstack([va, -0.5 * va + np.sqrt(3) / 2 * vb, -0.5 * va - np.sqrt(3) / 2 * vb])
    d = np.floor(np.clip(0.5 + v / vdc, 0.05, 0.95) * TOPO) / TOPO
    vn = d * vdc
    vn = vn - vn.mean(axis=0)
    a = np.exp(-R * TS / L)
    i = np.zeros((3, M + 2))
    for k in range(M):
        i[:, k + 2] = a * i[:, k + 1] + (1 - a) / R * vn[:, k]
    rng = np.random.default_rng(semente)
    im = i[:, :M] + rng.normal(0, ruido, (3, M))
    im = np.round(im / A_ADC) * A_ADC
    al = (2 * im[0] - im[1] - im[2]) / 3
    be = (im[1] - im[2]) / np.sqrt(3)
    idd = al * np.cos(th) + be * np.sin(th)
    iq = -al * np.sin(th) + be * np.cos(th)
    # sem ruido, para comparar
    al0 = (2 * i[0, :M] - i[1, :M] - i[2, :M]) / 3
    be0 = (i[1, :M] - i[2, :M]) / np.sqrt(3)
    id0 = al0 * np.cos(th) + be0 * np.sin(th)
    return dict(vd=vd[:N], vq=vq[:N], id=idd[N:].reshape(periodos, N).mean(axis=0),
                iq=iq[N:].reshape(periodos, N).mean(axis=0),
                id_um=idd[-N:], id_verdade=id0[-N:])


def regressores(s, xd=None, xq=None):
    """Regressores do modelo acoplado; xd, xq trocam as saidas (instrumentos)."""
    idd, iq = s["id"] - s["id"].mean(), s["iq"] - s["iq"].mean()
    vd, vq = s["vd"] - s["vd"].mean(), s["vq"] - s["vq"].mean()
    xd = idd if xd is None else xd
    xq = iq if xq is None else xq
    k = np.arange(2, N)
    phi_d = np.column_stack([xd[k - 1], vd[k - 2], vq[k - 2], xq[k - 1]])
    phi_q = np.column_stack([xq[k - 1], vq[k - 2], vd[k - 2], -xd[k - 1]])
    return np.vstack([phi_d, phi_q]), np.r_[idd[k], iq[k]]


def simula_modelo(p, s):
    """Saida livre do modelo (sem usar as medidas de corrente)."""
    a, b, e, c = p
    vd, vq = s["vd"] - s["vd"].mean(), s["vq"] - s["vq"].mean()
    xd, xq = np.zeros(N), np.zeros(N)
    for k in range(2, N):
        xd[k] = a * xd[k - 1] + b * vd[k - 2] + e * vq[k - 2] + c * xq[k - 1]
        xq[k] = a * xq[k - 1] + b * vq[k - 2] + e * vd[k - 2] - c * xd[k - 1]
    return xd, xq


def estima(s):
    Phi, Y = regressores(s)
    p_ls, *_ = np.linalg.lstsq(Phi, Y, rcond=None)
    p_iv = p_ls
    for _ in range(3):                               # IV com a saida simulada como instrumento
        xd, xq = simula_modelo(p_iv, s)
        Z, _ = regressores(s, xd, xq)
        p_iv = np.linalg.solve(Z.T @ Phi, Z.T @ Y)
    return p_ls, p_iv


def ajuste(p, s):
    xd, xq = simula_modelo(p, s)
    yd, yq = s["id"] - s["id"].mean(), s["iq"] - s["iq"].mean()
    k = slice(50, N)
    return (100 * (1 - np.linalg.norm(yd[k] - xd[k]) / np.linalg.norm(yd[k] - yd[k].mean())),
            100 * (1 - np.linalg.norm(yq[k] - xq[k]) / np.linalg.norm(yq[k] - yq[k].mean())))


def figuras_sinais(s):
    t = np.arange(N) * TS * 1e3
    j = t <= 20
    fig, axs = plt.subplots(2, 1, figsize=(13, 6.5), sharex=True)
    axs[0].step(t[j], s["vd"][j], color=COR_A, lw=1.8, where="post", label="$v_d$")
    axs[0].step(t[j], s["vq"][j], color=COR_C, lw=1.8, where="post", label="$v_q$")
    axs[0].set_ylabel("tensão [V]")
    axs[0].legend(frameon=False, loc="upper right", ncol=2)
    for x, cor, nome in zip(s["d"], (COR_A, COR_B, COR_C), ("dA", "dB", "dC")):
        axs[1].plot(t[j], x[j], color=cor, lw=1.2, label=nome)
    axs[1].set_ylabel("razão cíclica")
    axs[1].set_ylim(0, 1.15)
    axs[1].set_xlabel("tempo [ms]")
    axs[1].legend(frameon=False, loc="upper right", ncol=3)
    for ax in axs:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "excitacao.png", dpi=110)
    plt.close(fig)

    fig, axs = plt.subplots(2, 1, figsize=(13, 6.5), sharex=True)
    for x, cor, nome in zip(s["i"], (COR_A, COR_B, COR_C), ("iA", "iB", "iC")):
        axs[0].plot(t[j], x[j], color=cor, lw=1.2, label=nome)
    axs[0].set_ylabel("corrente [A]")
    axs[0].set_ylim(-0.5, 0.55)
    axs[0].legend(frameon=False, loc="upper right", ncol=3)
    axs[1].plot(t[j], s["id"][j], color=COR_A, lw=1.2, label="$i_d$")
    axs[1].plot(t[j], s["iq"][j], color=COR_C, lw=1.2, label="$i_q$")
    axs[1].set_ylabel("corrente [A]")
    axs[1].set_ylim(-0.2, 0.45)
    axs[1].set_xlabel("tempo [ms]")
    axs[1].legend(frameon=False, loc="upper right", ncol=2)
    for ax in axs:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "correntes.png", dpi=110)
    plt.close(fig)


def figura_espectro():
    # espectro da PRBS (bits de Tb = 4 Ts) x resposta da carga
    Tb = NB * TS
    f = np.logspace(1, np.log10(10e3), 400)
    prbs_db = 20 * np.log10(np.abs(np.sinc(f * Tb)) + 1e-6)
    carga_db = 20 * np.log10(1 / np.sqrt(1 + (2 * np.pi * f * L / R) ** 2))
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.semilogx(f, prbs_db, color=COR_A, lw=2, label="espectro da PRBS (bit de 200 µs)")
    ax.semilogx(f, carga_db, color=COR_B, lw=2, label="carga RL: |I/V| normalizado")
    ax.axvline(R / (2 * np.pi * L), color=COR_B, ls=":", lw=1)
    ax.axvline(0.44 / Tb, color=COR_A, ls=":", lw=1)
    ax.text(R / (2 * np.pi * L) * 1.05, -27, "polo: 398 Hz", color=COR_B)
    ax.text(0.44 / Tb * 1.05, -6, "−3 dB: 2,2 kHz", color=COR_A)
    ax.axvline(1 / (2 * TS), color=COR_CINZA, ls="--", lw=1)
    ax.text(1 / (2 * TS) * 0.97, -36, "Nyquist\n10 kHz", color=COR_CINZA, ha="right")
    ax.set_ylim(-40, 5)
    ax.set_xlabel("frequência [Hz]")
    ax.set_ylabel("dB")
    ax.legend(frameon=False, loc="lower left")
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(IMGS / "espectro.png", dpi=110)
    plt.close(fig)


def figura_validacao(p_ls, p_iv, s_val):
    t = np.arange(N) * TS * 1e3
    j = (t >= 40) & (t <= 60)
    xd_ls, _ = simula_modelo(p_ls, s_val)
    xd_iv, _ = simula_modelo(p_iv, s_val)
    yd = s_val["id"] - s_val["id"].mean()
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(t[j], yd[j], ".", color=COR_CINZA, ms=4, label="$i_d$ medida (simulada, com ruído)")
    ax.plot(t[j], xd_ls[j], color=COR_B, lw=2, label="modelo LS")
    ax.plot(t[j], xd_iv[j], color=COR_A, lw=2, label="modelo IV")
    ax.set_xlabel("tempo [ms]")
    ax.set_ylabel("$i_d$ − média [A]")
    ax.set_ylim(-0.2, 0.25)
    ax.legend(frameon=False, loc="upper right", ncol=3)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "validacao.png", dpi=110)
    plt.close(fig)


def figura_vies(p_ref):
    ruidos = np.array([0, 5, 10, 15, 20]) * 1e-3
    est = {"LS": [], "IV": []}
    for r in ruidos:
        ls, iv = [], []
        for sem in range(20):
            p_ls, p_iv = estima(ensaio(r, semente=100 + sem))
            ls.append(p_ls[0])
            iv.append(p_iv[0])
        est["LS"].append((np.mean(ls), np.std(ls)))
        est["IV"].append((np.mean(iv), np.std(iv)))
    fig, ax = plt.subplots(figsize=(13, 5))
    for nome, cor, desl in (("LS", COR_B, -0.3), ("IV", COR_A, 0.3)):
        m = np.array(est[nome])
        ax.errorbar(ruidos * 1e3 + desl, m[:, 0], yerr=m[:, 1], color=cor, marker="o", ms=8,
                    lw=2, capsize=5, label=f"polo estimado ({nome})")
    ax.axhline(p_ref[0], color=COR_CINZA, ls="--", lw=1.5, label=f"referência {p_ref[0]:.4f}")
    ax.axvspan(8, 12, color=COR_AMARELO, alpha=0.25)
    ax.text(10, 0.80, "ruído medido\nno ensaio 2", ha="center", fontsize=13)
    ax.set_xlabel("ruído de medida por fase [mA rms]")
    ax.set_ylabel("polo $a$")
    ax.set_ylim(0.78, 0.9)
    ax.legend(frameon=False, loc="lower left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "vies.png", dpi=110)
    plt.close(fig)
    return ruidos, est


def figura_bode(p_ref, p_ls, p_iv):
    # resposta em frequencia de vd -> id (eixo isolado, c = e = 0)
    f = np.logspace(1, np.log10(9e3), 300)
    z = np.exp(1j * 2 * np.pi * f * TS)
    fig, ax = plt.subplots(figsize=(13, 5))
    for p, cor, nome, ls in ((p_ref, COR_CINZA, "referência", "--"), (p_ls, COR_B, "LS", "-"),
                             (p_iv, COR_A, "IV", "-")):
        G = p[1] * z ** -2 / (1 - p[0] * z ** -1)
        ax.semilogx(f, 20 * np.log10(np.abs(G) * R), color=cor, lw=2, ls=ls, label=nome)
    ax.set_xlabel("frequência [Hz]")
    ax.set_ylabel("|I/V|·R [dB]")
    ax.legend(frameon=False, loc="lower left")
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(IMGS / "bode.png", dpi=110)
    plt.close(fig)


def media_sincrona():
    """Figura da media e tabela: ajuste e polo (IV) para 20 V e 40 V, 1 a 16 periodos."""
    m = ensaio_media(0.010, 8, semente=11)
    t = np.arange(N) * TS * 1e3
    j = (t >= 40) & (t <= 50)
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(t[j], m["id_um"][j], ".", color=COR_CINZA, ms=5, label="um período (como no ensaio)")
    ax.plot(t[j], m["id"][j], color=COR_B, lw=1.5, label="média de 8 períodos")
    ax.plot(t[j], m["id_verdade"][j], color=COR_A, lw=2.5, ls="--", label="sem ruído")
    ax.set_xlabel("tempo dentro do período da PRBS [ms]")
    ax.set_ylabel("$i_d$ [A]")
    ax.set_ylim(0.0, 0.42)
    ax.legend(frameon=False, loc="upper right", ncol=3)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "media.png", dpi=110)
    plt.close(fig)
    erro_um = np.std(m["id_um"] - m["id_verdade"]) * 1e3
    erro_media = np.std(m["id"] - m["id_verdade"]) * 1e3
    print(f"media de 8 periodos: erro em id {erro_um:.1f} mA (um periodo) -> {erro_media:.1f} mA (media)")

    print("Vdc  vd0  dv   P   polo IV   ajuste IV (validacao em outro ensaio)")
    for vdc, vd0, dv in ((20.0, 5.0, 3.0), (40.0, 10.0, 6.0)):
        for P in (1, 4, 8, 16):
            s1 = ensaio_media(0.010, P, semente=20 + P, vdc=vdc, vd0=vd0, dv=dv)
            s2 = ensaio_media(0.010, P, semente=40 + P, vdc=vdc, vd0=vd0, dv=dv)
            _, p_iv = estima(s1)
            fd, fq = ajuste(p_iv, s2)
            print(f"{vdc:4.0f} {vd0:4.0f} {dv:4.0f} {P:3d}   {p_iv[0]:.4f}    {fd:.1f} / {fq:.1f} %")


def main():
    a = np.exp(-R * TS / L)
    print(f"esperado (continuo discretizado): a = {a:.4f}, b = {(1 - a) / R:.5f}, c ~ wTs = {W * TS:.4f}")
    s0 = ensaio(0.0)
    p_ref, _ = estima(s0)
    print("referencia (LS sem ruido): a %.4f b %.5f e %.5f c %.4f" % tuple(p_ref))
    print("razao: min %.3f max %.3f" % (s0["d"].min(), s0["d"].max()))
    print("id: media %.3f, de %.3f a %.3f | iq: media %.3f, de %.3f a %.3f"
          % (s0["id"].mean(), s0["id"].min(), s0["id"].max(), s0["iq"].mean(), s0["iq"].min(), s0["iq"].max()))

    s = ensaio(0.010, semente=1)          # "medido"
    s_val = ensaio(0.010, semente=2)      # outro registro, para validar
    p_ls, p_iv = estima(s)
    for nome, p in (("LS", p_ls), ("IV", p_iv)):
        fd, fq = ajuste(p, s_val)
        print(f"{nome} (10 mA): a {p[0]:.4f} b {p[1]:.5f} e {p[2]:.5f} c {p[3]:.4f} | "
              f"ajuste na validacao: id {fd:.1f} %, iq {fq:.1f} %")
    for eixo, nome in ((1, "so d"), (2, "so q")):
        pl, pi = estima(ensaio(0.010, semente=3, eixo=eixo))
        print(f"eixoPRBS {eixo} ({nome}): LS a {pl[0]:.4f} b {pl[1]:.5f} | IV a {pi[0]:.4f} b {pi[1]:.5f}")
    # ruido em dq
    print("ruido em id: %.1f mA rms" % (np.std(ensaio(0.010, 5)["id"] - s0["id"]) * 1e3))

    figuras_sinais(s)
    figura_espectro()
    figura_validacao(p_ls, p_iv, s_val)
    figura_bode(p_ref, p_ls, p_iv)
    media_sincrona()
    ruidos, est = figura_vies(p_ref)
    for nome in est:
        print(nome + ": " + "  ".join(f"{r * 1e3:.0f} mA: {m:.4f}±{d:.4f}" for r, (m, d) in zip(ruidos, est[nome])))


if __name__ == "__main__":
    main()
