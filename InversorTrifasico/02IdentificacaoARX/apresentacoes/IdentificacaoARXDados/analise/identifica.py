"""Identificacao ARX com os dados do ensaio VSI02IdentificacaoARX (PRBS em vd e vq).

Le a matriz Dados3F exportada do CCS (../../../dados/Dados01A.csv). O Graph -
Time do CCS exporta no maximo 16383 valores: as linhas 8 a 11 (vd, vq, id, iq)
podem faltar. Nesse caso:
  - vd e vq sao reconstruidas (sao a PRBS conhecida: 5 +- 3 V e 0 +- 3 V) e
    conferidas com as amostras que vieram e com as razoes ciclicas;
  - id e iq sao calculadas das correntes ABC (ultimo periodo, sem media).
Antes, corrige-se o salto entre as amostras do zero e do topo do contador: com o
neutro isolado iA + iB + iC = 0, e a regressao da soma medida sobre "fase usou o
topo" da o salto de cada fase (sem usar modelo nenhum).

Depois confere os dados, estima a resposta ao impulso (FIR) e compara estruturas
ARX por eixo:

  SISO   y(k) = a1 y(k-1) [+ a2 y(k-2)] + b1 u(k-nk) [+ b2 u(k-nk-1)]
         (so o eixo proprio: vira funcao de transferencia)
  MIMO   + c y_outro(k-1) [+ e u_outro(k-nk)]  (regressores dos dois eixos)

com atrasos nk = 1, 2 e 3, estimadas por minimos quadrados (LS). A variavel
instrumental (IV, saida simulada do modelo como instrumento) continua em estima(),
mas nao e usada: com a media de 16 periodos o ruido e pequeno e LS = IV (2026-11-08).
Para voltar a usar, METODOS = ("LS", "IV") e METODO = "IV". Validacao cruzada:
estima numa metade do registro e simula livremente (so com vd, vq) na outra,
nos dois sentidos.

Gera as figuras em ../imgs/ e imprime os numeros dos slides.
Uso: python3 identifica.py
"""

from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[3] / "01MalhaAberta/apresentacoes/EnsaioMalhaAberta" / "analise"))
from figuras import le_csv_ccs                                    # noqa: E402

ARQUIVO = AQUI.parents[2] / "dados" / "Dados01A.csv"
IMGS = AQUI.parent / "imgs"
IMGS.mkdir(exist_ok=True)

COR_A, COR_B, COR_C = "#1F5FBF", "#D62828", "#2A9D3A"
COR_ACENTO, COR_AMARELO, COR_CINZA = "#4A6FA5", "#E8C547", "#6C757D"
plt.rcParams.update({"font.size": 17, "axes.titlesize": 17, "axes.labelsize": 17,
                     "xtick.labelsize": 15, "ytick.labelsize": 15, "legend.fontsize": 15,
                     "font.family": "sans-serif", "axes.spines.top": False,
                     "axes.spines.right": False})

METODO = "LS"                  # estimador usado nos resultados ("IV" = variavel instrumental)
METODOS = ("LS",)              # estimadores comparados nas figuras/tabelas
COR_MET = {"LS": COR_A, "IV": COR_B}

TS, F = 50e-6, 60.0
R_NOM, L_NOM = 25.0, 10e-3
W = 2 * np.pi * F
EIXOS = ("d", "q")
OUTRO = {"d": "q", "q": "d"}

# Estruturas: na, nb, nk, cruz_y (y do outro eixo), cruz_u (u do outro eixo)
ESTRUTURAS = [
    ("SISO 1,1,1", dict(na=1, nb=1, nk=1, cy=False, cu=False)),
    ("SISO 1,1,2", dict(na=1, nb=1, nk=2, cy=False, cu=False)),
    ("SISO 1,1,3", dict(na=1, nb=1, nk=3, cy=False, cu=False)),
    ("SISO 1,2,2", dict(na=1, nb=2, nk=2, cy=False, cu=False)),
    ("SISO 2,2,2", dict(na=2, nb=2, nk=2, cy=False, cu=False)),
    ("MIMO 1,1,2", dict(na=1, nb=1, nk=2, cy=True, cu=True)),
    ("MIMO 1,1,3", dict(na=1, nb=1, nk=3, cy=True, cu=True)),
    ("MIMO 1,2,2", dict(na=1, nb=2, nk=2, cy=True, cu=True)),
    ("MIMO 1,2,2 sem e", dict(na=1, nb=2, nk=2, cy=True, cu=False)),
]

# Ordem 2 sem acoplamento (so o eixo proprio), comparada com a SISO 1,2,2
ORDEM2 = [("SISO 1,2,2", dict(na=1, nb=2, nk=2, cy=False, cu=False))] + [
    (f"SISO 2,{nb},{nk}", dict(na=2, nb=nb, nk=nk, cy=False, cu=False))
    for nb, nk in ((1, 1), (2, 1), (1, 2), (2, 2), (3, 2), (2, 3))]


# ---------------------------------------------------------------------------
# Canais da matriz Dados3F[12][2044] do firmware (uma linha por canal): o
# essencial vem primeiro, porque o Graph do CCS exporta so 16383 valores.
CANAIS = ("vd", "vq", "id", "iq", "iA", "iB", "iC", "th")
# (ate o ensaio de 2026-11-08 a matriz tinha mais 4 linhas: Vdc, dA, dB, dC; as
# linhas 0-7 sao as mesmas, entao o Dados01A.csv tambem e lido assim)
N_DADOS3F = 2044


def le_dados3f(caminho):
    """Matriz Dados3F exportada do CCS, num arquivo so:
    .csv  Graph - Time com a expressao Dados3F (8 x 2044 = 16352 floats seguidos);
    .bin  Save Memory em binario (floats de 32 bits, little endian);
    .dat  Save Memory em TI Data (cabecalho 1651 e um hexadecimal por linha, de 16 ou 32 bits)."""
    caminho = Path(caminho)
    sufixo = caminho.suffix.lower()
    if sufixo == ".csv":
        # usa a numeracao (Sample) para por cada valor na sua posicao da matriz:
        # o CCS pode exportar so um trecho, e "undefined" onde nao leu
        x = np.full(len(CANAIS) * N_DADOS3F, np.nan)
        for linha_csv in caminho.read_text().splitlines()[2:]:
            campos = linha_csv.split(",")
            if len(campos) > 1 and campos[1] not in ("", "undefined"):
                k = int(campos[0])
                if k < len(x):
                    x[k] = float(campos[1])
    elif sufixo == ".bin":
        x = np.frombuffer(caminho.read_bytes(), dtype="<f4")
    else:
        palavras = caminho.read_text().split()
        if palavras[0] == "1651":
            palavras = palavras[5:]
        valores = [int(p, 16) for p in palavras if p.lower().startswith("0x")]
        tipo = "<u4" if len(palavras[0]) > 6 else "<u2"
        x = np.array(valores, dtype=tipo).view("<f4")
    x = np.asarray(x, dtype=float)
    s = {"N": N_DADOS3F, "faltam": [], "vd_parcial": None}
    s["parciais"] = {}
    for k, c in enumerate(CANAIS):
        linha_k = x[k * N_DADOS3F:(k + 1) * N_DADOS3F]
        if len(linha_k) == N_DADOS3F and not np.isnan(linha_k).any():
            s[c] = linha_k
        else:
            s["faltam"].append(c)
            if len(linha_k) and not np.isnan(linha_k).all():
                s["parciais"][c] = linha_k[~np.isnan(linha_k)]
    s["vd_parcial"] = s["parciais"].get("vd")
    return s


VD0, VQ0, DV_PRBS = 5.0, 0.0, 3.0      # padroes do firmware (tensaoD0, tensaoQ0, amplitudePRBS)


def prbs(tap, n=511, semente=0x1FF):
    r, saida = semente, []
    for _ in range(n):
        bit = ((r >> 8) ^ (r >> tap)) & 1
        r = ((r << 1) | bit) & 0x1FF
        saida.append(1.0 if r & 1 else -1.0)
    return np.array(saida)


def park(ia, ib, ic, th):
    al = (2 * ia - ib - ic) / 3
    be = (ib - ic) / np.sqrt(3)
    return al * np.cos(th) + be * np.sin(th), -al * np.sin(th) + be * np.cos(th)


def corrige_salto(s):
    """Salto entre as amostras do topo e do zero: regressao da soma iA+iB+iC
    (que deveria ser nula) sobre 'fase usou o topo' (razao em vigor < 0,5)."""
    N = s["N"]
    I = np.vstack([s["iA"], s["iB"], s["iC"]])
    D = np.vstack([s["dA"], s["dB"], s["dC"]])
    topo = np.vstack([np.r_[D[f, 0], D[f, :-1]] < 0.5 for f in range(3)]).astype(float)
    soma = I.sum(axis=0)
    M = np.column_stack([np.ones(N), topo[0], topo[1], topo[2]])
    p, *_ = np.linalg.lstsq(M, soma, rcond=None)
    Ic = I - np.vstack([p[0] / 3 + p[1 + f] * topo[f] for f in range(3)])
    return Ic, dict(constante=p[0], salto=p[1:], topo=topo, soma=soma, soma_corr=Ic.sum(axis=0))


def carrega(arquivo=ARQUIVO):
    """Le a matriz Dados3F, reconstroi o que faltar e corrige o salto zero/topo."""
    s = le_dados3f(arquivo)
    N = s["N"]
    s["vd_rec"] = "vd" in s["faltam"]
    if s["vd_rec"]:
        s["vd"] = VD0 + DV_PRBS * np.repeat(prbs(4), N // 511)
        s["vq"] = VQ0 + DV_PRBS * np.repeat(prbs(3), N // 511)
        if s["vd_parcial"] is not None:
            n = len(s["vd_parcial"])
            s["vd_confere"] = (n, bool(np.allclose(s["vd"][:n], s["vd_parcial"])))
    if "vdc" not in s:
        # barramento quase constante: media das amostras que vieram
        p = s["parciais"].get("vdc")
        s["vdc"] = np.full(N, p.mean() if p is not None else 19.85)
    if "dA" not in s:
        # razoes (nao gravadas): recalculadas de vd, vq, angulo e Vdc
        vdc = s["vdc"]
        al = s["vd"] * np.cos(s["th"]) - s["vq"] * np.sin(s["th"])
        be = s["vd"] * np.sin(s["th"]) + s["vq"] * np.cos(s["th"])
        v = (al, -0.5 * al + np.sqrt(3) / 2 * be, -0.5 * al - np.sqrt(3) / 2 * be)
        s["dA"], s["dB"], s["dC"] = (np.clip(0.5 + x_ / vdc, 0.05, 0.95) for x_ in v)
    # tensao aplicada (razao x Vdc) em dq, para conferir as entradas
    D = np.vstack([s["dA"], s["dB"], s["dC"]])
    vn = (D - D.mean(axis=0)) * s["vdc"]
    s["vd_ap"], s["vq_ap"] = park(vn[0], vn[1], vn[2], s["th"])
    s["iA_bruta"], s["iB_bruta"], s["iC_bruta"] = s["iA"], s["iB"], s["iC"]
    Ic, s["salto"] = corrige_salto(s)
    s["iA"], s["iB"], s["iC"] = Ic
    s["id_bruta"], s["iq_bruta"] = park(s["iA_bruta"], s["iB_bruta"], s["iC_bruta"], s["th"])
    s["id_rec"] = "id" in s["faltam"]
    if s["id_rec"]:
        # id, iq com media nao exportadas: Park das correntes ABC corrigidas (ultimo periodo)
        s["id"], s["iq"] = park(Ic[0], Ic[1], Ic[2], s["th"])
    return s


def desvios(s):
    y = {"d": s["id"] - s["id"].mean(), "q": s["iq"] - s["iq"].mean()}
    u = {"d": s["vd"] - s["vd"].mean(), "q": s["vq"] - s["vq"].mean()}
    return y, u


def kmin(e):
    return max(e["na"], e["nk"] + e["nb"] - 1, 1)


def linha(o, k, e, ys, u):
    """Regressores do eixo o na amostra k; ys fornece as saidas passadas."""
    p = OUTRO[o]
    r = [ys[o][k - i] for i in range(1, e["na"] + 1)]
    r += [u[o][k - e["nk"] - j] for j in range(e["nb"])]
    if e["cu"]:
        r += [u[p][k - e["nk"] - j] for j in range(e["nb"])]
    if e["cy"]:
        r += [ys[p][k - 1]]
    return r


def matriz(o, ks, e, ys, u):
    return np.array([linha(o, k, e, ys, u) for k in ks])


def simula(theta, e, y, u, ini, fim):
    """Simulacao livre entre ini e fim (comeca com as medidas nas primeiras amostras)."""
    ys = {o: y[o].copy() for o in EIXOS}
    for k in range(ini + kmin(e), fim):
        for o in EIXOS:
            ys[o][k] = np.dot(theta[o], linha(o, k, e, ys, u))
    return ys


def estima(e, y, u, ini, fim, metodo="LS"):
    ks = np.arange(ini + kmin(e), fim)
    theta = {}
    for o in EIXOS:
        Phi = matriz(o, ks, e, y, u)
        theta[o], *_ = np.linalg.lstsq(Phi, y[o][ks], rcond=None)
    if metodo == "IV":
        for _ in range(4):
            ys = simula(theta, e, y, u, ini, fim)
            novo = {}
            for o in EIXOS:
                Phi = matriz(o, ks, e, y, u)
                Z = matriz(o, ks, e, ys, u)
                novo[o] = np.linalg.solve(Z.T @ Phi, Z.T @ y[o][ks])
            if not all(estavel(novo[o], e) for o in EIXOS):
                break                               # IV instavel: fica com a ultima estimativa
            theta = novo
    return theta


def estavel(th, e):
    a = th[:e["na"]]
    return bool(np.all(np.isfinite(th)) and np.all(np.abs(np.roots(np.r_[1, -a])) < 1))


def ajuste(theta, e, y, u, ini, fim, descarte=40):
    ys = simula(theta, e, y, u, ini, fim)
    k = slice(ini + descarte, fim)
    return {o: 100 * (1 - np.linalg.norm(y[o][k] - ys[o][k]) / np.linalg.norm(y[o][k] - y[o][k].mean()))
            for o in EIXOS}


def fisicos(th, e):
    """Polo dominante, ganho estatico, R e L equivalentes (ordem 1 no proprio eixo)."""
    a = th[:e["na"]]
    b = th[e["na"]:e["na"] + e["nb"]]
    polos = np.roots(np.r_[1, -a]) if e["na"] > 1 else np.array([a[0]])
    ganho = b.sum() / (1 - a.sum())
    pd = np.max(np.abs(polos))
    R = 1 / ganho
    L = -R * TS / np.log(pd) if 0 < pd < 1 else np.nan
    return pd, ganho, R, L


def aic(theta, e, y, u, ini, fim):
    ks = np.arange(ini + kmin(e), fim)
    v = 0.0
    p = 0
    for o in EIXOS:
        res = y[o][ks] - matriz(o, ks, e, y, u) @ theta[o]
        v += np.log(np.mean(res ** 2))
        p += len(theta[o])
    return len(ks) * v / 2 + 2 * p / 2


# ---------------------------------------------------------------------------
def fir(y, u, n=40):
    k = np.arange(n, len(y["d"]))
    h = {}
    for o in EIXOS:
        p = OUTRO[o]
        Phi = np.column_stack([u[o][k - j] for j in range(n)] + [u[p][k - j] for j in range(n)])
        c, *_ = np.linalg.lstsq(Phi, y[o][k], rcond=None)
        h[o] = (c[:n], c[n:])
    return h


def fig_dados(s, t_max=15.0, arquivo="dados.png", lw=2.2):
    """Tensoes a esquerda (dq e fases), correntes a direita (dq e fases); 15 ms."""
    t = np.arange(s["N"]) * TS * 1e3
    j = t <= t_max
    D = np.vstack([s["dA"], s["dB"], s["dC"]])
    vf = (D - D.mean(axis=0)) * s["vdc"]          # tensao de fase aplicada (media no periodo)
    fig, axs = plt.subplots(2, 2, figsize=(17, 8.5), sharex=True)
    abc = (COR_A, COR_B, COR_C)
    axs[0, 0].step(t[j], s["vd"][j], color=COR_A, lw=lw, where="post", label="$v_d$")
    axs[0, 0].step(t[j], s["vq"][j], color=COR_B, lw=lw, where="post", label="$v_q$")
    axs[0, 0].set_ylabel("tensão dq [V]")
    for f, cor, nome in zip(range(3), abc, ("$v_A$", "$v_B$", "$v_C$")):
        axs[1, 0].step(t[j], vf[f][j], color=cor, lw=lw * 0.8, where="post", label=nome)
    axs[1, 0].set_ylabel("tensão de fase [V]")
    axs[0, 1].plot(t[j], s["id"][j], color=COR_A, lw=lw, label="$i_d$")
    axs[0, 1].plot(t[j], s["iq"][j], color=COR_B, lw=lw, label="$i_q$")
    axs[0, 1].set_ylabel("corrente dq [A]")
    for x, cor, nome in zip((s["iA"], s["iB"], s["iC"]), abc, ("$i_A$", "$i_B$", "$i_C$")):
        axs[1, 1].plot(t[j], x[j], color=cor, lw=lw * 0.8, label=nome)
    axs[1, 1].set_ylabel("corrente de fase [A]")
    for ax, nc in zip(axs.flat, (2, 2, 3, 3)):
        ax.margins(x=0, y=0.08)
        ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 0.98), ncol=nc,
                  borderaxespad=0, handlelength=1.5, fontsize=19)
        ax.grid(alpha=0.3)
    for ax in axs.flat:
        ax.tick_params(labelsize=18)
        ax.yaxis.label.set_size(20)
        ax.xaxis.label.set_size(20)
    for ax in axs[1]:
        ax.set_xlabel("tempo [ms]")
    fig.tight_layout(w_pad=4)
    fig.savefig(IMGS / arquivo, dpi=110)
    plt.close(fig)


def fig_prbs_corr(y, u, h, n=16):
    """PRBS como ruido branco: autocorrelacao da entrada e resposta ao impulso por correlacao
    (h = Ryu/Ruu(0), valida so se a entrada fosse branca) contra o FIR por minimos quadrados."""
    ud, yd = u["d"], y["d"]
    N = len(ud)
    def xcorr(a, b):                                   # correlacao circular (registro = 1 periodo)
        return np.real(np.fft.ifft(np.conj(np.fft.fft(a)) * np.fft.fft(b))) / N
    ruu = xcorr(ud, ud)
    ryu = xcorr(ud, yd)
    lag = np.arange(-12, 13)
    fig, axs = plt.subplots(1, 2, figsize=(15, 5.5))
    ax = axs[0]
    ml, sl, bl = ax.stem(lag, ruu[lag] / ruu[0], linefmt=COR_A, markerfmt="o", basefmt=" ")
    plt.setp(ml, color=COR_A, markersize=8)
    plt.setp(sl, linewidth=2.5)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("deslocamento [amostras]")
    ax.set_ylabel("autocorrelação de $v_d$ (normalizada)")
    ax.set_title("PRBS com bit de 4 amostras")
    ax.grid(alpha=0.3)
    ax = axs[1]
    k = np.arange(n)
    ax.plot(k - 0.12, ryu[:n] / ruu[0] * 1e3, "s", color=COR_CINZA, ms=9, label="correlação $R_{vi}/R_{vv}(0)$")
    ml, sl, bl = ax.stem(k + 0.12, h["d"][0][:n] * 1e3, linefmt=COR_A, markerfmt="o", basefmt=" ",
                         label="mínimos quadrados (FIR)")
    plt.setp(ml, color=COR_A, markersize=9)
    plt.setp(sl, linewidth=2.5)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(k[::2])
    ax.set_xlabel("atraso [amostras]")
    ax.set_ylabel("$v_d \\to i_d$ [mA/V]")
    ax.set_title("resposta ao impulso")
    ax.legend(frameon=False, loc="upper right")
    ax.grid(alpha=0.3)
    fig.tight_layout(w_pad=3)
    fig.savefig(IMGS / "prbs_corr.png", dpi=110)
    plt.close(fig)


def fig_fir(h, n=16, th_siso=None):
    """Resposta ao impulso estimada (FIR por minimos quadrados) em hastes."""
    a = np.exp(-R_NOM * TS / L_NOM)
    k = np.arange(n)
    teo = np.where(k >= 2, (1 - a) / R_NOM * a ** np.clip(k - 2, 0, None), 0.0)
    fig, ax = plt.subplots(figsize=(14, 5.5))
    for o, cor, dx, nome in (("d", COR_A, -0.12, "$v_d \\to i_d$"), ("q", COR_C, 0.12, "$v_q \\to i_q$")):
        ml, sl, bl = ax.stem(k + dx, h[o][0][:n] * 1e3, linefmt=cor, markerfmt="o", basefmt=" ", label=nome)
        plt.setp(ml, color=cor, markersize=9)
        plt.setp(sl, linewidth=2.5)
    ax.plot(k, teo * 1e3, "o", color=COR_B, ms=10, ls="none", label="RL nominal, atraso 2")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(k)
    ax.set_xlabel("atraso [amostras de 50 µs]")
    ax.set_ylabel("resposta ao impulso [mA/V]")
    ax.legend(frameon=False, loc="upper right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "fir.png", dpi=110)
    plt.close(fig)


def fig_ajustes(tab):
    nomes = [n for n, _ in ESTRUTURAS]
    x = np.arange(len(nomes))
    fig, axs = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    for ax, o in zip(axs, EIXOS):
        w = 0.8 / len(METODOS)
        for i_, met in enumerate(METODOS):
            desl = (i_ - (len(METODOS) - 1) / 2) * w
            ax.bar(x + desl, [tab[n][met]["fit"][o] for n in nomes], width=w, color=COR_MET[met], label=met)
        ax.set_xticks(x)
        ax.set_xticklabels(nomes, rotation=55, ha="right")
        ax.set_title(f"eixo {o}: FIT na validação")
        ax.set_ylim(50, 100)
        ax.grid(alpha=0.3, axis="y")
    axs[0].set_ylabel("FIT [%]")
    if len(METODOS) > 1:
        axs[0].legend(frameon=False, loc="upper left", ncol=2)
    fig.tight_layout()
    fig.savefig(IMGS / "ajustes.png", dpi=110)
    plt.close(fig)


def fig_validacao(theta, e, y, u, N, titulo_arq, t0=60.0, dt=8.0):
    """Medida x simulacao livre na 2a metade (nao usada na estimacao); janela curta, fontes grandes."""
    meio = N // 2
    ys = simula(theta, e, y, u, meio, N)
    t = np.arange(N) * TS * 1e3
    j = (t >= t0) & (t <= t0 + dt)
    fig, axs = plt.subplots(2, 1, figsize=(9.5, 8.6), sharex=True)
    for ax, o, cor in zip(axs, EIXOS, (COR_A, COR_C)):
        ax.plot(t[j], y[o][j] * 1e3, "o", color=COR_B, ms=6, label="medida")
        ax.plot(t[j], ys[o][j] * 1e3, color=cor, lw=2.8, label="modelo")
        ax.set_ylabel(f"$i_{o}$ − média [mA]", fontsize=21)
        ax.tick_params(labelsize=18)
        ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 0.98), ncol=2, fontsize=19,
                  borderaxespad=0)
        ax.grid(alpha=0.3)
        ax.margins(x=0)
    axs[1].set_xlabel("tempo [ms]", fontsize=21)
    fig.tight_layout(h_pad=2.5)
    fig.savefig(IMGS / titulo_arq, dpi=110)
    plt.close(fig)


def fig_residuos(theta, e, y, u, N):
    ks = np.arange(kmin(e), N)
    fig, axs = plt.subplots(1, 2, figsize=(14, 5))
    lim = 1.96 / np.sqrt(len(ks))
    for ax, o, cor in zip(axs, EIXOS, (COR_A, COR_C)):
        res = y[o][ks] - matriz(o, ks, e, y, u) @ theta[o]
        res = res - res.mean()
        lags = np.arange(0, 21)
        ac = [np.dot(res[:len(res) - L], res[L:]) / np.dot(res, res) for L in lags]
        uu = u[o][ks] - u[o][ks].mean()
        xc = [np.dot(uu[:len(uu) - L], res[L:]) / np.sqrt(np.dot(uu, uu) * np.dot(res, res)) for L in lags]
        ax.stem(lags, ac, linefmt=cor, markerfmt="o", basefmt=" ", label="autocorrelação do resíduo")
        ax.plot(lags, xc, "s", color=COR_B, ms=6, label=f"correlação $v_{o}$ × resíduo")
        ax.axhspan(-lim, lim, color=COR_AMARELO, alpha=0.3)
        ax.set_ylim(-0.6, 1.05)
        print(f"residuo eixo {o}: autocorrelacao no atraso 1 = {ac[1]:.3f}")
        ax.set_xlabel("atraso [amostras]")
        ax.set_title(f"eixo {o}: resíduo de 1 passo (desvio {res.std() * 1e3:.1f} mA)")
        ax.legend(frameon=False, loc="upper right")
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "residuos.png", dpi=110)
    plt.close(fig)


def fig_bode(theta, e, rot):
    f = np.logspace(1, np.log10(9e3), 300)
    z = np.exp(1j * 2 * np.pi * f * TS)
    a_nom = np.exp(-R_NOM * TS / L_NOM)
    Gn = (1 - a_nom) / R_NOM * z ** -2 / (1 - a_nom / z)
    fig, axs = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    curvas = [(Gn, COR_CINZA, "RL nominal, atraso 2", "--")]
    for o, cor in zip(EIXOS, (COR_A, COR_C)):
        th = theta[o]
        a = th[:e["na"]]
        b = th[e["na"]:e["na"] + e["nb"]]
        num = sum(b[j] * z ** -(e["nk"] + j) for j in range(e["nb"]))
        den = 1 - sum(a[i] * z ** -(i + 1) for i in range(e["na"]))
        curvas.append((num / den, cor, f"identificado, eixo {o} ({rot})", "-"))
    for G, cor, nome, ls in curvas:
        axs[0].semilogx(f, 20 * np.log10(np.abs(G) * R_NOM), color=cor, lw=2, ls=ls, label=nome)
        axs[1].semilogx(f, np.degrees(np.unwrap(np.angle(G))), color=cor, lw=2, ls=ls)
    axs[0].set_ylabel("|G|·25 Ω [dB]")
    axs[0].legend(frameon=False, loc="lower left")
    axs[1].set_ylabel("fase [°]")
    axs[1].set_xlabel("frequência [Hz]")
    for ax in axs:
        ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(IMGS / "bode.png", dpi=110)
    plt.close(fig)


def matriz_tf(th, z):
    """G(z) 2x2 do MIMO 1,2,2: [Id; Iq] = A(z)^-1 B(z) [Vd; Vq], th[o] = [a, b1, b2, e1, e2, c]."""
    zi = 1 / z
    A = np.array([[1 - th["d"][0] * zi, -th["d"][5] * zi], [-th["q"][5] * zi, 1 - th["q"][0] * zi]])
    B = np.array([[th["d"][1] * zi**2 + th["d"][2] * zi**3, th["d"][3] * zi**2 + th["d"][4] * zi**3],
                  [th["q"][3] * zi**2 + th["q"][4] * zi**3, th["q"][1] * zi**2 + th["q"][2] * zi**3]])
    A = np.moveaxis(A, -1, 0)
    B = np.moveaxis(B, -1, 0)
    return np.linalg.solve(A, B)                 # [f, 2, 2]


def fig_matriz(th_mimo, th_siso):
    f = np.logspace(1, np.log10(9e3), 300)
    z = np.exp(1j * 2 * np.pi * f * TS)
    G = matriz_tf(th_mimo, z)
    a, b1, b2 = th_siso["d"]
    Gs = (b1 * z**-2 + b2 * z**-3) / (1 - a / z)
    db = lambda x: 20 * np.log10(np.abs(x) * 1e3)
    fig, ax = plt.subplots(figsize=(9.5, 8.2))
    ax.semilogx(f, db(G[:, 0, 0]), color=COR_A, lw=3, label="$G_{dd}$ (MIMO)")
    ax.semilogx(f, db(G[:, 1, 1]), color=COR_C, lw=2, ls=":", label="$G_{qq}$ (MIMO)")
    ax.semilogx(f, db(Gs), color=COR_CINZA, lw=2, ls="--", label="$G_d$ (SISO 1,2,2)")
    ax.semilogx(f, db(G[:, 0, 1]), color=COR_B, lw=3, label="$G_{dq}$ (MIMO)")
    ax.semilogx(f, db(G[:, 1, 0]), color=COR_AMARELO, lw=2, ls=":", label="$G_{qd}$ (MIMO)")
    ax.set_xlabel("frequência [Hz]")
    ax.set_ylabel("|G| [dB, ref. 1 mA/V]")
    ax.legend(frameon=False, loc="lower left", fontsize=18)
    ax.tick_params(labelsize=18)
    ax.xaxis.label.set_size(21)
    ax.yaxis.label.set_size(21)
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(IMGS / "matriz_tf.png", dpi=110)
    plt.close(fig)
    den = np.polymul([1, -th_mimo["d"][0]], [1, -th_mimo["q"][0]]) - np.r_[0, 0, th_mimo["d"][5] * th_mimo["q"][5]]
    print("MIMO: polos", np.round(np.roots(den), 4), "| |Gdq/Gdd| em 10 Hz:",
          round(abs(G[0, 0, 1] / G[0, 0, 0]), 3), "| ganho estatico Gdd, Gs [mA/V]:",
          round(abs(matriz_tf(th_mimo, np.array([1.0 + 0j]))[0, 0, 0]) * 1e3, 2), round(abs((b1 + b2) / (1 - a)) * 1e3, 2))


def fig_media(s):
    """id com media sincrona (16 periodos) x id de um periodo so (Park das correntes ABC)."""
    t = np.arange(s["N"]) * TS * 1e3
    j = (t >= 40) & (t <= 55)
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(t[j], s["id_bruta"][j], ".", color=COR_CINZA, ms=5, label="um período (correntes ABC)")
    ax.plot(t[j], s["id"][j], color=COR_A, lw=2, label="média de 16 períodos")
    ax.set_xlabel("tempo dentro do período da PRBS [ms]")
    ax.set_ylabel("$i_d$ [A]")
    ax.set_ylim(0.0, 0.4)
    ax.legend(frameon=False, loc="upper right", ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "media.png", dpi=110)
    plt.close(fig)


def ordem2(y, u, N):
    """Ajuste na validacao e polos da familia de ordem 2 sem acoplamento."""
    meio = N // 2
    res = []
    for nome, e in ORDEM2:
        for met in METODOS:
            f1 = ajuste(estima(e, y, u, 0, meio, met), e, y, u, meio, N)
            f2 = ajuste(estima(e, y, u, meio, N, met), e, y, u, 0, meio)
            th = estima(e, y, u, 0, N, met)
            polos = {o: np.roots(np.r_[1, -th[o][:e["na"]]]) for o in EIXOS}
            zeros = {o: np.roots(th[o][e["na"]:e["na"] + e["nb"]]) if e["nb"] > 1 else np.array([])
                     for o in EIXOS}
            R = {o: fisicos(th[o], e)[2] for o in EIXOS}
            res.append(dict(nome=nome, met=met, fit={o: (f1[o] + f2[o]) / 2 for o in EIXOS},
                            polos=polos, zeros=zeros, R=R, aic=aic(th, e, y, u, 0, N)))

    fig, axs = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1.3, 1]})
    nomes = [n for n, _ in ORDEM2]
    x = np.arange(len(nomes))
    w = 0.8 / len(METODOS)
    for i_, met in enumerate(METODOS):
        desl = (i_ - (len(METODOS) - 1) / 2) * w
        v = [np.mean(list(r["fit"].values())) for r in res if r["met"] == met]
        axs[0].bar(x + desl, v, width=w, color=COR_MET[met], label=met)
    axs[0].set_xticks(x)
    axs[0].set_xticklabels(nomes, rotation=45, ha="right")
    axs[0].set_ylim(60, 100)
    axs[0].set_ylabel("FIT na validação, média d e q [%]")
    if len(METODOS) > 1:
        axs[0].legend(frameon=False, loc="upper right", ncol=2)
    axs[0].grid(alpha=0.3, axis="y")
    ax = axs[1]
    for r in res:
        if not r["nome"].startswith("SISO 2"):
            continue
        cor = COR_MET[r["met"]]
        for o, mk in (("d", "o"), ("q", "s")):
            p = r["polos"][o]
            ax.plot(p.real, p.imag, mk, color=cor, ms=9, alpha=0.75, mfc="none" if o == "q" else cor)
    ax.axvline(0, color=COR_CINZA, lw=0.8)
    ax.axhline(0, color=COR_CINZA, lw=0.8)
    ax.axvspan(0.86, 0.89, color=COR_AMARELO, alpha=0.4)
    ax.text(0.875, 0.27, "polo do\nindutor", ha="center")
    ax.set_xlim(-1, 1)
    ax.set_ylim(-0.35, 0.35)
    ax.set_xlabel("parte real")
    ax.set_ylabel("parte imaginária")
    ax.set_title("polos das estruturas de ordem 2")
    if len(METODOS) > 1:
        for met in METODOS:
            ax.plot([], [], "o", color=COR_MET[met], label=met)
    ax.plot([], [], "o", color=COR_CINZA, label="eixo d")
    ax.plot([], [], "s", color=COR_CINZA, mfc="none", label="eixo q")
    ax.legend(frameon=False, loc="lower left", ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMGS / "ordem2.png", dpi=110)
    plt.close(fig)

    print("\nordem 2 sem acoplamento:")
    for r in res:
        print(f"  {r['nome']:11s} {r['met']} ajuste {r['fit']['d']:5.1f}/{r['fit']['q']:5.1f} AIC {r['aic']:7.0f} | " +
              " | ".join(f"{o}: polos {np.round(r['polos'][o].real, 3)} zeros {np.round(r['zeros'][o], 3)} "
                         f"R {r['R'][o]:.1f}" for o in EIXOS))


# ---------------------------------------------------------------------------
def main():
    s = carrega()
    N = s["N"]
    y, u = desvios(s)

    # conferencias
    print(f"N = {N}; Vdc media {s['vdc'].mean():.2f} V; canais que faltam: {s['faltam']}")
    if s["vd_rec"]:
        print("vd, vq reconstruidas da PRBS; confere com as amostras de vd que vieram:", s.get("vd_confere"))
    print("vd aplicada (razoes) - usada: rms %.4f V | vq: %.4f V" %
          (np.std(s["vd_ap"] - s["vd"]), np.std(s["vq_ap"] - s["vq"])))
    sal = s["salto"]
    print(f"iA+iB+iC: media {sal['soma'].mean() * 1e3:.1f} mA, rms {sal['soma'].std() * 1e3:.1f} mA (medida) -> "
          f"media {sal['soma_corr'].mean() * 1e3:.1f}, rms {sal['soma_corr'].std() * 1e3:.1f} mA (corrigida)")
    print("constante %.1f mA; salto topo-zero por fase [mA]: %s" %
          (sal["constante"] * 1e3, np.round(sal["salto"] * 1e3, 1)))
    print(f"id media {s['id'].mean():.4f} (bruta {s['id_bruta'].mean():.4f}), iq media {s['iq'].mean():.4f}")
    print("razao: %.3f a %.3f" % (min(s["dA"].min(), s["dB"].min(), s["dC"].min()),
                                  max(s["dA"].max(), s["dB"].max(), s["dC"].max())))

    h = fir(y, u)
    np.set_printoptions(precision=2, suppress=True)
    for o in EIXOS:
        print(f"FIR v{o}->i{o} [mA/V]:", h[o][0] * 1e3)
        print(f"FIR v{OUTRO[o]}->i{o} [mA/V]:", h[o][1] * 1e3)

    meio = N // 2
    tab = {}
    print("\nestrutura           met  fit_d  fit_q   (media das duas metades) | parametros (registro inteiro)")
    for nome, e in ESTRUTURAS:
        tab[nome] = {}
        for met in METODOS:
            f1 = ajuste(estima(e, y, u, 0, meio, met), e, y, u, meio, N)
            f2 = ajuste(estima(e, y, u, meio, N, met), e, y, u, 0, meio)
            fit = {o: (f1[o] + f2[o]) / 2 for o in EIXOS}
            th = estima(e, y, u, 0, N, met)
            fis = {o: fisicos(th[o], e) for o in EIXOS}
            tab[nome][met] = dict(fit=fit, theta=th, fis=fis, aic=aic(th, e, y, u, 0, N))
            print(f"{nome:18s} {met}  {fit['d']:5.1f}  {fit['q']:5.1f}  AIC {tab[nome][met]['aic']:8.0f} | " +
                  " | ".join(f"{o}: " + " ".join(f"{v:.5f}" for v in th[o]) +
                             f" (polo {fis[o][0]:.4f}, R {fis[o][2]:.1f}, L {fis[o][3] * 1e3:.2f} mH)"
                             for o in EIXOS))

    # um periodo so (Park das correntes ABC do ultimo periodo), para comparar com a media
    sb = dict(s, id=s["id_bruta"], iq=s["iq_bruta"])
    yb, ub = desvios(sb)
    for nome in ("SISO 1,2,2", "MIMO 1,2,2 sem e"):
        e = dict(ESTRUTURAS)[nome]
        f1 = ajuste(estima(e, yb, ub, 0, meio, METODO), e, yb, ub, meio, N)
        f2 = ajuste(estima(e, yb, ub, meio, N, METODO), e, yb, ub, 0, meio)
        th = estima(e, yb, ub, 0, N, METODO)
        fis = {o: fisicos(th[o], e) for o in EIXOS}
        print(f"UM PERIODO {nome} {METODO}: ajuste {(f1['d'] + f2['d']) / 2:.1f}/{(f1['q'] + f2['q']) / 2:.1f}, "
              f"R {fis['d'][2]:.1f}/{fis['q'][2]:.1f}, L {fis['d'][3] * 1e3:.2f}/{fis['q'][3] * 1e3:.2f} mH")

    ordem2(y, u, N)
    fig_media(s)
    print("id com media x um periodo: diferenca rms %.1f mA" % (np.std(s["id"] - s["id_bruta"]) * 1e3))
    fig_dados(s)
    fig_dados(s, t_max=1e9, arquivo="dados_completo.png", lw=1.2)
    fig_prbs_corr(y, u, h)
    fig_fir(h, th_siso=estima(dict(ESTRUTURAS)["SISO 1,2,2"], y, u, 0, N, METODO))
    fig_ajustes(tab)
    e_mimo = dict(ESTRUTURAS)["MIMO 1,2,2"]
    e_siso = dict(ESTRUTURAS)["SISO 1,2,2"]
    th_mimo = estima(e_mimo, y, u, 0, meio, METODO)
    fig_validacao(th_mimo, e_mimo, y, u, N, "validacao_mimo.png")
    fig_residuos(estima(e_mimo, y, u, 0, N, METODO), e_mimo, y, u, N)
    th = estima(e_mimo, y, u, 0, N, METODO)
    for o in EIXOS:
        print(f"MIMO 1,2,2 ({METODO}) eixo {o}: " + " ".join(f"{v:.5f}" for v in th[o]))
    for o in EIXOS:
        r = (y[o] - simula(th, e_mimo, y, u, 0, N)[o])[40:]
        print(f"eixo {o}: desvio do sinal {y[o][40:].std() * 1e3:.1f} mA, erro da simulacao livre {r.std() * 1e3:.1f} mA")
    fig_bode(estima(e_siso, y, u, 0, N, METODO), e_siso, f"SISO 1,2,2 {METODO}")

    fig_matriz(estima(e_mimo, y, u, 0, N, METODO), estima(e_siso, y, u, 0, N, METODO))
    # funcao de transferencia SISO 1,2,2 (registro inteiro)
    th = estima(e_siso, y, u, 0, N, METODO)
    for o in EIXOS:
        a, b1, b2 = th[o]
        print(f"G_{o}(z) = ({b1:.5f} z^-2 + {b2:.5f} z^-3) / (1 - {a:.4f} z^-1)")
    a_nom = np.exp(-R_NOM * TS / L_NOM)
    print(f"nominal: polo {a_nom:.4f}, b {(1 - a_nom) / R_NOM:.5f}, wTs {W * TS:.4f}")


if __name__ == "__main__":
    main()
