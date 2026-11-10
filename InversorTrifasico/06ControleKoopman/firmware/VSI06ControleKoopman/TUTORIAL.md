# VSI06ControleKoopman: FCS-MPC com modelo aprendido por EDMD (LINCE/UFPA)

Base: `VSI05MPCAdaptativoRLS` (hardware, medidas, chaveamento no topo, cenários, tempos). O modelo
da carga não vem de R e L: é aprendido dos dados, na própria placa, por EDMD (aproximação do
operador de Koopman), com os observáveis `z(k) = [i(k); s(k−1)]` e a entrada `s(k)` (vetor do
inversor normalizado por V~dc~, em αβ):

$$i(k+1) = G\,[\,i(k);\ s(k-1);\ s(k)\,],\qquad G\ (2\times 6)\ \text{por mínimos quadrados}$$

O FCS testa os 8 estados com esse modelo e escolhe o que deixa a corrente mais perto da
referência no fim do intervalo do vetor, em k + 3/2. Projeto e simulação em MATLAB:
`InversorTrifasico/06ControleKoopman/matlab/principal.m`.

## Watch

Para escrever: **`habilita`**, **`cenario`**, **`grava`**.
Para ver: `modeloPronto`, `koopmanG` (12 valores), `resistenciaKoopman`, `indutanciaKoopman`,
`tempoEDMD`, `correnteD`, `tempoMaximoTotal`, `perdasPrazo`, `falha`.

| `cenario` | O que faz | Exportar `Dados3F` (16352) como |
|---|---|---|
| 1 | identificação: vetores pseudoaleatórios em malha aberta, média de 16; no fim a placa calcula G | `Koopman01.csv` |
| 2 | FCS com o modelo de Koopman, média de 16 | `Koopman02.csv` |
| 3 | FCS com o modelo físico (25,3 Ω; 9,8 mH), média de 16 (comparação) | `Koopman03.csv` |
| 4 | FCS com o modelo de Koopman, registro cru | `Koopman04.csv` (+ `Tempos`, 8176 → `Tempos04.csv`) |

## Ensaio

1. CCS: projeto `VSI06ControleKoopman`, configuração de **RAM** (compila com `-O2`). *Build*, *Debug*, *Run*.
2. Fonte em 20 V (limite de 0,5 A); espere 5 s; `habilita = 1`.
3. `cenario = 1`, espere 2 s, `grava = 1`. Espere `grava` voltar a 0 e `modeloPronto` = 1
   (o cálculo de G leva alguns milissegundos). Pause: anote `resistenciaKoopman` (≈ 25 Ω),
   `indutanciaKoopman` (≈ 9,8 mH) e copie os 12 valores de `koopmanG` para `G.txt`.
   Exporte `Dados3F` → `Koopman01.csv`. *Run*.
4. Para os cenários 2, 3 e 4: `cenario = N`, espere 2 s, `grava = 1`, espere voltar a 0, pause,
   exporte, *Run*. No cenário 4, anote também `tempoMaximoTotal` e `perdasPrazo` (deve ser 0).
5. `habilita = 0`.

Na identificação o inversor aplica vetores ao acaso, sem controle: a corrente fica abaixo de
≈ 0,4 A com a carga de 25 Ω a 20 V (simulação). A proteção de 0,8 A continua ativa.

Os arquivos vão para `InversorTrifasico/06ControleKoopman/dados/`; a análise é
`matlab/k05_analisa_ensaio.m`.
