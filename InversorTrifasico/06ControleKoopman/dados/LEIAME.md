# Dados do ensaio VSI06ControleKoopman

Exportar a matriz `Dados3F` (Graph - Time, float de 32 bits, tamanho 16352) de cada cenário:

| Arquivo | Cenário |
|---|---|
| `Koopman01.csv` | 1: identificação (vetores pseudoaleatórios, média de 16) |
| `Koopman02.csv` | 2: FCS com o modelo de Koopman, média de 16 |
| `Koopman03.csv` | 3: FCS com o modelo físico, média de 16 |
| `Koopman04.csv` | 4: FCS com o modelo de Koopman, registro cru |
| `Tempos04.csv` | matriz `Tempos` (tamanho 8176) do cenário 4 (opcional) |
| `G.txt` | os 12 valores de `koopmanG` copiados da Watch (opcional) |

Análise: `../matlab/k05_analisa_ensaio.m`.
