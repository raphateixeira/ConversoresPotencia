// ============================================================================
//  BK02IdentificacaoGaN - conversor buck num braco do inversor GaN: ensaio de
//  identificacao (PRBS na razao ciclica, em malha aberta)
//
//  Placas: LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (encaixado em J1-J4)
//  Montagem: so o braco A chaveia. A chave de cima (S_A+) recebe o PWM; a de
//  baixo (S_A-) fica aberta e a corrente de roda livre passa pela conducao
//  reversa do GaN (cerca de 2 V), como o diodo de um buck classico.
//    borne VA -> indutor L -> no de saida (capacitor C e carga R ao GND)
//    no de saida -> borne VB (o sensor de tensao da fase B mede v_o)
//    bornes +48V/GND: fonte de 20 V
//  Valores do projeto: L = 2,2 mH, C = 47 uF, R = 15 Ohm (ver a apresentacao
//  Buck/Ensaios/BuckBracoInversor). Os bracos B e C ficam desligados.
//  LINCE / UFPA
//
//  Base: VSI02IdentificacaoARX (mesmo PWM simetrico de 20 kHz, mesmos
//  sensores, mesma PRBS de 9 bits, mesma media sincrona), com um braco so.
//
//  Variaveis para a janela Watch do CCS (pause o programa, mude o valor e
//  continue):
//    habilita        1 = liga o conversor | 0 = desliga
//    modoChave       0 = chave de baixo aberta (buck com "diodo", padrao)
//                    1 = sincrono (chave de baixo complementar, tempo morto)
//                    (so muda com habilita = 0)
//    modo            0 = PRBS (padrao) | 1 = onda quadrada (validacao)
//                    2 = razao fixa (so razaoD0)
//    razaoD0         ponto de operacao (0,5)
//    amplitudePRBS   amplitude da PRBS e da onda quadrada (0,05: d entre 0,45 e 0,55)
//    amostrasPorBit  duracao de um bit da PRBS em periodos de PWM (4)
//    periodosMedia   periodos da PRBS na media sincrona (16)
//    amostrasQuadrada  meio periodo da onda quadrada (200 = 10 ms)
//    tempoRampa      tempo para a razao de operacao andar 100 % (0,2 s)
//    correnteMaxima, tensaoMaxima   protecao por software (1,5 A e 15 V)
//    grava           1 = comecar | 2 = gravando | 3 = media | 0 = parado
//  Para observar: razaoAplicada, razaoOperacao, correnteIndutor, tensaoSaida,
//  tensaoBraco, tensaoBarramento, correnteSaida, potenciaSaida, falha,
//  periodoAtual, offsetZero, offsetTopo.
//
//  Partida: ao ligar, a razao parte de 5 % e sobe em rampa ate razaoD0
//  (sem a rampa, o degrau de 0 a 50 % faria um pico de 1,4 A no indutor). A
//  excitacao (PRBS ou onda quadrada) so comeca quando a rampa termina.
//
//  Zero do sensor de corrente: media movel das leituras com habilita = 0 (a
//  fonte precisa estar ligada: sem barramento o INA240 fica sem alimentacao).
//  Aqui nao da para calibrar chaveando, como no VSI02: chaveando, o buck tem
//  corrente. Um erro de zero constante nao atrapalha o ARX (que usa desvios
//  em torno da media).
//
//  Corrente: amostra no zero do contador, o meio do pulso da chave de cima.
//  Com o PWM simetrico, em conducao continua, a amostra no meio do pulso e
//  o valor medio da ondulacao. Usa-se sempre a mesma amostra (no VSI02 a troca
//  zero/topo conforme a razao trazia um salto de 25 mA, que aqui viraria um
//  degrau correlacionado com a PRBS). A amostra do topo (meio do tempo
//  desligado) tambem e lida e gravada, para comparar.
//
//  Gravacao: escreva grava = 1. No modo 0, com amostrasPorBit = 4, os 2044
//  pontos sao exatamente um periodo da PRBS (511 bits x 4): o primeiro periodo
//  e descartado e os periodosMedia seguintes sao somados (media sincrona: o
//  ruido cai com a raiz do numero de periodos). Nos modos 1 e 2 (ou com outro
//  amostrasPorBit), grava um registro so, sem descarte e sem media.
//
//  Tudo vai para uma matriz so, DadosBuck[8][N_AMOSTRAS] (uma linha por canal):
//
//    0   d          razao aplicada (CMPA/TOPO)
//    1   iL         corrente no indutor [A], amostra do zero (media)
//    2   vo         tensao de saida [V], sensor da fase B, filtro de 1,2 kHz (media)
//    3   Vdc        tensao do barramento [V] (media)
//    4   vA         tensao media do braco A [V], filtro de 1,2 kHz (media)
//    5   iL cru     iL do ultimo periodo, sem media [A]
//    6   vo cru     vo do ultimo periodo, sem media [V]
//    7   iL topo    corrente no topo do contador [A] (media)
//
//  8 x 2044 = 16352 valores: cabe no limite do Graph - Time do CCS (16383).
//  Para exportar: pause e, no Graph - Time, expressao DadosBuck, float de 32
//  bits, tamanho 16352; exporte o CSV. Ou Memory > Save Memory a partir de
//  DadosBuck, 32704 palavras. Leitura: analise/simula_buck.py, ler_dados().
//  A corrente de saida nao tem sensor: io = vo / R na analise.
//
//  Atraso: a razao escrita na amostra k entra no proximo zero do contador
//  (k + 1); a corrente amostrada em k + 2 e a primeira que a sente por
//  inteiro (ARX com nk = 2).
// ============================================================================

#include "driverlib.h"
#include "device.h"
#include <math.h>

// ---------------------------- Parametros ------------------------------------
#define FREQ_RELOGIO_PWM   100e6f    // relogio dos modulos de PWM: 200 MHz / 2 = 100 MHz
#define FREQ_PWM           20e3f     // frequencia de chaveamento: 20 kHz (periodo de 50 us)
#define TEMPO_MORTO        100e-9f   // tempo morto do modo sincrono: 100 ns
#define RAZAO_MINIMA       0.05f     // limites da razao ciclica
#define RAZAO_MAXIMA       0.95f
#define PINO_HABILITA      124U      // GPIO124 (J2-13): /PWM enable do BOOSTXL, ativo em nivel BAIXO
#define PINO_BAIXO_A       1U        // GPIO1 (J4-39): chave de baixo do braco A

// O contador do PWM sobe de 0 ate TOPO e desce de volta a 0: um periodo de
// PWM tem 2 x TOPO contagens de 10 ns. TOPO = 100 MHz / (2 x 20 kHz) = 2500.
#define TOPO               ((uint16_t)(FREQ_RELOGIO_PWM / (2.0f * FREQ_PWM)))
#define CONTAGENS_MORTO    ((uint16_t)(TEMPO_MORTO * FREQ_RELOGIO_PWM + 0.5f))   // 10
#define PERIODO_AMOSTRA    (1.0f / FREQ_PWM)                                     // 50 us

// Medidas: ADC de 12 bits com referencia de 3,0 V.
// Tensoes: divisor de 100 kOhm / 4,22 kOhm (x 24,7) com 33 nF (filtro de 1,2 kHz).
// Corrente: shunt de 5 mOhm + INA240 (ganho 20): 0,1 V/A em torno de 1,65 V,
// com as entradas trocadas na placa (sinal -1: positiva = do braco para o indutor).
#define VOLTS_POR_CONTAGEM   (3.0f / 4096.0f * 24.7f)          // 18,1 mV
#define AMPERES_POR_CONTAGEM (-3.0f / (4096.0f * 0.1f))        // -7,32 mA
#define PESO_ZERO            0.001f  // media do zero do sensor: constante de tempo de 50 ms
#define N_PARTIDA            200U    // 10 ms sem protecao ao ligar (transitorio do buffer)
#define N_AMOSTRAS           2044U   // 511 bits x 4 = um periodo da PRBS (102 ms)
#define BITS_PRBS            511U    // periodo da PRBS de 9 bits
#define MAX_PERIODOS         64U     // limite de periodosMedia

// modo
#define MODO_PRBS          0U
#define MODO_QUADRADA      1U
#define MODO_FIXO          2U
// modoChave
#define CHAVE_ABERTA       0U        // chave de baixo sempre aberta (buck classico)
#define CHAVE_SINCRONA     1U        // chave de baixo complementar (buck sincrono)

// --------------------- Variaveis para a janela Watch ------------------------
volatile uint16_t habilita         = 0;       // 1 = liga o conversor | 0 = desliga
volatile uint16_t modoChave        = CHAVE_ABERTA;
volatile uint16_t modo             = MODO_PRBS;
volatile float    razaoD0          = 0.5f;    // ponto de operacao
volatile float    amplitudePRBS    = 0.05f;   // amplitude da excitacao (razao)
volatile uint16_t amostrasPorBit   = 4U;      // duracao de um bit da PRBS em periodos de PWM
volatile uint16_t periodosMedia    = 16U;     // periodos da PRBS na media (1 a 64)
volatile uint16_t amostrasQuadrada = 200U;    // meio periodo da onda quadrada (10 ms)
volatile float    tempoRampa       = 0.2f;    // [s] para a razao de operacao andar 100 %
volatile float    correnteMaxima   = 1.5f;    // [A] protecao: |iL| acima disso desliga
volatile float    tensaoMaxima     = 15.0f;   // [V] protecao: vo acima disso desliga
volatile float    resistenciaCarga = 15.0f;   // [Ohm] so para correnteSaida e potenciaSaida
volatile uint16_t grava            = 0;       // 1 = comecar | 2 = gravando | 3 = media | 0 = parado

volatile float    razaoAplicada;              // razao escrita: CMPA/TOPO (so leitura)
volatile float    razaoOperacao = RAZAO_MINIMA;   // ponto de operacao depois da rampa (so leitura)
volatile float    correnteIndutor;            // iL no zero do contador [A] (so leitura)
volatile float    correnteTopo;               // iL no topo do contador [A] (so leitura)
volatile float    tensaoSaida;                // vo [V] (so leitura)
volatile float    tensaoBraco;                // tensao media do braco A [V] (so leitura)
volatile float    tensaoBarramento;           // Vdc [V] (so leitura)
volatile float    correnteSaida;              // vo / resistenciaCarga [A] (so leitura)
volatile float    potenciaSaida;              // vo^2 / resistenciaCarga [W] (so leitura)
volatile uint16_t falha            = 0;       // 1 = protecao atuou (zere para religar)
volatile uint16_t emRampa          = 1;       // 1 = razao de operacao ainda andando (so leitura)
volatile float    offsetZero = 2253.0f;       // zero do sensor no zero do contador [contagens]
volatile float    offsetTopo = 2253.0f;       // e no topo [contagens]
volatile uint16_t amostra          = 0;       // posicao no registro (so leitura)
volatile uint16_t periodoAtual     = 0;       // periodo em gravacao: 0 = descartado (so leitura)

static uint16_t   habilitaAnterior = 0;
static uint16_t   contaPartida = 0;
static uint16_t   modoChaveAplicado = 0xFFFFU;
static uint16_t   periodosAlvo = 1U;
static uint16_t   media = 0U;                 // 1 = este registro faz media sincrona
static uint16_t   prbs = 0x1FFU;              // registrador de deslocamento
static float      bitPRBS = 1.0f;             // bit atual (+1 ou -1)
static uint16_t   contaBit = 0;
static uint16_t   contaQuadrada = 0;
static float      sinalQuadrada = -1.0f;

// Uma matriz so com tudo o que e gravado: no CCS basta carregar "DadosBuck"
// (Graph - Time com N_CANAIS x N_AMOSTRAS = 16352 floats, ou Save Memory).
// Ocupa 8 x 2044 x 2 = 32704 palavras, na faixa de RAM RAMGS0_12 do .cmd.
#define CANAL_D         0U
#define CANAL_IL        1U
#define CANAL_VO        2U
#define CANAL_VDC       3U
#define CANAL_VA        4U
#define CANAL_IL_CRU    5U
#define CANAL_VO_CRU    6U
#define CANAL_IL_TOPO   7U
#define N_CANAIS        8U

#pragma DATA_SECTION(DadosBuck, "DadosBuck")
float DadosBuck[N_CANAIS][N_AMOSTRAS];

__interrupt void AtualizaPWM(void);
static void ConfiguraPinos(void);
static void ConfiguraModuloPWM(void);
static void ConfiguraChaveBaixo(uint16_t modoDaChave);
static float EscreveRazao(float razao);
static void ConfiguraADC(void);
static float Excitacao(void);
static float PassoPRBS(void);
static void ComecaGravacao(void);
static void LeMedidas(void);
static void Protege(void);
static void Grava(void);
static void TerminaMedia(void);

// ============================================================================
void main(void)
{
    Device_init();                  // relogio de 200 MHz e perifericos ligados
    Device_initGPIO();
    Interrupt_initModule();         // controlador de interrupcoes
    Interrupt_initVectorTable();

    ConfiguraPinos();               // conversor desligado desde o inicio

    SysCtl_setEPWMClockDivider(SYSCTL_EPWMCLK_DIV_2);           // 100 MHz
    SysCtl_disablePeripheral(SYSCTL_PERIPH_CLK_TBCLKSYNC);
    ConfiguraModuloPWM();           // so o modulo do braco A
    ConfiguraChaveBaixo(modoChave);
    ConfiguraADC();                 // conversoes disparadas pelo PWM do braco A

    // Interrupcao no inicio de cada periodo do PWM (contador = 0): calcula a
    // razao ciclica do periodo seguinte.
    EPWM_setInterruptSource(EPWM1_BASE, EPWM_INT_TBCTR_ZERO);
    EPWM_setInterruptEventCount(EPWM1_BASE, 1U);
    EPWM_enableInterrupt(EPWM1_BASE);
    EPWM_clearEventTriggerInterruptFlag(EPWM1_BASE);
    Interrupt_register(INT_EPWM1, &AtualizaPWM);
    Interrupt_enable(INT_EPWM1);

    SysCtl_enablePeripheral(SYSCTL_PERIPH_CLK_TBCLKSYNC);       // o contador parte

    EINT;                           // libera as interrupcoes
    ERTM;                           // modo de depuracao em tempo real

    for (;;)
    {
        // A chave de baixo so muda de modo com o conversor desligado
        if ((habilita != 1U) && (modoChave != modoChaveAplicado))
        {
            ConfiguraChaveBaixo(modoChave);
        }

        // Habilitacao (ativa em nivel baixo): 0 liga, 1 desliga. Com falha = 1
        // fica desligado ate o usuario zerar falha.
        GPIO_writePin(PINO_HABILITA, ((habilita == 1U) && (falha == 0U)) ? 0U : 1U);

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
    float passo, erro, razao;
    uint16_t ligado = ((habilita == 1U) && (falha == 0U)) ? 1U : 0U;

    // Ao ligar: rampa a partir da razao minima
    if ((ligado == 1U) && (habilitaAnterior != 1U))
    {
        razaoOperacao = RAZAO_MINIMA;
        contaPartida = 0U;
    }
    habilitaAnterior = ligado;
    if (ligado != 1U)
    {
        razaoOperacao = RAZAO_MINIMA;
    }

    // Ponto de operacao com limite de velocidade: anda 100 % em tempoRampa
    passo = PERIODO_AMOSTRA / ((tempoRampa > 0.001f) ? tempoRampa : 0.001f);
    erro = razaoD0 - razaoOperacao;
    if (erro > passo)        erro = passo;
    else if (erro < -passo)  erro = -passo;
    razaoOperacao += erro;
    emRampa = (fabsf(razaoD0 - razaoOperacao) > 1e-6f) ? 1U : 0U;

    // Pedido de gravacao: espera o fim da rampa; a excitacao recomeca do inicio
    if ((grava == 1U) && (emRampa == 0U) && (ligado == 1U))
    {
        ComecaGravacao();
    }

    // Razao deste periodo: ponto de operacao + excitacao (so depois da rampa)
    razao = razaoOperacao;
    if ((ligado == 1U) && (emRampa == 0U))
    {
        razao += amplitudePRBS * Excitacao();
    }
    razaoAplicada = EscreveRazao(razao);

    LeMedidas();                    // le o ADC
    if (ligado == 1U)
    {
        Protege();
    }
    Grava();                        // grava, se pedido

    EPWM_clearEventTriggerInterruptFlag(EPWM1_BASE);
    Interrupt_clearACKGroup(INTERRUPT_ACK_GROUP3);
}

// ============================================================================
// Excitacao desta amostra, +1 ou -1 (0 no modo de razao fixa)
static float Excitacao(void)
{
    if (modo == MODO_PRBS)
    {
        if (contaBit == 0U)
        {
            bitPRBS = PassoPRBS();
        }
        if (++contaBit >= amostrasPorBit)
        {
            contaBit = 0U;
        }
        return bitPRBS;
    }
    if (modo == MODO_QUADRADA)
    {
        if (++contaQuadrada >= amostrasQuadrada)
        {
            contaQuadrada = 0U;
            sinalQuadrada = -sinalQuadrada;
        }
        return sinalQuadrada;
    }
    return 0.0f;
}

// PRBS de 9 bits, x^9 + x^5 + 1 (a mesma do eixo d do VSI02): periodo de 511 bits
static float PassoPRBS(void)
{
    uint16_t bit = ((prbs >> 8) ^ (prbs >> 4)) & 1U;

    prbs = ((prbs << 1) | bit) & 0x1FFU;
    return (prbs & 1U) ? 1.0f : -1.0f;
}

// Recomeca a excitacao e escolhe entre media sincrona e registro unico
static void ComecaGravacao(void)
{
    prbs = 0x1FFU;
    contaBit = 0U;
    contaQuadrada = 0U;
    sinalQuadrada = -1.0f;
    amostra = 0U;
    if ((modo == MODO_PRBS) && ((uint32_t)BITS_PRBS * amostrasPorBit == N_AMOSTRAS))
    {
        media = 1U;                 // registro = um periodo da PRBS
        periodosAlvo = periodosMedia;
        if (periodosAlvo < 1U) periodosAlvo = 1U;
        if (periodosAlvo > MAX_PERIODOS) periodosAlvo = MAX_PERIODOS;
        periodoAtual = 0U;          // o primeiro periodo e descartado
    }
    else
    {
        media = 0U;
        periodosAlvo = 1U;
        periodoAtual = 1U;
    }
    grava = 2U;
}

// ============================================================================
// Razao ciclica -> valor de comparacao (CMPA). A saida A fica em nivel alto
// enquanto o contador esta abaixo de CMPA: razao = CMPA / TOPO.
// Devolve a razao de fato aplicada (limitada e arredondada para CMPA).
static float EscreveRazao(float razao)
{
    uint16_t cmpa;

    if (razao < RAZAO_MINIMA) razao = RAZAO_MINIMA;
    if (razao > RAZAO_MAXIMA) razao = RAZAO_MAXIMA;
    cmpa = (uint16_t)(razao * (float)TOPO);
    EPWM_setCounterCompareValue(EPWM1_BASE, EPWM_COUNTER_COMPARE_A, cmpa);
    return (float)cmpa / (float)TOPO;
}

// ============================================================================
// Le corrente e tensoes. As conversoes do zero comecam junto com esta
// interrupcao; espera-se o fim delas (cerca de 1 us). A do topo foi feita
// meio periodo antes.
static void LeMedidas(void)
{
    uint16_t espera = 0U;
    float nZero, nTopo;

    while ((ADC_getInterruptStatus(ADCC_BASE, ADC_INT_NUMBER1) == false) && (espera < 1000U))
    {
        espera++;                   // limite: nunca trava a interrupcao
    }
    ADC_clearInterruptStatus(ADCC_BASE, ADC_INT_NUMBER1);
    if (ADC_getInterruptOverflowStatus(ADCC_BASE, ADC_INT_NUMBER1))
    {
        ADC_clearInterruptOverflowStatus(ADCC_BASE, ADC_INT_NUMBER1);   // marca perdida (pausa)
    }

    tensaoBarramento = VOLTS_POR_CONTAGEM * (float)ADC_readResult(ADCDRESULT_BASE, ADC_SOC_NUMBER0);
    tensaoSaida      = VOLTS_POR_CONTAGEM * (float)ADC_readResult(ADCBRESULT_BASE, ADC_SOC_NUMBER0);
    tensaoBraco      = VOLTS_POR_CONTAGEM * (float)ADC_readResult(ADCCRESULT_BASE, ADC_SOC_NUMBER0);

    nZero = (float)ADC_readResult(ADCCRESULT_BASE, ADC_SOC_NUMBER1);
    nTopo = (float)ADC_readResult(ADCCRESULT_BASE, ADC_SOC_NUMBER2);
    if (habilitaAnterior != 1U)     // desligado: corrente nula, a leitura e o zero
    {
        offsetZero += PESO_ZERO * (nZero - offsetZero);
        offsetTopo += PESO_ZERO * (nTopo - offsetTopo);
    }
    correnteIndutor = AMPERES_POR_CONTAGEM * (nZero - offsetZero);
    correnteTopo    = AMPERES_POR_CONTAGEM * (nTopo - offsetTopo);

    correnteSaida = tensaoSaida / resistenciaCarga;
    potenciaSaida = tensaoSaida * correnteSaida;
}

// Protecao por software: desliga o buffer na hora (sem esperar o laco
// principal). Os primeiros 10 ms depois de ligar ficam de fora: o buffer de
// PWM, ao ligar, faz o sensor ler um pico falso (VSI01).
static void Protege(void)
{
    if (contaPartida < N_PARTIDA)
    {
        contaPartida++;
        return;
    }
    if ((fabsf(correnteIndutor) > correnteMaxima) || (tensaoSaida > tensaoMaxima))
    {
        GPIO_writePin(PINO_HABILITA, 1U);
        falha = 1U;
        habilita = 0U;
        grava = 0U;
    }
}

// ============================================================================
// Periodo 0: so espera (transitorio). Periodos 1 a periodosAlvo: os canais
// com media somam a amostra de mesma posicao; os crus guardam o ultimo
// periodo. A divisao fica para o laco principal (grava = 3).
static void Grava(void)
{
    if (grava != 2U)
    {
        return;
    }
    if (periodoAtual >= 1U)
    {
        DadosBuck[CANAL_D][amostra]      = razaoAplicada;
        DadosBuck[CANAL_IL_CRU][amostra] = correnteIndutor;
        DadosBuck[CANAL_VO_CRU][amostra] = tensaoSaida;
        if (periodoAtual == 1U)
        {
            DadosBuck[CANAL_IL][amostra]      = correnteIndutor;
            DadosBuck[CANAL_VO][amostra]      = tensaoSaida;
            DadosBuck[CANAL_VDC][amostra]     = tensaoBarramento;
            DadosBuck[CANAL_VA][amostra]      = tensaoBraco;
            DadosBuck[CANAL_IL_TOPO][amostra] = correnteTopo;
        }
        else
        {
            DadosBuck[CANAL_IL][amostra]      += correnteIndutor;
            DadosBuck[CANAL_VO][amostra]      += tensaoSaida;
            DadosBuck[CANAL_VDC][amostra]     += tensaoBarramento;
            DadosBuck[CANAL_VA][amostra]      += tensaoBraco;
            DadosBuck[CANAL_IL_TOPO][amostra] += correnteTopo;
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

// Chamada no laco principal: termina a media sincrona (fora da interrupcao)
static void TerminaMedia(void)
{
    uint16_t k;
    float inverso = 1.0f / (float)periodosAlvo;

    if (media == 1U)
    {
        for (k = 0U; k < N_AMOSTRAS; k++)
        {
            DadosBuck[CANAL_IL][k]      *= inverso;
            DadosBuck[CANAL_VO][k]      *= inverso;
            DadosBuck[CANAL_VDC][k]     *= inverso;
            DadosBuck[CANAL_VA][k]      *= inverso;
            DadosBuck[CANAL_IL_TOPO][k] *= inverso;
        }
    }
    grava = 0U;
}

// ============================================================================
// ADC (os mesmos canais do VSI02):
//   ADCC: SOC0 = tensao do braco A, ADCINC3 (J3-24)
//         SOC1 = corrente do braco A no zero, ADCINC2 (J3-27)
//         SOC2 = a mesma corrente no topo
//   ADCB: SOC0 = tensao do borne VB, ADCINB3 (J3-25) = tensao de saida v_o
//   ADCD: SOC0 = barramento, ADCIN14 (J3-23)
// Os SOC0 e o SOC1 sao disparados pelo PWM no zero do contador (SOCA); o
// SOC2, no topo (SOCB). O fim do SOC1 da ADCC (a ultima do zero) marca
// "medidas prontas".
static void ConfiguraADC(void)
{
    const uint32_t adc[3] = {ADCB_BASE, ADCC_BASE, ADCD_BASE};
    uint16_t k;

    for (k = 0U; k < 3U; k++)
    {
        ADC_setPrescaler(adc[k], ADC_CLK_DIV_4_0);                       // 50 MHz
        ADC_setMode(adc[k], ADC_RESOLUTION_12BIT, ADC_MODE_SINGLE_ENDED);
        ADC_setInterruptPulseMode(adc[k], ADC_PULSE_END_OF_CONV);
        ADC_enableConverter(adc[k]);
    }
    DEVICE_DELAY_US(1000U);         // espera os ADCs ligarem

    // janela de amostragem: 20 ciclos de 5 ns = 100 ns
    ADC_setupSOC(ADCC_BASE, ADC_SOC_NUMBER0, ADC_TRIGGER_EPWM1_SOCA, ADC_CH_ADCIN3, 20U);  // vA
    ADC_setupSOC(ADCB_BASE, ADC_SOC_NUMBER0, ADC_TRIGGER_EPWM1_SOCA, ADC_CH_ADCIN3, 20U);  // vo (borne VB)
    ADC_setupSOC(ADCD_BASE, ADC_SOC_NUMBER0, ADC_TRIGGER_EPWM1_SOCA, ADC_CH_ADCIN14, 20U); // barramento
    ADC_setupSOC(ADCC_BASE, ADC_SOC_NUMBER1, ADC_TRIGGER_EPWM1_SOCA, ADC_CH_ADCIN2, 20U);  // iL no zero
    ADC_setupSOC(ADCC_BASE, ADC_SOC_NUMBER2, ADC_TRIGGER_EPWM1_SOCB, ADC_CH_ADCIN2, 20U);  // iL no topo

    ADC_setInterruptSource(ADCC_BASE, ADC_INT_NUMBER1, ADC_SOC_NUMBER1);
    ADC_enableContinuousMode(ADCC_BASE, ADC_INT_NUMBER1);   // marca o fim de toda conversao,
    ADC_enableInterrupt(ADCC_BASE, ADC_INT_NUMBER1);        // mesmo sem a marca anterior limpa
    ADC_clearInterruptStatus(ADCC_BASE, ADC_INT_NUMBER1);

    // o PWM do braco A dispara as conversoes quando o contador passa por zero
    EPWM_setADCTriggerSource(EPWM1_BASE, EPWM_SOC_A, EPWM_SOC_TBCTR_ZERO);
    EPWM_setADCTriggerEventPrescale(EPWM1_BASE, EPWM_SOC_A, 1U);
    EPWM_enableADCTrigger(EPWM1_BASE, EPWM_SOC_A);

    // e de novo, so a corrente, quando o contador chega ao topo
    EPWM_setADCTriggerSource(EPWM1_BASE, EPWM_SOC_B, EPWM_SOC_TBCTR_PERIOD);
    EPWM_setADCTriggerEventPrescale(EPWM1_BASE, EPWM_SOC_B, 1U);
    EPWM_enableADCTrigger(EPWM1_BASE, EPWM_SOC_B);
}

// ============================================================================
// O modulo EPWM1 = braco A. Saida A comanda a chave de cima; a saida B (chave
// de baixo) e o complemento de A com tempo morto, mas so chega ao pino no modo
// sincrono (ver ConfiguraChaveBaixo).
static void ConfiguraModuloPWM(void)
{
    const uint32_t base = EPWM1_BASE;

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
    EPWM_setCounterCompareValue(base, EPWM_COUNTER_COMPARE_A,
                                (uint16_t)(RAZAO_MINIMA * (float)TOPO));

    // Saida A: alta enquanto contador < CMPA (pulso centrado no zero)
    EPWM_setActionQualifierAction(base, EPWM_AQ_OUTPUT_A, EPWM_AQ_OUTPUT_LOW,
                                  EPWM_AQ_OUTPUT_ON_TIMEBASE_UP_CMPA);
    EPWM_setActionQualifierAction(base, EPWM_AQ_OUTPUT_A, EPWM_AQ_OUTPUT_HIGH,
                                  EPWM_AQ_OUTPUT_ON_TIMEBASE_DOWN_CMPA);

    // Tempo morto: A liga atrasada; B = A invertida, tambem liga atrasada
    EPWM_setRisingEdgeDeadBandDelayInput(base, EPWM_DB_INPUT_EPWMA);
    EPWM_setFallingEdgeDeadBandDelayInput(base, EPWM_DB_INPUT_EPWMA);
    EPWM_setDeadBandDelayPolarity(base, EPWM_DB_RED, EPWM_DB_POLARITY_ACTIVE_HIGH);
    EPWM_setDeadBandDelayPolarity(base, EPWM_DB_FED, EPWM_DB_POLARITY_ACTIVE_LOW);
    EPWM_setDeadBandDelayMode(base, EPWM_DB_RED, true);
    EPWM_setDeadBandDelayMode(base, EPWM_DB_FED, true);
    EPWM_setRisingEdgeDelayCount(base, CONTAGENS_MORTO);
    EPWM_setFallingEdgeDelayCount(base, CONTAGENS_MORTO);

    // Seguranca: quando o depurador pausa o programa, o sinal de parada do
    // emulador (TZ6) forca A e B em nivel baixo: as duas chaves desligam.
    EPWM_enableTripZoneSignals(base, EPWM_TZ_SIGNAL_CBC6);
    EPWM_setTripZoneAction(base, EPWM_TZ_ACTION_EVENT_TZA, EPWM_TZ_ACTION_LOW);
    EPWM_setTripZoneAction(base, EPWM_TZ_ACTION_EVENT_TZB, EPWM_TZ_ACTION_LOW);
}

// Chave de baixo do braco A: no modo aberto, o pino GPIO1 deixa de ser PWM e
// vira saida comum em nivel baixo (a chave nunca liga); no sincrono, volta a
// ser EPWM1B. Chamada so com o conversor desligado.
static void ConfiguraChaveBaixo(uint16_t modoDaChave)
{
    if (modoDaChave == CHAVE_SINCRONA)
    {
        GPIO_setPinConfig(GPIO_1_EPWM1B);
    }
    else
    {
        GPIO_writePin(PINO_BAIXO_A, 0U);
        GPIO_setDirectionMode(PINO_BAIXO_A, GPIO_DIR_MODE_OUT);
        GPIO_setPinConfig(GPIO_1_GPIO1);
    }
    modoChaveAplicado = modoDaChave;
}

// ============================================================================
static void ConfiguraPinos(void)
{
    uint16_t pino;

    // Habilitacao primeiro: comeca em 1 (conversor desligado)
    GPIO_writePin(PINO_HABILITA, 1U);
    GPIO_setPadConfig(PINO_HABILITA, GPIO_PIN_TYPE_PULLUP);
    GPIO_setPinConfig(GPIO_124_GPIO124);
    GPIO_setDirectionMode(PINO_HABILITA, GPIO_DIR_MODE_OUT);

    // Braco A: chave de cima no EPWM1A (J4-40); a de baixo (GPIO1, J4-39) e
    // configurada em ConfiguraChaveBaixo
    GPIO_setPadConfig(0U, GPIO_PIN_TYPE_STD);
    GPIO_setPinConfig(GPIO_0_EPWM1A);
    GPIO_setPadConfig(PINO_BAIXO_A, GPIO_PIN_TYPE_STD);

    // Bracos B e C (GPIO2 a GPIO5, J4-38 a J4-35): saidas comuns em nivel
    // baixo, as quatro chaves sempre abertas. O borne VB fica livre para o
    // sensor de tensao medir v_o.
    for (pino = 2U; pino <= 5U; pino++)
    {
        GPIO_writePin(pino, 0U);
        GPIO_setPadConfig(pino, GPIO_PIN_TYPE_STD);
        GPIO_setDirectionMode(pino, GPIO_DIR_MODE_OUT);
    }
    GPIO_setPinConfig(GPIO_2_GPIO2);
    GPIO_setPinConfig(GPIO_3_GPIO3);
    GPIO_setPinConfig(GPIO_4_GPIO4);
    GPIO_setPinConfig(GPIO_5_GPIO5);
}
