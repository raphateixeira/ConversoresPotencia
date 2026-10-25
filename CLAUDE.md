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
  passou de 2 K palavras: `--gen_func_subsections=on` no `.cproject` (como no VSI02).
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
  `VSI02ControleCorrente/`: carga RL (4,7 Ω, 1 mH, estrela); estrutura pedida pelo professor
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
