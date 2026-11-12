# BK02IdentificacaoGaN: buck num braço do inversor GaN, ensaio de identificação (LINCE/UFPA)

LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (J1–J4), fonte de 20 V (limite de 0,5 A). Só o **braço A**
chaveia: a chave de cima recebe o PWM e a de baixo fica **aberta**. A corrente de roda livre passa
pela condução reversa do GaN (≈ 2 V), que faz o papel do diodo de um buck clássico. Em malha aberta,
o programa aplica

$$d = D_0 + \Delta d\,\mathrm{PRBS}$$

e grava i~L~, v~o~, V~dc~ e d para identificar um modelo ARX. PWM, sensores e PRBS são os do
`VSI02IdentificacaoARX`. A apresentação com o projeto e a simulação do ensaio fica em
`Buck/Ensaios/BuckBracoInversor/`.

## 1. Montagem

| Ligação | De | Para |
|---|---|---|
| Fonte de 20 V | + e − da fonte | bornes +48V e GND do BOOSTXL |
| Indutor L = 2,2 mH (≥ 1,5 A) | borne **VA** | nó de saída |
| Capacitor C = 47 µF (≥ 35 V; eletrolítico: + no nó de saída) | nó de saída | GND |
| Carga R = 15 Ω (≥ 20 W) | nó de saída | GND |
| Medida de v~o~ | nó de saída | borne **VB** (o sensor de tensão da fase B mede v~o~) |
| — | borne VC | nada |

O GND da saída é o mesmo GND do barramento (borne GND do BOOSTXL). Os braços B e C ficam
desligados (GPIO2 a GPIO5 em nível baixo): com as duas chaves abertas, o borne VB não puxa
corrente e serve só de entrada para o divisor de 100 kΩ / 4,22 kΩ com 33 nF (filtro de 1,2 kHz).

## 2. Variáveis da Watch

| Variável | Padrão | Para quê |
|---|---|---|
| `habilita` | 0 | 1 liga o conversor, 0 desliga |
| `modoChave` | 0 | 0 = chave de baixo aberta (pedido do ensaio); 1 = síncrono (complementar, tempo morto de 100 ns). Só muda com `habilita` = 0 |
| `modo` | 0 | 0 = PRBS; 1 = onda quadrada (validação); 2 = razão fixa |
| `razaoD0` | 0,5 | ponto de operação |
| `amplitudePRBS` | 0,05 | amplitude da PRBS e da onda quadrada (d de 0,45 a 0,55) |
| `amostrasPorBit` | 4 | duração de um bit: 4 × 50 µs = 200 µs |
| `periodosMedia` | 16 | períodos da PRBS na média síncrona (1 a 64) |
| `amostrasQuadrada` | 200 | meio período da onda quadrada: 200 × 50 µs = 10 ms |
| `tempoRampa` | 0,2 s | tempo para a razão de operação andar 100 % (0 → 50 % em 0,1 s) |
| `correnteMaxima` | 1,5 A | proteção: \|i~L~\| acima disso desliga e marca `falha` |
| `tensaoMaxima` | 15 V | proteção: v~o~ acima disso desliga e marca `falha` |
| `resistenciaCarga` | 15 Ω | só para `correnteSaida` e `potenciaSaida` |
| `grava` | 0 | 1 recomeça a excitação e grava; 2 gravando; 3 calculando a média; volta a 0 no fim |

Para ver: `razaoAplicada`, `razaoOperacao`, `emRampa`, `correnteIndutor`, `correnteTopo`,
`tensaoSaida`, `tensaoBraco`, `tensaoBarramento`, `correnteSaida`, `potenciaSaida`, `falha`,
`periodoAtual`, `offsetZero`, `offsetTopo`.

**Partida em rampa**: ao ligar, a razão parte de 5 % e anda até `razaoD0` limitada por
`tempoRampa`; mudanças de `razaoD0` com o conversor ligado também andam em rampa. Sem ela, o degrau
de 0 a 50 % daria 1,4 A de pico no indutor e 12 V de pico na saída. A excitação só começa quando a
rampa termina (`emRampa` = 0).

**Proteção**: a interrupção desliga o buffer na hora (`falha` = 1, `habilita` = 0). Para religar:
`falha` = 0 e depois `habilita` = 1. Os primeiros 10 ms depois de ligar ficam fora da proteção (o
buffer, ao ligar, faz o sensor ler um pico falso; ver VSI01). A placa ainda tem a proteção própria
de 12 A.

## 3. O que é gravado: a matriz `DadosBuck` (8 × 2044 amostras de 50 µs = 102 ms)

| Linha | Variável | Conteúdo |
|---|---|---|
| 0 | d | razão aplicada (CMPA/TOPO) |
| 1 | iL | corrente no indutor [A], amostra no zero do contador (média) |
| 2 | vo | tensão de saída [V], sensor da fase B, filtro de 1,2 kHz (média) |
| 3 | Vdc | barramento [V] (média) |
| 4 | vA | tensão média do braço A [V], filtro de 1,2 kHz (média) |
| 5 | iL cru | i~L~ do último período, sem média |
| 6 | vo cru | v~o~ do último período, sem média |
| 7 | iL topo | corrente no topo do contador (meio do tempo desligado) [A] (média) |

16 352 valores, dentro do limite do *Graph - Time* do CCS (16 383). A corrente de saída não tem
sensor: i~o~ = v~o~/R na análise; i~C~ = i~L~ − i~o~.

No `modo` 0 com `amostrasPorBit` = 4, os 2044 pontos são exatamente um período da PRBS (511 bits):
o primeiro período é descartado e os `periodosMedia` seguintes entram na **média síncrona** (16
períodos: 17 × 102 ms ≈ 1,7 s, ruído ÷ 4). Nos `modos` 1 e 2 grava um registro só, sem média: as
linhas "média" e "cru" ficam iguais.

A corrente é sempre a amostra do zero do contador (meio do pulso da chave de cima): com o PWM
simétrico, em condução contínua, é o valor médio da ondulação. A razão escrita na amostra k vale a
partir do zero k + 1: conte com **atraso de 2 amostras** no ARX (nk = 2).

O zero do sensor de corrente é a média móvel com `habilita` = 0 (a fonte precisa estar ligada: sem
barramento o INA240 fica sem alimentação). Não dá para calibrar chaveando, como no VSI02, porque o
buck chaveando tem corrente. Um erro de zero constante não atrapalha o ARX, que usa desvios em torno
da média; compare `correnteIndutor` com `potenciaSaida`/`tensaoSaida` para conferir.

## 4. Ensaio

1. Monte o circuito da seção 1 **com a fonte desligada**. *Build* e *Debug* do
   **`BK02IdentificacaoGaN`** (*Run*).
2. Fonte em 20 V (limite de 0,5 A). Confira `tensaoBarramento` ≈ 20 V e `tensaoSaida` ≈ 0. Espere
   uns segundos com `habilita` = 0 (zero do sensor).
3. `modo` = 2 (razão fixa), `habilita` = 1. Espere a rampa (`emRampa` = 0). Esperado com
   d = 0,5: v~o~ ≈ 8,7 V, i~L~ ≈ 0,58 A, `tensaoBraco` ≈ 9,0 V (com a chave de baixo aberta,
   v~A~ = d(V~dc~ + 2) − 2). No osciloscópio, o nó VA vai de 20 V a ≈ −2 V.
4. **Ensaio de identificação**: `modo` = 0, `grava` = 1. Espere `grava` voltar a 0 (≈ 1,8 s).
   Pause e exporte `DadosBuck` (*Graph - Time*: float de 32 bits, 16352 valores; ou *Save Memory*,
   32704 palavras) como `DadosBuck01.csv`.
5. **Validação**: `modo` = 1 (onda quadrada de 20 ms), `grava` = 1, exporte `DadosBuck02.csv`.
6. Opcional: repita 3–5 com `modoChave` = 1 (desligue antes: `habilita` = 0) para comparar com o
   buck síncrono (v~o~ ≈ 9,7 V com d = 0,5, sem a queda de 2 V).
7. `habilita` = 0.

Análise: `python3 Buck/Ensaios/BuckBracoInversor/analise/simula_buck.py DadosBuck01.csv` (ARX por
mínimos quadrados e por Steiglitz–McBride, com ganho, polos e FIT).

## 5. Cuidados

- **Condução contínua**: com a chave de baixo aberta, se i~L~ chegar a zero o conversor entra em
  condução descontínua (o modelo deixa de ser linear e o *bootstrap* da chave de cima pode não
  recarregar). Com os valores da seção 1 e Δd = 0,05, i~L~ fica entre 0,26 e 0,92 A durante a
  PRBS. Não aumente `amplitudePRBS` nem a carga (R maior) sem simular antes.
- Fonte de 0,5 A: com d = 0,55 a fonte entrega ≈ 0,36 A. Acima de d ≈ 0,6 ela entra em limite.
- Pausar o programa desliga as duas chaves (CBC6, parada do emulador).
- Compilado e ligado com o cl2000 25.11 (sem erros); **ainda não testado na placa**.
