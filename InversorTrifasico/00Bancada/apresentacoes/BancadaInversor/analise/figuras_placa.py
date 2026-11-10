"""Figuras do inversor e das placas para a apresentacao "Bancada do inversor trifasico".

Gera em ../imgs/:
  circuito.png          inversor trifasico com a carga RL em estrela (20 V, 25 Ohm, 10 mH)
  braco.png             os tres estados de um braco (cima, baixo, tempo morto)
  anim_pwm.gif          contador, comparacao e saidas A/B formando o PWM
  tempo_morto.png       zoom numa borda: as duas saidas em nivel baixo por 100 ns
  ti_launchpad.png      LaunchPad (SPRUI77C, fig. 1), precisa de ../../../docs/sprui77.pdf
  montagem_boostxl.png  BOOSTXL girado na posicao de encaixe, com anotacoes
  montagem_esquema.png  esquema do encaixe J1-J4
  pinos_launchpad.png   serigrafia da LaunchPad com os pinos do PWM (SPRUI77C, fig. 18)

Uso: python3 figuras_placa.py   (numpy, matplotlib, Pillow; pdftoppm para as figuras da TI)
contador() e saidas() tambem sao usadas pelas figuras da malha aberta (01MalhaAberta).
"""

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
from PIL import Image

AQUI = Path(__file__).resolve().parent
IMGS = AQUI.parent / "imgs"
DOCS = AQUI.parents[2] / "docs"              # PDFs da TI (fora do repositorio)
IMGS.mkdir(exist_ok=True)

# Cores do tema (TemaRTx): fases A, B, C e destaques
COR_A, COR_B, COR_C = "#1B365D", "#B23A48", "#2E7D32"
COR_ACENTO, COR_AMARELO, COR_CINZA = "#4A6FA5", "#E8C547", "#6C757D"
plt.rcParams.update({"font.size": 15, "axes.titlesize": 16, "axes.labelsize": 15,
                     "font.family": "sans-serif", "axes.spines.top": False,
                     "axes.spines.right": False})

# Parametros do PWM (iguais ao main.c do VSI01) e da bancada
F_RELOGIO = 100e6          # Hz
F_PWM = 20e3               # Hz
TOPO = int(F_RELOGIO / (2 * F_PWM))      # 2500
T_MORTO = 100e-9           # s
VDC = 20.0                 # barramento [V]
R, L = 25.0, 10e-3         # carga por fase


def salva(fig, nome):
    fig.savefig(IMGS / nome, dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("gravado", nome)


def contador(t):
    """Contador up-down (0 -> TOPO -> 0) no instante t [s]."""
    fase = (t * F_PWM) % 1.0
    return np.where(fase < 0.5, 2 * fase * TOPO, 2 * (1 - fase) * TOPO)


def saidas(t, razao, morto=T_MORTO):
    """Saidas A e B com tempo morto (atraso na subida de cada uma)."""
    cmpa = razao * TOPO
    a_ideal = contador(t) < cmpa
    a_atr = contador(t - morto) < cmpa          # sinal atrasado de 'morto'
    a = a_ideal & a_atr                         # A sobe atrasada, desce na hora
    b = (~a_ideal) & (~a_atr)                   # B = complemento, sobe atrasada
    return a.astype(float), b.astype(float)


def figura_circuito():
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 12); ax.set_ylim(0, 6.4); ax.axis("off")
    # barramento
    ax.plot([1, 7.6], [5.6, 5.6], color="k", lw=2.5)
    ax.plot([1, 7.6], [0.6, 0.6], color="k", lw=2.5)
    ax.plot([1, 1], [0.6, 2.6], color="k", lw=2); ax.plot([1, 1], [3.6, 5.6], color="k", lw=2)
    ax.plot([0.7, 1.3], [3.6, 3.6], color="k", lw=3); ax.plot([0.85, 1.15], [2.6, 2.6], color="k", lw=3)
    ax.plot([0.7, 1.3], [3.3, 3.3], color="k", lw=3); ax.plot([0.85, 1.15], [2.9, 2.9], color="k", lw=3)
    ax.text(0.2, 3.1, "$V_{dc}$\n20 V", ha="center", va="center")
    ax.text(1.2, 5.85, "+", fontsize=18); ax.text(1.2, 0.15, "GND (−)", fontsize=14)
    cores = [COR_A, COR_B, COR_C]
    xs = [3.0, 4.8, 6.6]
    for k, (x, cor, nome) in enumerate(zip(xs, cores, "ABC")):
        ax.plot([x, x], [5.6, 4.9], color="k", lw=2)
        ax.plot([x, x], [0.6, 1.3], color="k", lw=2)
        for yc, rot in [(4.35, f"{nome}+"), (1.85, f"{nome}−")]:
            ax.add_patch(FancyBboxPatch((x - 0.35, yc - 0.55), 0.7, 1.1,
                                        boxstyle="round,pad=0.02", fc="white", ec=cor, lw=2.5))
            ax.text(x, yc, rot, ha="center", va="center", color=cor, fontsize=15, weight="bold")
        ax.plot([x, x], [3.8, 2.4], color="k", lw=2)
        ys = [3.45, 3.1, 2.75][k]                     # saida de cada braco numa altura
        ax.add_patch(Circle((x, ys), 0.09, color=cor))
        ax.text(x - 0.15, ys + 0.12, nome, color=cor, ha="right", fontsize=16, weight="bold")
        # ligacao do ponto do meio do braco ate a carga (cruza os outros bracos sem conexao)
        yl = [4.6, 3.1, 1.6][k]
        xr = 7.9 - 0.2 * k
        ax.plot([x, xr, xr, 8.2], [ys, ys, yl, yl], color=cor, lw=2)
        # carga R + L
        ax.add_patch(Rectangle((8.2, yl - 0.18), 0.9, 0.36, fc="white", ec=cor, lw=2))
        ax.text(8.65, yl, "25 Ω", ha="center", va="center", fontsize=12)
        xx = np.linspace(9.2, 10.1, 200)
        ax.plot(xx, yl + 0.18 * np.abs(np.sin((xx - 9.2) / 0.9 * 4 * np.pi)), color=cor, lw=2)
        ax.text(9.65, yl - 0.45, "10 mH", ha="center", fontsize=12)
        ax.plot([10.1, 10.8], [yl, yl], color=cor, lw=2)
    ax.plot([10.8, 10.8], [1.6, 4.6], color="k", lw=2)
    ax.add_patch(Circle((10.8, 3.1), 0.08, color="k"))
    ax.text(11.0, 3.1, "neutro\n(n)", va="center", fontsize=14)
    ax.text(4.8, 6.15, "inversor (BOOSTXL-3PHGANINV)", ha="center", fontsize=15, color=COR_CINZA)
    ax.text(9.6, 5.35, "carga RL em estrela", ha="center", fontsize=15, color=COR_CINZA)
    salva(fig, "circuito.png")


def figura_braco():
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.6))
    casos = [("chave de cima ligada", True, False, "$v = V_{dc}$ = 20 V"),
             ("chave de baixo ligada", False, True, "$v$ = 0 V"),
             ("tempo morto: as duas desligadas", False, False, "$v$ depende da corrente")]
    for ax, (tit, cima, baixo, rot) in zip(axs, casos):
        ax.set_xlim(0, 4); ax.set_ylim(0, 6); ax.axis("off")
        ax.plot([2, 2], [5.6, 4.8], "k", lw=2); ax.plot([2, 2], [0.4, 1.2], "k", lw=2)
        ax.text(2.15, 5.55, "+20 V", fontsize=14); ax.text(2.15, 0.3, "GND", fontsize=14)
        for yc, lig in [(4.1, cima), (1.9, baixo)]:
            cor = COR_C if lig else COR_CINZA
            ax.add_patch(FancyBboxPatch((1.55, yc - 0.65), 0.9, 1.3, boxstyle="round,pad=0.02",
                                        fc=(cor if lig else "white"), ec=cor, lw=2.5, alpha=0.9))
            ax.text(2, yc, "ligada" if lig else "desligada", ha="center", va="center",
                    color="white" if lig else COR_CINZA, fontsize=12, weight="bold")
        ax.plot([2, 2], [3.45, 2.55], "k", lw=2)
        ax.add_patch(Circle((2, 3.0), 0.09, color=COR_A)); ax.plot([2, 3.4], [3, 3], color=COR_A, lw=2)
        ax.text(3.45, 3.0, "fase", va="center", fontsize=14, color=COR_A)
        ax.set_title(tit, fontsize=15)
        ax.text(2, -0.3, rot, ha="center", fontsize=15)
    axs[0].text(0.1, 4.1, "saída A\n(EPWMxA)", fontsize=12, va="center", color=COR_CINZA)
    axs[0].text(0.1, 1.9, "saída B\n(EPWMxB)", fontsize=12, va="center", color=COR_CINZA)
    fig.text(0.5, -0.06, "Nunca as duas ligadas: seria um curto-circuito no barramento.",
             ha="center", fontsize=16, color=COR_B, weight="bold")
    salva(fig, "braco.png")


def animacao_pwm():
    razao = 0.35
    morto = 2.0e-6                     # exagerado para aparecer no desenho (o real e 100 ns)
    t = np.linspace(0, 2 / F_PWM, 2000)
    cnt = contador(t)
    a, b = saidas(t, razao, morto)
    tus = t * 1e6
    fig, axs = plt.subplots(3, 1, figsize=(11, 6.6), sharex=True,
                            gridspec_kw={"height_ratios": [2.2, 1, 1]})
    axs[0].plot(tus, cnt, color=COR_CINZA, lw=1, alpha=0.4)
    axs[0].axhline(razao * TOPO, color=COR_B, lw=2, ls="--")
    axs[0].text(99, razao * TOPO + 120, f"CMPA = {razao * TOPO:.0f}", color=COR_B, ha="right")
    axs[0].text(99, TOPO + 60, f"TOPO = {TOPO}", ha="right", color=COR_CINZA)
    axs[0].set_ylabel("contador"); axs[0].set_ylim(-100, 2700)
    linha_c, = axs[0].plot([], [], color=COR_A, lw=2.5)
    ponto, = axs[0].plot([], [], "o", color=COR_A, ms=9)
    linha_a, = axs[1].plot([], [], color=COR_A, lw=2.5, drawstyle="steps-post")
    linha_b, = axs[2].plot([], [], color=COR_B, lw=2.5, drawstyle="steps-post")
    for ax, nome in [(axs[1], "A (cima)"), (axs[2], "B (baixo)")]:
        ax.set_ylim(-0.2, 1.3); ax.set_yticks([0, 1]); ax.set_ylabel(nome, fontsize=13)
    axs[2].set_xlabel("tempo [µs]"); axs[2].set_xlim(0, 100)
    txt = axs[0].text(2, 2550, "", fontsize=14)
    fig.suptitle("Contador sobe e desce; A fica alta enquanto contador < CMPA "
                 "(tempo morto exagerado)", fontsize=14)
    fig.tight_layout()
    n_quadros = 80

    def quadro(i):
        k = int((i + 1) / n_quadros * (len(t) - 1))
        linha_c.set_data(tus[:k], cnt[:k]); ponto.set_data([tus[k]], [cnt[k]])
        linha_a.set_data(tus[:k], a[:k]); linha_b.set_data(tus[:k], b[:k])
        estado = ("chave de cima ligada" if a[k] else
                  "chave de baixo ligada" if b[k] else "tempo morto: as duas desligadas")
        txt.set_text(estado)
        return linha_c, ponto, linha_a, linha_b, txt

    anim = FuncAnimation(fig, quadro, frames=n_quadros, interval=80, blit=False)
    anim.save(IMGS / "anim_pwm.gif", writer=PillowWriter(fps=12), dpi=75)
    plt.close(fig)
    print("gravado anim_pwm.gif")


def figura_tempo_morto():
    t = np.linspace(-0.4e-6, 0.6e-6, 4000)
    t0 = 0.35 * TOPO / (2 * TOPO * F_PWM)     # descida de A no instante em que contador = CMPA
    a, b = saidas(t + t0, 0.35)
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(t * 1e9, a * 3.3 + 4.2, color=COR_A, lw=2.5, label="J4-40 (A, chave de cima)")
    ax.plot(t * 1e9, b * 3.3, color=COR_B, lw=2.5, label="J4-39 (B, chave de baixo)")
    ax.axvspan(0, 100, color=COR_AMARELO, alpha=0.4)
    ax.text(115, 5.6, "100 ns: as duas em 0", ha="left", fontsize=14)
    ax.set_xlabel("tempo [ns] (osciloscópio em 50 ns/div)"); ax.set_yticks([])
    ax.legend(loc="lower left", fontsize=13, frameon=False, bbox_to_anchor=(0, -0.45), ncol=2)
    ax.set_ylim(-0.5, 9)
    salva(fig, "tempo_morto.png")


def figuras_montagem():
    # LaunchPad (desenho da TI, recortado em 220 dpi de docs/sprui77.pdf, pagina 3)
    lp = DOCS / "sprui77.pdf"
    if lp.exists():
        import subprocess, tempfile
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["pdftoppm", "-r", "220", "-png", "-f", "3", "-l", "3",
                            str(lp), f"{d}/p"], check=True)
            im = Image.open(next(Path(d).glob("p*.png")))
            im.crop((340, 250, 1680, 1110)).save(IMGS / "ti_launchpad.png", optimize=True)
            print("gravado ti_launchpad.png")

    # BoosterPack (foto da TI) girado 90 graus no sentido anti-horario: e assim
    # que ele fica sobre a LaunchPad (J1/J3 a esquerda, pino 1 = 3V3 em cima)
    foto = Image.open(IMGS / "ti_placa_boostxl.png")
    W, H = foto.size
    girada = foto.rotate(90, expand=True)

    def g(x, y):            # coordenada da foto original -> foto girada
        return y, W - x

    fig, ax = plt.subplots(figsize=(7.5, 11))
    ax.imshow(girada); ax.axis("off")
    notas = [((975, 70), "pino 1 de J1 = 3V3\n(lado da USB da LaunchPad)", (-330, -60), COR_B),
             ((855, 90), "J1 (fora) e J3 (dentro)", (-420, 120), COR_A),
             ((855, 575), "J4 (dentro) e J2 (fora)", (210, 120), COR_A),
             ((674, 85), "jumper J6: retirar\n(confira a serigrafia)", (-410, 330), COR_B),
             ((405, 575), "+48V e GND:\nfonte do barramento", (210, -80), COR_C),
             ((600, 575), "VC, VB, VA:\ncarga", (210, 40), COR_C)]
    for (x, y), texto, (dx, dy), cor in notas:
        px, py = g(x, y)
        ax.annotate(texto, xy=(px, py), xytext=(px + dx, py + dy), fontsize=13, color=cor,
                    weight="bold", arrowprops=dict(arrowstyle="->", color=cor, lw=2),
                    bbox=dict(fc="white", ec=cor, alpha=0.9))
    ax.set_title("BOOSTXL visto de cima, na posição de encaixe", fontsize=15)
    salva(fig, "montagem_boostxl.png")


def figura_alinhamento():
    """Esquema (fora de escala) do encaixe: J1..J4 do BoosterPack sobre J1..J4 da LaunchPad."""
    fig, ax = plt.subplots(figsize=(8, 8.6))
    ax.set_xlim(-1, 9); ax.set_ylim(1.4, 13.2); ax.axis("off"); ax.set_aspect("equal")
    ax.add_patch(FancyBboxPatch((0.5, 0), 5, 12.3, boxstyle="round,pad=0.05", fc="#F4C7C7",
                                ec=COR_B, lw=2))
    ax.add_patch(Rectangle((2.5, 12.1), 1, 0.6, fc=COR_CINZA))
    ax.text(3, 12.95, "USB", ha="center", fontsize=13)
    ax.text(3, 1.75, "LaunchPad F28379D (continua para baixo)", ha="center", fontsize=13,
            color=COR_B, weight="bold")
    # colunas de headers: J1, J3 (esquerda) e J4, J2 (direita), pino 1 em cima
    for x, nome in [(1.0, "J1"), (1.45, "J3"), (4.55, "J4"), (5.0, "J2")]:
        for k in range(10):
            ax.add_patch(Circle((x, 10.6 - 0.3 * k), 0.09, color="k"))
        ax.text(x, 10.95, nome, ha="center", fontsize=12, weight="bold")
    for x, nome in [(1.0, "J5"), (1.45, "J7"), (4.55, "J8"), (5.0, "J6")]:
        for k in range(10):
            ax.add_patch(Circle((x, 5.0 - 0.3 * k), 0.07, color=COR_CINZA))
        ax.text(x, 5.35, nome, ha="center", fontsize=11, color=COR_CINZA)
    ax.add_patch(Circle((1.0, 10.6), 0.18, fill=False, ec=COR_B, lw=2.5))
    ax.annotate("pino 1 = 3V3", xy=(1.0, 10.6), xytext=(-0.9, 11.9), fontsize=13, color=COR_B,
                arrowprops=dict(arrowstyle="->", color=COR_B, lw=2))
    # contorno do BoosterPack
    # proporcoes tiradas da foto da TI: a placa comeca na altura do pino 1 e
    # se estende ~1,8" abaixo dos conectores (por cima de J5-J8)
    ax.add_patch(FancyBboxPatch((0.58, 2.5), 4.73, 8.4, boxstyle="round,pad=0.05", fill=False,
                                ec=COR_A, lw=3, ls="--"))
    ax.text(3, 6.5, "BOOSTXL-3PHGANINV\npor cima", ha="center",
            fontsize=14, color=COR_A, weight="bold")
    ax.annotate("os pinos de J1–J4 da LaunchPad\nentram nos conectores fêmea\nda face de baixo do BOOSTXL",
                xy=(5.0, 9.0), xytext=(5.7, 8.6), fontsize=12,
                arrowprops=dict(arrowstyle="->", color="k"))
    ax.annotate("as soldas de baixo do BOOSTXL\nficam sobre J5–J8:\nisolar (fita Kapton)",
                xy=(4.8, 3.6), xytext=(5.7, 2.4), fontsize=12, color=COR_B,
                arrowprops=dict(arrowstyle="->", color=COR_B))
    salva(fig, "montagem_esquema.png")


def figura_pinos_launchpad():
    """Serigrafia da LaunchPad (SPRUI77C, fig. 18) girada com a USB para cima e
    os pinos do PWM marcados. Na figura da TI a placa esta deitada, com o
    XDS100v2 (lado da USB) a esquerda."""
    pdf = DOCS / "sprui77.pdf"
    if not pdf.exists():
        return
    import subprocess, tempfile
    Image.MAX_IMAGE_PIXELS = None
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-r", "600", "-png", "-f", "18", "-l", "18",
                        str(pdf), f"{d}/p"], check=True)
        pagina = Image.open(next(Path(d).glob("p*.png")))
        serig = pagina.crop((463, 4934, 2507, 5915))          # figura 18 (vista de cima)
    x0, y0, x1, y1 = 275, 20, 836, 867                        # regiao de J1-J4 e do XDS100v2
    rec = serig.crop((x0, y0, x1, y1))
    hc = y1 - y0
    girada = rec.rotate(-90, expand=True)                     # USB para cima
    xc = 0                                                    # a imagem inteira tem os conectores
    girada = girada.crop((xc, 0, 800, girada.size[1]))

    def g(x, y):     # rotulo na figura da TI (pixels) -> figura girada e cortada
        return hc - 1 - (y - y0) - xc, x - x0

    fig, ax = plt.subplots(figsize=(12, 8.6))
    ax.imshow(girada); ax.axis("off")
    k = 1.02         # escala entre a figura vista e a gerada
    W = girada.size[0]
    direita = [((463, 75), "J2-20  GND: terra das pontas", "k"),
               ((463, 200), "J4-40  A, chave de cima", COR_A),
               ((498, 200), "J4-39  A, chave de baixo", COR_A),
               ((533, 200), "J4-38  B, chave de cima", COR_B),
               ((569, 200), "J4-37  B, chave de baixo", COR_B),
               ((604, 200), "J4-36  C, chave de cima", COR_C),
               ((639, 200), "J4-35  C, chave de baixo", COR_C)]
    esquerda = [((463, 810), "J1-1  3V3: não encostar", COR_CINZA),
                ((463, 672), "J3-21  5V: não encostar", COR_CINZA)]
    for lista, xt, ha in [(direita, W + 40, "left"), (esquerda, -40, "right")]:
        for j, ((x, y), texto, cor) in enumerate(lista):
            px, py = g(x * k, y * k)
            yt = 60 + j * 62 if ha == "left" else 60 + j * 80
            ax.add_patch(Circle((px, py), 15, fill=False, ec=cor, lw=2.5))
            ax.annotate(texto, xy=(px, py), xytext=(xt, yt), fontsize=14, color=cor, ha=ha,
                        weight="bold", va="center",
                        arrowprops=dict(arrowstyle="->", color=cor, lw=1.6),
                        bbox=dict(fc="white", ec=cor, alpha=0.95))
    ax.set_xlim(-420, W + 430)
    ax.set_ylim(girada.size[1] + 10, -60)
    ax.text(W / 2, -35, "▲ lado da USB (XDS100v2)", ha="center", fontsize=14, weight="bold")
    ax.text(W / 2, girada.size[1] + 45, "o número impresso fica ao lado do pino",
            ha="center", fontsize=13, color=COR_CINZA)
    salva(fig, "pinos_launchpad.png")


if __name__ == "__main__":
    figura_circuito()
    figura_braco()
    animacao_pwm()
    figura_tempo_morto()
    figuras_montagem()
    figura_alinhamento()
    figura_pinos_launchpad()
