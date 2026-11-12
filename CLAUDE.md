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
- Bibliografia do Buck em `Buck/_metadata.yml`; as notas das SimulacoesMatlab e do Microrredes declaram a sua.
- Inversor (reorganizado em 2026-11-08): `InversorTrifasico/` tem uma pasta por etapa de ensaio,
  `01MalhaAberta/` … `06ControleKoopman/`, cada uma com `firmware/` (projetos do CCS), `dados/` (CSV exportados)
  e `apresentacoes/<Nome>/` (index.qmd, `imgs/`, `analise/`); `00Bancada/` (uma apresentação só, `apresentacoes/BancadaInversor/`, desde 2026-11-10: inversor, braço,
  tempo morto, estados, PWM; fonte trifásica, carga 25 Ω/10 mH, Clarke/Park, dq, discreto, atraso; placas, montagem,
  pinos, sensores, proteção, ordem de ligação; PDFs da TI em `00Bancada/docs/`, fora do git). **A teoria fica só
  ali**: as apresentações das etapas citam a Bancada em vez de repetir (a Nota 01 das simulações foi apagada). `PlanoIC03/` (IC da Alessandra) e `SimulacoesMatlab/` (ex-ConectadoRede: simulações
  MATLAB/Simulink VSI01–09, conteúdo intocado). Scripts de análise acham os dados e os scripts de outras etapas
  por `AQUI.parents[2] / "dados"` e `AQUI.parents[3] / "<etapa>/apresentacoes/<Nome>" / "analise"`.
- Firmware: `Buck/Firmware/` e `InversorTrifasico/` são workspaces do CCS (`.theia/`); a numeração
  `VSINN` do firmware é a mesma das simulações em `InversorTrifasico/SimulacoesMatlab/` até VSI04; o firmware VSI05
  (FCS + RLS) corresponde à simulação VSI08.
  Firmware (2026-11-08): VSI01 malha aberta → VSI02 identificação ARX → VSI03 controle PI → VSI04 FCS-MPC →
  VSI05 FCS + RLS (o PI modular antigo foi retirado). Simulações: VSI01–04 iguais, VSI05 potência PI, VSI06 potência
  MPC, VSI07 RST, VSI08 MPC adaptativo RLS, VSI09. Antes da renumeração:
  VSI02 = ControleCorrente(PI), VSI03 = PotênciaPI, VSI05 = PotênciaMPC, VSI06 = IdentificaçãoARX.
- Detalhes das simulações: `InversorTrifasico/SimulacoesMatlab/CLAUDE.md`.
- Visual: cabeçalho `.rtx-hero` e cartões `.categoria-card` do TemaRTx (não inventar paleta).

## Firmware (anotações trazidas do CLAUDE.md do ProjetosCCS)

Padrões comuns aos projetos da LaunchPad (struct de parâmetros, `placa.c/.h`, exportação pela Watch,
cuidados com `-O2`) estão no CLAUDE.md do `ProjetosCCS`.

- `InversorTrifasico/<etapa>/firmware/` — projetos do CCS do inversor trifásico (LAUNCHXL-F28379D + **BOOSTXL-3PHGANINV**
  em J1–J4: ePWM1/2/3 = braços A/B/C em GPIO0–5, GPIO124 = /PWM enable **ativo em nível
  baixo** (0 liga o buffer; o VSI01 antigo estava invertido), como no
  MotorControl SDK `solutions/boostxl_3phganinv/f2837x`). Sem barramento, o BoosterPack fica
  sem 5 V/3,3 V (LM5017): INA240 e buffer desligados, os comparadores disparam. Outro *workspace* do CCS (pasta própria com `.theia/`).
  `VSI01MalhaAberta/` = **primeiro experimento, para iniciantes**, firmware único da etapa 01 desde 2026-11-10
  (fusão do VSI01MalhaAberta de 2026-10-23, modos 0–3, com o VSI01MalhaAbertaCargaRL de 2026-11-04, **testado
  na placa**; as duas cópias e a SemGravacao foram apagadas, ficam no histórico). **Um `main.c` só**, nomes
  descritivos em português (`TOPO`, `TEMPO_MORTO`, `CONTAGENS_MORTO`, `razaoCiclica[3]`, `AtualizaPWM`,
  `ConfiguraModuloPWM`, `EscreveRazao`, `ConfiguraPinos`, `LeMedidas`). Watch: `modo` 0 = 50 % / 1 = 25-50-75 % /
  2 = senoides (`amplitude` 0,4, `frequencia`) / 3 = `razaoManual[3]`; `habilita`; `grava`. Padrão `modo` = 0.
  fPWM = 20 kHz, tempo morto 100 ns, razão limitada a 5–95 %, CBC6 (parada do emulador) força A e B em 0,
  contadores sincronizados só pelo TBCLKSYNC (a cadeia de sync da proposta foi retirada: faltava
  `setCountModeAfterSync`). ADC: SOC0 = tensão (ADCINC3/B3/A3, ×24,7, filtro de 1 kHz), SOC1 = corrente
  (ADCIN2), SOC2 = corrente no topo (SOCB), barramento ADCIN14 (ADCD); INT1 no fim do SOC1 da ADCA, lido na ISR;
  zero dos INA240 por média móvel enquanto `habilita` = 0; `grava` enche 13 vetores (`ramgs0..6`, `ramgs8..13`).
  `--gen_func_subsections=on` no `.cproject`. **Sem proteção por software**: a de 1 A desligava no 1º período
  (iC lia −1,2 A falsos ao ligar). Mapeamento dos pinos conferido nos `.syscfg.json` do MotorControl SDK.
  Corrente medida a 20 V com a carga (modo 2, 0,4): 0,32 A de pico. A versão testada não tinha `modo` (só as
  senoides) e tinha um `A{` perdido na linha 131 (não compilava): corrigido na fusão; a fusão em si ainda
  não foi compilada no CCS nem testada na placa. `TUTORIAL.md` na pasta.
  Apresentações da etapa 01, em sequência: `RoteiroMalhaAberta` (modos, osciloscópio, filtro RC de 10 kΩ/100 nF,
  carga RL, valores esperados a 20 V; `analise/figuras.py` importa PWM e cores de
  `00Bancada/.../analise/figuras_placa.py`), `CodigoMalhaAberta` (o `main.c` parte por parte, **com números de
  linha**: atualizar se o `main.c` mudar) e `EnsaioMalhaAberta` (ensaios 1 e 2; `analise/plota_medidas.py` lê o
  Save Memory). Os CSV dos ensaios (`01MalhaAberta/dados/Dados01.csv`, `Dados02.csv`, `Dados02RB.csv`) nunca
  foram versionados.
  `VSI02IdentificacaoARX/` (2026-11-05, ainda não testado na placa): base `VSI01MalhaAberta` (versão carga RL);
  v_dq = (tensaoD0, tensaoQ0) + amplitudePRBS·PRBS (9 bits, **polinômios diferentes** em d e q:
  x^9+x^5+1 e x^9+x^4+1, |xcorr| < 0,09; mesmo polinômio com sementes diferentes repete a sequência
  com atraso de 382 bits), `eixoPRBS` 0 dq / 1 d / 2 q, `amostrasPorBit` = 4 → N = 2044 = um período;
  `grava` = 1 reinicia a PRBS. Park inversa (invariante em amplitude, vA = vd cos θ), d = 0,5 + v/Vdc
  (Vdc filtrado). Corrente combinada no firmware (zero se d ≥ 0,5, topo se d < 0,5, offsets próprios).
  Grava 12 vetores (`ramgs0..6`, `ramgs8..12`). Padrão 5 V ± 3 V (|v| ≤ 8,5 V < 0,45 Vdc); simulação
  do ensaio: sem ruído recupera polo 0,8825, com 10 mA o LS dá 0,86 (viés de erro de equação).
  Ensaio real (2026-11-06, 20 V, 1 período, `02IdentificacaoARX/dados/` (dados antigos apagados)): melhor ARX = MIMO 1,2,2 sem
  tensão cruzada, IV (R ≈ 26 Ω, L ≈ 10 mH, ajuste 85 % = teto do ruído; atraso 2 + fração pela mistura
  zero/topo). **Média síncrona** (2026-11-06): `periodosMedia` (padrão 8) descarta o 1º período e
  acumula id/iq nos seguintes; divisão no laço principal (`grava` = 3), não na ISR. Simulação: 40 V
  (10 ± 6 V) + 8 períodos → ajuste ≈ 96 %. Padrão `periodosMedia` = 16 (fonte só até 20 V).
  Desde 2026-11-08 grava numa matriz só, `Dados3F[12][2044]` (linhas iA iB iC dA dB dC Vdc θ vd vq id iq),
  seção `Dados3F` na faixa `RAMGS0_12` (RAMGS0–12 fundidos nos dois `.cmd`; 49056 de 53248 palavras);
  exporta-se `Dados3F` no Graph (24528 floats) ou Save Memory; `analise/organiza_dados3f.py` e
  `identifica.le_dados3f()` leem .csv/.bin/.dat.
  Ensaio de 2026-11-08 (`InversorTrifasico/02IdentificacaoARX/dados/Dados01A.csv`): o Graph do CCS exporta **no máximo 16383 valores**
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
  `InversorTrifasico/03ControlePI/apresentacoes/ControlePIDados/analise/simula_pi.py` (300 Hz: subida ≈ 1 ms, |v| ≤ 6,7 V).
  VSI03 testado na placa em 2026-11-08 (`InversorTrifasico/03ControlePI/dados/DadosControlePI01.csv`, 300 Hz com desacoplamento): subida
  0,9 ms, sem sobressinal, igual à simulação; regime dá R = 25,3 Ω (o ARX superestima 3 %). Apresentação
  `InversorTrifasico/03ControlePI/apresentacoes/ControlePIDados` (`analise/analisa_pi.py`).
  `VSI04ControleFCS/` (2026-11-08, testado: `InversorTrifasico/04ControleFCS/dados/ControleFCS01.csv` cru, `ControleFCS02.csv` média 16; subida
  0,15 ms, sobressinal 5 %, ondulação ±30 mA, fsw 3,40 kHz reconstruído dos estados = simulação; `analise/analisa_fcs.py`): base VSI03; `modo` 2 = FCS-MPC (padrão), 1 = PI, 0 = malha aberta.
  Testa os 8 estados a cada 50 µs em αβ (a = e^(−RTs/L), b = (1−a)/R; meio passo para compensar o atraso),
  custo |i* − î(k+3/2)|² + `lambdaComutacao`·n; chaveia por forçamento contínuo das saídas A do ePWM
  (`EPWM_setActionQualifierContSWForceAction`, sombra no TOPO) e lê a corrente no zero; volta ao PWM com
  `LiberaPWM`. `frequenciaChaveamento` (média, janela de 1 s). R = 25,3 Ω. Simulação e apresentação:
  `InversorTrifasico/04ControleFCS/apresentacoes/ControleFCS` (`analise/simula_fcs.py`; 20 V: fsw ≈ 3,4 kHz, erro rms 16 mA; 15 V: 12 mA).
  `VSI05MPCAdaptativoRLS/` (2026-11-08, testado; ex-VSI08; simulação equivalente: SimulacoesMatlab/VSI08): base VSI04;
  RLS de 3 parâmetros em αβ, i(k+1) = θ1 i(k) + θ2 v(k−1) + θ3 v(k) (v/Vdc), 2 atualizações por amostra, λ = 0,999,
  P0 = 100 I, limites R 0,5–1,5× e L/R 0,5–2× do modelo inicial (`rejeicoes`), proteção de P (`reinicioP`); o RLS roda
  depois da decisão; FCS prevê i(k+2) com θ. `metodoRLS` 1 = variável instrumental POR PREDIÇÃO
  (z = [î(k−1|k−2), v(k−2), v̂(k−1)], v̂ = vetor que o FCS escolheria com a corrente prevista; `InstrumentoIV`).
  Variável `cenario` 1–4 configura o ensaio (1 modelo errado fixo 35 Ω/14 mH, média 16; 2 RLS recomeça, cru;
  3 adaptativo, média 16; 4 IV por predição, cru); cenário e modelo tratados na interrupção (o laço principal pode
  ficar sem CPU). Compilar com -O2 e `--fp_mode=relaxed` (TMU): sem isso a interrupção não cabia. Dados3F: θ1 θ3 id iq
  vd vq iA iB; tempos por CPU Timer 1 (Watch `tempoMedio*`, `tempoMaximoTotal`, `folgaMinima`, `perdasPrazo`;
  matriz `Tempos[4][2044]`, export 8176).
  Ensaio (`InversorTrifasico/05FCSAdaptativoRLS/dados/DadosRLS01..04`, `Tempos02/04`): RLS converge de 35 Ω/14 mH em ~10 ms para 25,3 Ω/9,0 mH;
  erro em regime −11 → +6 mA; IV por predição: 25,7 Ω/10,0 mH em ~10 ms (sem viés de L); ISR 15,9 µs (RLS) e
  19,3 µs (IV) de 50 µs. Tentativas descartadas: IV atrasada (instrumento fraco, divergiu) e IV com FCS simulado
  em malha fechada (instável). Análise: `InversorTrifasico/05FCSAdaptativoRLS/apresentacoes/ControleFCSRLS/analise/` (`simula_rls.py`, `analisa_rls.py`,
  `analisa_ensaio_rls.py`, `fig_iv_ensaio.py`).
  Próximo passo possível (não iniciado): aprendizagem por reforço no lugar do FCS e do RLS — ação discreta
  (8 estados, tipo DQN), recompensa = −custo do FCS; treino em simulação com R, L, Vdc, ruído, atraso e tempo morto
  variados (base `simula_rls.py`), começando por imitação do FCS; adaptação pelo histórico/rede recorrente ou θ do
  RLS como entrada; na placa só a inferência, FCS+RLS como alternativa de segurança. Variante de menor risco: RL
  residual/supervisora ajustando o custo do FCS. Comparar pelos cenários 1–4.

  `06ControleKoopman/` (2026-11-10): controle baseado em dados (Koopman/EDMD). Projeto em MATLAB (`matlab/principal.m`,
  scripts k01–k05, funções em arquivos próprios; figuras em `apresentacoes/ControleKoopman/imgs`): k01 EDMD nos dados da
  PRBS (dicionário de atrasos: FIT 63 → 96 %; monômios não ajudam; autovalores 0,875 ± j0,016); k02 EDMD nos dados do FCS
  (z = [i; s(k−1)], u = s(k), αβ; R/L 24,9 Ω/8,9 mH, validado no ensaio do RLS); k03 ensaio proposto em malha aberta com
  vetores pseudoaleatórios (LFSR 0xACE1/0xB400, 2 amostras/símbolo) + média de 16 → 25,4 Ω/9,8 mH (malha fechada vicia L);
  Koopman-FCS simulado = FCS físico (+0,2 mA); custo em k+3/2 (média de î(k+1), î(k+2)) — custo em k+2 dá +5 mA (explica
  o +6 mA do VSI05); k04 indutor saturável (hipótese): levantado prevê melhor mas não ganha em malha fechada.
  Firmware `VSI06ControleKoopman` (base VSI05, não testado): cenário 1 identificação + EDMD na placa (`CalculaEDMD`, 6×6
  double, laço principal) → `koopmanG`, `modeloPronto`; 2 Koopman-FCS média 16; 3 físico média 16; 4 Koopman cru.
  LFSR e EDMD conferidos com o MATLAB (idênticos). Dados em `06ControleKoopman/dados/Koopman0N.csv` (`k05_analisa_ensaio.m`).

  `07ControleDeePC/` (2026-11-10, só simulação, sem firmware; **tema do primeiro artigo internacional da linha**,
  prévia em português no modelo IEEE Access em `~/Artigos/ArtigoDeePC/PaperIEEEAccessDeePC_PT.tex`, fora do repositório
  público): DeePC/SPC com os dados reais da PRBS (`dados/prbs_dq.csv`), forma incremental (Δv, Δi), Hankel circular,
  T_ini = 2, N = 10, q = 1, r_u = 1e-2, λ_g = 3 (em `parametros.m`). `matlab/principal.m` roda t00 (testes) e d00–d12, cada
  etapa em escopo próprio; números em `matlab/resultados/dNN.mat`; `salva.m` grava PNG em `imgs/` e PDF vetorial na
  pasta do artigo, se existir. Funções: `simula_dq` (planta 'media' ou 'pwm' chaveada com tempo morto; opções alfa,
  atraso, w, dv, troca; tipos mpc/mpcabs/pi/ma; `.fgm` = gradiente rápido projetado), `ganhos` (spc, spcc, deepc, arx,
  fisico, oraculo), `malha_linear` (malha fechada como ss: rho, margens de disco, banda, ganhos H2 de ruído),
  `gera_dados` (repete a PRBS em simulação), `desempenho` (nota J = erro rms de rastreamento no período),
  `simula_adaptativo`. Cores fixas por entidade: DeePC/SPC azul, FCS laranja, prévia/2ª variante verde, modelo/indireto
  magenta tracejado, PI cinza tracejado (paleta conferida para daltonismo; **sem eixo duplo**).
  Resultados (simulação): o simulador PWM reproduz a PRBS real melhor que o médio (4,2 × 6,8 mA; a rotação do
  referencial no atraso, 1,6°, explica i_q e v_q); PI 300 Hz medido × simulado: 2,1 mA rms; o preditor da PRBS prevê o
  ensaio do PI com FIT 94 %; T_ini filtra ruído (10 passos: 8,9 → 3,4 mA de T_ini 2 a 6). Lei linear de ordem 6: SPC
  dados reais = MPC modelo certo (banda 692 Hz, MG 9,7 dB, MF 54°); PI 500 Hz tem margem maior na mesma banda (12,2 dB).
  Estável em 99 % da grade R, L de 0,15 a 6×; ganho até 5,5×; 3 amostras a mais de atraso. Monte Carlo: SPC = oráculo
  até 8,5 mA e com 100 amostras; indiretos (ARX, físico) nunca perdem; **DeePC com λ_g fixo piora +35 % a 8,5 mA**
  (+42 % com os dados reais de 1 período): recomendar a forma SPC. Dados de 60 Hz valem até ≈ 120 Hz. Cortar a tensão =
  ótimo restrito; FGM converge em 3 iterações. Lei: 20 contas por amostra (56 com prévia); Gram + Cholesky em float32
  dá os mesmos ganhos (erro 1e-6). Adaptação com dados de malha fechada é viesada; re-ensaio de 10 ms em malha aberta
  (200 amostras) devolve J = 9,6 mA. Apresentação `apresentacoes/ControleDeePC` (55 slides, 7 partes, com protocolo de
  ensaios E1–E8 e proposta do artigo). Falta: firmware `VSI07ControleDeePC` (base VSI03) e os ensaios na bancada;
  referências marcadas "a conferir" foram citadas de memória.

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
  divisores de seção. Notação: D = D0 + d, Vo = Vo0 + y (d e y sem til no ARX).
  `BK02IdentificacaoGaN/` (2026-11-12, compila no cl2000, **não testado na placa**): buck no **braço A do
  BOOSTXL-3PHGANINV** (base VSI02): EPWM1A chaveia, chave de baixo aberta (GPIO1 como GPIO em 0; `modoChave` 1 =
  síncrono, EPWM1B com tempo morto), braços B e C desligados (GPIO2–5 em 0). Saída ligada ao borne VB: o sensor de
  tensão da fase B (ADCINB3, filtro de 1,2 kHz) mede v_o; i_L = INA240 da fase A (sempre a amostra do zero). Projeto
  L = 2,2 mH, C = 47 µF, R = 15 Ω, 20 V, D0 = 0,5 ± 0,05 (1 mH/100 µF entrava em descontínua na PRBS). Rampa de
  partida (`tempoRampa`), proteção 1,5 A/15 V, `modo` 0 PRBS (média síncrona) / 1 quadrada / 2 fixa,
  `DadosBuck[8][2044]` (d iL vo Vdc vA | iL vo crus | iL topo). Apresentação `Buck/Ensaios/BuckBracoInversor`
  (`analise/simula_buck.py`: planta chaveada exata, ARX; LS viesado com o ruído, **Steiglitz–McBride** acerta;
  `python3 simula_buck.py dados.csv` analisa o ensaio real). Cabeçalhos de tabela do tema ficam em maiúsculas: unidades/math no cabeçalho vão em
  `[...]{style="text-transform:none"}`.
