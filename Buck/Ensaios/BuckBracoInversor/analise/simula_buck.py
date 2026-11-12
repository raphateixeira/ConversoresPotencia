"""Buck num braco do BOOSTXL-3PHGANINV: dimensionamento, simulacao do ensaio e ARX.

Simula o ensaio do firmware BK02IdentificacaoGaN (Buck/Firmware/) antes de ir a bancada:
  - planta chaveada exata, periodo a periodo (exponencial de matriz por trecho do PWM),
    com a conducao reversa do GaN (chave de baixo aberta) e o filtro RC do sensor de tensao;
  - PWM simetrico (contador sobe e desce), razao com 1 periodo de atraso (sombra no zero);
  - amostras no zero do contador (meio do pulso), sensores quantizados e com ruido;
  - PRBS de 9 bits (x^9 + x^5 + 1, como no firmware), 4 amostras por bit, media sincrona;
  - ARX por minimos quadrados (regressores circulares: o registro e um periodo da PRBS),
    validado numa onda quadrada sem media e comparado com o modelo fisico.

Gera em ../imgs/: formas_onda.png, bode_buck.png, ensaio_simulado.png, arx_validacao.png,
partida.png. Imprime os numeros usados nos slides.

Uso: python3 simula_buck.py              simulacao e figuras (numpy, scipy, matplotlib)
     python3 simula_buck.py dados.csv    ARX do ensaio real: CSV exportado do CCS
                                         (DadosBuck, 8 x 2044, modo 0 com media)
"""

from pathlib import Path
import numpy as np
from scipy.linalg import expm
from scipy import signal
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
IMGS = AQUI.parent / "imgs"
IMGS.mkdir(exist_ok=True)

# Cores (TemaRTx): dados em cinza, ARX em azul, modelo fisico em verde tracejado
COR_DADOS, COR_ARX, COR_FIS = "#6C757D", "#1B365D", "#2E7D32"
COR_VERM, COR_ACENTO, COR_AMARELO = "#B23A48", "#4A6FA5", "#E8C547"
plt.rcParams.update({"font.size": 15, "axes.titlesize": 16, "axes.labelsize": 15,
                     "font.family": "sans-serif", "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3})

# ----------------------------- Parametros ------------------------------------
P = dict(
    VDC=20.0,            # fonte de bancada [V] (limite 0,5 A)
    L=2.2e-3,            # indutor [H]
    RL=0.5,              # resistencia do indutor (estimada) [Ohm]
    RON=0.020,           # GaN 15 mOhm + shunt 5 mOhm [Ohm]
    C=47e-6,             # capacitor [F]
    R=15.0,              # carga [Ohm]
    VSD=2.0,             # queda da conducao reversa do GaN (LMG5200: 2 V a 0,5 A) [V]
    TAU=(100e3 * 4.22e3 / 104.22e3) * 33e-9,   # filtro do sensor de tensao: 4,05 kOhm x 33 nF
    FPWM=20e3,
    TOPO=2500,
)
TS = 1.0 / P["FPWM"]
D0, AMP = 0.5, 0.05                  # ponto de operacao e amplitude da PRBS (padrao do firmware)
N_BIT, BITS = 4, 511
N = N_BIT * BITS                     # 2044 amostras = um periodo da PRBS
PERIODOS = 16                        # media sincrona
SIG_I, Q_I = 5e-3, 3.0 / (4096 * 0.1)      # ruido e quantizacao da corrente [A]
SIG_V, Q_V = 10e-3, 3.0 / 4096 * 24.7      # da tensao [V]


def matrizes(p, assinc=True):
    """Modelo continuo x = [iL, vo, vm]: dx/dt = A x + B vsw. vm = vo filtrado (sensor)."""
    A = np.array([[-(p["RL"] + p["RON"]) / p["L"], -1 / p["L"], 0],
                  [1 / p["C"], -1 / (p["R"] * p["C"]), 0],
                  [0, 1 / p["TAU"], -1 / p["TAU"]]])
    B = np.array([1 / p["L"], 0, 0])
    return A, B


def discretiza(A, B, h):
    M = np.zeros((4, 4))
    M[:3, :3], M[:3, 3] = A * h, B * h
    E = expm(M)
    return E[:3, :3], E[:3, 3]


class Buck:
    """Planta chaveada: um passo = um periodo de PWM com a razao (CMPA) daquele periodo.

    O periodo comeca no zero do contador: chave ligada em [0, dT/2] e [T - dT/2, T],
    desligada no meio (saida A alta enquanto contador < CMPA, como no firmware).
    """

    def __init__(self, p=P, assinc=True):
        self.p, self.assinc = p, assinc
        self.A, self.B = matrizes(p)
        self.cache = {}
        self.vsw_off = -p["VSD"] if assinc else 0.0
        self.min_il = np.inf

    def _trechos(self, cmpa):
        if cmpa not in self.cache:
            d = cmpa / self.p["TOPO"]
            ton = d * TS / 2
            self.cache[cmpa] = (discretiza(self.A, self.B, ton),
                                discretiza(self.A, self.B, TS - 2 * ton))
        return self.cache[cmpa]

    def periodo(self, x, d):
        cmpa = int(np.clip(d, 0.05, 0.95) * self.p["TOPO"])
        (Fon, Gon), (Foff, Goff) = self._trechos(cmpa)
        x = Fon @ x + Gon * self.p["VDC"]
        x = Foff @ x + Goff * self.vsw_off
        self.min_il = min(self.min_il, x[0])        # minimo da ondulacao (fim do trecho desligado)
        x = Fon @ x + Gon * self.p["VDC"]
        return x, cmpa / self.p["TOPO"]


def regime(planta, d):
    """Estado no zero do contador em regime com a razao d."""
    x = np.zeros(3)
    for _ in range(3000):
        x, _ = planta.periodo(x, d)
    planta.min_il = np.inf               # o transitorio de partida (modelo linear) nao conta
    return x


def prbs(n_bits, tap=4, semente=0x1FF):
    """PRBS de 9 bits igual a PassoPRBS do firmware: +1/-1."""
    r, saida = semente, []
    for _ in range(n_bits):
        b = ((r >> 8) ^ (r >> tap)) & 1
        r = ((r << 1) | b) & 0x1FF
        saida.append(1.0 if r & 1 else -1.0)
    return np.array(saida)


def ensaio(planta, razao, x0, rng):
    """Aplica a sequencia de razoes como o firmware: a razao calculada na interrupcao k vale
    no periodo [k+1, k+2]. Devolve as medidas no zero de cada periodo (iL, vm, Vdc) e a razao."""
    n = len(razao)
    x = x0.copy()
    il, vm, dap = np.zeros(n), np.zeros(n), np.zeros(n)
    d_vigor = razao[0]
    for k in range(n):
        il[k], vm[k] = x[0], x[2]
        dap[k] = np.clip(razao[k], 0.05, 0.95)
        x, _ = planta.periodo(x, d_vigor)        # periodo [k, k+1] usa a razao escrita em k-1
        d_vigor = razao[k]
    il_m = np.round((il + SIG_I * rng.standard_normal(n)) / Q_I) * Q_I
    vm_m = np.round((vm + SIG_V * rng.standard_normal(n)) / Q_V) * Q_V
    vdc_m = planta.p["VDC"] + 0.05 * rng.standard_normal(n)
    return dict(d=dap, il=il_m, vo=vm_m, vdc=vdc_m, il_real=il, vm_real=vm)


# --------------------------------- ARX ---------------------------------------
def arx_ls(y, u, na, nb, nk, circular=True):
    """y(k) = -a1 y(k-1) - ... + b1 u(k-nk) + ...  Sinais ja sem a media."""
    cols = [-np.roll(y, i) for i in range(1, na + 1)] + [np.roll(u, nk + j) for j in range(nb)]
    Phi = np.column_stack(cols)
    ini = 0 if circular else max(na, nk + nb)
    th, *_ = np.linalg.lstsq(Phi[ini:], y[ini:], rcond=None)
    return np.r_[1, th[:na]], np.r_[np.zeros(nk), th[na:]]


def filtra_circular(b, a, x):
    """Filtra um sinal periodico (o registro e um periodo exato): regime do filtro."""
    return signal.lfilter(b, a, np.tile(x, 4))[-len(x):]


def steiglitz_mcbride(y, u, na, nb, nk, iteracoes=15):
    """ARX repetido: a cada passo, y e u passam por 1/A da estimativa anterior e o LS e
    refeito. Converge para o erro de saida (sem o vies do LS quando ha ruido de medida)."""
    a, b = arx_ls(y, u, na, nb, nk)
    for _ in range(iteracoes):
        a, b = arx_ls(filtra_circular([1], a, y), filtra_circular([1], a, u), na, nb, nk)
    return a, b


def simula_tf(num, den, u, y0=None):
    """Simulacao livre (erro de saida) de num/den com a entrada u (sem a media)."""
    return signal.lfilter(num, den, u)


def fit(y, yh):
    return 100 * (1 - np.linalg.norm(y - yh) / np.linalg.norm(y - y.mean()))


def fisico_discreto(p=P, assinc=True):
    """Modelo medio discretizado (ZOH) com 1 amostra de atraso; entrada u = d Vdc [V].
    Na chave aberta, vsw = d (Vdc + VSD) - VSD: o ganho de u e (Vdc + VSD)/Vdc."""
    A, B = matrizes(p)
    ganho = (p["VDC"] + p["VSD"]) / p["VDC"] if assinc else 1.0
    F, G = discretiza(A, B * ganho, TS)
    sis = []
    for linha in ([1, 0, 0], [0, 0, 1]):          # iL e vm (o que o ADC ve)
        num, den = signal.ss2tf(F, G[:, None], np.array([linha]), np.zeros((1, 1)))
        sis.append((np.r_[0, num[0]], np.r_[den, 0]))   # + 1 atraso
    return sis


def salva(fig, nome):
    fig.savefig(IMGS / nome, dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("gravado", nome)


# ------------------------------- Figuras -------------------------------------
def fig_formas_onda():
    """Tres periodos de PWM: contador, chave, vsw nas duas formas e iL com as amostras."""
    p = P
    d = D0
    t = np.linspace(0, 3 * TS, 3001)
    fase = (t / TS) % 1
    cont = np.where(fase < 0.5, 2 * fase, 2 * (1 - fase)) * p["TOPO"]
    liga = cont < d * p["TOPO"]
    # iL em regime: integra o modelo com passo fino a partir do estado no zero
    planta = Buck()
    x = regime(planta, d)
    A, B = matrizes(p)
    h = t[1] - t[0]
    Fh, Gh = discretiza(A, B, h)
    il = np.zeros_like(t)
    for i in range(len(t)):
        il[i] = x[0]
        x = Fh @ x + Gh * (p["VDC"] if liga[i] else -p["VSD"])
    fig, ax = plt.subplots(3, 1, figsize=(13, 8.5), sharex=True)
    tu = t * 1e6
    ax[0].plot(tu, cont, color=COR_ARX, lw=2, label="contador")
    ax[0].axhline(d * p["TOPO"], color=COR_VERM, ls="--", lw=1.5, label="CMPA = d·TOPO")
    ax[0].set_ylabel("contagens"); ax[0].legend(loc="upper right", ncol=2, fontsize=12)
    ax[1].plot(tu, np.where(liga, p["VDC"], -p["VSD"]), color=COR_VERM, lw=2,
               label="chave de baixo aberta (−2 V)")
    ax[1].plot(tu, np.where(liga, p["VDC"], 0.0), color=COR_FIS, lw=1.5, ls="--",
               label="síncrono (0 V)")
    ax[1].set_ylabel("v$_{SW}$ [V]"); ax[1].legend(loc="center right", fontsize=12)
    ax[2].plot(tu, il, color=COR_ARX, lw=2, label="i$_L$")
    zeros = np.array([0, 1, 2, 3]) * TS
    izero = np.interp(zeros, t, il)
    ax[2].plot(zeros * 1e6, izero, "o", color=COR_VERM, ms=10, label="amostra no zero")
    ax[2].axhline(il.mean(), color=COR_DADOS, ls=":", lw=1.5, label="média")
    ax[2].set_ylabel("i$_L$ [A]"); ax[2].set_xlabel("t [µs]")
    ax[2].legend(loc="upper right", ncol=3, fontsize=12)
    fig.tight_layout()
    salva(fig, "formas_onda.png")
    return il.max() - il.min(), il.mean()


def fig_bode(arx_i, arx_v):
    p = P
    A, B = matrizes(p)
    ganho = (p["VDC"] + p["VSD"]) / p["VDC"]
    f = np.logspace(1, np.log10(10e3), 400)
    w = 2 * np.pi * f
    resp = {}
    for nome, linha in (("iL", [1, 0, 0]), ("vo", [0, 1, 0]), ("vm", [0, 0, 1])):
        H = np.array([np.array(linha) @ np.linalg.solve(1j * wi * np.eye(3) - A, B * ganho)
                      for wi in w])
        resp[nome] = H * np.exp(-1j * w * 1.5 * TS)        # atraso medio de 1,5 amostra
    _, Hi = signal.freqz(arx_i[1], arx_i[0], worN=f, fs=1 / TS)
    _, Hv = signal.freqz(arx_v[1], arx_v[0], worN=f, fs=1 / TS)
    # espectro da PRBS (bit de 4 amostras)
    u = np.repeat(prbs(BITS), N_BIT)
    U = np.abs(np.fft.rfft(u)) ** 2
    fu = np.fft.rfftfreq(N, TS)
    fig, ax = plt.subplots(3, 1, figsize=(13, 9.5), sharex=True)
    ax[0].semilogx(f, 20 * np.log10(np.abs(resp["iL"])), color=COR_FIS, lw=2.5, ls="--",
                   label="modelo médio")
    ax[0].semilogx(f, 20 * np.log10(np.abs(Hi)), color=COR_ARX, lw=1.5, label="ARX (simulação)")
    ax[0].set_ylabel("|i$_L$/u| [dB A/V]"); ax[0].legend(fontsize=12, loc="lower left")
    ax[1].semilogx(f, 20 * np.log10(np.abs(resp["vo"])), color=COR_DADOS, lw=1.5,
                   label="v$_o$ (no capacitor)")
    ax[1].semilogx(f, 20 * np.log10(np.abs(resp["vm"])), color=COR_FIS, lw=2.5, ls="--",
                   label="v$_o$ medida (filtro de 1,2 kHz)")
    ax[1].semilogx(f, 20 * np.log10(np.abs(Hv)), color=COR_ARX, lw=1.5, label="ARX (simulação)")
    ax[1].set_ylabel("|v$_o$/u| [dB]"); ax[1].legend(fontsize=12, loc="lower left")
    sel = (fu > 0) & (fu <= 10e3)
    ax[2].semilogx(fu[sel], 10 * np.log10(U[sel] / U[sel].max() + 1e-12), color=COR_ACENTO, lw=1)
    ax[2].axvline(0.44 / (N_BIT * TS), color=COR_VERM, ls="--", lw=1.5)
    ax[2].text(0.44 / (N_BIT * TS) * 1.08, -8, "−3 dB: 0,44/T$_b$ = 2,2 kHz", color=COR_VERM,
               fontsize=12)
    ax[2].set_ylim(-40, 3)
    ax[2].set_ylabel("PRBS [dB]"); ax[2].set_xlabel("f [Hz]")
    for a in ax:
        a.axvline(1 / (2 * np.pi * np.sqrt(p["L"] * p["C"])), color=COR_AMARELO, lw=2, alpha=0.8)
    fig.tight_layout()
    salva(fig, "bode_buck.png")


def fig_ensaio(dados_ult, med_il, med_vo, u):
    t = np.arange(N) * TS * 1e3
    janela = t < 10
    fig, ax = plt.subplots(3, 1, figsize=(13, 9), sharex=True)
    ax[0].step(t[janela], u[janela], where="post", color=COR_ACENTO, lw=1.5)
    ax[0].set_ylabel("u = d·V$_{dc}$ [V]")
    ax[1].plot(t[janela], dados_ult["il"][janela], color=COR_DADOS, lw=1, marker=".", ms=4,
               label="um período (cru)")
    ax[1].plot(t[janela], med_il[janela], color=COR_ARX, lw=2, label="média de 16 períodos")
    ax[1].set_ylabel("i$_L$ [A]"); ax[1].legend(fontsize=12, loc="upper right", ncol=2)
    ax[2].plot(t[janela], dados_ult["vo"][janela], color=COR_DADOS, lw=1, marker=".", ms=4,
               label="um período (cru)")
    ax[2].plot(t[janela], med_vo[janela], color=COR_ARX, lw=2, label="média de 16 períodos")
    ax[2].set_ylabel("v$_o$ medida [V]"); ax[2].set_xlabel("t [ms]")
    ax[2].legend(fontsize=12, loc="upper right", ncol=2)
    fig.tight_layout()
    salva(fig, "ensaio_simulado.png")


def fig_validacao(val, sims, fits):
    t = np.arange(len(val["il"])) * TS * 1e3
    janela = t < 45
    fig, ax = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    rotulos = (("il", "i$_L$ [A]", "ARX(2,2,2)"), ("vo", "v$_o$ medida [V]", "ARX(3,3,2)"))
    for a, (nome, rot, rot_arx) in zip(ax, rotulos):
        y = val[nome]
        a.plot(t[janela], y[janela], color=COR_DADOS, lw=1, label="simulação chaveada (crua)")
        a.plot(t[janela], sims[nome]["arx"][janela] + y.mean(), color=COR_ARX, lw=2,
               label=f"{rot_arx} (FIT {fits[nome]['arx']:.0f} %)")
        a.plot(t[janela], sims[nome]["fis"][janela] + y.mean(), color=COR_FIS, lw=2, ls="--",
               label=f"modelo físico (FIT {fits[nome]['fis']:.0f} %)")
        a.set_ylabel(rot)
        a.legend(fontsize=12, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False)
    ax[1].set_xlabel("t [ms]")
    fig.tight_layout()
    salva(fig, "arx_validacao.png")


def partida_fina(razao, p=P, sub=40):
    """Partida com o diodo de verdade: com a chave aberta, iL nao fica negativa (conducao
    descontinua no inicio da rampa, quando d < VSD/(Vdc + VSD)). Trechos ligados exatos; o
    trecho desligado em sub passos, com iL >= 0 ao fim de cada um."""
    A, B = matrizes(p)
    cache = {}
    x = np.zeros(3)
    il, vo = np.zeros(len(razao)), np.zeros(len(razao))
    for k, d in enumerate(razao):
        il[k], vo[k] = x[0], x[1]
        cmpa = int(np.clip(d, 0.05, 0.95) * p["TOPO"])
        if cmpa not in cache:
            ton = cmpa / p["TOPO"] * TS / 2
            cache[cmpa] = (discretiza(A, B, ton), discretiza(A, B, (TS - 2 * ton) / sub))
        (Fon, Gon), (Fs, Gs) = cache[cmpa]
        x = Fon @ x + Gon * p["VDC"]
        for _ in range(sub):
            if x[0] > 0:
                x = Fs @ x + Gs * (-p["VSD"])
                x[0] = max(x[0], 0.0)
            else:                            # diodo bloqueado: iL = 0, vsw = vo
                x = Fs @ x + Gs * x[1]
                x[0] = 0.0
        x = Fon @ x + Gon * p["VDC"]
    return il, vo


def fig_partida():
    """Partida: degrau de 5 % para 50 % contra a rampa de 100 ms do firmware."""
    n = 3000
    resultados = {}
    for nome, n_rampa in (("degrau", 1), ("rampa de 100 ms", 2000)):
        razao = np.minimum(np.arange(1, n + 1) / n_rampa, 1.0) * D0
        resultados[nome] = partida_fina(razao)
    t = np.arange(n) * TS * 1e3
    fig, ax = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    for nome, cor in (("degrau", COR_VERM), ("rampa de 100 ms", COR_ARX)):
        il, vo = resultados[nome]
        ax[0].plot(t, il, color=cor, lw=2, label=f"{nome}: pico de {il.max():.2f} A".replace(".", ","))
        ax[1].plot(t, vo, color=cor, lw=2, label=f"{nome}: pico de {vo.max():.1f} V".replace(".", ","))
    ax[0].set_ylabel("i$_L$ [A]"); ax[0].legend(fontsize=12, loc="center right")
    ax[1].set_ylabel("v$_o$ [V]"); ax[1].set_xlabel("t [ms]")
    ax[1].legend(fontsize=12, loc="center right")
    fig.tight_layout()
    salva(fig, "partida.png")
    return {k: v[0].max() for k, v in resultados.items()}


# ------------------------------ Dados reais ----------------------------------
CANAIS = ["d", "il", "vo", "vdc", "va", "il_cru", "vo_cru", "il_topo"]   # linhas de DadosBuck


def ler_dados(arquivo):
    """Le o CSV exportado do Graph - Time (DadosBuck, 16352 floats, uma coluna) ou do Save
    Memory e devolve um dicionario com os 8 canais de 2044 amostras."""
    txt = Path(arquivo).read_text().replace(",", " ").split()
    valores = []
    for x in txt:
        try:
            valores.append(float(x))
        except ValueError:
            continue
    v = np.array(valores[-8 * N:]).reshape(8, N)
    return dict(zip(CANAIS, v))


def identifica_dados(arquivo):
    """Ensaio real (modo 0, PRBS com media): ARX por LS e por Steiglitz-McBride."""
    dd = ler_dados(arquivo)
    u = dd["d"] * dd["vdc"]
    uc = u - u.mean()
    print(f"{arquivo}: d medio {dd['d'].mean():.3f}, Vdc {dd['vdc'].mean():.2f} V, "
          f"iL {dd['il'].mean():.3f} A, vo {dd['vo'].mean():.2f} V, vA {dd['va'].mean():.2f} V")
    for nome, saida, n in (("iL", "il", 2), ("vo", "vo", 3)):
        y = dd[saida] - dd[saida].mean()
        for metodo, fn in (("LS", arx_ls), ("SM", steiglitz_mcbride)):
            a, b = fn(y, uc, n, n, 2)
            ys = filtra_circular(b, a, uc)
            polos = np.roots(a).astype(complex)
            print(f"  {nome} {metodo} ARX({n},{n},2): ganho {np.sum(b)/np.sum(a):.4f}, FIT {fit(y, ys):.1f} %,"
                  f" polos {np.round(polos, 4)}, f {np.round(np.abs(np.log(polos)/TS)/(2*np.pi), 0)} Hz")


# --------------------------------- Main --------------------------------------
def main():
    p = P
    rng = np.random.default_rng(1)
    f0 = 1 / (2 * np.pi * np.sqrt(p["L"] * p["C"]))
    z0 = np.sqrt(p["L"] / p["C"])
    zeta = (1 / (2 * p["R"])) * z0 + (p["RL"] + p["RON"]) / (2 * z0)
    lcrit = p["R"] * (1 - D0) / (2 * p["FPWM"])
    print(f"f0 = {f0:.0f} Hz, Z0 = {z0:.2f} Ohm, zeta = {zeta:.3f}, Lcrit(D0) = {lcrit*1e6:.0f} uH")
    print(f"filtro do sensor: tau = {p['TAU']*1e6:.0f} us, fc = {1/(2*np.pi*p['TAU']):.0f} Hz")

    dil, ilm = fig_formas_onda()
    print(f"ondulacao de iL = {dil*1e3:.0f} mA pp, media = {ilm:.3f} A")

    # Regime em cada extremo da PRBS
    for assinc in (True, False):
        for d in (D0 - AMP, D0, D0 + AMP):
            pl = Buck(assinc=assinc)
            x = regime(pl, d)
            iin = d * x[0]
            print(f"{'assinc' if assinc else 'sinc  '} d={d:.2f}: vo={x[1]:.2f} V, iL={x[0]:.3f} A,"
                  f" Iin~{iin:.3f} A, min iL={pl.min_il:.3f} A, P_R={x[1]**2/p['R']:.1f} W")

    # Ensaio: 1 periodo descartado + 16 com media
    planta = Buck()
    u_prbs = np.repeat(prbs(BITS), N_BIT)
    razao = np.tile(D0 + AMP * u_prbs, PERIODOS + 1)
    x0 = regime(planta, D0)
    dados = ensaio(planta, razao, x0, rng)
    print(f"min iL no ensaio = {planta.min_il:.3f} A (CCM se > 0); max iL = {dados['il_real'].max():.3f} A")
    blocos = lambda s: s[N:].reshape(PERIODOS, N)
    med = {k: blocos(dados[k]).mean(axis=0) for k in ("il", "vo", "d", "vdc")}
    ult = {k: dados[k][-N:] for k in ("il", "vo")}
    u = med["d"] * med["vdc"]                 # tensao comandada u = d Vdc

    # ARX nos dados medios (desvios)
    yc = {k: med[k] - med[k].mean() for k in ("il", "vo")}
    uc = u - u.mean()
    descreve = lambda nome, a, b: print(
        f"{nome}: a = {np.round(a, 4)}, b = {np.round(b, 5)}, ganho = {np.sum(b)/np.sum(a):.4f}\n"
        f"   polos z: {np.round(np.roots(a), 4)}  f [Hz]: "
        f"{np.round(np.abs(np.log(np.roots(a).astype(complex)) / TS) / (2 * np.pi), 0)}")
    ls_i = arx_ls(yc["il"], uc, 2, 2, 2)                 # d Vdc -> iL, LS direto
    ls_v = arx_ls(yc["vo"], uc, 3, 3, 2)                 # d Vdc -> vo medida, LS direto
    arx_i = steiglitz_mcbride(yc["il"], uc, 2, 2, 2)     # os mesmos, ARX iterado (SM)
    arx_v = steiglitz_mcbride(yc["vo"], uc, 3, 3, 2)
    arx_iv = arx_ls(yc["vo"], yc["il"], 2, 2, 1)         # iL -> vo medida (capacitor + filtro)
    descreve("LS d->iL ARX(2,2,2)", *ls_i)
    descreve("LS d->vo ARX(3,3,2)", *ls_v)
    descreve("SM d->iL ARX(2,2,2)", *arx_i)
    descreve("SM d->vo ARX(3,3,2)", *arx_v)
    descreve("LS iL->vo ARX(2,2,1)", *arx_iv)
    pr = np.roots(arx_iv[0]).real
    print(f"   da cascata: R ~ {np.sum(arx_iv[1])/np.sum(arx_iv[0]):.2f} Ohm, "
          f"C ~ {-TS/np.log(pr.max())/P['R']*1e6:.1f} uF (com R nominal), "
          f"tau do filtro ~ {-TS/np.log(pr.min())*1e6:.0f} us")
    U3 = np.tile(uc, 3)
    print("ARX direto d -> vo (FIT da simulacao livre nos proprios dados):")
    for na in (2, 3, 4, 5):
        a, b = arx_ls(yc["vo"], uc, na, na, 2)
        sa = simula_tf(b, a, U3)[-N:]
        print(f"   ARX({na},{na},2): FIT = {fit(yc['vo'], sa):.1f} %, ganho = {np.sum(b)/np.sum(a):.3f}")
    fis_i, fis_v = fisico_discreto()
    for nome, (b, a) in (("fisico iL", fis_i), ("fisico vm", fis_v)):
        print(f"{nome}: ganho estatico = {np.sum(b)/np.sum(a):.4f}, polos:",
              np.round(np.roots(a), 4))

    # Validacao: onda quadrada D0 -+ AMP, periodo de 20 ms, sem media
    plv = Buck()
    nv = N
    quad = D0 + AMP * np.where((np.arange(nv) * TS) % 20e-3 < 10e-3, -1.0, 1.0)
    val = ensaio(plv, quad, regime(plv, D0), rng)
    uv = val["d"] * val["vdc"]
    uvc = uv - uv.mean()
    for nome, mod, y in (("LS iL", ls_i, val["il"]), ("LS vo", ls_v, val["vo"])):
        sa = simula_tf(mod[1], mod[0], uvc)
        sa -= sa[400:].mean()
        yy = y - y.mean()
        print(f"validacao {nome}: FIT = {fit(yy[400:], sa[400:]):.1f} %")
    il_arx = simula_tf(arx_i[1], arx_i[0], uvc)
    vo_arx = simula_tf(arx_v[1], arx_v[0], uvc)
    vo_cas = simula_tf(arx_iv[1], arx_iv[0], il_arx)      # cascata: a saida do 1o alimenta o 2o
    vo_cas -= vo_cas[400:].mean()
    yy = val["vo"] - val["vo"].mean()
    print(f"validacao cascata vo: FIT = {fit(yy[400:], vo_cas[400:]):.1f} %")
    sims, fits = {}, {}
    for nome, sa, fis in (("il", il_arx, fis_i), ("vo", vo_arx, fis_v)):
        y = val[nome] - val[nome].mean()
        sf = simula_tf(fis[0], fis[1], uvc)
        # descarta o transitorio inicial da simulacao livre (sem condicao inicial)
        sa, sf = sa - sa[400:].mean(), sf - sf[400:].mean()
        sims[nome] = dict(arx=sa, fis=sf)
        fits[nome] = dict(arx=fit(y[400:], sa[400:]), fis=fit(y[400:], sf[400:]))
        print(f"validacao {nome}: FIT ARX = {fits[nome]['arx']:.1f} %, fisico = {fits[nome]['fis']:.1f} %")
    # ARX de um periodo cru, sem media
    a1 = arx_ls(ult["il"] - ult["il"].mean(), uc, 2, 2, 2)
    sa1 = simula_tf(a1[1], a1[0], uvc)
    sa1 -= sa1[400:].mean()
    y = val["il"] - val["il"].mean()
    print(f"iL ARX com 1 periodo cru: FIT = {fit(y[400:], sa1[400:]):.1f} %, polos",
          np.round(np.roots(a1[0]), 4))

    fig_bode(arx_i, arx_v)
    fig_ensaio(ult, med["il"], med["vo"], u)
    fig_validacao({k: val[k][: nv] for k in ("il", "vo")}, sims, fits)
    picos = fig_partida()
    print("pico de iL na partida:", {k: round(v, 2) for k, v in picos.items()})


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:          # python3 simula_buck.py ../../../../Buck/.../DadosBuck01.csv
        identifica_dados(sys.argv[1])
    else:
        main()
