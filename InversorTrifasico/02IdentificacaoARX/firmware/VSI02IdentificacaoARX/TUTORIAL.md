# VSI02IdentificacaoARX: ensaio de identificação com PRBS em vd e vq (LINCE/UFPA)

LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (J1–J4), carga RL trifásica em estrela (25 Ω e 10 mH por
fase), barramento de 20 V. Malha aberta: o programa aplica

$$v_d = V_{d0} + \Delta V\,\mathrm{PRBS}_d, \qquad v_q = V_{q0} + \Delta V\,\mathrm{PRBS}_q$$

convertidas para abc pela Park inversa (60 Hz), e grava as correntes, as razões cíclicas e id, iq
para identificar um modelo ARX por eixo. PWM, pinos e ADC são os do `VSI01MalhaAberta`.

## 1. Variáveis da Watch

| Variável | Padrão | Para quê |
|---|---|---|
| `habilita` | 0 | 1 liga o inversor, 0 desliga |
| `tensaoD0`, `tensaoQ0` | 5 V, 0 V | ponto de operação (pico da tensão de fase) |
| `amplitudePRBS` | 3 V | amplitude da PRBS; 0 = sem excitação |
| `eixoPRBS` | 0 | 0 = PRBS em d e em q; 1 = só em d; 2 = só em q |
| `amostrasPorBit` | 4 | duração de um bit: 4 × 50 µs = 200 µs |
| `periodosMedia` | 16 | períodos da PRBS na média síncrona de i~d~ e i~q~ (1 a 64) |
| `frequencia` | 60 Hz | frequência do referencial dq |
| `grava` | 0 | 1 recomeça a PRBS e grava; 2 gravando; 3 calculando a média; volta a 0 no fim |

Para ver: `correnteD`, `correnteQ`, `correnteAgora`, `tensaoBarramento`, `razaoAplicada`,
`offsetZero`, `offsetTopo`, `periodoAtual` (andamento da gravação; 0 = período descartado).

Limite: $\sqrt{v_d^2 + v_q^2} \le 0{,}45\,V_{dc}$ (9 V com 20 V), senão a razão cíclica satura em
5 % ou 95 %. O padrão chega a 8,5 V.

## 2. O que é gravado: a matriz `Dados3F` (8 × 2044 amostras de 50 µs = 102 ms)

| Linha | Variável | Conteúdo |
|---|---|---|
| 0–1 | vd, vq | tensões comandadas [V] |
| 2–3 | id, iq | correntes em dq [A] (média síncrona) |
| 4–6 | iA, iB, iC | correntes [A] do último período |
| 7 | ângulo | ângulo da Park [rad] |

São 16 352 valores, dentro do limite do *Graph - Time* do CCS (16 383). V~dc~ fica na Watch
(`tensaoBarramento`); as razões cíclicas saem de vd, vq, ângulo e V~dc~. As correntes já saem com a
soma das três fases zerada (neutro isolado: um terço da soma medida é tirado de cada fase);
`somaCorrentes` mostra a soma medida, para diagnóstico.

Com `amostrasPorBit` = 4, os 2044 pontos são exatamente um período das duas PRBS (511 bits), e a
gravação faz **média síncrona**: descarta o primeiro período (transitório) e, nos `periodosMedia`
seguintes, soma i~d~ e i~q~ na mesma posição de cada período e divide no fim. A PRBS se repete e,
em dq, a resposta da carga também; o ruído não: ele cai com √`periodosMedia` (8 períodos: ÷ 2,8).
`correnteDGravada` e `correnteQGravada` são a média; os outros vetores guardam o último período
(as correntes ABC, as razões e o ângulo não se repetem: 102 ms não é um número inteiro de ciclos
de 60 Hz). Com o padrão de 16 períodos a gravação leva 17 × 102 ms ≈ 1,7 s (ruído ÷ 4). Com `amostrasPorBit` ≠ 4 grava um
registro só, sem média.
A razão escrita na amostra k vale a partir do zero k + 1: conte com atraso de 2 amostras no ARX.

## 3. Ensaio

1. *Build* e *Debug* do **`VSI02IdentificacaoARX`**.
2. Fonte em 20 V (limite de 0,5 A); `tensaoBarramento` ≈ 20 V. Espere uns segundos com
   `habilita = 0`: o programa mede o zero dos sensores.
3. `habilita = 1`. Por 110 ms o programa aplica 50 % nas três fases (corrente nula) e mede o zero
   dos sensores **chaveando** (`calibrando` = 1); depois começa a PRBS.
4. `grava = 1`, espere `grava` voltar a 0 e pause com **‖**.
5. Exporte **uma variável só**: no *Graph - Time*, expressão `Dados3F`, float de 32 bits,
   tamanho **16352** (não deixe o tamanho antigo, 24528: o CCS exporta o trecho errado); exporte o
   CSV (por exemplo `Ident20V_A.csv`). Ou, sem gráfico: *Memory → Save Memory* a partir de
   `Dados3F`, 32704 palavras (`.dat` ou `.bin`).
   Para ver as variáveis com nome: `python3 organiza_dados3f.py arquivo.csv` (em
   `InversorTrifasico/02IdentificacaoARX/apresentacoes/IdentificacaoARXDados/analise/`) gera `arquivo_organizado.csv` com as
   colunas `t_ms, iA, iB, iC, dA, dB, dC, Vdc, angulo, vd, vq, id, iq`.
6. Sugestão de sequência: `eixoPRBS` = 0 (d e q juntos) em 20 V e depois em 40 V, gravando cada
   um duas vezes (uma gravação estima o modelo, a outra valida). `eixoPRBS` = 1 e 2 são opcionais.
7. Para desligar: `habilita = 0`, fonte, USB.

## 4. Barramento maior (mais sinal)

As tensões comandadas devem crescer com o barramento: $\sqrt{v_d^2+v_q^2} \le 0{,}45\,V_{dc}$.

| V~dc~ | `tensaoD0` | `amplitudePRBS` | Ajuste esperado (8 períodos) |
|---|---|---|---|
| 20 V | 5 V | 3 V | ≈ 94 % |
| 30 V | 7,5 V | 4,5 V | ≈ 95 % |
| 40 V | 10 V | 6 V | ≈ 96 % |

Suba aos poucos; limite da fonte em 1 A; confira a potência dos resistores (≈ 3,4 W por fase a
40 V). Para medir o ruído real em cada tensão: `amplitudePRBS = 0`, grave e veja o desvio de
`correnteDGravada`.

## 5. O que esperar

- id em torno de 0,2 A, com degraus de cerca de ±0,12 A (3 V / 25 Ω); iq em torno de −0,03 A.
- Polo discreto esperado: $e^{-RT_s/L} = 0{,}8825$; ganho $(1-a)/R = 0{,}0047$ A/V.
- Na simulação do ensaio, com ruído de 10 mA, um ARX por mínimos quadrados dá polo de 0,86 (o ruído
  puxa o polo para baixo): para estimativas sem viés, use variável instrumental ou erro de saída,
  ou junte vários registros.
