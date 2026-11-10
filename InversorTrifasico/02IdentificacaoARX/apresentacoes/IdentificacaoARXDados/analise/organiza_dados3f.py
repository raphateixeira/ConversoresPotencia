"""Converte a matriz Dados3F exportada do CCS num CSV com uma coluna por variavel.

No firmware VSI02IdentificacaoARX, tudo o que e gravado fica numa matriz so,
Dados3F[8][2044]; no CCS ela sai como 16352 valores seguidos (Graph - Time)
ou como memoria (Save Memory). Cada canal e identificado pela posicao:

  linha  0-1   vd, vq       tensoes comandadas [V]
  linha  2-3   id, iq       correntes em dq [A] (media sincrona)
  linha  4-6   iA, iB, iC   correntes das fases [A] (ultimo periodo)
  linha  7     angulo       angulo da Park [rad]

Gera <arquivo>_organizado.csv com as colunas
  t_ms, vd, vq, id, iq, iA, iB, iC, angulo
(uma linha por amostra) e imprime um resumo de cada variavel para conferir.

Uso: python3 organiza_dados3f.py ../../../dados/Identificacao/Ident20V_A.csv
     (aceita tambem .bin e .dat do Save Memory)
"""

import sys
from pathlib import Path
import numpy as np
from identifica import le_dados3f, CANAIS, TS

NOMES = {"vd": "vd", "vq": "vq", "id": "id", "iq": "iq", "iA": "iA", "iB": "iB", "iC": "iC",
         "th": "angulo", "vdc": "Vdc", "dA": "dA", "dB": "dB", "dC": "dC"}
UNIDADES = {"vd": "V", "vq": "V", "id": "A", "iq": "A", "iA": "A", "iB": "A", "iC": "A",
            "th": "rad", "vdc": "V", "dA": "", "dB": "", "dC": ""}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    arquivo = Path(sys.argv[1])
    s = le_dados3f(arquivo)
    t_ms = np.arange(s["N"]) * TS * 1e3
    presentes = [c for c in CANAIS if c in s]
    colunas = [t_ms] + [s[c] for c in presentes]
    saida = arquivo.with_name(arquivo.stem + "_organizado.csv")
    np.savetxt(saida, np.column_stack(colunas), delimiter=",",
               header="t_ms," + ",".join(NOMES[c] for c in presentes), comments="", fmt="%.6g")
    print(f"{s['N']} amostras por variavel; gravado {saida}")
    if s["faltam"]:
        print("  nao exportadas:", ", ".join(NOMES[c] for c in s["faltam"]))
    for c in presentes:
        x = s[c]
        print(f"  {NOMES[c]:7s} media {x.mean():9.4f} {UNIDADES[c]:3s} de {x.min():9.4f} a {x.max():9.4f}")


if __name__ == "__main__":
    main()
