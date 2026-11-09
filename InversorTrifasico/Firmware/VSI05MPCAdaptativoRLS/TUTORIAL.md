# VSI05MPCAdaptativoRLS: FCS-MPC com o modelo atualizado por RLS (LINCE/UFPA)

Base: `VSI04ControleFCS`. A cada 50 µs o RLS atualiza o modelo da carga em αβ,

$$i(k+1) = \theta_1\, i(k) + \theta_2\, v(k-1) + \theta_3\, v(k) \qquad (v \text{ normalizada por } V_{dc})$$

e o FCS usa os θ estimados para prever i(k+2) de cada um dos 8 estados.

## Variáveis novas da Watch

| Variável | Padrão | Para quê |
|---|---|---|
| `usaRLS` | 1 | 1 = FCS com o modelo estimado; 0 = modelo fixo (`resistencia`, `indutancia`) |
| `metodoRLS` | 0 | 0 = RLS; 1 = variável instrumental por predição (tira o viés de L) |
| `esquecimento` | 0,999 | fator λ do RLS (memória de ≈ 1000 amostras = 50 ms) |
| `reiniciaRLS` | 1 | escreva 1: recomeça θ de `resistencia`/`indutancia` (volta a 0 sozinho) |
| `reiniciaNaGravacao` | 1 | 1 = recomeça o RLS no início do registro (grava a convergência) |

Para ver: `theta[3]`, `resistenciaEstimada`, `indutanciaEstimada`, `rejeicoes` (atualizações que
dariam um modelo não físico), `frequenciaChaveamento`, `correnteD`, `correnteQ`.

## Tempo de cálculo

CPU Timer 1 (5 ns). Watch: `tempoMedioMedidas`, `tempoMedioRLS`, `tempoMedioFCS`, `tempoMedioTotal`
(médias móveis de ≈ 50 ms, em µs), `tempoMaximoTotal`, `latenciaMedia`, `folgaMinima` (folga até o
topo do contador, prazo da decisão do FCS) e `perdasPrazo`. Por amostra: matriz `Tempos[4][2044]`
(medidas, RLS, FCS, interrupção inteira), exportada no *Graph - Time* com tamanho 8176.

## Gravação: `Dados3F` (8 × 2044)

θ~1~ | θ~3~ | i~d~, i~q~ | v~d~, v~q~ | i~A~, i~B~. As referências são o perfil fixo do VSI03.

## Ensaio (simplificado: a variável `cenario` configura tudo)

Watch mínima: **`habilita`**, **`cenario`**, **`grava`**. Para ver: `correnteD`, `resistenciaEstimada`,
`indutanciaEstimada`, `tempoMaximoTotal`, `perdasPrazo`, `falha`.

| `cenario` | O que configura | Exportar |
|---|---|---|
| 1 | FCS com modelo **errado e fixo** (35 Ω, 14 mH), média de 16 períodos | `Dados3F` → `RLS01.csv` |
| 2 | RLS recomeça do modelo errado: **convergência**, registro cru | `Dados3F` → `RLS02.csv` e `Tempos` → `Tempos02.csv` |
| 3 | **adaptativo em regime** (RLS continua), média de 16 períodos | `Dados3F` → `RLS03.csv` |
| 4 | **variável instrumental por predição**, recomeça do modelo errado, registro cru | `Dados3F` → `RLS04.csv` |

1. CCS: projeto `VSI05MPCAdaptativoRLS`, configuração de **RAM** (compila com `-O2`). *Build*, *Debug*, *Run*.
2. Fonte em 20 V; espere 5 s. `habilita = 1`.
3. Para cada cenário: escreva `cenario = N`, espere 2 s, escreva `grava = 1`, espere `grava` voltar a 0
   (≈ 2 s), pause e exporte (`Dados3F`: tamanho **16352**; `Tempos`: **8176**), *Run*.
4. Em cada cenário, anote `tempoMaximoTotal` e `perdasPrazo` (deve ser 0).
5. `habilita = 0`.
