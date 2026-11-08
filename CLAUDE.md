# CLAUDE.md

`ConversoresPotencia` (público, Pages em raphateixeira.github.io/ConversoresPotencia/) junta, desde
2026-10-25, `ControleBuck`, `ControleInversor3f`, `ControleVSI`, `MicroGrids` (cada um inteiro numa
subpasta, com histórico) e a parte Buck/inversor do `ProjetosCCS`. Os repositórios antigos foram
arquivados com redirecionamento. `ControleCC2CC` ficou de fora (IC com colaborador externo).

- Um único projeto Quarto na raiz: **não criar `_quarto.yml` em subpastas** (viraria outro projeto).
  Páginas novas entram em `project.render` e no menu do sistema em `website.navbar.right`.
- **Uma só página índice** (`index.qmd` da raiz), com uma seção por sistema e links diretos para o
  conteúdo; não criar índices por subpasta. Âncoras fixas usadas na navbar: `#buck`, `#firmware-buck`,
  `#inversor`, `#carga-rl`, `#firmware-inversor`, `#conectado-rede`, `#microrredes`.
- Caminhos para a raiz: tema `TemaRTx.scss` e `imgs/ufpa-colorido.png` com `../` conforme a profundidade.
- Bibliografia do Buck em `Buck/_metadata.yml`; as notas do ConectadoRede e do Microrredes declaram a sua.
- Firmware: `Buck/Firmware/` e `InversorTrifasico/Firmware/` são workspaces do CCS (`.theia/`); a numeração
  `VSINN` do firmware é a mesma das simulações em `InversorTrifasico/ConectadoRede/`.
  Sequência (renumerada em 2026-11-08): VSI01 malha aberta → VSI02 identificação ARX → VSI03 controle PI →
  VSI04 controle FCS (MPC de corrente) → VSI05 potência PI → VSI06 potência MPC → VSI07–09 iguais. Antes:
  VSI02 = ControleCorrente(PI), VSI03 = PotênciaPI, VSI05 = PotênciaMPC, VSI06 = IdentificaçãoARX.
- Detalhes das simulações: `InversorTrifasico/ConectadoRede/CLAUDE.md`.
- Visual: cabeçalho `.rtx-hero` e cartões `.categoria-card` do TemaRTx (não inventar paleta).

## Firmware (anotações trazidas do CLAUDE.md do ProjetosCCS)

Padrões comuns aos projetos da LaunchPad (struct de parâmetros, `placa.c/.h`, exportação pela Watch,
cuidados com `-O2`) estão no CLAUDE.md do `ProjetosCCS`.

- `InversorTrifasico/Firmware/` — projetos do CCS do inversor trifásico (LAUNCHXL-F28379D + **BOOSTXL-3PHGANINV**
  em J1–J4: ePWM1/2/3 = braços A/B/C em GPIO0–5, GPIO124 = /PWM enable **ativo em nível
  baixo** (0 liga o buffer; o VSI01 antigo estava invertido), como no
  MotorControl SDK `solutions/boostxl_3phganinv/f2837x`). Sem barramento, o BoosterPack fica
  sem 5 V/3,3 V (LM5017): INA240 e buffer desligados, os comparadores disparam. Outro *workspace* do CCS (pasta própria com `.theia/`).
  `VSI01MalhaAberta/` = **primeiro experimento, para iniciantes** (reescrito em 2026-10-23 a
  partir de uma proposta do professor, revisada): **um `main.c` só**, nomes descritivos em
  português (`TOPO`, `TEMPO_MORTO`, `CONTAGENS_MORTO`, `razaoCiclica[3]`, `AtualizaPWM`,
  `ConfiguraModuloPWM`, `EscreveRazao`, `ConfiguraPinos`), variáveis na janela **Watch**
  (`modo` 0 = 50 % / 1 = 25-50-75 % / 2 = senoidal, `habilita`, `indice`, `frequencia`).
  fPWM = 20 kHz, tempo morto 100 ns, razão limitada a 5–95 %, CBC6 (parada do emulador) força
  A e B em 0, contadores sincronizados só pelo TBCLKSYNC (a cadeia de sync da proposta foi
  retirada: faltava `setCountModeAfterSync`). Mede as tensões das fases do BoosterPack
  (ADCINC3/B3/A3 = vA/vB/vC, ×24,7, filtro de 1 kHz) e o barramento (ADCIN14, ADCD), SOCA do
  EPWM1 no zero, lidos na ISR depois do ADCINT1; `grava` = 1 → 2 (gravando) → 0 enche
  `tensaoA/B/C` (2000 floats, `ramgs0..2`), exportados da Watch para CSV e lidos por
  `InversorTrifasico/Ensaios/InversorMalhaAberta/analise/plota_tensoes.py`. Com o ADC, o `.text` do `main.obj`
  passou de 2 K palavras: `--gen_func_subsections=on` no `.cproject` (como no VSI03).
  `VSI01MalhaAbertaSemGravacao/` = cópia da versão **testada na placa** em 2026-10-23 (modos
  0–3, sem ADC; código de máquina do `main.obj` idêntico ao build que funcionou). Na versão com
  ADC, as funções do PWM (`ConfiguraPinos`, `ConfiguraModuloPWM`, `EscreveRazao`) têm código de
  máquina idêntico ao testado; só entraram as chamadas a `ConfiguraADC`/`LeTensoes`. `TUTORIAL.md` na
  pasta. Apresentação `InversorTrifasico/Ensaios/InversorMalhaAberta/` (revealjs, 31 slides, figuras e GIFs gerados
  por `analise/figuras.py`, inclusive a montagem das placas a partir das figuras da TI e a
  simulação da carga RL a 12 V). Modo 3 = razão manual (`razaoManual[3]`). A apresentação
  inclui o mapa dos pinos (`imgs/pinos_launchpad.png`, serigrafia da SPRUI77C fig. 18 girada) e
  um filtro RC de 10 kΩ/100 nF (corte de 159 Hz) para ver a senoide do modo 2, nos pinos J4 ou
  nos bornes VA/VB/VC.
  `VSI01MalhaAbertaCargaRL/` (2026-11-04, **testado na placa**): o `main.c` do VSI01MalhaAberta com um
  modo só (senoides, `AMPLITUDE` = 0,4 fixa, sem `indice`), carga 25 Ω/10 mH, Vdc = 20 V. ADC: SOC0 =
  tensão (ADCIN3, como no VSI01), SOC1 = corrente (ADCIN2), INT1 no fim do SOC1 da ADCA; zero dos INA240
  por média móvel enquanto `habilita` = 0; `grava` enche `tensaoA/B/C` e `correnteA/B/C` (`ramgs0..5`).
  **Sem proteção por software**: a de 1 A desligava no 1º período (iC lia −1,2 A falsos ao ligar), por
  isso o inversor parecia não chavear. Mapeamento dos pinos conferido nos `.syscfg.json` do MotorControl
  SDK (BOOSTXL-3PhGaNInv e LAUNCHXL_F28379D). Corrente medida a 20 V com a carga: 0,32 A de pico.
  `VSI02IdentificacaoARX/` (2026-11-05, ainda não testado na placa): base `VSI01MalhaAbertaCargaRL`;
  v_dq = (tensaoD0, tensaoQ0) + amplitudePRBS·PRBS (9 bits, **polinômios diferentes** em d e q:
  x^9+x^5+1 e x^9+x^4+1, |xcorr| < 0,09; mesmo polinômio com sementes diferentes repete a sequência
  com atraso de 382 bits), `eixoPRBS` 0 dq / 1 d / 2 q, `amostrasPorBit` = 4 → N = 2044 = um período;
  `grava` = 1 reinicia a PRBS. Park inversa (invariante em amplitude, vA = vd cos θ), d = 0,5 + v/Vdc
  (Vdc filtrado). Corrente combinada no firmware (zero se d ≥ 0,5, topo se d < 0,5, offsets próprios).
  Grava 12 vetores (`ramgs0..6`, `ramgs8..12`). Padrão 5 V ± 3 V (|v| ≤ 8,5 V < 0,45 Vdc); simulação
  do ensaio: sem ruído recupera polo 0,8825, com 10 mA o LS dá 0,86 (viés de erro de equação).
  Ensaio real (2026-11-06, 20 V, 1 período, `Dados3FRL/Identificacao/`): melhor ARX = MIMO 1,2,2 sem
  tensão cruzada, IV (R ≈ 26 Ω, L ≈ 10 mH, ajuste 85 % = teto do ruído; atraso 2 + fração pela mistura
  zero/topo). **Média síncrona** (2026-11-06): `periodosMedia` (padrão 8) descarta o 1º período e
  acumula id/iq nos seguintes; divisão no laço principal (`grava` = 3), não na ISR. Simulação: 40 V
  (10 ± 6 V) + 8 períodos → ajuste ≈ 96 %. Padrão `periodosMedia` = 16 (fonte só até 20 V).
  Desde 2026-11-08 grava numa matriz só, `Dados3F[12][2044]` (linhas iA iB iC dA dB dC Vdc θ vd vq id iq),
  seção `Dados3F` na faixa `RAMGS0_12` (RAMGS0–12 fundidos nos dois `.cmd`; 49056 de 53248 palavras);
  exporta-se `Dados3F` no Graph (24528 floats) ou Save Memory; `analise/organiza_dados3f.py` e
  `identifica.le_dados3f()` leem .csv/.bin/.dat.
  Ensaio de 2026-11-08 (`Dados3FRL/Dados01A.csv`): o Graph do CCS exporta **no máximo 16383 valores**
  (perdeu vd, vq, id, iq); soma iA+iB+iC = 0,2 A e topo 25 mA abaixo do zero (zero mal medido).
  Por isso: linhas reordenadas (vd vq id iq iA iB iC θ | Vdc dA dB dC; exportar 16352 = 8 linhas;
  `CANAIS_ANTIGOS` lê o Dados01A) e **calibração chaveando** ao habilitar (110 ms a 50 %, `calibrando`
  = 1, somas inteiras de 2000 amostras; `grava` espera o fim). `identifica.corrige_salto()` corrige o
  salto pela soma das correntes (sem modelo).
  Desde 2026-11-08 a apresentação `IdentificacaoARXDados` usa **só mínimos quadrados** (com a média de 16
  períodos LS = IV). A variável instrumental fica guardada para uso futuro (ruído maior, um período só:
  LS dá R ≈ 31 Ω): `estima(..., "IV")` e `METODO`/`METODOS` em `identifica.py`; a apresentação de simulação a mostra.
  `VSI03ControlePI/` (2026-11-08, ainda não testado na placa): base `VSI02IdentificacaoARX` (hardware, leitura
  zero/topo, calibração chaveando, `Dados3F` idênticos); PI por eixo com kp = 2πfcL, ki = 2πfcR (`bandaPI` = 300 Hz,
  R = 26,2 Ω, L = 9,8 mH), desacoplamento ωL (`desacopla`), |v| ≤ 0,45 Vdc com anti-windup (integrador para quando
  satura), proteção por software `correnteMaxima` (0,8 A, só após a calibração; `falha`), `modo` 0 = malha aberta.
  Referências: `referenciaD0` 0,15 A + `degrauD` 0,1 A (10–60 ms), `referenciaQ0` 0 + `degrauQ` −0,05 A (35–85 ms),
  perfil de 2044 amostras repetido (média síncrona). `Dados3F`: idRef iqRef id iq vd vq (médias) iA iB (iC = −iA − iB).
  Park das correntes e inversa com o mesmo ângulo (como no VSI02). Simulação e leitura dos dados:
  `Ensaios/ControlePIDados/analise/simula_pi.py` (300 Hz: subida ≈ 1 ms, |v| ≤ 6,7 V).
  `VSI03ControlePIModular/` (ex-VSI02ControleCorrente, nunca testado): carga RL (4,7 Ω, 1 mH, estrela); estrutura pedida pelo professor
  (`main.c`, `hal.c/h`, `controle.c/h`, `tarefas.c/h`, não `placa.c`). ISR = ADCA INT1 (SOCA do
  EPWM1 no zero, a cada `nControle` períodos); correntes ADCINC2/B2/A2 (iA/iB/iC), vA/vB/vC em
  C3/B3/A3, Vdc em ADCIN14 (ADCD); i = −7,32 mA·(N − N0) (REF5030 de 3,0 V, INA240 0,1 V/A,
  invertido), V = 24,7·vADC; CMPSS6/3/1 + GPIO24 → TRIP4 → DCAEVT1 → OST; limiar em torno do
  offset medido. Níveis 1 (50 %), 2 (malha aberta), 3 (PI dq + desacoplamento, kp = 2πfcL,
  ki = 2πfcR), 4 (identificação: PRBS 9 bits/degrau/multisseno Schroeder em v_dq). Registro de 4
  canais × 2000 em `ramgs0..3`, multisseno em `ramgs4`. UART SCIA 115200 com comandos de texto
  (S, H, D, L, C, N, F, V, R, P, E, I, M, G, B; ver `tarefas.h`). Precisa de
  `--gen_func_subsections=on` (no `.cproject`); no `.cmd` de FLASH o `.text` não usa a FLASHB.
  Compilado fora do CCS com o cl2000 de `/Applications/Texas/ccs2101` (RAM e FLASH linkam).
  Pendentes: script Python do PC (Etapa 3) e `TUTORIAL.md` (Etapa 4).
- `Buck/Firmware/` — projetos do CCS do conversor buck da IC (`Buck/`: Vin = 30 V,
  L = 525 µH, C = 41,7 µF, R = 1 Ω, MOSFET + diodo → uma chave só). Outro *workspace* do CCS
  (pasta própria com `.theia/`). Saída da placa por **PWM** (EPWM1A, GPIO0, J4.40), não pelo DAC;
  y no ADCINA3 (J3.26) via divisor `kSensor`; ADC disparado pelo SOCA do ePWM1 (contador = 0).
  Dois structs no `main.c`: `ParametrosConversor` (fPWM, Ts, Vin, uMax, kSensor) e
  `ParametrosDegrau`. `BK01Degrau/`: malha aberta, u = d·Vin; rampa 0→10 V (0,5 s),
  acomodação (0,5 s), onda quadrada 10↔12 V (Tq = 20 ms), fPWM = 20 kHz, Ts = 50 µs,
  grava `uV` (tensão comandada) e `yV` (2000 amostras, `ramgs0`/`ramgs1`).
  `PWM_prbs/` (projeto do aluno, nome interno `Gpio_PWM`, **não renomear arquivos**): registradores
  bitfield, laço por *polling* do ADCINT1, PRBS de 9 bits [9 5 0] com `PRBS_NB` = 4 (Tb = 200 µs),
  Ts = 50 µs, `TAM_EXP` = 2044 (um período), `DadosBuck[3][TAM_EXP]` (t, d, y). Arquivos em
  ISO-8859-1 com CRLF (preservar); caminhos da C2000Ware apontam para `D:\TexasInstruments` (Windows).
  Nota de identificação do buck (`Buck/Ensaios/IdentificacaoBuckPRBS/`, revealjs **sem Jupyter**: código em MATLAB,
  `analise/ident_buck.m` gera as figuras em `imgs/`; números dos slides copiados da saída do
  script): modelo médio G(s) = 1,532e9/(s²+2400s+5,106e7) (entrada d), Ts = 50 µs, PRBS de
  9 bits com Nb = 4, ARX(2,2,2) (atraso extra do CMPA com sombra), ruído de medida σ = 20 mV,
  validação em outro trecho da PRBS e na onda quadrada do BK01. Sem slides de roteiro nem
  divisores de seção. Notação: D = D0 + d, Vo = Vo0 + y (d e y sem til no ARX). Cabeçalhos de tabela do tema ficam em maiúsculas: unidades/math no cabeçalho vão em
  `[...]{style="text-transform:none"}`.
