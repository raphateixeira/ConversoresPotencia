// ============================================================================
//  VSI06ControleKoopman - FCS-MPC de corrente com modelo aprendido dos dados
//  (operador de Koopman aproximado por EDMD, calculado na propria placa)
//
//  Placas: LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (encaixado em J1-J4)
//  Carga: RL trifasica em estrela (25 Ohm e 10 mH por fase), neutro isolado
//  LINCE / UFPA
//
//  Base: VSI05MPCAdaptativoRLS (hardware, medidas, referencias, protecao,
//  chaveamento no topo, cenarios e tempos). Projeto e simulacao em MATLAB:
//  InversorTrifasico/06ControleKoopman/matlab.
//
//  Observaveis (dicionario) e entrada, em alfa-beta, com a temporizacao do FCS
//  (corrente lida no zero k; vetor escolhido em k vale do topo k+1/2 ao k+3/2):
//    z(k) = [i(k); s(k-1)],  u(k) = s(k)   (s = vetor do inversor / Vdc)
//    i(k+1) = G [i(k); s(k-1); s(k)],  G = 2 x 6 (EDMD: minimos quadrados)
//  O dicionario linear e o que a simulacao e os dados reais indicaram (os
//  monomios de grau 2 e 3 nao melhoram a carga RL; ver a apresentacao).
//
//  1. Identificacao (cenario 1): o inversor aplica vetores pseudoaleatorios
//     (LFSR de 16 bits, 0xACE1/0xB400, 3 bits por simbolo, 2 amostras por
//     simbolo, recomecado a cada periodo de 2044 amostras), em malha aberta.
//     A gravacao faz a media sincrona de 16 periodos de i_alfa e i_beta. No fim,
//     o laco principal calcula G (sistema 6 x 6 em precisao dupla) e liga
//     modeloPronto. Corrente esperada: ate ~0,4 A (protecao em 0,8 A).
//  2. FCS com G: para cada estado e,
//       i(k+1) = Gi i(k) + Gp s(k-1) + Gs s_e
//       i(k+2) = Gi i(k+1) + (Gp + Gs) s_e
//       custo  = |i*(k+3/2) - (i(k+1) + i(k+2))/2|^2   (fim do intervalo do vetor)
//     usaKoopman = 0 troca G pelo modelo fisico (resistencia, indutancia), na
//     mesma forma: Gi = th1 I, Gp = th2 I, Gs = th3 I.
//
//  ENSAIO: escreva cenario = 1, 2, 3 ou 4 e depois grava = 1.
//    1 identificacao EDMD (malha aberta, media de 16) -> calcula G sozinho
//    2 FCS com o modelo de Koopman, media de 16 periodos
//    3 FCS com o modelo fisico (25,3 Ohm, 9,8 mH), media de 16 (comparacao)
//    4 FCS com o modelo de Koopman, registro cru (1 periodo)
//  Watch minima: habilita, cenario, grava, modeloPronto; para ver: koopmanG,
//  resistenciaKoopman, indutanciaKoopman, correnteD, tempoMaximoTotal,
//  perdasPrazo, falha.
//
//  Gravacao (grava = 1), Dados3F[8][2044]:
//    cenario 1:    0-1 i_alfa, i_beta (media) | 2 estado aplicado | 3-4 i_alfa,
//                  i_beta (ultimo periodo) | 5-7 iA, iB, iC (ultimo periodo)
//    cenarios 2-4: 0-1 idRef, iqRef | 2-3 id, iq | 4-5 vd, vq | 6-7 iA, iB
//                  (como no VSI03/VSI04: os mesmos scripts leem)
//
//  Tempo de calculo (CPU Timer 1, 5 ns por contagem): Watch tempoMedioMedidas,
//  tempoMedioFCS, tempoMedioTotal, tempoMaximoTotal, latenciaMedia,
//  folgaMinima, perdasPrazo; tempoEDMD = tempo do calculo de G no laco [ms].
//  Por amostra, Tempos[4][2044] [us]: 0 medidas | 1 (nao usado) | 2 FCS |
//  3 interrupcao inteira. Exporte no Graph - Time com tamanho 8176.
// ============================================================================

#include "driverlib.h"
#include "device.h"
#include <math.h>

// ---------------------------- Parametros ------------------------------------
#define FREQ_RELOGIO_PWM   100e6f    // relogio dos modulos de PWM: 200 MHz / 2 = 100 MHz
#define FREQ_PWM           20e3f     // frequencia de chaveamento: 20 kHz (periodo de 50 us)
#define TEMPO_MORTO        100e-9f   // tempo morto entre as chaves de um braco: 100 ns
#define RAZAO_MINIMA       0.05f     // limites da razao ciclica: evitam pulsos mais
#define RAZAO_MAXIMA       0.95f     // curtos que o tempo morto
#define PINO_HABILITA      124U      // GPIO124 (J2-13): /PWM enable do BOOSTXL, ativo em nivel BAIXO
#define VDC_MINIMO         5.0f      // abaixo disso (barramento desligado) usa VDC_NOMINAL
#define VDC_NOMINAL        20.0f     // [V]
#define FRACAO_VDC         0.45f     // |v| maximo = 0,45 Vdc (razao entre 5 e 95 %)

#define TOPO               ((uint16_t)(FREQ_RELOGIO_PWM / (2.0f * FREQ_PWM)))
#define CONTAGENS_MORTO    ((uint16_t)(TEMPO_MORTO * FREQ_RELOGIO_PWM + 0.5f))   // 10
#define PERIODO_AMOSTRA    (1.0f / FREQ_PWM)                                     // 50 us
#define DOIS_PI            6.283185307f
#define RAIZ3_2            0.8660254038f                                         // sqrt(3)/2
#define INV_RAIZ3          0.5773502692f                                         // 1/sqrt(3)

// Medidas (iguais ao VSI02)
#define VOLTS_POR_CONTAGEM   (3.0f / 4096.0f * 24.7f)          // 18,1 mV
#define AMPERES_POR_CONTAGEM (-3.0f / (4096.0f * 0.1f))        // -7,32 mA
#define PESO_ZERO            0.001f  // media do zero dos sensores: constante de tempo de 50 ms
#define PESO_VDC             0.01f   // media do barramento usado na razao: 5 ms
#define N_ESPERA_CALIB       200U    // calibracao chaveando: espera 10 ms...
#define N_CALIBRACAO         2000U   // ...e soma 2000 amostras (100 ms)
#define N_AMOSTRAS           2044U   // amostras por periodo do perfil (102 ms), como no VSI02
#define MAX_PERIODOS         64U     // limite de periodosMedia

// Perfil de referencias dentro de cada periodo de N_AMOSTRAS (amostras de 50 us)
#define AMOSTRA_D_LIGA     200U      // degrau em d: de 10 ms...
#define AMOSTRA_D_DESLIGA  1200U     // ...a 60 ms
#define AMOSTRA_Q_LIGA     700U      // degrau em q: de 35 ms...
#define AMOSTRA_Q_DESLIGA  1700U     // ...a 85 ms

#define MODO_MALHA_ABERTA  0U
#define MODO_PI            1U
#define MODO_FCS           2U
#define DOIS_TERCOS        0.6666666667f

// --------------------- Variaveis para a janela Watch ------------------------
volatile uint16_t habilita       = 0;       // 1 = liga o inversor | 0 = desliga
volatile uint16_t modo           = MODO_FCS; // 0 = malha aberta | 1 = PI | 2 = FCS-MPC
volatile float    frequencia     = 60.0f;   // frequencia do referencial dq [Hz]
volatile float    referenciaD0   = 0.15f;   // ponto de operacao de id [A]
volatile float    referenciaQ0   = 0.0f;    // ponto de operacao de iq [A]
volatile float    degrauD        = 0.10f;   // degrau em id [A] (0 = sem degrau)
volatile float    degrauQ        = -0.05f;  // degrau em iq [A]
volatile float    bandaPI        = 300.0f;  // banda da malha de corrente fc [Hz]
volatile float    resistencia    = 25.3f;   // R da carga (regime do ensaio do PI) [Ohm]
volatile float    indutancia     = 9.8e-3f; // L identificado [H]
volatile uint16_t desacopla      = 1U;      // 1 = desacoplamento wL ligado
volatile float    tensaoD0       = 5.0f;    // malha aberta: vd [V]
volatile float    tensaoQ0       = 0.0f;    // malha aberta: vq [V]
volatile float    correnteMaxima = 0.8f;    // protecao por software [A] (pico de fase)
volatile uint16_t periodosMedia  = 16U;     // periodos na media sincrona (1 a 64)
volatile uint16_t grava          = 0;       // 1 = comecar | 2 = gravando | 3 = media | 0 = parado
volatile float    lambdaComutacao = 0.0f;   // FCS: peso das comutacoes no custo [A^2 por comutacao]
volatile uint16_t usaKoopman     = 1U;      // 1 = FCS usa G do EDMD (se modeloPronto) | 0 = modelo fisico
volatile uint16_t modeloPronto   = 0U;      // 1 = G calculado (so leitura; escreva 0 para descartar)
volatile float    koopmanG[12];             // G [2][6] por linhas: [Gi | Gp | Gs] (so leitura)
volatile float    resistenciaKoopman, indutanciaKoopman;   // R e L equivalentes de G (so leitura)
volatile float    tempoEDMD      = 0.0f;    // tempo do calculo de G no laco principal [ms]
volatile uint16_t cenario        = 0U;      // 1 a 4: configura o ensaio sozinho (ver o cabecalho); 0 = manual
static uint16_t   cenarioAnterior = 0U;
static uint16_t   identificando  = 0U;      // 1 = cenario 1: vetores pseudoaleatorios em malha aberta
static uint16_t   calculaEDMD    = 0U;      // 1 = laco principal deve calcular G
static uint16_t   lfsr           = 0xACE1U; // gerador dos vetores da identificacao
static float      rUsado = 0.0f, lUsado = 0.0f, vdcUsado = 0.0f;
static float      modelo[2][6];             // modelo em uso pelo FCS: [Gi | Gp | Gs]
static float      modeloFixo[2][6];         // modelo fisico na mesma forma

volatile uint16_t estadoAtual    = 0;       // FCS: estado das chaves (bit 2 = A, bit 1 = B, bit 0 = C)
volatile float    frequenciaChaveamento = 0.0f; // FCS: media por chave [Hz] (so leitura)
volatile float    custoMinimo    = 0.0f;    // FCS: custo do estado escolhido [A^2] (so leitura)
volatile float    ganhoA, ganhoB, ganhoAh, ganhoBh;   // FCS: modelo discreto (so leitura)

volatile float    referenciaD, referenciaQ;     // referencias desta amostra [A] (so leitura)
volatile float    tensaoDAgora, tensaoQAgora;   // vd e vq aplicadas [V] (so leitura)
volatile float    correnteD, correnteQ;         // id e iq [A] (so leitura)
volatile float    kp, ki;                       // ganhos calculados de bandaPI, R e L (so leitura)
volatile uint32_t saturacoes     = 0;           // amostras com |v| no limite (so leitura)
volatile uint16_t falha          = 0;           // 1 = protecao desligou o inversor
volatile float    somaCorrentes;                // iA + iB + iC medidas, antes da correcao (so leitura)
volatile float    razaoAplicada[3];             // razoes escritas (so leitura)
volatile float    correnteAgora[3];             // iA, iB, iC [A] (so leitura)
volatile float    tensaoBarramento;             // tensao do barramento [V] (so leitura)
volatile float    offsetZero[3] = {2253.0f, 2253.0f, 2253.0f};   // zero dos sensores no zero [contagens]
volatile float    offsetTopo[3] = {2253.0f, 2253.0f, 2253.0f};   // e no topo do contador [contagens]
volatile uint16_t amostra        = 0;       // posicao no periodo do perfil (so leitura)
volatile uint16_t periodoAtual   = 0;       // periodo em gravacao: 0 = descartado (so leitura)
volatile uint16_t calibrando     = 0;       // 1 = medindo o zero chaveando, a 50 % (so leitura)
static uint16_t   habilitaAnterior = 0;
static uint16_t   contaCalib = 0;
static uint32_t   somaZero[3], somaTopo[3];
static uint16_t   periodosAlvo   = 1U;
static float      integralD = 0.0f, integralQ = 0.0f;   // parte integral do PI [V]

static float      angulo = 0.0f;
static float      cosAngulo = 1.0f, senAngulo = 0.0f;
static float      vdcFiltrado = VDC_NOMINAL;
static float      razaoAnterior[3] = {0.5f, 0.5f, 0.5f};
static uint16_t   fcsAtivo = 0U;            // 1 = saidas forcadas pelo FCS
static float      vAlfaAplicado = 0.0f, vBetaAplicado = 0.0f;   // vetor em vigor ate o proximo topo
static uint32_t   contaComutacoes = 0UL, contaJanela = 0UL;
static float      sAnt[2];                  // vetor em vigor s(k-1), normalizado (alfa, beta)
static float      cosMeio = 1.0f, senMeio = 0.0f;   // rotacao de 1,5 amostra (instante do custo)

// Uma matriz so com tudo o que e gravado (ver cabecalho). Mesma secao e mesmo
// tamanho do VSI02: faixa RAMGS0_12 do .cmd.
#define CANAL_IDREF     0U      // controle: referencia de id [A]      | identificacao: i_alfa (media)
#define CANAL_IQREF     1U      // controle: referencia de iq [A]      | identificacao: i_beta (media)
#define CANAL_ID        2U      // controle: id [A] (media)            | identificacao: estado aplicado
#define CANAL_IQ        3U      // controle: iq [A] (media)            | identificacao: i_alfa (ultimo periodo)
#define CANAL_VD        4U      // controle: vd aplicada [V] (media)   | identificacao: i_beta (ultimo periodo)
#define CANAL_VQ        5U      // controle: vq aplicada [V] (media)   | identificacao: iA (ultimo periodo)
#define CANAL_IA        6U      // controle: iA [A] (ultimo periodo)   | identificacao: iB (ultimo periodo)
#define CANAL_IB        7U      // controle: iB [A] (ultimo periodo)   | identificacao: iC (ultimo periodo)
#define N_CANAIS        8U

#pragma DATA_SECTION(Dados3F, "Dados3F")
float Dados3F[N_CANAIS][N_AMOSTRAS];

// Tempos de calculo por amostra [us], gravados junto com Dados3F (mesma secao)
#define N_TEMPOS        4U
#pragma DATA_SECTION(Tempos, "Dados3F")
float Tempos[N_TEMPOS][N_AMOSTRAS];

#define CICLOS_POR_US   200.0f      // CPU Timer 1 a 200 MHz
#define US_POR_CONTAGEM 0.01f       // contador do PWM a 100 MHz
#define PESO_TEMPO      0.001f      // media movel dos tempos: ~1000 amostras (50 ms)
volatile float    tempoMedioMedidas = 0.0f, tempoMedioFCS = 0.0f;
volatile float    tempoMedioTotal = 0.0f, tempoMaximoTotal = 0.0f;   // [us]
volatile float    latenciaMedia = 0.0f;     // zero do contador -> entrada da interrupcao [us]
volatile float    folgaMinima = 25.0f;      // menor folga ate o topo na decisao do FCS [us]
volatile uint32_t perdasPrazo = 0UL;        // decisoes do FCS depois do topo
static uint32_t   tInicio;
static float      inversoPeriodos = 1.0f;
static float      cosPasso = 1.0f, senPasso = 0.0f;
static float      dMedidas = 0.0f, dFCS = 0.0f, dTotal = 0.0f;

static const uint32_t modulo[3] = {EPWM1_BASE, EPWM2_BASE, EPWM3_BASE};   // fases A, B, C
static const uint32_t resultado[3] = {ADCCRESULT_BASE, ADCBRESULT_BASE, ADCARESULT_BASE}; // A, B, C

__interrupt void AtualizaPWM(void);
static void ConfiguraPinos(void);
static void ConfiguraModuloPWM(uint32_t base);
static float EscreveRazao(uint32_t base, float razao);
static void ConfiguraADC(void);
static void Referencias(void);
static void ControlePI(void);
static void ControleFCS(void);
static void LiberaPWM(void);
static void Configuracao(void);
static void Identificacao(void);
static void AplicaEstado(uint16_t novo);
static void CalculaEDMD(void);
static void Protecao(void);
static void LeMedidas(void);
static void Grava(void);
static void TerminaMedia(void);

// ============================================================================
void main(void)
{
    uint16_t fase;

    Device_init();
    Device_initGPIO();
    Interrupt_initModule();
    Interrupt_initVectorTable();

    ConfiguraPinos();               // inversor desligado desde o inicio

    SysCtl_setEPWMClockDivider(SYSCTL_EPWMCLK_DIV_2);           // 100 MHz
    SysCtl_disablePeripheral(SYSCTL_PERIPH_CLK_TBCLKSYNC);
    for (fase = 0U; fase < 3U; fase++)
    {
        ConfiguraModuloPWM(modulo[fase]);
    }
    ConfiguraADC();

    EPWM_setInterruptSource(EPWM1_BASE, EPWM_INT_TBCTR_ZERO);
    EPWM_setInterruptEventCount(EPWM1_BASE, 1U);
    EPWM_enableInterrupt(EPWM1_BASE);
    EPWM_clearEventTriggerInterruptFlag(EPWM1_BASE);
    Interrupt_register(INT_EPWM1, &AtualizaPWM);
    Interrupt_enable(INT_EPWM1);

    SysCtl_enablePeripheral(SYSCTL_PERIPH_CLK_TBCLKSYNC);

    // CPU Timer 1 livre (decrescente, 200 MHz): mede o tempo de calculo
    CPUTimer_stopTimer(CPUTIMER1_BASE);
    CPUTimer_setPeriod(CPUTIMER1_BASE, 0xFFFFFFFFUL);
    CPUTimer_setPreScaler(CPUTIMER1_BASE, 0U);
    CPUTimer_reloadTimerCounter(CPUTIMER1_BASE);
    CPUTimer_startTimer(CPUTIMER1_BASE);

    EINT;
    ERTM;

    for (;;)
    {
        GPIO_writePin(PINO_HABILITA, (habilita == 1U) ? 0U : 1U);

        // rotacoes do angulo de uma e duas amostras (evita seno/cosseno na interrupcao)
        cosPasso = cosf(DOIS_PI * frequencia * PERIODO_AMOSTRA);
        senPasso = sinf(DOIS_PI * frequencia * PERIODO_AMOSTRA);

        // ganhos do PI: zero sobre o polo da carga (fora da interrupcao)
        kp = DOIS_PI * bandaPI * indutancia;
        ki = DOIS_PI * bandaPI * resistencia;

        // rotacao de 1,5 amostra: o custo do FCS e calculado no fim do intervalo do vetor
        cosMeio = cosf(1.5f * DOIS_PI * frequencia * PERIODO_AMOSTRA);
        senMeio = sinf(1.5f * DOIS_PI * frequencia * PERIODO_AMOSTRA);

        if (calculaEDMD == 1U)
        {
            CalculaEDMD();          // fim do cenario 1: G a partir da media gravada
        }

        if (grava == 3U)
        {
            TerminaMedia();
        }
    }
}

// ============================================================================
// Chamada a cada 50 us, no inicio do periodo do PWM
__interrupt void AtualizaPWM(void)
{
    uint16_t fase;
    float valfa, vbeta, v[3];

    tInicio = CPUTimer_getTimerCount(CPUTIMER1_BASE);
    latenciaMedia += PESO_TEMPO * ((float)EPWM_getTimeBaseCounterValue(EPWM1_BASE) * US_POR_CONTAGEM - latenciaMedia);
    dFCS = 0.0f;
    Configuracao();                 // cenario e modelo fixo (so quando mudam)

    // Ao ligar: calibracao do zero chaveando, a 50 %; PI parte do zero
    if ((habilita == 1U) && (habilitaAnterior != 1U))
    {
        for (fase = 0U; fase < 3U; fase++)
        {
            somaZero[fase] = 0UL;
            somaTopo[fase] = 0UL;
        }
        contaCalib = 0U;
        calibrando = 1U;
        integralD = 0.0f;
        integralQ = 0.0f;
        saturacoes = 0UL;
    }
    if (habilita != 1U)
    {
        calibrando = 0U;
    }
    habilitaAnterior = habilita;

    // pedido de gravacao (espera o fim da calibracao): perfil do inicio
    if ((grava == 1U) && (calibrando == 0U))
    {
        amostra = 0U;
        periodosAlvo = periodosMedia;
        if (periodosAlvo < 1U) periodosAlvo = 1U;
        if (periodosAlvo > MAX_PERIODOS) periodosAlvo = MAX_PERIODOS;
        inversoPeriodos = 1.0f / (float)periodosAlvo;
        periodoAtual = 0U;
        grava = 2U;
    }

    angulo += DOIS_PI * frequencia * PERIODO_AMOSTRA;
    if (angulo >= DOIS_PI)
    {
        angulo -= DOIS_PI;
    }

    cosAngulo = cosf(angulo);       // mesmo angulo na Park das correntes e na
    senAngulo = sinf(angulo);       // Park inversa das tensoes (como no VSI02)

    // Medidas primeiro: o PI usa as correntes desta amostra
    LeMedidas();                    // le o ADC, calcula id e iq
    dMedidas = (float)(tInicio - CPUTimer_getTimerCount(CPUTIMER1_BASE)) / CICLOS_POR_US;
    Protecao();
    Referencias();                  // idRef e iqRef desta amostra

    if ((habilita != 1U) || (calibrando == 1U))
    {
        tensaoDAgora = 0.0f;        // desligado ou calibrando: 50 % nas tres fases
        tensaoQAgora = 0.0f;
        integralD = 0.0f;
        integralQ = 0.0f;
    }
    else if (identificando == 1U)
    {
        Identificacao();            // vetores pseudoaleatorios, malha aberta
    }
    else if (modo == MODO_FCS)
    {
        ControleFCS();              // escolhe o estado e forca as saidas (sem PWM)
    }
    else if (modo == MODO_PI)
    {
        ControlePI();
    }
    else
    {
        tensaoDAgora = tensaoD0;    // malha aberta
        tensaoQAgora = tensaoQ0;
    }

    if (((modo != MODO_FCS) && (identificando == 0U)) || (habilita != 1U) || (calibrando == 1U))
    {
        LiberaPWM();                // de volta ao PWM, se estava forcado

        // Park inversa (invariante em amplitude) e Clarke inversa
        valfa = tensaoDAgora * cosAngulo - tensaoQAgora * senAngulo;
        vbeta = tensaoDAgora * senAngulo + tensaoQAgora * cosAngulo;
        v[0] = valfa;
        v[1] = -0.5f * valfa + RAIZ3_2 * vbeta;
        v[2] = -0.5f * valfa - RAIZ3_2 * vbeta;

        for (fase = 0U; fase < 3U; fase++)
        {
            razaoAnterior[fase] = razaoAplicada[fase];
            razaoAplicada[fase] = EscreveRazao(modulo[fase], 0.5f + v[fase] / vdcFiltrado);
        }
    }

    Grava();

    // tempos: medias moveis e pior caso
    dTotal = (float)(tInicio - CPUTimer_getTimerCount(CPUTIMER1_BASE)) / CICLOS_POR_US;
    tempoMedioMedidas += PESO_TEMPO * (dMedidas - tempoMedioMedidas);
    tempoMedioTotal += PESO_TEMPO * (dTotal - tempoMedioTotal);
    if (dFCS > 0.0f)
    {
        tempoMedioFCS += PESO_TEMPO * (dFCS - tempoMedioFCS);
    }
    if (dTotal > tempoMaximoTotal)
    {
        tempoMaximoTotal = dTotal;
    }

    EPWM_clearEventTriggerInterruptFlag(EPWM1_BASE);
    Interrupt_clearACKGroup(INTERRUPT_ACK_GROUP3);
}

// ============================================================================
// Referencias de corrente: ponto de operacao + degraus em instantes fixos do
// periodo de N_AMOSTRAS. Fora da gravacao, amostra tambem corre (perfil continuo).
static void Referencias(void)
{
    uint16_t n = amostra;

    referenciaD = referenciaD0;
    referenciaQ = referenciaQ0;
    if ((n >= AMOSTRA_D_LIGA) && (n < AMOSTRA_D_DESLIGA))
    {
        referenciaD += degrauD;
    }
    if ((n >= AMOSTRA_Q_LIGA) && (n < AMOSTRA_Q_DESLIGA))
    {
        referenciaQ += degrauQ;
    }
}

// ============================================================================
// PI por eixo + desacoplamento + limite de tensao com anti-windup.
static void ControlePI(void)
{
    float erroD = referenciaD - correnteD;
    float erroQ = referenciaQ - correnteQ;
    float novaIntD = integralD + ki * PERIODO_AMOSTRA * erroD;
    float novaIntQ = integralQ + ki * PERIODO_AMOSTRA * erroQ;
    float vd = kp * erroD + novaIntD;
    float vq = kp * erroQ + novaIntQ;
    float wL = DOIS_PI * frequencia * indutancia;
    float vMax = FRACAO_VDC * vdcFiltrado;
    float modulo2, escala;

    if (desacopla == 1U)
    {
        vd -= wL * correnteQ;
        vq += wL * correnteD;
    }

    modulo2 = vd * vd + vq * vq;
    if (modulo2 > vMax * vMax)
    {
        escala = vMax / sqrtf(modulo2);     // reduz o vetor ao limite, mesma direcao
        vd *= escala;
        vq *= escala;
        saturacoes++;                       // integradores ficam como estavam
    }
    else
    {
        integralD = novaIntD;
        integralQ = novaIntQ;
    }
    tensaoDAgora = vd;
    tensaoQAgora = vq;
}

// ============================================================================
// Cenarios e modelo fixo: tratados na interrupcao, so quando algo muda (nao
// dependem do laco principal, que pode ficar sem tempo de CPU).
static void Configuracao(void)
{
    uint16_t l, m;

    if (cenario != cenarioAnterior)
    {
        switch (cenario)
        {
        case 1U:    // identificacao EDMD: vetores pseudoaleatorios em malha aberta, media de 16
            identificando = 1U; periodosMedia = 16U;
            break;
        case 2U:    // FCS com o modelo de Koopman, media de 16
            identificando = 0U; usaKoopman = 1U; periodosMedia = 16U;
            break;
        case 3U:    // FCS com o modelo fisico, media de 16 (comparacao)
            identificando = 0U; usaKoopman = 0U; periodosMedia = 16U;
            resistencia = 25.3f; indutancia = 9.8e-3f;
            break;
        case 4U:    // FCS com o modelo de Koopman, registro cru
            identificando = 0U; usaKoopman = 1U; periodosMedia = 1U;
            break;
        default:
            break;
        }
        tempoMaximoTotal = 0.0f;
        perdasPrazo = 0UL;
        folgaMinima = 25.0f;
        cenarioAnterior = cenario;
    }

    // modelo fisico na forma [Gi | Gp | Gs]: recalcula se R, L ou Vdc mudaram
    if ((resistencia != rUsado) || (indutancia != lUsado) || (fabsf(vdcFiltrado - vdcUsado) > 0.2f))
    {
        rUsado = resistencia;
        lUsado = indutancia;
        vdcUsado = vdcFiltrado;
        ganhoA  = expf(-rUsado * PERIODO_AMOSTRA / lUsado);
        ganhoAh = expf(-rUsado * 0.5f * PERIODO_AMOSTRA / lUsado);
        ganhoBh = vdcUsado * (1.0f - ganhoAh) / rUsado;
        for (l = 0U; l < 2U; l++)
        {
            for (m = 0U; m < 6U; m++)
            {
                modeloFixo[l][m] = 0.0f;
            }
            modeloFixo[l][l] = ganhoA;                    // Gi = th1 I
            modeloFixo[l][2U + l] = ganhoAh * ganhoBh;    // Gp = th2 I
            modeloFixo[l][4U + l] = ganhoBh;              // Gs = th3 I
        }
    }

    // modelo em uso pelo FCS (troca so entre amostras: nunca no meio da busca)
    for (l = 0U; l < 2U; l++)
    {
        for (m = 0U; m < 6U; m++)
        {
            modelo[l][m] = ((usaKoopman == 1U) && (modeloPronto == 1U)) ? koopmanG[6U * l + m] : modeloFixo[l][m];
        }
    }
}

// ============================================================================
// FCS-MPC com o modelo em uso (Koopman/EDMD ou fisico): testa os 8 estados.
static void ControleFCS(void)
{
    uint16_t e, melhor = estadoAtual, sa, sb, sc, n;
    float ia, ib, c, s, refA, refB, va, vb, b1a, b1b, p1a, p1b, p2a, p2b, g, gMin = 1.0e30f;
    float gp0, gp1, gp2, gp3;           // Gp + Gs
    float folga;
    uint32_t t0;
    uint16_t ctr;

    t0 = CPUTimer_getTimerCount(CPUTIMER1_BASE);

    // 1. corrente medida em alfa-beta (zero do contador, amostra k)
    ia = (2.0f * correnteAgora[0] - correnteAgora[1] - correnteAgora[2]) / 3.0f;
    ib = (correnteAgora[1] - correnteAgora[2]) * INV_RAIZ3;

    // 2. referencia em alfa-beta no fim do intervalo do vetor novo (k + 3/2)
    c = cosAngulo * cosMeio - senAngulo * senMeio;
    s = senAngulo * cosMeio + cosAngulo * senMeio;
    refA = referenciaD * c - referenciaQ * s;
    refB = referenciaD * s + referenciaQ * c;

    // 3. parte de i(k+1) que nao depende do vetor novo: Gi i(k) + Gp s(k-1)
    b1a = modelo[0][0] * ia + modelo[0][1] * ib + modelo[0][2] * sAnt[0] + modelo[0][3] * sAnt[1];
    b1b = modelo[1][0] * ia + modelo[1][1] * ib + modelo[1][2] * sAnt[0] + modelo[1][3] * sAnt[1];
    gp0 = modelo[0][2] + modelo[0][4];  gp1 = modelo[0][3] + modelo[0][5];
    gp2 = modelo[1][2] + modelo[1][4];  gp3 = modelo[1][3] + modelo[1][5];

    // 4. os 8 estados (s normalizado por Vdc)
    for (e = 0U; e < 8U; e++)
    {
        sa = (e >> 2) & 1U;
        sb = (e >> 1) & 1U;
        sc = e & 1U;
        va = DOIS_TERCOS * ((float)sa - 0.5f * (float)(sb + sc));
        vb = INV_RAIZ3 * ((float)sb - (float)sc);
        p1a = b1a + modelo[0][4] * va + modelo[0][5] * vb;                     // i(k+1)
        p1b = b1b + modelo[1][4] * va + modelo[1][5] * vb;
        p2a = modelo[0][0] * p1a + modelo[0][1] * p1b + gp0 * va + gp1 * vb;   // i(k+2), vetor mantido
        p2b = modelo[1][0] * p1a + modelo[1][1] * p1b + gp2 * va + gp3 * vb;
        p1a = 0.5f * (p1a + p2a) - refA;                                        // erro em k + 3/2
        p1b = 0.5f * (p1b + p2b) - refB;
        n = ((e ^ estadoAtual) & 1U) + (((e ^ estadoAtual) >> 1) & 1U) + (((e ^ estadoAtual) >> 2) & 1U);
        g = p1a * p1a + p1b * p1b + (lambdaComutacao + 1.0e-9f) * (float)n;
        if (g < gMin)
        {
            gMin = g;
            melhor = e;
        }
    }
    custoMinimo = gMin;
    AplicaEstado(melhor);

    // prazo: o estado novo tem de estar escrito antes do topo do contador
    dFCS = (float)(t0 - CPUTimer_getTimerCount(CPUTIMER1_BASE)) / CICLOS_POR_US;
    ctr = EPWM_getTimeBaseCounterValue(EPWM1_BASE);
    if (EPWM_getTimeBaseCounterDirection(EPWM1_BASE) == EPWM_TIME_BASE_STATUS_COUNT_UP)
    {
        folga = (float)(TOPO - ctr) * US_POR_CONTAGEM;
    }
    else
    {
        folga = -(float)(TOPO - ctr) * US_POR_CONTAGEM;    // ja passou do topo
        perdasPrazo++;
    }
    if (folga < folgaMinima)
    {
        folgaMinima = folga;
    }
}

// ============================================================================
// Identificacao (cenario 1): vetor pseudoaleatorio, 2 amostras por simbolo,
// sequencia recomecada a cada periodo de N_AMOSTRAS (mesma de sequencia_vetores.m).
static void Identificacao(void)
{
    static uint16_t estadoIdent = 0U;
    uint16_t j;

    if (amostra == 0U)
    {
        lfsr = 0xACE1U;
    }
    if ((amostra & 1U) == 0U)
    {
        for (j = 0U; j < 3U; j++)
        {
            if (lfsr & 1U)
            {
                lfsr = (lfsr >> 1) ^ 0xB400U;
            }
            else
            {
                lfsr >>= 1;
            }
        }
        estadoIdent = lfsr & 7U;
    }
    AplicaEstado(estadoIdent);
}

// ============================================================================
// Aplica um estado das chaves (forca as saidas A; carrega no topo) e guarda o
// vetor normalizado s(k), que sera s(k-1) na proxima amostra.
static void AplicaEstado(uint16_t novo)
{
    uint16_t fase, n, sa, sb, sc;
    float va, vb, c1, s1;

    n = ((novo ^ estadoAtual) & 1U) + (((novo ^ estadoAtual) >> 1) & 1U) + (((novo ^ estadoAtual) >> 2) & 1U);
    contaComutacoes += n;
    for (fase = 0U; fase < 3U; fase++)
    {
        EPWM_setActionQualifierContSWForceAction(modulo[fase], EPWM_AQ_OUTPUT_A,
            ((novo >> (2U - fase)) & 1U) ? EPWM_AQ_SW_OUTPUT_HIGH : EPWM_AQ_SW_OUTPUT_LOW);
        razaoAplicada[fase] = (float)((novo >> (2U - fase)) & 1U);
    }
    fcsAtivo = 1U;
    estadoAtual = novo;

    sa = (novo >> 2) & 1U;
    sb = (novo >> 1) & 1U;
    sc = novo & 1U;
    va = DOIS_TERCOS * ((float)sa - 0.5f * (float)(sb + sc));
    vb = INV_RAIZ3 * ((float)sb - (float)sc);
    sAnt[0] = va;
    sAnt[1] = vb;
    vAlfaAplicado = va * vdcFiltrado;
    vBetaAplicado = vb * vdcFiltrado;

    c1 = cosAngulo * cosPasso - senAngulo * senPasso;          // angulo de k + 1
    s1 = senAngulo * cosPasso + cosAngulo * senPasso;
    tensaoDAgora =  vAlfaAplicado * c1 + vBetaAplicado * s1;
    tensaoQAgora = -vAlfaAplicado * s1 + vBetaAplicado * c1;

    if (++contaJanela >= (uint32_t)FREQ_PWM)
    {
        frequenciaChaveamento = (float)contaComutacoes / 6.0f;
        contaComutacoes = 0UL;
        contaJanela = 0UL;
    }
}

// ============================================================================
// EDMD (laco principal, fim do cenario 1): minimos quadrados de
//   i(k+1) = G x(k),  x(k) = [i(k); s(k-1); s(k)]
// sobre a media sincrona gravada (indices circulares: o registro e um periodo).
// Equacoes normais (6 x 6) em precisao dupla, eliminacao de Gauss-Jordan com pivo.
static void CalculaEDMD(void)
{
    double A[6][8], x[6], f, th1, th3, rr;
    uint16_t k, kp, ka, l, m, c, piv, e, sa, sb, sc;
    uint32_t t0 = CPUTimer_getTimerCount(CPUTIMER1_BASE);

    for (l = 0U; l < 6U; l++)
    {
        for (m = 0U; m < 8U; m++)
        {
            A[l][m] = 0.0;
        }
    }
    for (k = 0U; k < N_AMOSTRAS; k++)
    {
        kp = (k + 1U < N_AMOSTRAS) ? k + 1U : 0U;
        ka = (k > 0U) ? k - 1U : N_AMOSTRAS - 1U;
        x[0] = Dados3F[CANAL_IDREF][k];
        x[1] = Dados3F[CANAL_IQREF][k];
        for (c = 0U; c < 2U; c++)                   // s(k-1) e s(k), do estado gravado
        {
            e = (uint16_t)Dados3F[CANAL_ID][(c == 0U) ? ka : k];
            sa = (e >> 2) & 1U;  sb = (e >> 1) & 1U;  sc = e & 1U;
            x[2U + 2U * c] = DOIS_TERCOS * ((double)sa - 0.5 * (double)(sb + sc));
            x[3U + 2U * c] = INV_RAIZ3 * ((double)sb - (double)sc);
        }
        for (l = 0U; l < 6U; l++)
        {
            for (m = 0U; m < 6U; m++)
            {
                A[l][m] += x[l] * x[m];
            }
            A[l][6] += x[l] * Dados3F[CANAL_IDREF][kp];   // lado direito, eixo alfa
            A[l][7] += x[l] * Dados3F[CANAL_IQREF][kp];   // e beta
        }
    }
    for (c = 0U; c < 6U; c++)                       // Gauss-Jordan com pivo parcial
    {
        piv = c;
        for (l = c + 1U; l < 6U; l++)
        {
            if (fabs(A[l][c]) > fabs(A[piv][c])) piv = l;
        }
        if (fabs(A[piv][c]) < 1.0e-12)
        {
            calculaEDMD = 0U;                       // dados sem excitacao: nao troca o modelo
            return;
        }
        for (m = 0U; m < 8U; m++)
        {
            f = A[c][m];  A[c][m] = A[piv][m];  A[piv][m] = f;
        }
        for (l = 0U; l < 6U; l++)
        {
            if (l != c)
            {
                f = A[l][c] / A[c][c];
                for (m = c; m < 8U; m++)
                {
                    A[l][m] -= f * A[c][m];
                }
            }
        }
    }
    for (l = 0U; l < 6U; l++)                       // G por linhas: 0 = alfa, 1 = beta
    {
        koopmanG[l]      = (float)(A[l][6] / A[l][l]);
        koopmanG[6U + l] = (float)(A[l][7] / A[l][l]);
    }
    th1 = 0.5 * (koopmanG[0] + koopmanG[7]);
    th3 = 0.5 * (koopmanG[4] + koopmanG[11]);
    if ((th1 > 0.0) && (th1 < 1.0) && (th3 > 0.0))
    {
        rr = (double)vdcFiltrado * (1.0 - sqrt(th1)) / th3;
        resistenciaKoopman = (float)rr;
        indutanciaKoopman = (float)(-rr * PERIODO_AMOSTRA / log(th1));
    }
    tempoEDMD = (float)(t0 - CPUTimer_getTimerCount(CPUTIMER1_BASE)) / (CICLOS_POR_US * 1000.0f);
    modeloPronto = 1U;
    calculaEDMD = 0U;
}

// Volta ao PWM: desliga o forcamento (vale a partir do proximo topo)
static void LiberaPWM(void)
{
    uint16_t fase;

    if (fcsAtivo == 1U)
    {
        for (fase = 0U; fase < 3U; fase++)
        {
            EPWM_setActionQualifierContSWForceAction(modulo[fase], EPWM_AQ_OUTPUT_A, EPWM_AQ_SW_DISABLED);
        }
        fcsAtivo = 0U;
        vAlfaAplicado = 0.0f;
        vBetaAplicado = 0.0f;
        sAnt[0] = 0.0f;
        sAnt[1] = 0.0f;
    }
}

// ============================================================================
// Protecao por software: so depois da calibracao (zero ja medido).
static void Protecao(void)
{
    uint16_t fase;

    if ((habilita != 1U) || (calibrando == 1U))
    {
        return;
    }
    for (fase = 0U; fase < 3U; fase++)
    {
        if (fabsf(correnteAgora[fase]) > correnteMaxima)
        {
            habilita = 0U;
            falha = 1U;
        }
    }
}

// ============================================================================
// Razao ciclica -> valor de comparacao (CMPA). A saida A fica em nivel alto
// enquanto o contador esta abaixo de CMPA: razao = CMPA / TOPO.
// Devolve a razao de fato aplicada (limitada e arredondada para CMPA).
static float EscreveRazao(uint32_t base, float razao)
{
    uint16_t cmpa;

    if (razao < RAZAO_MINIMA) razao = RAZAO_MINIMA;
    if (razao > RAZAO_MAXIMA) razao = RAZAO_MAXIMA;
    cmpa = (uint16_t)(razao * (float)TOPO);
    EPWM_setCounterCompareValue(base, EPWM_COUNTER_COMPARE_A, cmpa);
    return (float)cmpa / (float)TOPO;
}

// ============================================================================
// Le correntes e barramento. As conversoes do zero comecam junto com esta
// interrupcao; espera-se o fim delas (cerca de 1 us). As do topo foram feitas
// meio periodo antes.
static void LeMedidas(void)
{
    uint16_t espera = 0U;
    uint16_t fase;
    float nZero, nTopo, ialfa, ibeta;

    while ((ADC_getInterruptStatus(ADCA_BASE, ADC_INT_NUMBER1) == false) && (espera < 1000U))
    {
        espera++;                   // limite: nunca trava a interrupcao
    }
    ADC_clearInterruptStatus(ADCA_BASE, ADC_INT_NUMBER1);
    if (ADC_getInterruptOverflowStatus(ADCA_BASE, ADC_INT_NUMBER1))
    {
        ADC_clearInterruptOverflowStatus(ADCA_BASE, ADC_INT_NUMBER1);   // marca perdida (pausa)
    }

    tensaoBarramento = VOLTS_POR_CONTAGEM * (float)ADC_readResult(ADCDRESULT_BASE, ADC_SOC_NUMBER0);
    if (tensaoBarramento > VDC_MINIMO)
    {
        vdcFiltrado += PESO_VDC * (tensaoBarramento - vdcFiltrado);
    }

    for (fase = 0U; fase < 3U; fase++)
    {
        nZero = (float)ADC_readResult(resultado[fase], ADC_SOC_NUMBER1);
        nTopo = (float)ADC_readResult(resultado[fase], ADC_SOC_NUMBER2);
        if (habilita != 1U)         // desligado: corrente nula, a leitura e o zero
        {
            offsetZero[fase] += PESO_ZERO * (nZero - offsetZero[fase]);
            offsetTopo[fase] += PESO_ZERO * (nTopo - offsetTopo[fase]);
        }
        else if ((calibrando == 1U) && (contaCalib >= N_ESPERA_CALIB))
        {
            somaZero[fase] += (uint32_t)nZero;   // chaveando a 50 %: corrente nula
            somaTopo[fase] += (uint32_t)nTopo;
        }
        // pulso de cima largo (razao >= 0,5): amostra do zero; senao, a do topo
        if ((fcsAtivo == 1U) || (razaoAnterior[fase] >= 0.5f))   // FCS: chaveia no topo, le no zero
        {
            correnteAgora[fase] = AMPERES_POR_CONTAGEM * (nZero - offsetZero[fase]);
        }
        else
        {
            correnteAgora[fase] = AMPERES_POR_CONTAGEM * (nTopo - offsetTopo[fase]);
        }
    }

    if (calibrando == 1U)
    {
        if (++contaCalib >= N_ESPERA_CALIB + N_CALIBRACAO)
        {
            for (fase = 0U; fase < 3U; fase++)
            {
                offsetZero[fase] = (float)somaZero[fase] / (float)N_CALIBRACAO;
                offsetTopo[fase] = (float)somaTopo[fase] / (float)N_CALIBRACAO;
            }
            calibrando = 0U;        // zero medido: o controle comeca
        }
    }

    // Neutro isolado: iA + iB + iC = 0. O que aparece na soma e erro de medida
    // comum as tres fases (zero dos sensores, parte do ruido): tira-se um terco
    // de cada fase. somaCorrentes guarda a soma medida, para diagnostico.
    somaCorrentes = correnteAgora[0] + correnteAgora[1] + correnteAgora[2];
    for (fase = 0U; fase < 3U; fase++)
    {
        correnteAgora[fase] -= somaCorrentes * (1.0f / 3.0f);
    }

    // Clarke e Park (invariante em amplitude), com o angulo desta amostra
    ialfa = (2.0f * correnteAgora[0] - correnteAgora[1] - correnteAgora[2]) / 3.0f;
    ibeta = (correnteAgora[1] - correnteAgora[2]) * INV_RAIZ3;
    correnteD =  ialfa * cosAngulo + ibeta * senAngulo;
    correnteQ = -ialfa * senAngulo + ibeta * cosAngulo;
}

// ============================================================================
// Periodo 0: descartado (transitorio). Periodos 1 a periodosAlvo: referencias
// e correntes das fases recebem o periodo atual; id, iq, vd e vq somam a
// amostra de mesma posicao (media no laco principal, grava = 3). A posicao
// "amostra" corre sempre: e ela que define o perfil das referencias.
static void Grava(void)
{
    float a0 = 0.0f, a1 = 0.0f, a2 = 0.0f, a3 = 0.0f;
    uint16_t ident = identificando;

    if (grava == 2U)
    {
        if (periodoAtual >= 1U)
        {
            if (ident == 1U)        // identificacao: alfa-beta e o estado aplicado
            {
                a0 = (2.0f * correnteAgora[0] - correnteAgora[1] - correnteAgora[2]) / 3.0f;
                a1 = (correnteAgora[1] - correnteAgora[2]) * INV_RAIZ3;
                Dados3F[CANAL_ID][amostra] = (float)estadoAtual;
                Dados3F[CANAL_IQ][amostra] = a0;
                Dados3F[CANAL_VD][amostra] = a1;
                Dados3F[CANAL_VQ][amostra] = correnteAgora[0];
                Dados3F[CANAL_IA][amostra] = correnteAgora[1];
                Dados3F[CANAL_IB][amostra] = correnteAgora[2];
                if (periodoAtual == 1U)     // media sincrona de i_alfa e i_beta (canais 0-1)
                {
                    Dados3F[CANAL_IDREF][amostra] = a0;
                    Dados3F[CANAL_IQREF][amostra] = a1;
                }
                else
                {
                    Dados3F[CANAL_IDREF][amostra] += a0;
                    Dados3F[CANAL_IQREF][amostra] += a1;
                }
                if ((periodoAtual == periodosAlvo) && (periodosAlvo > 1U))
                {
                    Dados3F[CANAL_IDREF][amostra] *= inversoPeriodos;
                    Dados3F[CANAL_IQREF][amostra] *= inversoPeriodos;
                }
            }
            else                    // controle: referencias, dq e fases (como no VSI03/04)
            {
                Dados3F[CANAL_IDREF][amostra] = referenciaD;
                Dados3F[CANAL_IQREF][amostra] = referenciaQ;
                Dados3F[CANAL_IA][amostra]    = correnteAgora[0];
                Dados3F[CANAL_IB][amostra]    = correnteAgora[1];
                a0 = correnteD;  a1 = correnteQ;  a2 = tensaoDAgora;  a3 = tensaoQAgora;
                if (periodoAtual == 1U)
                {
                    Dados3F[CANAL_ID][amostra] = a0;
                    Dados3F[CANAL_IQ][amostra] = a1;
                    Dados3F[CANAL_VD][amostra] = a2;
                    Dados3F[CANAL_VQ][amostra] = a3;
                }
                else
                {
                    Dados3F[CANAL_ID][amostra] += a0;
                    Dados3F[CANAL_IQ][amostra] += a1;
                    Dados3F[CANAL_VD][amostra] += a2;
                    Dados3F[CANAL_VQ][amostra] += a3;
                }
                if ((periodoAtual == periodosAlvo) && (periodosAlvo > 1U))
                {
                    Dados3F[CANAL_ID][amostra] *= inversoPeriodos;
                    Dados3F[CANAL_IQ][amostra] *= inversoPeriodos;
                    Dados3F[CANAL_VD][amostra] *= inversoPeriodos;
                    Dados3F[CANAL_VQ][amostra] *= inversoPeriodos;
                }
            }
            Tempos[0][amostra] = dMedidas;
            Tempos[1][amostra] = 0.0f;
            Tempos[2][amostra] = dFCS;
            Tempos[3][amostra] = dTotal;          // interrupcao inteira da amostra anterior
        }
    }
    amostra++;
    if (amostra >= N_AMOSTRAS)
    {
        amostra = 0U;
        if (grava == 2U)
        {
            if (periodoAtual >= periodosAlvo)
            {
                grava = 0U;                 // pronto (media ja dividida)
                if (ident == 1U)
                {
                    calculaEDMD = 1U;       // laco principal calcula G
                }
            }
            else
            {
                periodoAtual++;
            }
        }
    }
}

// Chamada no laco principal: termina a media sincrona
static void TerminaMedia(void)
{
    uint16_t k;
    float inverso = 1.0f / (float)periodosAlvo;

    for (k = 0U; k < N_AMOSTRAS; k++)
    {
        Dados3F[CANAL_ID][k] *= inverso;
        Dados3F[CANAL_IQ][k] *= inverso;
        Dados3F[CANAL_VD][k] *= inverso;
        Dados3F[CANAL_VQ][k] *= inverso;
    }
    grava = 0U;
}

// ============================================================================
// ADC: em cada conversor, SOC0 = tensao da fase (nao usada aqui, mantida como
// no VSI01), SOC1 = corrente no zero do contador e SOC2 = corrente no topo:
//   fase A: ADCC, ADCINC3 (J3-24) e ADCINC2 (J3-27)
//   fase B: ADCB, ADCINB3 (J3-25) e ADCINB2 (J3-28)
//   fase C: ADCA, ADCINA3 (J3-26) e ADCINA2 (J3-29)
//   barramento: ADCD, ADCIN14 (J3-23)
// SOC0 e SOC1 sao disparados juntos pelo PWM da fase A no zero do contador
// (SOCA); o SOC2, no topo (SOCB).
static void ConfiguraADC(void)
{
    const uint32_t adc[4] = {ADCA_BASE, ADCB_BASE, ADCC_BASE, ADCD_BASE};
    uint16_t k;

    for (k = 0U; k < 4U; k++)
    {
        ADC_setPrescaler(adc[k], ADC_CLK_DIV_4_0);                       // 50 MHz
        ADC_setMode(adc[k], ADC_RESOLUTION_12BIT, ADC_MODE_SINGLE_ENDED);
        ADC_setInterruptPulseMode(adc[k], ADC_PULSE_END_OF_CONV);
        ADC_enableConverter(adc[k]);
    }
    DEVICE_DELAY_US(1000U);         // espera os ADCs ligarem

    // janela de amostragem: 20 ciclos de 5 ns = 100 ns
    ADC_setupSOC(ADCC_BASE, ADC_SOC_NUMBER0, ADC_TRIGGER_EPWM1_SOCA, ADC_CH_ADCIN3, 20U);  // vA
    ADC_setupSOC(ADCB_BASE, ADC_SOC_NUMBER0, ADC_TRIGGER_EPWM1_SOCA, ADC_CH_ADCIN3, 20U);  // vB
    ADC_setupSOC(ADCA_BASE, ADC_SOC_NUMBER0, ADC_TRIGGER_EPWM1_SOCA, ADC_CH_ADCIN3, 20U);  // vC
    ADC_setupSOC(ADCD_BASE, ADC_SOC_NUMBER0, ADC_TRIGGER_EPWM1_SOCA, ADC_CH_ADCIN14, 20U); // barramento
    ADC_setupSOC(ADCC_BASE, ADC_SOC_NUMBER1, ADC_TRIGGER_EPWM1_SOCA, ADC_CH_ADCIN2, 20U);  // iA
    ADC_setupSOC(ADCB_BASE, ADC_SOC_NUMBER1, ADC_TRIGGER_EPWM1_SOCA, ADC_CH_ADCIN2, 20U);  // iB
    ADC_setupSOC(ADCA_BASE, ADC_SOC_NUMBER1, ADC_TRIGGER_EPWM1_SOCA, ADC_CH_ADCIN2, 20U);  // iC
    ADC_setupSOC(ADCC_BASE, ADC_SOC_NUMBER2, ADC_TRIGGER_EPWM1_SOCB, ADC_CH_ADCIN2, 20U);  // iA no topo
    ADC_setupSOC(ADCB_BASE, ADC_SOC_NUMBER2, ADC_TRIGGER_EPWM1_SOCB, ADC_CH_ADCIN2, 20U);  // iB no topo
    ADC_setupSOC(ADCA_BASE, ADC_SOC_NUMBER2, ADC_TRIGGER_EPWM1_SOCB, ADC_CH_ADCIN2, 20U);  // iC no topo

    // fim da ultima conversao da ADCA no zero (SOC1) marca "medidas prontas"
    ADC_setInterruptSource(ADCA_BASE, ADC_INT_NUMBER1, ADC_SOC_NUMBER1);
    ADC_enableContinuousMode(ADCA_BASE, ADC_INT_NUMBER1);   // marca o fim de toda conversao,
    ADC_enableInterrupt(ADCA_BASE, ADC_INT_NUMBER1);        // mesmo sem a marca anterior limpa
    ADC_clearInterruptStatus(ADCA_BASE, ADC_INT_NUMBER1);

    // o PWM da fase A dispara as conversoes quando o contador passa por zero
    EPWM_setADCTriggerSource(EPWM1_BASE, EPWM_SOC_A, EPWM_SOC_TBCTR_ZERO);
    EPWM_setADCTriggerEventPrescale(EPWM1_BASE, EPWM_SOC_A, 1U);
    EPWM_enableADCTrigger(EPWM1_BASE, EPWM_SOC_A);

    // e de novo, so as correntes, quando o contador chega ao topo
    EPWM_setADCTriggerSource(EPWM1_BASE, EPWM_SOC_B, EPWM_SOC_TBCTR_PERIOD);
    EPWM_setADCTriggerEventPrescale(EPWM1_BASE, EPWM_SOC_B, 1U);
    EPWM_enableADCTrigger(EPWM1_BASE, EPWM_SOC_B);
}

// ============================================================================
// Um modulo de PWM = um braco do inversor. Saida A comanda a chave de cima,
// saida B a de baixo (complemento de A, com tempo morto).
static void ConfiguraModuloPWM(uint32_t base)
{
    // Contador: sobe e desce entre 0 e TOPO, com o relogio de 100 MHz
    EPWM_setClockPrescaler(base, EPWM_CLOCK_DIVIDER_1, EPWM_HSCLOCK_DIVIDER_1);
    EPWM_setTimeBaseCounterMode(base, EPWM_COUNTER_MODE_UP_DOWN);
    EPWM_setTimeBasePeriod(base, TOPO);
    EPWM_setTimeBaseCounter(base, 0U);
    EPWM_disablePhaseShiftLoad(base);

    // Valor de comparacao com "sombra": o valor novo so vale quando o
    // contador passa por zero (nao muda no meio de um pulso)
    // FCS: forcamento continuo da saida A com sombra carregada no TOPO do
    // contador (as chaves mudam no meio do periodo). Desligado = PWM normal.
    EPWM_setActionQualifierContSWForceShadowMode(base, EPWM_AQ_SW_SH_LOAD_ON_CNTR_PERIOD);
    EPWM_setActionQualifierContSWForceAction(base, EPWM_AQ_OUTPUT_A, EPWM_AQ_SW_DISABLED);

    EPWM_setCounterCompareShadowLoadMode(base, EPWM_COUNTER_COMPARE_A,
                                         EPWM_COMP_LOAD_ON_CNTR_ZERO);
    EPWM_setCounterCompareValue(base, EPWM_COUNTER_COMPARE_A, TOPO / 2U);

    // Saida A: desce quando o contador, subindo, alcanca CMPA; sobe quando o
    // contador, descendo, passa por CMPA -> alta enquanto contador < CMPA
    EPWM_setActionQualifierAction(base, EPWM_AQ_OUTPUT_A, EPWM_AQ_OUTPUT_LOW,
                                  EPWM_AQ_OUTPUT_ON_TIMEBASE_UP_CMPA);
    EPWM_setActionQualifierAction(base, EPWM_AQ_OUTPUT_A, EPWM_AQ_OUTPUT_HIGH,
                                  EPWM_AQ_OUTPUT_ON_TIMEBASE_DOWN_CMPA);

    // Tempo morto: A liga atrasada; B = A invertida, tambem liga atrasada.
    // Assim as duas chaves nunca ficam ligadas ao mesmo tempo.
    EPWM_setRisingEdgeDeadBandDelayInput(base, EPWM_DB_INPUT_EPWMA);
    EPWM_setFallingEdgeDeadBandDelayInput(base, EPWM_DB_INPUT_EPWMA);
    EPWM_setDeadBandDelayPolarity(base, EPWM_DB_RED, EPWM_DB_POLARITY_ACTIVE_HIGH);
    EPWM_setDeadBandDelayPolarity(base, EPWM_DB_FED, EPWM_DB_POLARITY_ACTIVE_LOW);
    EPWM_setDeadBandDelayMode(base, EPWM_DB_RED, true);
    EPWM_setDeadBandDelayMode(base, EPWM_DB_FED, true);
    EPWM_setRisingEdgeDelayCount(base, CONTAGENS_MORTO);
    EPWM_setFallingEdgeDelayCount(base, CONTAGENS_MORTO);

    // Seguranca: quando o depurador pausa o programa, o contador congela e a
    // saida ficaria parada (uma chave ligada direto). O sinal de parada do
    // emulador (TZ6) forca A e B em nivel baixo: as duas chaves desligam.
    EPWM_enableTripZoneSignals(base, EPWM_TZ_SIGNAL_CBC6);
    EPWM_setTripZoneAction(base, EPWM_TZ_ACTION_EVENT_TZA, EPWM_TZ_ACTION_LOW);
    EPWM_setTripZoneAction(base, EPWM_TZ_ACTION_EVENT_TZB, EPWM_TZ_ACTION_LOW);
}

// ============================================================================
static void ConfiguraPinos(void)
{
    // Habilitacao primeiro: comeca em 1 (inversor desligado)
    GPIO_writePin(PINO_HABILITA, 1U);
    GPIO_setPadConfig(PINO_HABILITA, GPIO_PIN_TYPE_PULLUP);
    GPIO_setPinConfig(GPIO_124_GPIO124);
    GPIO_setDirectionMode(PINO_HABILITA, GPIO_DIR_MODE_OUT);

    // Saidas de PWM (J4-40 a J4-35)
    GPIO_setPadConfig(0U, GPIO_PIN_TYPE_STD);  GPIO_setPinConfig(GPIO_0_EPWM1A);  // A, chave de cima
    GPIO_setPadConfig(1U, GPIO_PIN_TYPE_STD);  GPIO_setPinConfig(GPIO_1_EPWM1B);  // A, chave de baixo
    GPIO_setPadConfig(2U, GPIO_PIN_TYPE_STD);  GPIO_setPinConfig(GPIO_2_EPWM2A);  // B, chave de cima
    GPIO_setPadConfig(3U, GPIO_PIN_TYPE_STD);  GPIO_setPinConfig(GPIO_3_EPWM2B);  // B, chave de baixo
    GPIO_setPadConfig(4U, GPIO_PIN_TYPE_STD);  GPIO_setPinConfig(GPIO_4_EPWM3A);  // C, chave de cima
    GPIO_setPadConfig(5U, GPIO_PIN_TYPE_STD);  GPIO_setPinConfig(GPIO_5_EPWM3B);  // C, chave de baixo
}
