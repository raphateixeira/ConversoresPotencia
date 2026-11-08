"""Ensaio do PI (firmware VSI03ControlePI) simulado e leitura dos dados medidos.

Simulacao: mesmo algoritmo do firmware (PI por eixo, kp = 2 pi fc L, ki = 2 pi fc R,
desacoplamento wL, |v| <= 0,45 Vdc com anti-windup, perfil de degraus que se repete a
cada 2044 amostras) sobre o modelo MIMO 1,2,2 identificado (mesmo atraso de 2 amostras),
com ruido de medida. Gera ../imgs/simula_pi.png e imprime os numeros do ensaio esperado.

Leitura: le_dados_pi(arquivo) le a matriz Dados3F[8][2044] exportada do CCS (Graph, 16352
valores, ou Save Memory .dat/.bin), linhas idRef iqRef id iq vd vq iA iB (iC = -iA - iB).

Uso: python3 simula_pi.py                 (simulacao)
     python3 simula_pi.py arquivo.csv     (simulacao + dados medidos na mesma figura)
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "IdentificacaoARXDados" / "analise"))
import identifica as I                                   # noqa: E402

IMGS = AQUI.parent / "imgs"
TS, F, N = 50e-6, 60.0, 2044
R, L = 26.2, 9.8e-3                                      # valores do firmware
VDC = 20.0
REF = dict(d0=0.15, q0=0.0, dd=0.10, dq=-0.05, d_liga=200, d_desl=1200, q_liga=700, q_desl=1700)
CANAIS = ("idref", "iqref", "id", "iq", "vd", "vq", "iA", "iB")
plt.rcParams.update({"font.size": 18, "axes.labelsize": 19, "axes.titlesize": 19,
                     "xtick.labelsize": 16, "ytick.labelsize": 16, "legend.fontsize": 16})


def referencias():
    n = np.arange(N)
    rd = REF["d0"] + REF["dd"] * ((n >= REF["d_liga"]) & (n < REF["d_desl"]))
    rq = REF["q0"] + REF["dq"] * ((n >= REF["q_liga"]) & (n < REF["q_desl"]))
    return rd, rq


def simula(fc=300.0, desacopla=True, ruido=0.0085, periodos=3, semente=0):
    """Retorna o ultimo periodo: rd, rq, id, iq, vd, vq (como o firmware grava, sem media)."""
    s = I.carrega()
    y, u = I.desvios(s)
    e = dict(I.ESTRUTURAS)["MIMO 1,2,2"]
    th = I.estima(e, y, u, 0, s["N"], I.METODO)          # [a, b1, b2, e1, e2, c] por eixo
    kp, ki = 2 * np.pi * fc * L, 2 * np.pi * fc * R
    wL = 2 * np.pi * F * L
    vmax = 0.45 * VDC
    rd1, rq1 = referencias()
    M = N * periodos
    rd, rq = np.tile(rd1, periodos), np.tile(rq1, periodos)
    i = {"d": np.zeros(M), "q": np.zeros(M)}
    v = {"d": np.zeros(M), "q": np.zeros(M)}
    integ = {"d": 0.0, "q": 0.0}
    rng = np.random.default_rng(semente)
    sat = 0
    for k in range(3, M):
        for o, p in (("d", "q"), ("q", "d")):
            t = th[o]
            i[o][k] = (t[0] * i[o][k - 1] + t[1] * v[o][k - 2] + t[2] * v[o][k - 3]
                       + t[3] * v[p][k - 2] + t[4] * v[p][k - 3] + t[5] * i[p][k - 1])
        im = {o: i[o][k] + ruido * rng.standard_normal() for o in "dq"}
        r = {"d": rd[k], "q": rq[k]}
        nova = {o: integ[o] + ki * TS * (r[o] - im[o]) for o in "dq"}
        vv = {o: kp * (r[o] - im[o]) + nova[o] for o in "dq"}
        if desacopla:
            vv["d"] -= wL * im["q"]
            vv["q"] += wL * im["d"]
        mod = np.hypot(vv["d"], vv["q"])
        if mod > vmax:
            vv = {o: vv[o] * vmax / mod for o in "dq"}
            sat += 1
        else:
            integ = nova
        v["d"][k], v["q"][k] = vv["d"], vv["q"]
    j = slice(M - N, M)
    return dict(idref=rd[j], iqref=rq[j], id=i["d"][j], iq=i["q"][j], vd=v["d"][j], vq=v["q"][j],
                sat=sat, kp=kp, ki=ki)


def metricas(x):
    """Subida (10-90 %) e sobressinal do degrau em d; interferencia em q no degrau de d."""
    a, b = REF["d_liga"], REF["d_liga"] + 300
    y = x["id"][a:b] - REF["d0"]
    dd = REF["dd"]
    t10 = np.argmax(y >= 0.1 * dd); t90 = np.argmax(y >= 0.9 * dd)
    sobre = max(0.0, (y.max() - dd) / dd * 100)
    interf = np.abs(x["iq"][a:b] - REF["q0"]).max()
    return (t90 - t10) * TS * 1e3, sobre, interf * 1e3


def le_dados_pi(arquivo):
    arquivo = Path(arquivo)
    if arquivo.suffix.lower() == ".csv":
        vals = []
        for linha in open(arquivo):
            partes = linha.strip().split(",")
            try:
                vals.append(float(partes[-1] if partes[-1] else partes[0]))
            except ValueError:
                continue                          # cabecalhos do CCS ("Dados3F,", "Sample,Value")
        x = np.array(vals)
    elif arquivo.suffix.lower() == ".dat":
        linhas = [l.split() for l in open(arquivo) if l.strip() and not l.startswith("1651")]
        x = np.array([float(l[-1]) for l in linhas])
    else:
        x = np.fromfile(arquivo, dtype="<f4")
    x = x[:8 * N]
    if x.size < 8 * N:
        raise ValueError(f"{arquivo}: {x.size} valores, esperado {8 * N}")
    d = {c: x[k * N:(k + 1) * N] for k, c in enumerate(CANAIS)}
    d["iC"] = -d["iA"] - d["iB"]
    return d


def figura(sims, medido=None, nome="simula_pi.png"):
    t = np.arange(N) * TS * 1e3
    fig, axs = plt.subplots(2, 2, figsize=(16, 8.4), sharex=True)
    cores = ("#1F5FBF", "#2A9D3A", "#D62828")
    for (rot, x), cor in zip(sims.items(), cores):
        axs[0, 0].plot(t, x["id"] * 1e3, color=cor, lw=2.2, label=rot)
        axs[1, 0].plot(t, x["iq"] * 1e3, color=cor, lw=2.2)
        axs[0, 1].plot(t, x["vd"], color=cor, lw=1.6)
        axs[1, 1].plot(t, x["vq"], color=cor, lw=1.6)
    x0 = next(iter(sims.values()))
    axs[0, 0].plot(t, x0["idref"] * 1e3, "k--", lw=1.5, label="referência")
    axs[1, 0].plot(t, x0["iqref"] * 1e3, "k--", lw=1.5)
    if medido is not None:
        axs[0, 0].plot(t, medido["id"] * 1e3, ".", color="#E8C547", ms=3, label="medido")
        axs[1, 0].plot(t, medido["iq"] * 1e3, ".", color="#E8C547", ms=3)
        axs[0, 1].plot(t, medido["vd"], ".", color="#E8C547", ms=3)
        axs[1, 1].plot(t, medido["vq"], ".", color="#E8C547", ms=3)
    axs[0, 0].set_ylabel("$i_d$ [mA]"); axs[1, 0].set_ylabel("$i_q$ [mA]")
    axs[0, 1].set_ylabel("$v_d$ [V]"); axs[1, 1].set_ylabel("$v_q$ [V]")
    axs[0, 0].legend(frameon=False, loc="upper right", fontsize=14)
    for ax in axs.flat:
        ax.grid(alpha=0.3); ax.margins(x=0)
    for ax in axs[1]:
        ax.set_xlabel("tempo [ms]")
    fig.tight_layout(w_pad=3)
    fig.savefig(IMGS / nome, dpi=110)
    plt.close(fig)


def main():
    sims = {}
    for fc, des in ((300.0, True), (500.0, True), (300.0, False)):
        rot = f"{fc:.0f} Hz" + ("" if des else ", sem desacopl.")
        sims[rot] = simula(fc, des, ruido=0.0)
        tr, so, it = metricas(sims[rot])
        x = sims[rot]
        print(f"{rot}: kp {x['kp']:.1f} V/A, ki {x['ki']:.0f} V/(A s); subida {tr:.2f} ms, "
              f"sobressinal {so:.0f} %, iq no degrau de id {it:.1f} mA; |v| max "
              f"{np.hypot(x['vd'], x['vq']).max():.2f} V; saturacoes {x['sat']}")
    med = le_dados_pi(sys.argv[1]) if len(sys.argv) > 1 else None
    figura(sims, med)


if __name__ == "__main__":
    main()
