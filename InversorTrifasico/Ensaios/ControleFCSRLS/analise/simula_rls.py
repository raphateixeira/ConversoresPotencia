"""FCS-MPC adaptativo: RLS atualiza o modelo da carga e o FCS usa o modelo estimado.

Modelo (alfa e beta, mesmos parametros; carga simetrica), com a temporizacao do firmware
(corrente lida no zero k; o vetor escolhido em k vale do topo k+1/2 ao topo k+3/2):
    i(k+1) = th1 i(k) + th2 v(k-1) + th3 v(k)
    th1 = a = e^(-R Ts/L),  th3 = bh = (1 - ah)/R,  th2 = ah bh,  ah = e^(-R Ts/(2L))
v normalizada por Vdc (melhor condicionamento). RLS com esquecimento lam; duas atualizacoes por
amostra (alfa e beta). FCS: para cada estado, i(k+1) com o vetor em vigor e i(k+2) mantendo o
novo vetor; custo |i*(k+2) - i(k+2)|^2.
Recuperacao fisica: ah = sqrt(th1), R = (1 - ah)/th3', L = -R Ts / ln(th1).

Gera em ../imgs: rls_convergencia.png, rls_desempenho.png; imprime os numeros.
Uso: python3 simula_rls.py
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "ControlePIDados" / "analise"))
sys.path.insert(0, str(AQUI.parents[1] / "ControleFCS" / "analise"))
import simula_pi as SP                                    # noqa: E402
import simula_fcs as SF                                   # noqa: E402

IMGS = AQUI.parent / "imgs"
TS, N, F = SP.TS, SP.N, 60.0
R, L, VDC = 25.3, 9.8e-3, 20.0
SUB = 20
AZUL, VERM, VERDE, CINZA = "#1F5FBF", "#D62828", "#2A9D3A", "#6C757D"
plt.rcParams.update({"font.size": 20, "axes.labelsize": 21, "axes.titlesize": 21,
                     "xtick.labelsize": 18, "ytick.labelsize": 18, "legend.fontsize": 17})
VET = np.array([SF.vetor(e, 1.0) for e in range(8)])     # vetores normalizados (Vdc = 1)


def theta_de(Rm, Lm):
    a, ah = np.exp(-Rm * TS / Lm), np.exp(-Rm * TS / 2 / Lm)
    bh = (1 - ah) / Rm * VDC                              # v normalizada por Vdc
    return np.array([a, ah * bh, bh])


def fisicos(th):
    ah = np.sqrt(max(th[0], 1e-6))
    Rm = (1 - ah) / th[2] * VDC
    return Rm, -Rm * TS / np.log(max(th[0], 1e-6))


def simula(Rmod=35.0, Lmod=14e-3, adapta=True, ruido=0.0085, lam=0.999, periodos=3, semente=0, Rreal=R, Lreal=L,
           metodo="RLS", k_troca=2000, lam_iv=0.9998, dither=0.0, bits=4):
    rng = np.random.default_rng(semente)
    h = TS / SUB
    af, bf = np.exp(-Rreal * h / Lreal), (1 - np.exp(-Rreal * h / Lreal)) / Rreal
    rd1, rq1 = SP.referencias()
    M = N * periodos
    rd, rq = np.tile(rd1, periodos), np.tile(rq1, periodos)
    if dither > 0:                       # excitacao: PRBS (+-dither A) somada as referencias d e q
        import identifica_prbs as _p
        rd = rd + dither * np.resize(np.repeat(_p.prbs(4), bits), M)
        rq = rq + dither * np.resize(np.repeat(_p.prbs(3), bits), M)
    w = 2 * np.pi * F
    th = theta_de(Rmod, Lmod)
    P = np.diag([1e2, 1e2, 1e2])
    i = np.zeros(2)
    v_ant3, v_ant2, v_ant, estado = np.zeros(2), np.zeros(2), np.zeros(2), 0   # v(k-3), v(k-2), v(k-1)
    i_ant = np.zeros(2)
    i_sim = np.zeros(2)                                          # RIV: corrente simulada pelo modelo (instrumento)
    i_s, vs1, vs2, est_s = np.zeros(2), np.zeros(2), np.zeros(2), 0   # CLIV: FCS simulado em malha fechada
    fila = [(np.zeros(2), np.zeros(2)), (np.zeros(2), np.zeros(2))]   # PIV: (i prevista, vetor "sem ruido") de k-1 e k-2
    hist = {k: np.zeros(M) for k in ("id", "iq", "R", "L", "e", "idv", "iqv")}
    for k in range(M):
        tk = w * k * TS
        im = i + ruido * rng.standard_normal(2)
        if ruido > 0:
            im = np.round(im / 7.32e-3) * 7.32e-3
        # RLS: i(k) = th1 i(k-1) + th2 v(k-2) + th3 v(k-1)   (alfa e beta)
        if adapta and k > 2:
            for c in range(2):
                phi = np.array([i_ant[c], v_ant2[c], v_ant[c]])
                usa_rls = metodo == "RLS" or (metodo in ("HIB", "HCL", "HPIV") and k < k_troca)
                if usa_rls:
                    z = phi
                elif metodo == "RIV":
                    z = np.array([i_sim[c], v_ant2[c], v_ant[c]])
                elif metodo in ("PIV", "HPIV"):     # predicao de 1 passo + vetor que o FCS escolheria com ela
                    z = np.array([fila[1][0][c], v_ant2[c], fila[1][1][c]])
                elif metodo in ("CLIV", "HCL"):     # malha fechada: FCS simulado sem ruido
                    z = np.array([i_s[c], vs2[c], vs1[c]])
                else:                   # RIV atrasado (RIV2, ou HIB depois de k_troca)
                    z = np.array([i_sim[c], v_ant2[c], v_ant3[c]])
                Pz = P @ z
                lf = lam if usa_rls else lam_iv
                K = Pz / (lf + phi @ Pz)
                novo = th + K * (im[c] - phi @ th)
                if 0.5 < novo[0] < 0.999 and novo[2] > 0 and novo[1] > 0:   # so aceita modelo fisico
                    th = novo
                    P = (P - np.outer(K, phi @ P)) / lf
        i_sim = th[0] * i_sim + th[1] * v_ant2 + th[2] * v_ant if k > 2 else im.copy()
        # FCS simulado: avanca i_s com os vetores simulados e escolhe o proximo (mesma referencia)
        i_s = th[0] * i_s + th[1] * vs2 + th[2] * vs1 if k > 2 else im.copy()
        # FCS com o modelo atual (custo em k+2, mantendo o vetor novo)
        i1_base = th[0] * im + th[1] * v_ant                       # i(k+1) sem o termo do novo vetor
        t2 = tk + 2 * w * TS
        ref = np.array([rd[k] * np.cos(t2) - rq[k] * np.sin(t2), rd[k] * np.sin(t2) + rq[k] * np.cos(t2)])
        gmin, melhor = 1e30, estado
        for e in range(8):
            v = VET[e]
            i1 = i1_base + th[2] * v
            i2 = th[0] * i1 + (th[1] + th[2]) * v
            g = np.sum((ref - i2) ** 2) + 1e-9 * bin(e ^ estado).count("1")
            if g < gmin:
                gmin, melhor = g, e
        estado = melhor
        v_novo = VET[estado]
        # PIV: predicao de i(k+1) feita agora (sem o ruido de k+1) e o vetor que o FCS escolheria com ela
        i_pred = th[0] * im + th[1] * v_ant + th[2] * v_novo
        t3 = tk + 3 * w * TS
        ref3 = np.array([rd[min(k + 1, M - 1)] * np.cos(t3) - rq[min(k + 1, M - 1)] * np.sin(t3),
                         rd[min(k + 1, M - 1)] * np.sin(t3) + rq[min(k + 1, M - 1)] * np.cos(t3)])
        bp = th[0] * i_pred + th[1] * v_novo
        gh, mh = 1e30, estado
        for e in range(8):
            v = VET[e]
            p2 = th[0] * (bp + th[2] * v) + (th[1] + th[2]) * v
            g = np.sum((ref3 - p2) ** 2) + 1e-9 * bin(e ^ estado).count("1")
            if g < gh:
                gh, mh = g, e
        fila = [(i_pred, VET[mh]), fila[0]]
        bs = th[0] * i_s + th[1] * vs1
        gs, ms = 1e30, est_s
        for e in range(8):
            v = VET[e]
            p2 = th[0] * (bs + th[2] * v) + (th[1] + th[2]) * v
            g = np.sum((ref - p2) ** 2) + 1e-9 * bin(e ^ est_s).count("1")
            if g < gs:
                gs, ms = g, e
        est_s = ms
        vs2, vs1 = vs1, VET[est_s]
        # registro
        c, s = np.cos(tk), np.sin(tk)
        hist["id"][k], hist["iq"][k] = im[0] * c + im[1] * s, -im[0] * s + im[1] * c
        hist["idv"][k], hist["iqv"][k] = i[0] * c + i[1] * s, -i[0] * s + i[1] * c
        hist["R"][k], hist["L"][k] = fisicos(th)
        hist["e"][k] = np.hypot(rd[k] - hist["id"][k], rq[k] - hist["iq"][k])
        # planta: meio periodo com v(k-1), meio com v(k) (troca no topo)
        for j in range(SUB):
            vv = (v_ant if j < SUB // 2 else v_novo) * VDC
            i = af * i + bf * vv
        i_ant = im
        v_ant3, v_ant2, v_ant = v_ant2, v_ant, v_novo
    hist.update(idref=rd, iqref=rq)
    return hist


def erro_rms(x, ini):
    k = np.arange(ini, len(x["e"]))
    return np.sqrt(np.mean(x["e"][k] ** 2)) * 1e3


def regime(x):
    k = np.r_[N + 300:N + 690, N + 900:N + 1190, 2 * N + 300:2 * N + 690, 2 * N + 900:2 * N + 1190]
    ed = (x["idref"][k] - x["idv"][k]).mean() * 1e3
    eq = (x["iqref"][k] - x["iqv"][k]).mean() * 1e3
    rms = np.sqrt(np.mean((x["idref"][k] - x["idv"][k]) ** 2 + (x["iqref"][k] - x["iqv"][k]) ** 2)) * 1e3
    return ed, eq, rms


def main():
    t = np.arange(3 * N) * TS * 1e3
    casos = {
        "fixo correto (25,3 Ω; 9,8 mH)": simula(R, L, False),
        "fixo errado (35 Ω; 14 mH)": simula(35.0, 14e-3, False),
        "fixo errado (18 Ω; 7 mH)": simula(18.0, 7e-3, False),
        "adaptativo RLS": simula(35.0, 14e-3, True, metodo="RLS"),
        "adaptativo RLS, parte de 18 Ω; 7 mH": simula(18.0, 7e-3, True, metodo="RLS"),
        "híbrido RLS → RIV (experimental)": simula(35.0, 14e-3, True, metodo="HIB"),
        "híbrido, parte de 18 Ω; 7 mH": simula(18.0, 7e-3, True, metodo="HIB"),
    }
    sem = simula(35.0, 14e-3, True, ruido=0.0, metodo="RLS")
    print("caso | erro médio d / q [mA] | rms (corrente verdadeira) [mA] | R, L finais")
    for nome, x in casos.items():
        ed, eq, rms = regime(x)
        print(f"  {nome:34s} {ed:+5.1f} / {eq:+4.1f} | {rms:5.1f} | {np.mean(x['R'][-N:]):5.1f} Ω, "
              f"{np.mean(x['L'][-N:]) * 1e3:5.2f} mH")
    print(f"  RLS sem ruído: {np.mean(sem['R'][-N:]):.2f} Ω, {np.mean(sem['L'][-N:]) * 1e3:.2f} mH")
    xa = casos["híbrido RLS → RIV (experimental)"]
    k95 = np.argmax(np.abs(casos["adaptativo RLS"]["R"] - R) < 0.1 * R)
    print(f"  convergência (R a 10 %): {k95 * TS * 1e3:.1f} ms")

    # convergencia de R e L (1 s: a variavel instrumental e lenta)
    P10 = 10
    tl = np.arange(P10 * N) * TS * 1e3
    longos = ((simula(35.0, 14e-3, True, ruido=0.0, metodo="RLS", periodos=P10), CINZA, "RLS, sem ruído"),
              (simula(35.0, 14e-3, True, metodo="RLS", periodos=P10), VERM, "RLS, com ruído"),
              (simula(35.0, 14e-3, True, metodo="HIB", periodos=P10), AZUL, "RLS → var. instrumental (de 35 Ω; 14 mH)"),
              (simula(18.0, 7e-3, True, metodo="HIB", periodos=P10), VERDE, "RLS → var. instrumental (de 18 Ω; 7 mH)"))
    for x, cor, nome in longos:
        print(f"  {nome}: fim {np.mean(x['R'][-N:]):.1f} Ω, {np.mean(x['L'][-N:]) * 1e3:.2f} mH")
    fig, axs = plt.subplots(1, 2, figsize=(17, 6.8))
    for x, cor, nome in longos:
        axs[0].plot(tl, suav(x["R"], 100), color=cor, lw=2.4, label=nome)
        axs[1].plot(tl, suav(x["L"], 100) * 1e3, color=cor, lw=2.4, label=nome)
    axs[0].axhline(R, color="k", ls=":", lw=2.2, label="real")
    axs[1].axhline(L * 1e3, color="k", ls=":", lw=2.2, label="real")
    axs[0].set_ylabel("R estimado [Ω]"); axs[1].set_ylabel("L estimado [mH]")
    axs[0].set_ylim(18, 32); axs[1].set_ylim(3, 14)
    for ax in axs:
        ax.axvline(100, color=CINZA, ls="--", lw=1.2)
        ax.set_xlabel("tempo [ms] (média de 5 ms)"); ax.grid(alpha=0.3); ax.set_xlim(0, tl[-1])
    axs[0].text(105, 31, "troca para a\nvar. instrumental", fontsize=14, va="top", color=CINZA)
    h, l = axs[1].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, loc="lower center", ncol=3, fontsize=16)
    fig.tight_layout(w_pad=3, rect=(0, 0.12, 1, 1)); fig.savefig(IMGS / "rls_convergencia.png", dpi=110); plt.close(fig)

    # erro em regime: fixo errado x adaptativo
    fig, axs = plt.subplots(1, 2, figsize=(17, 6.8), sharey=True)
    j = slice(2 * N + 100, 2 * N + 700)
    tt = t[j] - t[2 * N]
    for ax, (nomes, tit) in zip(axs, ((("fixo errado (35 Ω; 14 mH)", "fixo errado (18 Ω; 7 mH)"), "modelo fixo errado"),
                                      (("adaptativo RLS", "fixo correto (25,3 Ω; 9,8 mH)"), "adaptativo (RLS) × modelo certo"))):
        for nome, cor in zip(nomes, (VERM, AZUL) if "fixo errado" in nomes[0] else (AZUL, "k")):
            x = casos[nome]
            ax.plot(tt, suav(x["idv"])[j] * 1e3, color=cor, lw=2.6, label=nome + " (média 1 ms)")
            ax.plot(tt, x["idv"][j] * 1e3, color=cor, lw=0.6, alpha=0.35)
        ax.step(tt, casos[nomes[0]]["idref"][j] * 1e3, where="post", color="#C8A400", lw=2, label="referência")
        ax.set_title(tit); ax.set_xlabel("tempo [ms]"); ax.grid(alpha=0.3)
        ax.legend(frameon=False, loc="upper right", fontsize=15)
    axs[0].set_ylabel("$i_d$ [mA]")
    fig.tight_layout(w_pad=3); fig.savefig(IMGS / "rls_desempenho.png", dpi=110); plt.close(fig)


def suav(v, n=20):
    return np.convolve(np.pad(v, (n // 2, n - 1 - n // 2), mode="edge"), np.ones(n) / n, mode="valid")


if __name__ == "__main__":
    main()
