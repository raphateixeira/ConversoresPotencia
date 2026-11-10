"""Figuras do ensaio 2 (codigo com correnteTopo, razao e barramento gravados).

Le ../../../dados/Dados02.csv (tensoes, correntes no zero e no topo do
contador) e Dados02RB.csv (razoes ciclicas aplicadas e barramento) e gera em
../imgs/:
  e2_zero_topo.png     iA no zero e no topo do contador, com a razao dA
  e2_residuo.png       residuo do ajuste de 60 Hz em funcao da razao ciclica
  e2_alfabeta.png      corrente no plano alfa-beta: so zero x combinada
  e2_tensao.png        vA medida (filtro da placa) x dA.Vdc
  e2_dq.png            vd, vq (da razao) e id, iq (corrente combinada)

Corrente combinada: amostra do zero quando d >= 0,5 (pulso de cima largo) e do
topo quando d < 0,5, com o desvio de zero do topo descontado.
A razao escrita na amostra k vale a partir do zero k+1: a tensao media que ela
produz fica centrada em k+1,5 (atraso de 1,5 amostra).

Uso: python3 figuras_ensaio2.py
"""

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from figuras import le_csv_ccs, ajusta, IMGS, CORES, COR_A, COR_B, COR_C, COR_CINZA, TS, F, R, L

DADOS = Path(__file__).resolve().parents[3] / "dados"
FASES = "ABC"
ATRASO_RAZAO = 1.5 * TS    # s


def clarke(a, b, c):
    return (2 * a - b - c) / 3, (b - c) / np.sqrt(3)


def park(al, be, th):
    return al * np.cos(th) + be * np.sin(th), -al * np.sin(th) + be * np.cos(th)


def main():
    v = le_csv_ccs(DADOS / "Dados02.csv")
    r = le_csv_ccs(DADOS / "Dados02RB.csv")
    n = len(v["tensaoA"])
    t = np.arange(n) * TS
    tm = t * 1e3
    d = {f: r["razao" + f] for f in FASES}
    vdc = r["barramento"]
    iz = {f: v["corrente" + f] for f in FASES}
    it_bruta = {f: v["correnteTopo" + f] for f in FASES}
    vm = {f: v["tensao" + f] for f in FASES}

    # desvio de zero do topo: a soma das tres correntes tem de ser nula
    desvio = (sum(it_bruta.values()).mean() - sum(iz.values()).mean()) / 3
    it = {f: it_bruta[f] - desvio for f in FASES}
    d_ant = {f: np.r_[d[f][0], d[f][:-1]] for f in FASES}      # razao em vigor na amostra
    comb = {f: np.where(d_ant[f] >= 0.5, iz[f], it[f]) for f in FASES}

    # --- iA no zero e no topo, com dA
    janela = tm <= 25
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(tm[janela], iz["A"][janela], color=COR_A, lw=1.5, label="iA no zero")
    ax.plot(tm[janela], it_bruta["A"][janela], color=COR_B, lw=1.5, label="iA no topo")
    ax.set_ylabel("iA [A]")
    ax.set_ylim(-0.5, 0.5)
    ax2 = ax.twinx()
    ax2.fill_between(tm[janela], 0, d["A"][janela], color=COR_CINZA, alpha=0.15, step="mid")
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("razão dA", color=COR_CINZA)
    ax2.spines["right"].set_visible(True)
    ax.set_zorder(ax2.get_zorder() + 1)
    ax.patch.set_visible(False)
    ax.legend(frameon=False, loc="upper right", ncol=2)
    ax.set_xlabel("tempo [ms]")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "e2_zero_topo.png", dpi=110)
    plt.close(fig)

    # --- residuo rms por faixa de razao (tres fases juntas)
    faixas = np.arange(0.1, 0.9, 0.1)
    rms = {}
    for nome, fonte, desloc in (("zero", iz, 0.0), ("topo", it, -TS / 2)):
        res = np.concatenate([ajusta(t + desloc, fonte[f])[3] for f in FASES])
        dd = np.concatenate([d_ant[f] for f in FASES])
        rms[nome] = [np.sqrt(np.mean(res[(dd >= a) & (dd < a + 0.1)] ** 2)) * 1e3 for a in faixas]
    fig, ax = plt.subplots(figsize=(13, 5))
    centros = faixas + 0.05
    ax.bar(centros - 0.02, rms["zero"], width=0.04, color=COR_A, label="no zero (pulso de cima)")
    ax.bar(centros + 0.02, rms["topo"], width=0.04, color=COR_B, label="no topo (pulso de baixo)")
    ax.axhline(7.32, color=COR_CINZA, ls="--", lw=1, label="1 contagem do ADC")
    ax.set_xlabel("razão cíclica da fase")
    ax.set_ylabel("resíduo rms [mA]")
    ax.set_xticks(np.round(faixas, 1))
    ax.set_ylim(0, 30)
    ax.legend(frameon=False, loc="upper center", ncol=3)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(IMGS / "e2_residuo.png", dpi=110)
    plt.close(fig)

    # --- corrente no plano alfa-beta: so zero x combinada
    fig, axs = plt.subplots(1, 2, figsize=(13, 6))
    for ax, fonte, titulo in ((axs[0], iz, "só no zero"), (axs[1], comb, "combinada (zero ou topo)")):
        a, b = clarke(*(fonte[f] for f in FASES))
        ax.plot(a, b, color=COR_B, lw=1)
        ax.set_title(titulo)
        ax.set_aspect("equal")
        ax.set_xlim(-0.42, 0.42)
        ax.set_ylim(-0.42, 0.42)
        ax.axhline(0, color=COR_CINZA, lw=0.8)
        ax.axvline(0, color=COR_CINZA, lw=0.8)
        ax.set_xlabel("$i_\\alpha$ [A]")
        ax.set_ylabel("$i_\\beta$ [A]")
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "e2_alfabeta.png", dpi=110)
    plt.close(fig)

    # --- tensao medida x razao.Vdc (um ciclo)
    janela = tm <= 17
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(tm[janela] + ATRASO_RAZAO * 1e3, (d["A"] * vdc)[janela], color=COR_CINZA, lw=3,
            label="dA·Vdc (deslocada de 1,5 amostra)")
    ax.plot(tm[janela], vm["A"][janela], color=COR_A, lw=1.5, label="vA medida (filtro de 1 kHz)")
    ax.set_ylabel("tensão do braço × GND [V]")
    ax.set_xlabel("tempo [ms]")
    ax.legend(frameon=False, loc="upper center")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "e2_tensao.png", dpi=110)
    plt.close(fig)

    # --- dq: angulo da propria razao, tensao em vigor (atraso de 1,5 amostra)
    w = 2 * np.pi * F
    da, db = clarke(*(d[f] for f in FASES))
    th = np.arctan2(db, da) - w * ATRASO_RAZAO
    vd, vq = park(*clarke(*(d[f] * vdc for f in FASES)), th + w * ATRASO_RAZAO)
    i_d, i_q = park(*clarke(*(comb[f] for f in FASES)), th)
    fig, axs = plt.subplots(2, 1, figsize=(13, 6.5), sharex=True)
    axs[0].plot(tm, vd, color=COR_A, lw=1.5, label="$v_d$")
    axs[0].plot(tm, vq, color=COR_C, lw=1.5, label="$v_q$")
    axs[0].set_ylabel("tensão [V]")
    axs[0].set_ylim(-2, 10)
    axs[1].plot(tm, i_d, color=COR_A, lw=1, label="$i_d$")
    axs[1].plot(tm, i_q, color=COR_C, lw=1, label="$i_q$")
    axs[1].set_ylabel("corrente [A]")
    axs[1].set_ylim(-0.15, 0.5)
    axs[1].set_xlabel("tempo [ms]")
    for ax in axs:
        ax.legend(frameon=False, loc="upper right", ncol=2)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "e2_dq.png", dpi=110)
    plt.close(fig)

    # --- numeros para os slides
    Z = np.hypot(R, w * L)
    print(f"Vdc: media {vdc.mean():.2f} V, pico a pico {np.ptp(vdc):.3f} V")
    print(f"desvio de zero do topo: {desvio * 1e3:.1f} mA por fase")
    print("residuo rms por faixa de razao [mA]:")
    for nome in rms:
        print(f"  {nome}: " + "  ".join(f"{a:.1f}:{x:.1f}" for a, x in zip(faixas, rms[nome])))
    dm = sum(d.values()) / 3
    for f in FASES:
        _, Vn, fv, _ = ajusta(t + ATRASO_RAZAO, (d[f] - dm) * vdc)
        _, Iz, fz, rz = ajusta(t, iz[f])
        _, It, _, rt = ajusta(t - TS / 2, it[f])
        _, Ic, fc, rc = ajusta(t, comb[f])
        _, Vu, fu, _ = ajusta(t + ATRASO_RAZAO, d[f] * vdc)
        _, Vm, fm, _ = ajusta(t, vm[f])
        print(f"fase {f}: Vn {Vn:.3f} V | I zero {Iz:.4f} (res {rz.std() * 1e3:.1f}) topo {It:.4f} "
              f"(res {rt.std() * 1e3:.1f}) comb {Ic:.4f} (res {rc.std() * 1e3:.1f}) | "
              f"|Z| {Vn / Ic:.2f} atraso comb {(fv - fc + 180) % 360 - 180:.1f} zero {(fv - fz + 180) % 360 - 180:.1f} | "
              f"v medida/dVdc {Vm / Vu:.4f} atraso filtro {(fu - fm + 180) % 360 - 180:.2f}")
    for nome, fonte in (("zero", iz), ("topo", it), ("comb", comb)):
        s = sum(fonte.values())
        print(f"soma {nome}: media {s.mean() * 1e3:.1f} mA, rms {s.std() * 1e3:.1f} mA")
    print(f"esperado: |Z| = {Z:.2f}, I = {np.mean([ajusta(t, (d[f] - dm) * vdc)[1] for f in FASES]) / Z:.4f} A, "
          f"atraso {np.degrees(np.arctan(w * L / R)):.1f} graus")
    print(f"dq: vd {vd.mean():.3f}±{vd.std():.3f}  vq {vq.mean():.3f}±{vq.std():.3f}  "
          f"id {i_d.mean():.4f}±{i_d.std():.4f}  iq {i_q.mean():.4f}±{i_q.std():.4f}")
    print(f"modelo dq: id {vd.mean() * R / Z**2:.4f}  iq {-vd.mean() * w * L / Z**2:.4f}")


if __name__ == "__main__":
    main()
