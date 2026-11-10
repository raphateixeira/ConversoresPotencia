// ============================================================================
//  VSI04ControleFCS - controle preditivo de conjunto finito (FCS-MPC) da
//  corrente do inversor trifasico com carga RL
//
//  Placas: LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (encaixado em J1-J4)
//  Carga: RL trifasica em estrela (25 Ohm e 10 mH por fase), neutro isolado
//  LINCE / UFPA
//
//  Base: VSI03ControlePI (mesmo hardware, medidas, referencias, protecao e
//  gravacao). O PI continua disponivel (modo = 1) para comparar.
//
//  FCS-MPC (modo = 2): sem modulador. A cada 50 us o programa testa os 8
//  estados das chaves (Sa, Sb, Sc), preve a corrente que cada um produziria e
//  aplica o que deixa a corrente mais perto da referencia:
//
//    1. mede i(k) no zero do contador (meio do intervalo entre comutacoes)
//    2. compensa o atraso: i(k+1/2) = ah i(k) + bh v(vetor em vigor)
//    3. para cada estado e:  i(k+3/2) = a i(k+1/2) + b v(e)        (alfa-beta)
//       custo g = |i*(k+3/2) - i(k+3/2)|^2 + lambda x (comutacoes)
//    4. o estado de menor custo vale do proximo topo do contador em diante
//
//  Modelo em alfa-beta (sem acoplamento: o termo wL so aparece em dq):
//    a = exp(-R Ts / L), b = (1 - a) / R; ah, bh = o mesmo com Ts/2.
//  Vetor do estado: v_alfa = (2/3) Vdc (Sa - (Sb + Sc)/2), v_beta = Vdc (Sb - Sc)/sqrt(3).
//  Referencia em alfa-beta: Park inversa de (idRef, iqRef) com o angulo de k+3/2.
//
//  Chaveamento: forcamento continuo por software das saidas A dos PWMs
//  (B = complemento com tempo morto), com sombra carregada no TOPO do contador:
//  as chaves mudam no meio do periodo e a corrente e lida no zero, longe das
//  comutacoes. Frequencia de chaveamento variavel: frequenciaChaveamento
//  mostra a media (por chave, ciclos por segundo, janela de 1 s).
//
//  Variaveis para a janela Watch: as do VSI03 (habilita, modo, referenciaD0,
//  referenciaQ0, degrauD, degrauQ, resistencia, indutancia, bandaPI,
//  desacopla, correnteMaxima, periodosMedia, grava) e lambdaComutacao
//  (peso das comutacoes no custo, 0 = so corrente).
//  Para observar: estadoAtual, frequenciaChaveamento, custoMinimo, correnteD,
//  correnteQ, referenciaD, referenciaQ, tensaoDAgora, tensaoQAgora, falha.
//
//  modo = 0 malha aberta (PWM) | 1 PI (PWM) | 2 FCS-MPC (padrao)
//  Calibracao do zero dos sensores ao ligar: igual ao VSI03 (PWM a 50 %).
//
//  Gravacao (grava = 1): Dados3F[8][2044], como no VSI03:
//    0-1 idRef, iqRef | 2-3 id, iq (media) | 4-5 vd, vq (media do vetor
//    aplicado, em dq) | 6-7 iA, iB (ultimo periodo; iC = -iA - iB).
//  Com FCS, periodosMedia = 1 grava um registro so (mostra a ondulacao e as
//  comutacoes); 16 da a resposta media, para comparar com o PI.
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

// Uma matriz so com tudo o que e gravado (ver cabecalho). Mesma secao e mesmo
// tamanho do VSI02: faixa RAMGS0_12 do .cmd.
#define CANAL_IDREF     0U      // referencia de id [A]
#define CANAL_IQREF     1U      // referencia de iq [A]
#define CANAL_ID        2U      // id [A] (media)
#define CANAL_IQ        3U      // iq [A] (media)
#define CANAL_VD        4U      // vd aplicada [V] (media)
#define CANAL_VQ        5U      // vq aplicada [V] (media)
#define CANAL_IA        6U      // corrente da fase A [A] (ultimo periodo)
#define CANAL_IB        7U      // corrente da fase B [A] (ultimo periodo)
#define N_CANAIS        8U

#pragma DATA_SECTION(Dados3F, "Dados3F")
float Dados3F[N_CANAIS][N_AMOSTRAS];

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

    EINT;
    ERTM;

    for (;;)
    {
        GPIO_writePin(PINO_HABILITA, (habilita == 1U) ? 0U : 1U);

        // ganhos do PI: zero sobre o polo da carga (fora da interrupcao)
        kp = DOIS_PI * bandaPI * indutancia;
        ki = DOIS_PI * bandaPI * resistencia;

        // modelo do FCS em alfa-beta: passo inteiro e meio passo
        ganhoA  = expf(-resistencia * PERIODO_AMOSTRA / indutancia);
        ganhoB  = (1.0f - ganhoA) / resistencia;
        ganhoAh = expf(-resistencia * 0.5f * PERIODO_AMOSTRA / indutancia);
        ganhoBh = (1.0f - ganhoAh) / resistencia;

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
    Protecao();
    Referencias();                  // idRef e iqRef desta amostra

    if ((habilita != 1U) || (calibrando == 1U))
    {
        tensaoDAgora = 0.0f;        // desligado ou calibrando: 50 % nas tres fases
        tensaoQAgora = 0.0f;
        integralD = 0.0f;
        integralQ = 0.0f;
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

    if ((modo != MODO_FCS) || (habilita != 1U) || (calibrando == 1U))
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
// FCS-MPC: testa os 8 estados das chaves e aplica o de menor custo.
static void ControleFCS(void)
{
    uint16_t e, melhor = estadoAtual, sa, sb, sc, n, fase;
    float ialfa, ibeta, ia2, ib2, th, c, s, refA, refB;
    float va, vb, pa, pb, g, gMin = 1.0e30f, vaMelhor = 0.0f, vbMelhor = 0.0f;
    float kv = DOIS_TERCOS * vdcFiltrado;
    float kb = INV_RAIZ3 * vdcFiltrado;
    float c1, s1;

    // 1. corrente medida em alfa-beta (zero do contador, amostra k)
    ialfa = (2.0f * correnteAgora[0] - correnteAgora[1] - correnteAgora[2]) / 3.0f;
    ibeta = (correnteAgora[1] - correnteAgora[2]) * INV_RAIZ3;

    // 2. compensacao do atraso: o vetor em vigor vale ate o topo (k + 1/2)
    ia2 = ganhoAh * ialfa + ganhoBh * vAlfaAplicado;
    ib2 = ganhoAh * ibeta + ganhoBh * vBetaAplicado;

    // referencia em alfa-beta no fim do intervalo do novo vetor (k + 3/2)
    th = angulo + 1.5f * DOIS_PI * frequencia * PERIODO_AMOSTRA;
    c = cosf(th);
    s = sinf(th);
    refA = referenciaD * c - referenciaQ * s;
    refB = referenciaD * s + referenciaQ * c;

    // 3. os 8 estados (bit 2 = fase A, bit 1 = B, bit 0 = C; 1 = chave de cima)
    for (e = 0U; e < 8U; e++)
    {
        sa = (e >> 2) & 1U;
        sb = (e >> 1) & 1U;
        sc = e & 1U;
        va = kv * ((float)sa - 0.5f * (float)(sb + sc));
        vb = kb * ((float)sb - (float)sc);
        pa = ganhoA * ia2 + ganhoB * va;          // corrente prevista em k + 3/2
        pb = ganhoA * ib2 + ganhoB * vb;
        n = ((e ^ estadoAtual) & 1U) + (((e ^ estadoAtual) >> 1) & 1U) + (((e ^ estadoAtual) >> 2) & 1U);
        g = (refA - pa) * (refA - pa) + (refB - pb) * (refB - pb)
            + (lambdaComutacao + 1.0e-9f) * (float)n;   // empate: menos comutacoes
        if (g < gMin)
        {
            gMin = g;
            melhor = e;
            vaMelhor = va;
            vbMelhor = vb;
        }
    }

    // 4. aplica: forca as saidas A (B complementar com tempo morto); carrega no topo
    n = ((melhor ^ estadoAtual) & 1U) + (((melhor ^ estadoAtual) >> 1) & 1U) + (((melhor ^ estadoAtual) >> 2) & 1U);
    contaComutacoes += n;
    for (fase = 0U; fase < 3U; fase++)
    {
        EPWM_setActionQualifierContSWForceAction(modulo[fase], EPWM_AQ_OUTPUT_A,
            ((melhor >> (2U - fase)) & 1U) ? EPWM_AQ_SW_OUTPUT_HIGH : EPWM_AQ_SW_OUTPUT_LOW);
        razaoAplicada[fase] = (float)((melhor >> (2U - fase)) & 1U);
    }
    fcsAtivo = 1U;
    estadoAtual = melhor;
    custoMinimo = gMin;
    vAlfaAplicado = vaMelhor;
    vBetaAplicado = vbMelhor;

    // tensao do vetor escolhido em dq (angulo do meio do intervalo, k + 1): gravacao
    c1 = cosf(angulo + DOIS_PI * frequencia * PERIODO_AMOSTRA);
    s1 = sinf(angulo + DOIS_PI * frequencia * PERIODO_AMOSTRA);
    tensaoDAgora =  vaMelhor * c1 + vbMelhor * s1;
    tensaoQAgora = -vaMelhor * s1 + vbMelhor * c1;

    // frequencia media de chaveamento (por chave), janela de 1 s
    if (++contaJanela >= (uint32_t)FREQ_PWM)
    {
        frequenciaChaveamento = (float)contaComutacoes / 6.0f;  // 3 bracos, 2 comutacoes por ciclo
        contaComutacoes = 0UL;
        contaJanela = 0UL;
    }
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
    if (grava == 2U)
    {
        if (periodoAtual >= 1U)
        {
            Dados3F[CANAL_IDREF][amostra] = referenciaD;
            Dados3F[CANAL_IQREF][amostra] = referenciaQ;
            Dados3F[CANAL_IA][amostra]    = correnteAgora[0];
            Dados3F[CANAL_IB][amostra]    = correnteAgora[1];
            if (periodoAtual == 1U)
            {
                Dados3F[CANAL_ID][amostra] = correnteD;
                Dados3F[CANAL_IQ][amostra] = correnteQ;
                Dados3F[CANAL_VD][amostra] = tensaoDAgora;
                Dados3F[CANAL_VQ][amostra] = tensaoQAgora;
            }
            else
            {
                Dados3F[CANAL_ID][amostra] += correnteD;
                Dados3F[CANAL_IQ][amostra] += correnteQ;
                Dados3F[CANAL_VD][amostra] += tensaoDAgora;
                Dados3F[CANAL_VQ][amostra] += tensaoQAgora;
            }
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
                grava = 3U;
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
