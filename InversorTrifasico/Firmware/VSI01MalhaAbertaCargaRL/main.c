// ============================================================================
//  VSI01MalhaAbertaCargaRL - inversor trifasico em malha aberta, medindo as
//  tensoes e as correntes das tres fases
//
//  Placas: LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (encaixado em J1-J4)
//  Carga: RL trifasica em estrela (25 Ohm e 10 mH por fase), neutro isolado
//  LINCE / UFPA
//
//  Igual ao VSI01MalhaAberta, com um modo so: as razoes ciclicas das tres
//  fases variam como senoides defasadas de 120 graus (sequencia A, B, C):
//
//    razao = 0,5 + AMPLITUDE x sen(angulo - fase)
//
//  Tensao de fase na carga: pico de AMPLITUDE x Vdc (8 V com Vdc = 20 V).
//
//  Variaveis para a janela Watch do CCS (pause o programa, mude o valor e
//  continue): habilita, frequencia, grava.
//  Para observar: tensaoAgora, correnteAgora, tensaoBarramento,
//  offsetCorrente, razaoCiclica.
//
//  habilita = 1 liga o inversor; habilita = 0 desliga. Enquanto o inversor
//  esta desligado (corrente nula), o programa mede o zero dos sensores de
//  corrente (offsetCorrente). Sem protecao por software: a placa desliga
//  sozinha acima de 12 A.
//
//  Gravacao: escreva grava = 1; os vetores abaixo recebem N_AMOSTRAS amostras
//  (grava vale 2 durante a gravacao e volta a 0 no fim). Depois, pause e veja
//  os vetores no Graph - Time (float de 32 bits, N_AMOSTRAS, 20000 Hz).
//
//    tensaoA/B/C          tensoes dos bracos x GND [V], filtradas em 1 kHz na placa
//    correnteA/B/C        correntes [A] no zero do contador (meio do pulso da chave de cima)
//    correnteTopoA/B/C    correntes [A] no topo do contador (meio do pulso da chave de
//                         baixo), 25 us antes da amostra correnteA/B/C de mesmo indice
//    razaoA/B/C           razoes ciclicas aplicadas (CMPA/TOPO, ja limitadas): o
//                         chaveamento de cada braco; tensao media do braco = razao x Vdc
//    barramento           tensao do barramento [V]
//
//  Atraso da razao: o valor escrito na amostra k entra no proximo zero do
//  contador (k + 1) e so aparece inteiro na corrente a partir da amostra k + 2.
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
#define AMPLITUDE          0.4f      // amplitude da razao ciclica: varia de 0,1 a 0,9

// O contador do PWM sobe de 0 ate TOPO e desce de volta a 0: um periodo de
// PWM tem 2 x TOPO contagens de 10 ns. TOPO = 100 MHz / (2 x 20 kHz) = 2500.
#define TOPO               ((uint16_t)(FREQ_RELOGIO_PWM / (2.0f * FREQ_PWM)))
#define CONTAGENS_MORTO    ((uint16_t)(TEMPO_MORTO * FREQ_RELOGIO_PWM + 0.5f))   // 10
#define PERIODO_AMOSTRA    (1.0f / FREQ_PWM)                                     // 50 us
#define DOIS_PI            6.283185307f

// Medidas: ADC de 12 bits com referencia de 3,0 V.
// Tensao: divisor de 100 kOhm / 4,22 kOhm no BoosterPack (tensao real =
// 24,7 x tensao no pino), filtrada em 1 kHz.
// Corrente: shunt de 5 mOhm + INA240 (ganho 20): 0,1 V/A em torno de 1,65 V.
// No BoosterPack o INA240 tem as entradas trocadas: a tensao no pino DESCE
// quando a corrente sai do inversor para a carga. Com o sinal -1, corrente
// positiva = do inversor para a carga.
#define VOLTS_POR_CONTAGEM   (3.0f / 4096.0f * 24.7f)          // 18,1 mV
#define AMPERES_POR_CONTAGEM (-3.0f / (4096.0f * 0.1f))        // -7,32 mA
#define PESO_ZERO            0.001f  // media do zero dos sensores: constante de tempo de 50 ms
#define N_AMOSTRAS           2000U   // amostras por vetor: 2000 x 50 us = 100 ms (6 ciclos de 60 Hz)
#define DECIMACAO            1U      // grava 1 amostra a cada DECIMACAO periodos de PWM

// --------------------- Variaveis para a janela Watch ------------------------
volatile uint16_t habilita   = 0;       // 1 = liga o inversor | 0 = desliga
volatile float    frequencia = 60.0f;   // frequencia das senoides [Hz]
volatile uint16_t grava      = 0;       // 1 = comecar a gravar | 2 = gravando | 0 = parado

volatile float    razaoCiclica[3];      // razoes ciclicas das fases A, B, C (so leitura)
volatile float    razaoAplicada[3];     // razoes de fato escritas: CMPA/TOPO, limitadas (so leitura)
volatile float    tensaoAgora[3];       // tensoes vA, vB, vC [V], em relacao ao GND (so leitura)
volatile float    correnteAgora[3];     // correntes iA, iB, iC [A] no zero do contador (so leitura)
volatile float    correnteTopoAgora[3]; // correntes iA, iB, iC [A] no topo do contador (so leitura)
volatile float    tensaoBarramento;     // tensao do barramento [V] (so leitura)
volatile float    offsetCorrente[3] = {2253.0f, 2253.0f, 2253.0f};   // zero dos sensores [contagens]
volatile uint16_t amostra    = 0;       // amostras ja gravadas (so leitura)
static float      angulo = 0.0f;        // angulo da senoide [rad]
static uint16_t   contaDecimacao = 0;

// Vetores gravados, um por bloco de RAM (secoes "ramgs0..6" e "ramgs8..13" do .cmd)
#pragma DATA_SECTION(tensaoA, "ramgs0")
#pragma DATA_SECTION(tensaoB, "ramgs1")
#pragma DATA_SECTION(tensaoC, "ramgs2")
#pragma DATA_SECTION(correnteA, "ramgs3")
#pragma DATA_SECTION(correnteB, "ramgs4")
#pragma DATA_SECTION(correnteC, "ramgs5")
#pragma DATA_SECTION(correnteTopoA, "ramgs8")
#pragma DATA_SECTION(correnteTopoB, "ramgs9")
#pragma DATA_SECTION(correnteTopoC, "ramgs10")
#pragma DATA_SECTION(razaoA, "ramgs11")
#pragma DATA_SECTION(razaoB, "ramgs12")
#pragma DATA_SECTION(razaoC, "ramgs13")
#pragma DATA_SECTION(barramento, "ramgs6")
float tensaoA[N_AMOSTRAS];              // [V]
float tensaoB[N_AMOSTRAS];
float tensaoC[N_AMOSTRAS];
float correnteA[N_AMOSTRAS];            // [A], zero do contador
float correnteB[N_AMOSTRAS];
float correnteC[N_AMOSTRAS];
float correnteTopoA[N_AMOSTRAS];        // [A], topo do contador
float correnteTopoB[N_AMOSTRAS];
float correnteTopoC[N_AMOSTRAS];
float razaoA[N_AMOSTRAS];               // razao ciclica aplicada (0 a 1)
float razaoB[N_AMOSTRAS];
float razaoC[N_AMOSTRAS];
float barramento[N_AMOSTRAS];           // [V]

static const uint32_t modulo[3] = {EPWM1_BASE, EPWM2_BASE, EPWM3_BASE};   // fases A, B, C
static const uint32_t resultado[3] = {ADCCRESULT_BASE, ADCBRESULT_BASE, ADCARESULT_BASE}; // A, B, C

__interrupt void AtualizaPWM(void);
static void ConfiguraPinos(void);
static void ConfiguraModuloPWM(uint32_t base);
static float EscreveRazao(uint32_t base, float razao);
static void ConfiguraADC(void);
static void LeMedidas(void);

// ============================================================================
void main(void)
A{
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
    }
}

// ============================================================================
// Chamada a cada 50 us, no inicio do periodo do PWM
__interrupt void AtualizaPWM(void)
{
    uint16_t fase;

    // Senoides defasadas de 120 graus: B atrasada e C adiantada em relacao a A
    angulo += DOIS_PI * frequencia * PERIODO_AMOSTRA;
    if (angulo >= DOIS_PI)
    {
        angulo -= DOIS_PI;
    }
    razaoCiclica[0] = 0.5f + AMPLITUDE * sinf(angulo);
    razaoCiclica[1] = 0.5f + AMPLITUDE * sinf(angulo - DOIS_PI / 3.0f);
    razaoCiclica[2] = 0.5f + AMPLITUDE * sinf(angulo + DOIS_PI / 3.0f);

    for (fase = 0U; fase < 3U; fase++)
    {
        razaoAplicada[fase] = EscreveRazao(modulo[fase], razaoCiclica[fase]);
    }

    LeMedidas();                    // le o ADC

    EPWM_clearEventTriggerInterruptFlag(EPWM1_BASE);
    Interrupt_clearACKGroup(INTERRUPT_ACK_GROUP3);
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
// Le tensoes, correntes e barramento e grava, se pedido. As conversoes
// comecam quando o contador da fase A passa por zero, no mesmo instante desta
// interrupcao; espera-se o fim delas (cerca de 1 us).
static void LeMedidas(void)
{
    uint16_t espera = 0U;
    uint16_t fase;
    uint16_t contagem;

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

    for (fase = 0U; fase < 3U; fase++)
    {
        tensaoAgora[fase] = VOLTS_POR_CONTAGEM * (float)ADC_readResult(resultado[fase], ADC_SOC_NUMBER0);

        contagem = ADC_readResult(resultado[fase], ADC_SOC_NUMBER1);
        if (habilita != 1U)         // desligado: corrente nula, a leitura e o zero
        {
            offsetCorrente[fase] += PESO_ZERO * ((float)contagem - offsetCorrente[fase]);
        }
        correnteAgora[fase] = AMPERES_POR_CONTAGEM * ((float)contagem - offsetCorrente[fase]);

        // convertida no topo do contador, meio periodo antes (SOCB do EPWM1)
        contagem = ADC_readResult(resultado[fase], ADC_SOC_NUMBER2);
        correnteTopoAgora[fase] = AMPERES_POR_CONTAGEM * ((float)contagem - offsetCorrente[fase]);
    }

    if (grava == 1U)                // pedido de gravacao: comeca do zero
    {
        amostra = 0U;
        contaDecimacao = 0U;
        grava = 2U;
    }
    if (grava == 2U)
    {
        if (++contaDecimacao >= DECIMACAO)
        {
            contaDecimacao = 0U;
            tensaoA[amostra]   = tensaoAgora[0];
            tensaoB[amostra]   = tensaoAgora[1];
            tensaoC[amostra]   = tensaoAgora[2];
            correnteA[amostra] = correnteAgora[0];
            correnteB[amostra] = correnteAgora[1];
            correnteC[amostra] = correnteAgora[2];
            correnteTopoA[amostra] = correnteTopoAgora[0];
            correnteTopoB[amostra] = correnteTopoAgora[1];
            correnteTopoC[amostra] = correnteTopoAgora[2];
            razaoA[amostra]    = razaoAplicada[0];
            razaoB[amostra]    = razaoAplicada[1];
            razaoC[amostra]    = razaoAplicada[2];
            barramento[amostra] = tensaoBarramento;
            amostra++;
            if (amostra >= N_AMOSTRAS)
            {
                grava = 0U;         // vetores completos
            }
        }
    }
}

// ============================================================================
// ADC: em cada conversor, SOC0 = tensao (como no VSI01MalhaAberta) e SOC1 =
// corrente da mesma fase:
//   fase A: ADCC, ADCINC3 (J3-24) e ADCINC2 (J3-27)
//   fase B: ADCB, ADCINB3 (J3-25) e ADCINB2 (J3-28)
//   fase C: ADCA, ADCINA3 (J3-26) e ADCINA2 (J3-29)
//   barramento: ADCD, ADCIN14 (J3-23)
// SOC0 e SOC1 sao disparados juntos pelo PWM da fase A no zero do contador
// (SOCA); cada conversor faz SOC0 e depois SOC1. O SOC2 converte de novo a
// corrente no topo do contador (SOCB), no meio do pulso da chave de baixo.
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

    // fim da ultima conversao da ADCA (SOC1) marca "medidas prontas"
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
