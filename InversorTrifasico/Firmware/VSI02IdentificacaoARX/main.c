// ============================================================================
//  VSI02IdentificacaoARX - ensaio de identificacao do inversor trifasico com
//  carga RL: PRBS somada as tensoes vd e vq, em malha aberta
//
//  Placas: LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (encaixado em J1-J4)
//  Carga: RL trifasica em estrela (25 Ohm e 10 mH por fase), neutro isolado
//  LINCE / UFPA
//
//  Base: VSI01MalhaAbertaCargaRL (mesmo PWM, mesmos pinos, mesmo ADC). Em vez
//  de senoides de amplitude fixa, as tensoes de fase sao calculadas em dq:
//
//    vd = tensaoD0 + amplitudePRBS x PRBSd     (PRBSd, PRBSq = +1 ou -1)
//    vq = tensaoQ0 + amplitudePRBS x PRBSq
//    vA, vB, vC = Park inversa de (vd, vq) com o angulo de frequencia [Hz]
//    razao da fase = 0,5 + v da fase / Vdc
//
//  vd e vq sao amplitudes de pico das tensoes de fase (Park invariante em
//  amplitude): vd = 8 V e vq = 0 dao vA = 8 cos(angulo). Para nao saturar a
//  razao (5 a 95 %), sqrt(vd^2 + vq^2) <= 0,45 Vdc = 9 V com Vdc = 20 V: o
//  padrao (5 V +- 3 V em d, 0 +- 3 V em q) chega a 8,5 V.
//  As duas PRBS tem 9 bits (511 bits por periodo) com polinomios diferentes
//  (x^9 + x^5 + 1 em d, x^9 + x^4 + 1 em q): quase nao se correlacionam.
//
//  Variaveis para a janela Watch do CCS (pause o programa, mude o valor e
//  continue): habilita, frequencia, tensaoD0, tensaoQ0, amplitudePRBS,
//  eixoPRBS, amostrasPorBit, periodosMedia, grava.
//  Para observar: correnteD, correnteQ, correnteAgora, somaCorrentes,
//  tensaoBarramento, razaoAplicada, offsetZero, offsetTopo, periodoAtual,
//  calibrando.
//
//  habilita = 1 liga o inversor; habilita = 0 desliga. Zero dos sensores de
//  corrente: com o inversor desligado, media movel das leituras; ao ligar, o
//  programa aplica 50 % nas tres fases (tensao nula na carga, corrente nula)
//  por 110 ms e mede de novo o zero das amostras do zero e do topo do contador,
//  agora chaveando (calibrando = 1); so entao comeca a PRBS. Assim o zero ja
//  inclui o efeito do chaveamento no sensor (no ensaio de 2026-11-08 a soma
//  das tres correntes deu 0,2 A e o topo lia 25 mA a menos que o zero). Sem protecao por software: a placa desliga sozinha acima de 12 A
//  (com 25 Ohm e Vdc = 20 V, a corrente nao passa de 0,5 A).
//
//  Corrente: cada fase e convertida no zero do contador (meio do pulso da
//  chave de cima) e no topo (meio do pulso da chave de baixo). Usa-se a
//  amostra do zero quando a razao e >= 0,5 e a do topo quando e < 0,5: a
//  amostra fica sempre longe das bordas de chaveamento (ensaio 2 do
//  VSI01MalhaAbertaCargaRL). Cada uma tem o seu zero (offsetZero, offsetTopo).
//
//  Gravacao: escreva grava = 1. A PRBS recomeca do inicio e os canais abaixo
//  recebem N_AMOSTRAS amostras. Com amostrasPorBit = 4, os 2044 pontos sao
//  exatamente um periodo das PRBS (511 bits x 4) e ha media sincrona:
//
//    - o primeiro periodo e descartado (transitorio da partida da PRBS);
//    - nos periodosMedia periodos seguintes, id e iq acumulam a amostra de
//      mesma posicao em cada periodo; no fim, divide-se por periodosMedia.
//      A PRBS se repete, e em dq a resposta da carga tambem: o sinal fica, o
//      ruido cai com a raiz de periodosMedia (8 periodos: ruido / 2,8);
//    - os outros canais guardam o ultimo periodo (vd e vq sao iguais em
//      todos os periodos; correntes ABC, razoes e angulo nao se repetem,
//      porque 102 ms nao sao um numero inteiro de ciclos de 60 Hz).
//
//  grava vale 2 durante a gravacao, 3 enquanto a media e calculada e volta a
//  0 no fim; periodoAtual mostra o andamento (0 = descartado). Com o padrao de
//  16 periodos (ruido / 4), o ensaio dura 17 x 102 ms = 1,7 s. Com amostrasPorBit diferente de 4, grava
//  um registro so, sem descarte e sem media.
//
//  Tudo vai para uma matriz so, Dados3F[8][N_AMOSTRAS] (uma linha por canal):
//
//    0-1   vd, vq       tensoes comandadas [V]
//    2-3   id, iq       Park das correntes com o mesmo angulo [A] (media)
//    4-6   iA, iB, iC   correntes das fases [A] do ultimo periodo
//    7     angulo       angulo usado na Park inversa [rad]
//
//  8 x 2044 = 16352 valores: cabe no limite do Graph - Time do CCS (16383).
//  Para exportar: pause e, no Graph - Time, expressao Dados3F, float de 32
//  bits, tamanho 16352; exporte o CSV. Ou Memory > Save Memory a partir de
//  Dados3F, 32704 palavras. Vdc fica na Watch (tensaoBarramento); as razoes
//  ciclicas saem de vd, vq, angulo e Vdc (d = 0,5 + v/Vdc).
//
//  Atraso: a razao escrita na amostra k entra no proximo zero do contador
//  (k + 1); a tensao media que ela produz fica centrada em k + 1,5.
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

// O contador do PWM sobe de 0 ate TOPO e desce de volta a 0: um periodo de
// PWM tem 2 x TOPO contagens de 10 ns. TOPO = 100 MHz / (2 x 20 kHz) = 2500.
#define TOPO               ((uint16_t)(FREQ_RELOGIO_PWM / (2.0f * FREQ_PWM)))
#define CONTAGENS_MORTO    ((uint16_t)(TEMPO_MORTO * FREQ_RELOGIO_PWM + 0.5f))   // 10
#define PERIODO_AMOSTRA    (1.0f / FREQ_PWM)                                     // 50 us
#define DOIS_PI            6.283185307f
#define RAIZ3_2            0.8660254038f                                         // sqrt(3)/2
#define INV_RAIZ3          0.5773502692f                                         // 1/sqrt(3)

// Medidas: ADC de 12 bits com referencia de 3,0 V.
// Tensao do barramento: divisor de 100 kOhm / 4,22 kOhm (x 24,7).
// Corrente: shunt de 5 mOhm + INA240 (ganho 20): 0,1 V/A em torno de 1,65 V,
// com as entradas trocadas na placa (sinal -1: positiva = do inversor para a carga).
#define VOLTS_POR_CONTAGEM   (3.0f / 4096.0f * 24.7f)          // 18,1 mV
#define AMPERES_POR_CONTAGEM (-3.0f / (4096.0f * 0.1f))        // -7,32 mA
#define PESO_ZERO            0.001f  // media do zero dos sensores: constante de tempo de 50 ms
#define PESO_VDC             0.01f   // media do barramento usado na razao: 5 ms
#define N_ESPERA_CALIB       200U    // calibracao chaveando: espera 10 ms...
#define N_CALIBRACAO         2000U   // ...e soma 2000 amostras (100 ms)
#define N_AMOSTRAS           2044U   // amostras por vetor: 511 bits x 4 = um periodo da PRBS (102 ms)
#define BITS_PRBS            511U    // periodo da PRBS de 9 bits
#define MAX_PERIODOS         64U    // limite de periodosMedia

// eixoPRBS
#define EIXO_DQ            0U        // PRBS em vd e em vq ao mesmo tempo
#define EIXO_D             1U        // so em vd
#define EIXO_Q             2U        // so em vq

// --------------------- Variaveis para a janela Watch ------------------------
volatile uint16_t habilita       = 0;       // 1 = liga o inversor | 0 = desliga
volatile float    frequencia     = 60.0f;   // frequencia do referencial dq [Hz]
volatile float    tensaoD0       = 5.0f;    // ponto de operacao de vd [V]
volatile float    tensaoQ0       = 0.0f;    // ponto de operacao de vq [V]
volatile float    amplitudePRBS  = 3.0f;    // amplitude da PRBS [V] (0 = sem excitacao)
volatile uint16_t eixoPRBS       = EIXO_DQ; // 0 = d e q | 1 = so d | 2 = so q
volatile uint16_t amostrasPorBit = 4U;      // duracao de um bit da PRBS em periodos de PWM
volatile uint16_t periodosMedia  = 16U;     // periodos da PRBS na media (1 a 64)
volatile uint16_t grava          = 0;       // 1 = comecar | 2 = gravando | 3 = media | 0 = parado

volatile float    tensaoDAgora, tensaoQAgora;   // vd e vq comandadas [V] (so leitura)
volatile float    correnteD, correnteQ;         // id e iq [A] (so leitura)
volatile float    somaCorrentes;                // iA + iB + iC medidas, antes da correcao (so leitura)
volatile float    razaoAplicada[3];             // razoes escritas: CMPA/TOPO (so leitura)
volatile float    correnteAgora[3];             // iA, iB, iC [A], zero ou topo (so leitura)
volatile float    tensaoBarramento;             // tensao do barramento [V] (so leitura)
volatile float    offsetZero[3] = {2253.0f, 2253.0f, 2253.0f};   // zero dos sensores no zero [contagens]
volatile float    offsetTopo[3] = {2253.0f, 2253.0f, 2253.0f};   // e no topo do contador [contagens]
volatile uint16_t amostra        = 0;       // posicao no periodo (so leitura)
volatile uint16_t periodoAtual   = 0;       // periodo em gravacao: 0 = descartado (so leitura)
volatile uint16_t calibrando     = 0;       // 1 = medindo o zero chaveando, a 50 % (so leitura)
static uint16_t   habilitaAnterior = 0;
static uint16_t   contaCalib = 0;
static uint32_t   somaZero[3], somaTopo[3];
static uint16_t   periodosAlvo   = 1U;      // periodos acumulados nesta gravacao

static float      angulo = 0.0f;            // angulo do referencial dq [rad]
static float      cosAngulo = 1.0f, senAngulo = 0.0f;
static float      vdcFiltrado = VDC_NOMINAL;
static float      razaoAnterior[3] = {0.5f, 0.5f, 0.5f};   // razao em vigor no periodo atual
static uint16_t   prbsD = 0x1FFU, prbsQ = 0x1FFU;          // registradores de deslocamento
static float      bitD = 1.0f, bitQ = 1.0f;                // bit atual (+1 ou -1)
static uint16_t   contaBit = 0;

// Uma matriz so com tudo o que e gravado: no CCS basta carregar "Dados3F"
// (Graph - Time com N_CANAIS x N_AMOSTRAS = 16352 floats, ou Save Memory).
// Linha c = canal c, na ordem abaixo; cada linha tem N_AMOSTRAS amostras.
// Ocupa 8 x 2044 x 2 = 32704 palavras, na faixa de RAM RAMGS0_12 do .cmd
// (RAMGS0 a RAMGS12 juntos, a partir de 0xC000). O Graph - Time do CCS
// exporta no maximo 16383 valores: por isso so 8 linhas.
#define CANAL_VD        0U      // vd comandada [V]
#define CANAL_VQ        1U      // vq comandada [V]
#define CANAL_ID        2U      // id [A] (media sincrona)
#define CANAL_IQ        3U      // iq [A] (media sincrona)
#define CANAL_IA        4U      // corrente da fase A [A] (ultimo periodo)
#define CANAL_IB        5U
#define CANAL_IC        6U
#define CANAL_ANGULO    7U      // angulo da Park [rad]
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
static void Excitacao(void);
static float PassoPRBS(uint16_t *registro, uint16_t tap);
static void LeMedidas(void);
static void Grava(void);
static void TerminaMedia(void);

// ============================================================================
void main(void)
{
    uint16_t fase;

    Device_init();                  // relogio de 200 MHz e perifericos ligados
    Device_initGPIO();
    Interrupt_initModule();         // controlador de interrupcoes
    Interrupt_initVectorTable();

    ConfiguraPinos();               // inversor desligado desde o inicio

    // Os tres modulos sao configurados com os contadores parados e partem
    // juntos quando o relogio comum (TBCLKSYNC) e liberado: ficam sincronizados.
    SysCtl_setEPWMClockDivider(SYSCTL_EPWMCLK_DIV_2);           // 100 MHz
    SysCtl_disablePeripheral(SYSCTL_PERIPH_CLK_TBCLKSYNC);
    for (fase = 0U; fase < 3U; fase++)
    {
        ConfiguraModuloPWM(modulo[fase]);
    }
    ConfiguraADC();                 // conversoes disparadas pelo PWM da fase A

    // Interrupcao no inicio de cada periodo do PWM da fase A (contador = 0):
    // calcula as razoes ciclicas do periodo seguinte.
    EPWM_setInterruptSource(EPWM1_BASE, EPWM_INT_TBCTR_ZERO);
    EPWM_setInterruptEventCount(EPWM1_BASE, 1U);
    EPWM_enableInterrupt(EPWM1_BASE);
    EPWM_clearEventTriggerInterruptFlag(EPWM1_BASE);
    Interrupt_register(INT_EPWM1, &AtualizaPWM);
    Interrupt_enable(INT_EPWM1);

    SysCtl_enablePeripheral(SYSCTL_PERIPH_CLK_TBCLKSYNC);       // os tres contadores partem

    EINT;                           // libera as interrupcoes
    ERTM;                           // modo de depuracao em tempo real

    for (;;)
    {
        // Habilitacao do inversor (ativa em nivel baixo): 0 liga, 1 desliga
        GPIO_writePin(PINO_HABILITA, (habilita == 1U) ? 0U : 1U);

        if (grava == 3U)            // fim da gravacao: divide as somas
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

    // Ao ligar: calibracao do zero chaveando, a 50 % (ver LeMedidas)
    if ((habilita == 1U) && (habilitaAnterior != 1U))
    {
        for (fase = 0U; fase < 3U; fase++)
        {
            somaZero[fase] = 0UL;
            somaTopo[fase] = 0UL;
        }
        contaCalib = 0U;
        calibrando = 1U;
    }
    if (habilita != 1U)
    {
        calibrando = 0U;
    }
    habilitaAnterior = habilita;

    // pedido de gravacao (espera o fim da calibracao): PRBS e vetores do inicio
    if ((grava == 1U) && (calibrando == 0U))
    {
        prbsD = 0x1FFU;
        prbsQ = 0x1FFU;
        contaBit = 0U;
        amostra = 0U;
        if ((uint32_t)BITS_PRBS * amostrasPorBit == N_AMOSTRAS)
        {
            // registro = um periodo da PRBS: descarta o primeiro e faz a media
            periodosAlvo = periodosMedia;
            if (periodosAlvo < 1U) periodosAlvo = 1U;
            if (periodosAlvo > MAX_PERIODOS) periodosAlvo = MAX_PERIODOS;
            periodoAtual = 0U;
        }
        else
        {
            periodosAlvo = 1U;      // sem periodo inteiro no registro: grava um so
            periodoAtual = 1U;
        }
        grava = 2U;
    }

    angulo += DOIS_PI * frequencia * PERIODO_AMOSTRA;
    if (angulo >= DOIS_PI)
    {
        angulo -= DOIS_PI;
    }

    Excitacao();                    // vd e vq com a PRBS
    if (calibrando == 1U)
    {
        tensaoDAgora = 0.0f;        // 50 % nas tres fases: tensao nula na carga
        tensaoQAgora = 0.0f;
    }

    // Park inversa (invariante em amplitude) e Clarke inversa
    cosAngulo = cosf(angulo);
    senAngulo = sinf(angulo);
    valfa = tensaoDAgora * cosAngulo - tensaoQAgora * senAngulo;
    vbeta = tensaoDAgora * senAngulo + tensaoQAgora * cosAngulo;
    v[0] = valfa;
    v[1] = -0.5f * valfa + RAIZ3_2 * vbeta;
    v[2] = -0.5f * valfa - RAIZ3_2 * vbeta;

    // razao = 0,5 + v / Vdc: tensao media do braco em torno de Vdc/2
    for (fase = 0U; fase < 3U; fase++)
    {
        razaoAnterior[fase] = razaoAplicada[fase];
        razaoAplicada[fase] = EscreveRazao(modulo[fase], 0.5f + v[fase] / vdcFiltrado);
    }

    LeMedidas();                    // le o ADC, calcula id e iq
    Grava();                        // grava, se pedido

    EPWM_clearEventTriggerInterruptFlag(EPWM1_BASE);
    Interrupt_clearACKGroup(INTERRUPT_ACK_GROUP3);
}

// ============================================================================
// vd e vq desta amostra: ponto de operacao + amplitudePRBS x bit (+1 ou -1).
// Um bit novo a cada amostrasPorBit periodos de PWM.
static void Excitacao(void)
{
    if (contaBit == 0U)
    {
        bitD = PassoPRBS(&prbsD, 4U);       // x^9 + x^5 + 1
        bitQ = PassoPRBS(&prbsQ, 3U);       // x^9 + x^4 + 1
    }
    if (++contaBit >= amostrasPorBit)
    {
        contaBit = 0U;
    }

    tensaoDAgora = tensaoD0;
    tensaoQAgora = tensaoQ0;
    if (eixoPRBS != EIXO_Q)
    {
        tensaoDAgora += amplitudePRBS * bitD;
    }
    if (eixoPRBS != EIXO_D)
    {
        tensaoQAgora += amplitudePRBS * bitQ;
    }
}

// PRBS de 9 bits: realimentacao do bit 8 com o bit "tap" (4 -> x^9 + x^5 + 1,
// 3 -> x^9 + x^4 + 1). Periodo de 511 bits. Devolve +1 ou -1.
static float PassoPRBS(uint16_t *registro, uint16_t tap)
{
    uint16_t bit = ((*registro >> 8) ^ (*registro >> tap)) & 1U;

    *registro = ((*registro << 1) | bit) & 0x1FFU;
    return (*registro & 1U) ? 1.0f : -1.0f;
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
        if (razaoAnterior[fase] >= 0.5f)
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
            calibrando = 0U;        // zero medido: a PRBS comeca
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
// Periodo 0: so espera (transitorio). Periodos 1 a periodosAlvo: os vetores
// recebem o periodo atual; correnteD/Q somam a amostra de mesma posicao. A
// divisao pelo numero de periodos fica para o laco principal (grava = 3).
static void Grava(void)
{
    if (grava != 2U)
    {
        return;
    }
    if (periodoAtual >= 1U)
    {
        Dados3F[CANAL_IA][amostra]     = correnteAgora[0];
        Dados3F[CANAL_IB][amostra]     = correnteAgora[1];
        Dados3F[CANAL_IC][amostra]     = correnteAgora[2];
        Dados3F[CANAL_ANGULO][amostra] = angulo;
        Dados3F[CANAL_VD][amostra]     = tensaoDAgora;
        Dados3F[CANAL_VQ][amostra]     = tensaoQAgora;
        if (periodoAtual == 1U)
        {
            Dados3F[CANAL_ID][amostra] = correnteD;
            Dados3F[CANAL_IQ][amostra] = correnteQ;
        }
        else
        {
            Dados3F[CANAL_ID][amostra] += correnteD;
            Dados3F[CANAL_IQ][amostra] += correnteQ;
        }
    }
    amostra++;
    if (amostra >= N_AMOSTRAS)
    {
        amostra = 0U;
        if (periodoAtual >= periodosAlvo)
        {
            grava = 3U;             // periodos completos: media no laco principal
        }
        else
        {
            periodoAtual++;
        }
    }
}

// Chamada no laco principal: termina a media sincrona (fora da interrupcao,
// que tem so 50 us)
static void TerminaMedia(void)
{
    uint16_t k;
    float inverso = 1.0f / (float)periodosAlvo;

    for (k = 0U; k < N_AMOSTRAS; k++)
    {
        Dados3F[CANAL_ID][k] *= inverso;
        Dados3F[CANAL_IQ][k] *= inverso;
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
