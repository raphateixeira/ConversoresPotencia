# VSI01MalhaAbertaCargaRL: inversor em malha aberta com carga RL (LINCE/UFPA)

LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (nos conectores J1–J4), carga RL trifásica em estrela
(25 Ω e 10 mH por fase, neutro isolado). Malha aberta, sem controle: as razões cíclicas das três
fases variam como senoides defasadas de 120°, e o programa mede e grava as **tensões e as
correntes das três fases**. O PWM é o mesmo do `VSI01MalhaAberta`.

## 1. O que é preciso

- **CCS** (Code Composer Studio) 20 ou mais novo, com o suporte a C2000.
- **C2000Ware 26.01** instalado (o projeto usa a `driverlib` e os cabeçalhos dela). Com outra
  versão, ajuste em *Project → Properties → Products*.
- Montagem das placas como no tutorial do `VSI01MalhaAberta`: **jumper J6 do inversor
  retirado** (a LaunchPad é alimentada pela USB), fita Kapton entre as placas, encaixe em
  J1–J4 com 3V3 sobre 3V3.

## 2. Abrir no CCS

1. Descompacte o `.zip`. *File → Open Folder*: a pasta descompactada (a que tem `.theia/`).
2. Compile o `VSI01MalhaAbertaCargaRL` (*Build*) e inicie a depuração (*Debug*), com a
   configuração `VSI01MalhaAbertaCargaRL`.
3. Para mudar um valor na Watch: pause com **‖** (*Suspend*), digite o valor, *Resume*. Com o
   programa pausado, as saídas de PWM vão para 0 (proteção). O **■** encerra a sessão e
   desconecta a placa: só no fim.

## 3. Variáveis da Watch

| Variável | Para quê |
|---|---|
| `habilita` | 1 liga o inversor, 0 desliga |
| `frequencia` | frequência das senoides [Hz] (60) |
| `grava` | 1 começa a gravar; vale 2 gravando e volta a 0 no fim |
| `tensaoAgora[3]`, `correnteAgora[3]` | última amostra de vA, vB, vC [V] e iA, iB, iC [A] |
| `tensaoBarramento` | Vdc [V] |
| `offsetCorrente[3]` | zero dos sensores de corrente [contagens], ≈ 2253 |
| `tensaoA/B/C` | vetores gravados: tensões dos braços × GND [V], filtradas em 1 kHz |
| `correnteA/B/C` | vetores gravados: correntes [A] no zero do contador (meio do pulso da chave de cima) |
| `correnteTopoA/B/C` | vetores gravados: correntes [A] no topo do contador (meio do pulso da chave de baixo), 25 µs antes |
| `razaoA/B/C` | vetores gravados: razão cíclica aplicada (CMPA/TOPO); tensão média do braço = razão × Vdc |
| `barramento` | vetor gravado: Vdc [V] |

Todos os vetores têm 2000 amostras de 50 µs (100 ms). A razão gravada na amostra k só entra no
PWM no zero seguinte (k + 1): na identificação, conte com um atraso de 1 a 2 amostras.

A amplitude é fixa no código: `AMPLITUDE` = 0,4 (razão cíclica de 0,1 a 0,9). Não há proteção
de corrente por software; a placa desliga sozinha acima de 12 A.

## 4. Medidas

| Grandeza | Pino do ADC | Conector | Conversão |
|---|---|---|---|
| vA, vB, vC | ADCINC3, ADCINB3, ADCINA3 | J3-24, J3-25, J3-26 | V = 24,7 · vpino (filtro de 1 kHz na placa) |
| iA, iB, iC | ADCINC2, ADCINB2, ADCINA2 | J3-27, J3-28, J3-29 | shunt de 5 mΩ + INA240: 1,65 V − 0,1 V/A · i |
| Vdc | ADCIN14 (ADCD) | J3-23 | V = 24,7 · vpino |

- Tudo é convertido uma vez por período de PWM (50 µs), no zero do contador da fase A.
- As tensões passam por um filtro RC de 1 kHz na placa: o ADC vê o **valor médio** da tensão
  do braço (senoide), não os pulsos. Para ver o chaveamento, use o osciloscópio no borne VA
  (garra só no GND).
- Corrente positiva = saindo do inversor para a carga. Enquanto `habilita = 0`, o programa
  mede o zero dos sensores (`offsetCorrente`).

## 5. Ensaio (barramento de 20 V, 60 Hz)

1. Programa rodando com `habilita = 0`. Fonte em 20 V com limite de 0,5 A; ligue a fonte.
   `tensaoBarramento` ≈ 20 V.
2. `habilita = 1`.
3. `grava = 1`, espere `grava` voltar a 0 e pause com **‖**.
4. *Graph - Time*: expressão `tensaoA` (ou `correnteA`, …), float de 32 bits, 2000 amostras,
   taxa de 20000 Hz.
5. Para levar os seis vetores ao computador de uma vez (a exportação da Watch só guarda os
   nomes, não os dados): janela **Memory**, *Save Memory*, endereço inicial `0xC000`, tamanho
   `0x6000` palavras, formato *TI Data* (`.dat`) ou binário (`.bin`). Depois:
   `python3 plota_medidas.py arquivo.dat` (na pasta
   `InversorTrifasico/Ensaios/InversorMalhaAberta/analise/`), que faz a figura e um CSV com
   `t_ms, vA, vB, vC, iA, iB, iC`.
6. Para desligar: `habilita = 0`, fonte, USB.

| | vA, vB, vC (× GND) | Fase na carga (pico) | Correntes (pico) | Fonte |
|---|---|---|---|---|
| Com a carga | 10 V ± 8 V | 8 V | 0,32 A (atraso de 8,6°) | ≈ 0,19 A |
| Sem carga | 10 V ± 8 V | — | ≈ 0 (ruído de algumas contagens de 7,3 mA) | ≈ 0 |

## 6. Se algo der errado

- **JTAG Communication Error (−1044)**: a sonda perdeu a placa (ruído ou alimentação).
  Encerre a sessão, desconecte a USB e a fonte, reconecte a USB, depois a fonte, e inicie a
  depuração de novo. Confira o J6 retirado e o cabo USB direto no computador.
- **"No compatible debug core found"**: reconecte a USB; se persistir, feche e abra o CCS.
- **Corrente da fase C estranha**: na LaunchPad rev. 1.1 o pino J3-29 está em curto com a
  referência do ADC.
