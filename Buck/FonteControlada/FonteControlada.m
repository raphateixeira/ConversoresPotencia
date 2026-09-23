%  FONTE CC CONTROLADA - BUCK
%  LINCE (UFPA-CAMTUC-FEE)
clear; clc; close all;

%% ================= 0. ESPECIFICAÇÕES DE ENTRADA (AJUSTAR) =============
Vac_rms    = 110;      % V   - tensão eficaz da rede CA
f_linha    = 60;       % Hz  - frequência da rede
Vd_diode   = 0.0;      % V   - queda direta de cada diodo da ponte (2 em condução)

Vo_ref     = 48;       % V   - tensão de saída regulada pelo buck
Io_max     = 5;        % A   - corrente máxima de carga
fsw        = 40e3;     % Hz  - frequência de chaveamento do buck

dVbulk_pct = 0.08;     % ripple admitido no barramento CC, fração de Vpico retificado
k_IL       = 0.30;     % ripple de corrente do indutor, fração de Io_max
dVo_pct    = 0.01;     % ripple de tensão de saída admitido, fração de Vo_ref
Resr_Co    = 20e-3;    % ohm - ESR estimado do capacitor de saída 
eta        = 0.93;     % eficiência estimada do conversor completo

%% 1. ESTÁGIO CA: PONTE + FILTRO CAPACITIVO
Vac_pk   = Vac_rms*sqrt(2);
Vrect_pk = Vac_pk - 2*Vd_diode;         % pico retificado, já descontando 2 diodos

Po  = Vo_ref*Io_max;                    % potência de saída nominal
Pin = Po/eta;                           % potência de entrada estimada

Ibulk_avg = Pin/Vrect_pk;               % corrente média drenada do barramento CC

dVbulk = dVbulk_pct*Vrect_pk;
Cbulk  = Ibulk_avg/(2*f_linha*dVbulk);  % C = Io/(2*f_linha*dV), ponte completa -> ripple em 2*f_linha

Vbulk_max = Vrect_pk;
Vbulk_min = Vrect_pk - dVbulk;
Vbulk_avg = (Vbulk_max + Vbulk_min)/2;

%% ================= 2. CONVERSOR BUCK: INDUTOR E CAPACITOR ==============
Dmin = Vo_ref/Vbulk_max;
Dmax = Vo_ref/Vbulk_min;

% Ponto de pior caso de ripple: D mais próximo de 0,5 dentro de [Dmin,Dmax]
if Dmin <= 0.5 && Dmax >= 0.5
    D_worst = 0.5;
elseif abs(Dmin - 0.5) < abs(Dmax - 0.5)
    D_worst = Dmin;
else
    D_worst = Dmax;
end
Vin_worst = Vo_ref/D_worst;             % tensão de entrada no pior caso

dIL = k_IL*Io_max;
L = (Vin_worst - Vo_ref)*D_worst/(fsw*dIL);

% Verificação de CCM (na corrente nominal de carga)
Io_crit = dIL/2;
CCM_ok  = Io_max > Io_crit;

IL_pk  = Io_max + dIL/2;
IL_rms = sqrt(Io_max^2 + (dIL^2)/12);   % DC + ripple triangular

% Capacitor de saída: orçamento de ripple dividido entre C e ESR
dVo_alvo   = dVo_pct*Vo_ref;
dVo_ESR    = dIL*Resr_Co;
dVo_C_budget = max(dVo_alvo - dVo_ESR, 1e-6);   % o que sobra para o termo capacitivo
Co = dIL/(8*fsw*dVo_C_budget);

%% ================= 3. ESFORÇOS NOS SEMICONDUTORES ======================
% Diodo de roda-livre do buck
Vdiode_block  = Vin_worst;
Idiode_avg    = Io_max*(1 - D_worst);
Idiode_rms    = Io_max*sqrt(1 - D_worst);

% Chave (MOSFET) do buck
Vsw_block = Vin_worst;
Isw_rms   = Io_max*sqrt(D_worst);

% Diodos da ponte retificadora (2 conduzem por semiciclo)
Idiode_bridge_avg = Ibulk_avg/2;
Vdiode_bridge_block = Vac_pk;

%% ================= 4. RESUMO IMPRESSO ===================================
fprintf('\n===================== RESUMO DO DIMENSIONAMENTO =====================\n');
fprintf('--- Entrada CA / Retificador ---\n');
fprintf('Vac_pk           = %8.1f V\n', Vac_pk);
fprintf('Vrect_pk (c/ Vd) = %8.1f V\n', Vrect_pk);
fprintf('Ibulk_avg        = %8.3f A\n', Ibulk_avg);
fprintf('Diodos da ponte  : V_reversa >= %.0f V, I_avg >= %.2f A (cada)\n', ...
        Vdiode_bridge_block, Idiode_bridge_avg);

fprintf('\n--- Barramento CC (capacitor de filtro) ---\n');
fprintf('dVbulk (ripple)  = %8.2f V  (%.1f %% de Vrect_pk)\n', dVbulk, dVbulk_pct*100);
fprintf('Cbulk (calculado)= %8.1f uF\n', Cbulk*1e6);
fprintf('Vbulk faixa      = %.1f V a %.1f V\n', Vbulk_min, Vbulk_max);
fprintf('Tensão nominal sugerida do capacitor >= %.0f V (margem 20%%% sobre Vac_pk)\n', 1.2*Vac_pk);

fprintf('\n--- Conversor Buck ---\n');
fprintf('D min / max      = %.3f / %.3f  (em Vbulk max/min)\n', Dmin, Dmax);
fprintf('D pior caso      = %.3f   (Vin nesse ponto = %.1f V)\n', D_worst, Vin_worst);
fprintf('L (calculado)    = %8.1f uH\n', L*1e6);
fprintf('dIL              = %8.2f A pico a pico (%.0f%% de Io_max)\n', dIL, k_IL*100);
fprintf('IL_pico          = %8.2f A\n', IL_pk);
fprintf('IL_rms           = %8.2f A\n', IL_rms);
fprintf('CCM garantido em Io_max? %s  (Io_crit = %.2f A)\n', mat2str(CCM_ok), Io_crit);

fprintf('\n--- Capacitor de saída ---\n');
fprintf('dVo alvo total   = %8.3f V  (%.1f%% de Vo_ref)\n', dVo_alvo, dVo_pct*100);
fprintf('  contrib. ESR   = %8.3f V  (Resr = %.0f mOhm)\n', dVo_ESR, Resr_Co*1e3);
fprintf('  orçamento p/ C = %8.3f V\n', dVo_C_budget);
fprintf('Co (calculado)   = %8.1f uF\n', Co*1e6);

fprintf('\n--- Semicondutores do buck ---\n');
fprintf('Chave  (MOSFET) : V_bloqueio >= %.0f V, I_rms = %.2f A\n', Vsw_block, Isw_rms);
fprintf('Diodo roda-livre: V_bloqueio >= %.0f V, I_avg = %.2f A, I_rms = %.2f A\n', ...
        Vdiode_block, Idiode_avg, Idiode_rms);
fprintf('=======================================================================\n\n');

%% ================= 5. SIMULAÇÃO NO TEMPO (VERIFICAÇÃO DO PROJETO) ======
% Modelo comportamental simplificado:
%  - Ponte + Cbulk: ODE de carga/descarga com resistência série (Rline)
%    limitando o pico de corrente de carga do capacitor.
%  - Buck: modelo chaveado ideal em CCM, com duty-cycle feedforward
%    D(t) = Vo_ref / Vbulk(t) (rejeita o ripple de 2*f_linha do barramento).
%  - Saída: capacitor Co + ESR, carga resistiva equivalente a Io_max.

Rline   = 0.3;                 % ohm - impedância série equivalente da fonte CA (AJUSTAR)
Dmax_fisico = 0.92;            % limite físico de duty cycle do PWM

Ts = 1/fsw;
dt = Ts/40;                    % 40 amostras por período de chaveamento
n_ciclos_linha = 4;
t_end = n_ciclos_linha/f_linha;
t  = 0:dt:t_end;
N  = length(t);

vbulk = zeros(1,N);  vbulk(1) = Vrect_pk*0.95;
iL    = zeros(1,N);  iL(1)    = Io_max;
vCo   = zeros(1,N);  vCo(1)   = Vo_ref;
vo    = zeros(1,N);  vo(1)    = Vo_ref;
duty_hist = zeros(1,N);

R_load = Vo_ref/Io_max;        % carga resistiva equivalente

D_now = D_worst;

for kk = 1:N-1

    tt = t(kk);

    % --- Retificador ---
    vs    = Vac_pk*sin(2*pi*f_linha*tt);
    vrect = max(abs(vs) - 2*Vd_diode, 0);

    % --- Atualiza duty cycle no início de cada período de chaveamento ---
    if mod(tt, Ts) < dt
        D_now = min(Dmax_fisico, Vo_ref/max(vbulk(kk), Vo_ref));
    end
    duty_hist(kk) = D_now;

    fase = mod(tt, Ts)/Ts;
    chave_on = fase < D_now;

    % --- Corrente de entrada do buck (vista pelo barramento) ---
    i_in = chave_on*iL(kk);

    % --- Capacitor de barramento (ponte + Cbulk) ---
    if vrect > vbulk(kk)
        icarga = (vrect - vbulk(kk))/Rline;
    else
        icarga = 0;
    end
    dvbulk = (icarga - i_in)/Cbulk*dt;
    vbulk(kk+1) = max(vbulk(kk) + dvbulk, 0);

    % --- Indutor do buck ---
    if chave_on
        vL = vbulk(kk) - vo(kk);
    else
        vL = -vo(kk);
    end
    diL = vL/L*dt;
    iL(kk+1) = max(iL(kk) + diL, 0);   % satura em 0 (aproximação de DCM)

    % --- Capacitor de saída + ESR ---
    io = vo(kk)/R_load;
    dvCo = (iL(kk) - io)/Co*dt;
    vCo(kk+1) = vCo(kk) + dvCo;

    vo(kk+1) = vCo(kk+1) + iL(kk+1)*Resr_Co;

end
duty_hist(N) = D_now;

%% ================= 6. GRÁFICOS DE VERIFICAÇÃO ===========================
figure('Name','Verificação do dimensionamento','Color','w');

subplot(3,1,1);
plot(t*1e3, vbulk, 'b', 'LineWidth', 1.2);
xlabel('tempo (ms)'); ylabel('V_{bulk} (V)');
title('Tensão no barramento CC (após ponte + C_{bulk})');
grid on;

subplot(3,1,2);
plot(t*1e3, iL, 'r', 'LineWidth', 1);
xlabel('tempo (ms)'); ylabel('i_L (A)');
title(sprintf('Corrente no indutor do buck (zoom no ripple: veja últimos %.0f us)', 5*Ts*1e6));
grid on;

subplot(3,1,3);
plot(t*1e3, vo, 'k', 'LineWidth', 1);
xlabel('tempo (ms)'); ylabel('V_o (V)');
title('Tensão de saída regulada');
grid on;

% --- Zoom no ripple de alta frequência (últimos períodos de chaveamento) ---
figure('Name','Zoom no ripple de chaveamento','Color','w');
janela = t > (t_end - 5*Ts);

subplot(2,1,1);
plot(t(janela)*1e6, iL(janela), 'r-o', 'MarkerSize',3, 'LineWidth', 1);
xlabel('tempo (us)'); ylabel('i_L (A)');
title(sprintf('Ripple de corrente no indutor (projeto: \\Delta i_L = %.2f A)', dIL));
grid on;

subplot(2,1,2);
plot(t(janela)*1e6, vo(janela), 'k-o', 'MarkerSize',3, 'LineWidth', 1);
xlabel('tempo (us)'); ylabel('V_o (V)');
title(sprintf('Ripple de tensão de saída (projeto: \\Delta V_o = %.3f V)', dVo_alvo));
grid on;

%% ================= 7. CONFERÊNCIA NUMÉRICA DO RIPPLE SIMULADO ==========
janela_regime = t > (t_end - 1/f_linha);   % último ciclo de linha, já em regime

dVbulk_sim = max(vbulk(janela_regime)) - min(vbulk(janela_regime));
dIL_sim    = max(iL(janela_regime))    - min(iL(janela_regime));
dVo_sim    = max(vo(janela_regime))    - min(vo(janela_regime));

fprintf('--- Conferência: projeto (analítico) x simulação ---\n');
fprintf('dVbulk : projeto = %.2f V   | simulado = %.2f V\n', dVbulk, dVbulk_sim);
fprintf('dIL    : projeto = %.2f A   | simulado = %.2f A\n', dIL, dIL_sim);
fprintf('dVo    : projeto = %.3f V   | simulado = %.3f V\n', dVo_alvo, dVo_sim);
fprintf('=======================================================================\n');