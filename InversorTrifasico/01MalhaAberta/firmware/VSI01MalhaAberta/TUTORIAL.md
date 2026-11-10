# VSI01MalhaAberta: inversor trifásico em malha aberta (LINCE/UFPA)

LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (nos conectores J1–J4), carga RL trifásica em estrela
(25 Ω e 10 mH por fase, neutro isolado), barramento de 20 V. O programa gera o PWM das três
fases, sem controle, e mede e grava as **tensões e as correntes das três fases**.

No site do projeto: *Bancada do Inversor Trifásico* (montagem, pinos, medidas, ordem de
ligação), *Inversor Trifásico em Malha Aberta: Roteiro* (o passo a passo com o osciloscópio e
os valores esperados) e *O Código do Inversor em Malha Aberta* (o `main.c` parte por parte).

## 1. O que é preciso

- **CCS** (Code Composer Studio) 20 ou mais novo, com o suporte a C2000.
- **C2000Ware 26.01** (o projeto usa a `driverlib`). Com outra versão, ajuste em
  *Project → Properties → Products*.
- Placas montadas como na Bancada: **jumper J6 do inversor retirado** (a LaunchPad é
  alimentada pela USB), fita Kapton entre as placas, encaixe em J1–J4 com 3V3 sobre 3V3.

## 2. Abrir no CCS

1. *File → Open Folder*: a pasta `InversorTrifasico` (ou a pasta descompactada do `.zip`).
2. Compile o `VSI01MalhaAberta` (*Build*) e inicie a depuração (*Debug*).
3. Para mudar um valor na Watch: pause com **‖** (*Suspend*), digite o valor, *Resume*. Com o
   programa pausado, as saídas de PWM vão para 0 (proteção). O **■** encerra a sessão e
   desconecta a placa: só no fim.

## 3. Variáveis da Watch

| Variável | Para quê |
|---|---|
| `modo` | 0 = 50 % nas três fases; 1 = 25/50/75 %; 2 = senoides; 3 = manual |
| `habilita` | 1 liga o inversor, 0 desliga |
| `amplitude`, `frequencia` | modo 2: razão = 0,5 + amplitude · sen (0,4 e 60 Hz) |
| `razaoManual[3]` | modo 3: razões de A, B, C (0,05 a 0,95) |
| `grava` | 1 começa a gravar; vale 2 gravando e volta a 0 no fim |
| `razaoAplicada[3]` | razões de fato aplicadas (CMPA/TOPO, limitadas a 5–95 %) |
| `tensaoAgora[3]`, `correnteAgora[3]` | última amostra de vA, vB, vC [V] e iA, iB, iC [A] |
| `tensaoBarramento` | Vdc [V] |
| `offsetCorrente[3]` | zero dos sensores de corrente [contagens], ≈ 2253 |

Vetores gravados (2000 amostras de 50 µs = 100 ms):

| Vetor | Conteúdo |
|---|---|
| `tensaoA/B/C` | tensões dos braços × GND [V], filtradas em 1 kHz |
| `correnteA/B/C` | correntes [A] no zero do contador (meio do pulso da chave de cima) |
| `correnteTopoA/B/C` | correntes [A] no topo do contador (meio do pulso da chave de baixo), 25 µs antes |
| `razaoA/B/C` | razão cíclica aplicada; tensão média do braço = razão × Vdc |
| `barramento` | Vdc [V] |

A razão gravada na amostra k só entra no PWM no zero seguinte (k + 1) e aparece inteira na
corrente a partir de k + 2. Corrente positiva = saindo do inversor para a carga. Enquanto
`habilita = 0`, o programa mede o zero dos sensores. Não há proteção de corrente por software;
a placa desliga sozinha acima de 12 A.

## 4. Etapa A: só a LaunchPad (USB)

Pontas em J4-40/39 (fase A, cima/baixo), J4-38/37 (B), J4-36/35 (C); terra em J2-20.

1. `modo = 0`: 20 kHz, 50 %, J4-40 o inverso de J4-39.
2. Zoom numa borda (50 ns/div): os dois em 0 por ≈ 100 ns (tempo morto); nunca os dois em 1.
3. `modo = 1`: J4-40, J4-38 e J4-36 com 25 %, 50 % e 75 %.
4. `modo = 2`, 5 ms/div: largura variando como senoide (60 Hz, 120° entre as fases).

## 5. Etapa B: com o inversor (20 V)

1. Programa rodando com `habilita = 0` e `modo = 0`. Fonte em 20 V com limite de 0,5 A; ligue
   a fonte: LEDs 5V e 3V3 do inversor acendem, `tensaoBarramento` ≈ 20 V.
2. `habilita = 1`. Osciloscópio em VA com a garra de terra **só no GND** (nunca em VA, VB, VC).
3. Com a carga: modo 1 dá −0,2 A, 0 e +0,2 A contínuos (fonte ≈ 0,1 A); modo 2 com amplitude
   0,4 dá 8 V e 0,32 A de pico a 60 Hz (fonte ≈ 0,19 A).
4. Gravar: `grava = 1`, espere `grava` voltar a 0 e pause. *Graph - Time*: expressão `correnteA`
   (ou outra), float de 32 bits, 2000 amostras, 20000 Hz. Para levar ao computador: exporte o
   Graph em CSV, ou *Save Memory* a partir de `0xC000`, `0x6000` palavras (tensões e
   correntes), formato *TI Data* (`.dat`) ou binário, e rode
   `python3 plota_medidas.py arquivo.dat` (em
   `InversorTrifasico/01MalhaAberta/apresentacoes/EnsaioMalhaAberta/analise/`).
5. Para desligar: `habilita = 0`, fonte, USB.

## 6. Se algo der errado

- **JTAG Communication Error (−1044)**: a sonda perdeu a placa (ruído ou alimentação).
  Encerre a sessão, desconecte a USB e a fonte, reconecte a USB, depois a fonte, e inicie a
  depuração de novo. Confira o J6 retirado e o cabo USB direto no computador.
- **"No compatible debug core found"**: reconecte a USB; se persistir, feche e abra o CCS.
- **Corrente da fase C estranha**: na LaunchPad rev. 1.1 o pino J3-29 está em curto com a
  referência do ADC.
