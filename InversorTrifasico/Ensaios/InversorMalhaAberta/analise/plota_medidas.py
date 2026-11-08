"""Tensoes e correntes das fases gravadas pelo VSI01MalhaAbertaCargaRL.

Os seis vetores (float de 32 bits, 2000 amostras cada) ficam um em cada bloco
de RAM do F28379D, 0x1000 palavras de 16 bits um depois do outro:

    tensaoA 0xC000   tensaoB 0xD000   tensaoC 0xE000
    correnteA 0xF000 correnteB 0x10000 correnteC 0x11000

No CCS, com o programa pausado: janela Memory, *Save Memory*, endereco
inicial 0xC000, tamanho 0x6000 palavras (os seis blocos de uma vez), formato
"TI Data" (.dat) ou binario (.bin). Este script le esse arquivo, plota
tensoes e correntes, e grava um CSV organizado com as colunas t_ms, vA, vB,
vC, iA, iB, iC.

Uso: python3 plota_medidas.py ../dados/memoria.dat [decimacao]
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

PERIODO_PWM = 50e-6        # s (20 kHz), igual ao main.c
N_AMOSTRAS = 2000          # amostras por vetor, igual ao main.c
FLOATS_POR_BLOCO = 0x1000 // 2   # bloco de RAM de 0x1000 palavras = 2048 floats
NOMES = ("vA", "vB", "vC", "iA", "iB", "iC")
CORES = ("#1B365D", "#B23A48", "#2E7D32")


def le_memoria(caminho):
    """Palavras de 16 bits a partir de 0xC000, como floats de 32 bits.

    .bin: bytes como na memoria (little endian). .dat (TI Data): cabecalho
    "1651 formato endereco pagina tamanho" e um valor hexadecimal por linha,
    de 16 bits (0x1234) ou de 32 bits (0x12345678).
    """
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".bin":
        return np.frombuffer(caminho.read_bytes(), dtype="<f4")
    linhas = caminho.read_text().split()
    if linhas[0] == "1651":
        linhas = linhas[5:]                     # pula o cabecalho
    valores = [int(x, 16) for x in linhas if x.lower().startswith("0x")]
    if len(linhas[0]) > 6:                      # valores de 32 bits
        return np.array(valores, dtype="<u4").view("<f4")
    return np.array(valores, dtype="<u2").view("<f4")   # pares de 16 bits, parte baixa primeiro


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    arquivo = Path(sys.argv[1])
    decimacao = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    memoria = le_memoria(arquivo)
    precisa = 5 * FLOATS_POR_BLOCO + N_AMOSTRAS
    if len(memoria) < precisa:
        sys.exit(f"arquivo com {len(memoria)} floats; sao precisos {precisa} "
                 "(salve 0x6000 palavras a partir de 0xC000)")
    sinais = [memoria[k * FLOATS_POR_BLOCO:k * FLOATS_POR_BLOCO + N_AMOSTRAS] for k in range(6)]
    vA, vB, vC, iA, iB, iC = sinais
    t_ms = np.arange(N_AMOSTRAS) * PERIODO_PWM * decimacao * 1e3

    saida = arquivo.with_name(arquivo.stem + "_organizado.csv")
    np.savetxt(saida, np.column_stack([t_ms] + sinais), delimiter=",",
               header="t_ms," + ",".join(NOMES), comments="", fmt="%.4f")
    print(f"{N_AMOSTRAS} amostras; gravado {saida}")
    for nome, x in zip(NOMES, sinais):
        u = "V" if nome[0] == "v" else "A"
        print(f"  {nome}: media {x.mean():.3f} {u}, de {x.min():.3f} a {x.max():.3f} {u}")
    soma = iA + iB + iC
    print(f"  iA + iB + iC: media {soma.mean():.3f} A, maximo |.| {np.abs(soma).max():.3f} A")

    fig, axs = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    for x, cor, nome in zip((vA, vB, vC), CORES, NOMES[:3]):
        axs[0].plot(t_ms, x, color=cor, lw=1.5, label=nome)
    axs[0].set_ylabel("tensão da fase × GND [V]")
    axs[0].legend(ncol=3, frameon=False)
    for x, cor, nome in zip((iA, iB, iC), CORES, NOMES[3:]):
        axs[1].plot(t_ms, x, color=cor, lw=1.5, label=nome)
    axs[1].set_ylabel("corrente da fase [A]")
    axs[1].set_xlabel("tempo [ms]")
    axs[1].legend(ncol=3, frameon=False)
    fig.tight_layout()
    figura = arquivo.with_suffix(".png")
    fig.savefig(figura, dpi=110)
    print(f"figura: {figura}")
    plt.show()


if __name__ == "__main__":
    main()
