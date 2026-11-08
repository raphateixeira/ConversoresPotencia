"""Figuras da apresentacao "Malha aberta com carga RL: tensoes e correntes medidas".

Le o CSV exportado do CCS pelo VSI01MalhaAbertaCargaRL (vetores correnteA/B/C e
tensaoA/B/C, 2000 amostras de 50 us) e gera em ../imgs/:
  tensoes.png        vA, vB, vC em relacao ao GND (100 ms)
  correntes.png      iA, iB, iC (100 ms)
  fase_A.png         tensao de fase na carga vAn e corrente iA (um ciclo e meio)
  linha.png          tensoes de linha vAB, vBC, vCA
  alfabeta.png       trajetorias de v e i no plano alfa-beta (Clarke)
  ajuste.png         corrente iA medida e senoide de 60 Hz ajustada (residuo)

Uso: python3 figuras.py [arquivo.csv]   (padrao: ../../../Dados3FRL/Dados01.csv)
Os numeros impressos no fim vao para os slides.
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
IMGS = AQUI.parent / "imgs"
IMGS.mkdir(exist_ok=True)
ARQUIVO = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI.parents[2] / "Dados3FRL" / "Dados01.csv"

# Cores do tema (TemaRTx): fases A, B, C
COR_A, COR_B, COR_C = "#1B365D", "#B23A48", "#2E7D32"
CORES = (COR_A, COR_B, COR_C)
COR_ACENTO, COR_CINZA = "#4A6FA5", "#6C757D"
plt.rcParams.update({"font.size": 15, "axes.titlesize": 16, "axes.labelsize": 15,
                     "font.family": "sans-serif", "axes.spines.top": False,
                     "axes.spines.right": False})

# Ensaio (iguais ao main.c e a bancada)
TS = 50e-6                 # s, uma amostra por periodo de PWM
F = 60.0                   # Hz
VDC = 19.83                # V, tensaoBarramento lida na Watch durante o ensaio
AMPLITUDE = 0.4            # amplitude da razao ciclica
R, L = 25.0, 10e-3         # carga por fase


def le_csv_ccs(caminho):
    """CSV do CCS: 1a linha com os nomes, 2a com Sample/Value, um bloco por vetor."""
    linhas = [l.split(",") for l in Path(caminho).read_text().splitlines()]
    nomes = {i: n.strip() for i, n in enumerate(linhas[0]) if n.strip()}
    vetores = {}
    for i, nome in nomes.items():
        col = [l[i + 1] for l in linhas[2:] if len(l) > i + 1]
        vetores[nome] = np.array([float(c) for c in col if c not in ("", "undefined")])
    return vetores


def ajusta(t, x, f=F):
    """x ~ c + A sen(wt + fi): devolve (c, A, fi em graus, residuo)."""
    w = 2 * np.pi * f
    M = np.column_stack([np.ones_like(t), np.sin(w * t), np.cos(w * t)])
    (c, a, b), *_ = np.linalg.lstsq(M, x, rcond=None)
    return c, np.hypot(a, b), np.degrees(np.arctan2(b, a)), x - M @ np.array([c, a, b])


def eixo_tempo(ax):
    ax.set_xlabel("tempo [ms]")
    ax.grid(alpha=0.3)


def main():
    v = le_csv_ccs(ARQUIVO)
    vA, vB, vC = v["tensaoA"], v["tensaoB"], v["tensaoC"]
    iA, iB, iC = v["correnteA"], v["correnteB"], v["correnteC"]
    n = len(vA)
    t = np.arange(n) * TS
    tm = t * 1e3

    # Tensao de fase na carga (neutro isolado): vAn = vA - (vA + vB + vC)/3
    vN = (vA + vB + vC) / 3
    vAn, vBn, vCn = vA - vN, vB - vN, vC - vN

    # --- tensoes x GND
    fig, ax = plt.subplots(figsize=(13, 5))
    for x, cor, nome in zip((vA, vB, vC), CORES, ("vA", "vB", "vC")):
        ax.plot(tm, x, color=cor, lw=1.8, label=nome)
    ax.axhline(VDC / 2, color=COR_CINZA, lw=1, ls="--")
    ax.set_ylabel("tensão do braço × GND [V]")
    ax.set_ylim(0, VDC)
    ax.legend(ncol=3, frameon=False, loc="upper right")
    eixo_tempo(ax)
    fig.tight_layout()
    fig.savefig(IMGS / "tensoes.png", dpi=110)
    plt.close(fig)

    # --- correntes
    fig, ax = plt.subplots(figsize=(13, 5))
    for x, cor, nome in zip((iA, iB, iC), CORES, ("iA", "iB", "iC")):
        ax.plot(tm, x, color=cor, lw=1.5, label=nome)
    ax.set_ylabel("corrente da fase [A]")
    ax.set_ylim(-0.45, 0.5)
    ax.legend(ncol=3, frameon=False, loc="upper right")
    eixo_tempo(ax)
    fig.tight_layout()
    fig.savefig(IMGS / "correntes.png", dpi=110)
    plt.close(fig)

    # --- fase A: vAn e iA em um ciclo e meio
    janela = tm <= 25
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(tm[janela], vAn[janela], color=COR_A, lw=2, label="vAn (tensão de fase na carga)")
    ax.set_ylabel("vAn [V]", color=COR_A)
    ax.axhline(0, color=COR_CINZA, lw=0.8)
    ax2 = ax.twinx()
    ax2.plot(tm[janela], iA[janela], color=COR_B, lw=1.5, label="iA")
    ax2.set_ylabel("iA [A]", color=COR_B)
    ax2.spines["right"].set_visible(True)
    lim_v = 1.15 * np.abs(vAn).max()
    ax.set_ylim(-lim_v, lim_v)
    ax2.set_ylim(-lim_v / (R * 1.0) * 1.0, lim_v / R)   # mesma escala que v/R
    linhas = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    ax.legend(linhas, [l.get_label() for l in linhas], frameon=False, loc="upper right")
    eixo_tempo(ax)
    fig.tight_layout()
    fig.savefig(IMGS / "fase_A.png", dpi=110)
    plt.close(fig)

    # --- tensoes de linha
    fig, ax = plt.subplots(figsize=(13, 5))
    for x, cor, nome in zip((vA - vB, vB - vC, vC - vA), CORES, ("vAB", "vBC", "vCA")):
        ax.plot(tm, x, color=cor, lw=1.8, label=nome)
    ax.axhline(0, color=COR_CINZA, lw=0.8)
    ax.set_ylabel("tensão de linha [V]")
    ax.legend(ncol=3, frameon=False, loc="upper right")
    eixo_tempo(ax)
    fig.tight_layout()
    fig.savefig(IMGS / "linha.png", dpi=110)
    plt.close(fig)

    # --- plano alfa-beta (Clarke, invariante em amplitude)
    def clarke(a, b, c):
        return (2 * a - b - c) / 3, (b - c) / np.sqrt(3)
    va, vb = clarke(vA, vB, vC)
    ia, ib = clarke(iA, iB, iC)
    fig, axs = plt.subplots(1, 2, figsize=(13, 6))
    axs[0].plot(va, vb, color=COR_A, lw=1)
    axs[0].set_title("tensão $v_{\\alpha\\beta}$ [V]")
    axs[1].plot(ia, ib, color=COR_B, lw=1)
    axs[1].set_title("corrente $i_{\\alpha\\beta}$ [A]")
    for ax, nome in zip(axs, ("v", "i")):
        ax.set_aspect("equal")
        ax.axhline(0, color=COR_CINZA, lw=0.8)
        ax.axvline(0, color=COR_CINZA, lw=0.8)
        ax.set_xlabel(f"${nome}_\\alpha$")
        ax.set_ylabel(f"${nome}_\\beta$")
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "alfabeta.png", dpi=110)
    plt.close(fig)

    # --- ajuste de 60 Hz na corrente iA
    c, A, fi, res = ajusta(t, iA)
    fig, axs = plt.subplots(2, 1, figsize=(13, 6.5), sharex=True,
                            gridspec_kw={"height_ratios": [2, 1]})
    axs[0].plot(tm, iA, ".", color=COR_B, ms=3, label="iA medida")
    axs[0].plot(tm, iA - res, color=COR_A, lw=2, label="senoide de 60 Hz ajustada")
    axs[0].set_ylabel("iA [A]")
    axs[0].set_ylim(-0.45, 0.55)
    axs[0].legend(frameon=False, loc="upper right", ncol=2)
    axs[0].grid(alpha=0.3)
    axs[1].plot(tm, res * 1e3, color=COR_CINZA, lw=1)
    axs[1].set_ylabel("resíduo [mA]")
    eixo_tempo(axs[1])
    fig.tight_layout()
    fig.savefig(IMGS / "ajuste.png", dpi=110)
    plt.close(fig)

    # --- numeros para os slides
    w = 2 * np.pi * F
    Z = np.hypot(R, w * L)
    V_esp = AMPLITUDE * VDC
    I_esp = V_esp / Z
    atraso_esp = np.degrees(np.arctan(w * L / R))
    print(f"arquivo: {ARQUIVO}  ({n} amostras, {n * TS * 1e3:.0f} ms)")
    print(f"esperado: Vfase = {V_esp:.2f} V, |Z| = {Z:.2f} Ohm, I = {I_esp:.3f} A, "
          f"atraso = {atraso_esp:.1f} graus, Vlinha = {np.sqrt(3) * V_esp:.2f} V")
    fases = {}
    for nome, x in (("vA", vA), ("vB", vB), ("vC", vC), ("vAn", vAn), ("vBn", vBn), ("vCn", vCn),
                    ("vAB", vA - vB), ("iA", iA), ("iB", iB), ("iC", iC)):
        c, A, fi, res = ajusta(t, x)
        fases[nome] = fi
        print(f"  {nome:4s}: media {c:7.3f}  pico (60 Hz) {A:7.3f}  fase {fi:7.1f}  "
              f"resíduo rms {res.std():.4f}  min {x.min():7.3f}  max {x.max():7.3f}")
    for f_ in "ABC":
        atraso = (fases[f"v{f_}n"] - fases[f"i{f_}"] + 180) % 360 - 180
        print(f"  atraso i{f_} em relacao a v{f_}n: {atraso:.1f} graus")
    print(f"  defasagem vA->vB: {(fases['vA'] - fases['vB']) % 360:.1f}, "
          f"vA->vC: {(fases['vA'] - fases['vC']) % 360:.1f} graus")
    print(f"  defasagem iA->iB: {(fases['iA'] - fases['iB']) % 360:.1f}, "
          f"iA->iC: {(fases['iA'] - fases['iC']) % 360:.1f} graus")
    soma = iA + iB + iC
    print(f"  iA+iB+iC: media {soma.mean():.4f} A, rms {soma.std():.4f} A, max |.| {np.abs(soma).max():.3f} A")
    print(f"  neutro vN: media {vN.mean():.3f} V, pico-a-pico {np.ptp(vN):.3f} V")


if __name__ == "__main__":
    main()
