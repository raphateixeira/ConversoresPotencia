clear, clc
Ts = 1/(48e3);
f = 60;
Vg = 110;
Vcc = 350;
Rs = 0.1;
R = 0.1;
Ls = 10e-3;
C = 1000e-6;

A = (2/3)*[1 -1/2 -1/2; 0 sqrt(3)/2 -sqrt(3)/2];

%THD = power_fftscope(out.Iabc);

%% Bancada: LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (VSI01 em diante)
% Separada das variáveis acima (VSI conectado à rede de 350 V, usadas pelo VSI06-09).
% Placa: guia SLUUBP1A da TI e MotorControl SDK (user_mtr1.h, BXL_3PHGANINV).

% Operação (valores a usar também no firmware; justificativa em VSI01MalhaAberta/index.qmd)
Bancada.fPWM    = 20e3;                 % chaveamento [Hz]: acima do audível; a 40 kHz a acomodação do INA240
                                        % (2 us) limitaria d >= 0,16; ISR com 10000 ciclos de 200 MHz
Bancada.Ts      = 1/Bancada.fPWM;       % amostragem = período da ISR (início do período do ePWM1) [s]
Bancada.EPWMCLK = 100e6;                % relógio dos ePWM [Hz]
Bancada.TBPRD   = Bancada.EPWMCLK/(2*Bancada.fPWM);   % contador sobe/desce: 2500 (11,3 bits)
Bancada.tMorto  = 100e-9;               % tempo morto [s] (10 contagens): GaN comuta em < 2 ns; o SDK da TI
                                        % usa 500-600 ns (padrão de motor). Conferir no osciloscópio.
Bancada.Vcc     = 40;                   % barramento CC [V]: teto da bancada (placa: 12-60 V, nominal 48 V; GaN 80 V)
Bancada.Vp      = 16;                   % amplitude das tensões de fase [V]: m = 0,8, d em [0,10; 0,90]
Bancada.f       = 60;                   % frequência das senoides [Hz]
Bancada.tRampa  = 1;                    % rampa de 0 a Vp [s]
Bancada.dMin    = 0.08;                 % razão cíclica mínima: borda >= 2 us da amostra em CTR = 0 (INA240)
Bancada.dMax    = 0.95;                 % razão cíclica máxima: recarga do bootstrap do LMG5200

% Estágio de potência (LMG5200: GaN 80 V / 10 A, sem diodo de corpo)
Bancada.Ron     = 15e-3;                % RDS(on) típico [ohm]
Bancada.Vsd     = 2;                    % queda reversa sem gate (tempo morto) [V], a confirmar; não representada no
                                        % modelo (o Two-Level Converter põe Vf em série com toda a condução)
Bancada.Imax    = 10;                   % corrente de pico nominal da placa [A]
Bancada.Iocp    = 12;                   % proteção de sobrecorrente da placa (TLV3201) [A]
Bancada.Itrip   = 5;                    % proteção por software sugerida (CMPSS + trip zone) [A]: ~3x a nominal

% Medição (BOOSTXL-3PHGANINV -> ADC de 12 bits, 0 a 3,3 V)
Bancada.Rsh       = 5e-3;               % shunt em linha [ohm]
Bancada.Gina      = 20;                 % ganho do INA240 [V/V]
Bancada.Vmeio     = 1.65;               % saída do INA240 com corrente nula [V]; polaridade invertida (sinal -1 no SDK)
Bancada.VfsTensao = 81.49905213;        % fundo de escala das tensões VA, VB, VC, VDC [V]
Bancada.fpTensao  = 1103.026917;        % polo do filtro RC das tensões medidas [Hz]
Bancada.Vadc      = 3.3;                % referência do ADC [V]
Bancada.nbits     = 12;

% Carga em Y com neutro isolado: indutor + resistor por fase
% Com Vp = 16 V: 1,56 A de pico (16 % da placa), 12 W por resistor, tau = L/R = 0,5 ms, fase de 10,7°.
Bancada.Lf  = 5e-3;                     % indutância [H]
Bancada.RLf = 0.1;                      % resistência série do indutor [ohm] (PROVISÓRIO: medir)
Bancada.Rc  = 10;                       % resistor de carga [ohm]

% Simulação chaveada (powergui discreto + ePWM emulado contagem a contagem)
Bancada.Tsim    = 20e-9;                % passo: múltiplo de 1/EPWMCLK que divide TBPRD e o tempo morto
Bancada.Tlog    = 1e-6;                 % amostragem dos sinais gravados [s]
Bancada.tRegime = 0.12;                 % tempo simulado depois da rampa [s]
Bancada.nJanela = 25000;                % pontos gravados a passo cheio no fim (25000 x 20 ns = 0,5 ms)