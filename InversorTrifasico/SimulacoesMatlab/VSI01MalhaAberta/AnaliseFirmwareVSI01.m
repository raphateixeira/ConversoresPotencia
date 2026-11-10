% AnaliseFirmwareVSI01 - análise detalhada de MalhaAberta.slx (fiel ao firmware): três cenários de
% tempo morto comparados com a teoria, medição pelo ADC da placa.
%
%   nominal : tMorto de Parametros.m (100 ns)
%   500 ns  : valor dos exemplos da TI (e do main.c atual)
%   ideal   : sem tempo morto (referência)
%
% A rampa é encurtada para 20 ms (no firmware é 1 s): a constante de tempo da carga,
% L/R = 0,5 ms, é muito menor, então o regime depois da rampa é o mesmo.
% Gera as figuras em figuras/ e os números da página da etapa. Para uma rodada simples, use SimulaVSI01.
% Uso: AnaliseFirmwareVSI01 (de dentro desta pasta) ou run VSI01MalhaAberta/AnaliseFirmwareVSI01.

% Parâmetros: sempre o arquivo único Comum/Parametros.m, localizado a partir desta pasta.
% Parametros começa com clear, por isso vem antes de qualquer variável.
run(fullfile(fileparts(mfilename('fullpath')), '..', 'IniciarProjeto.m'))   % Comum/ no path, caches em cache/
run(fullfile(fileparts(mfilename('fullpath')), '..', 'Comum', 'Parametros.m'))
pasta = fileparts(mfilename('fullpath'));
addpath(pasta);
figdir = fullfile(pasta, 'figuras');
if ~exist(figdir, 'dir'), mkdir(figdir); end

Bancada.tRampa = 20e-3;
cenarios = {'nominal', Bancada.tMorto; '500 ns', 0.5e-6; 'ideal', 0};
cor = [0.165 0.471 0.839; 0.922 0.408 0.204; 0.106 0.686 0.478];   % fases a, b, c / cenários 1, 2, 3

R = Bancada.RLf + Bancada.Rc;  L = Bancada.Lf;  w = 2*pi*Bancada.f;
Z = R + Bancada.Ron + 1j*w*L;                % Ron: uma chave em condução por fase
atraso = 1.5*w*Bancada.Ts;                    % ISR -> sombra (1 Ts) + centro do período (Ts/2)

res = struct();
for c = 1:size(cenarios, 1)
    B = Bancada;  B.tMorto = cenarios{c, 2};
    in = Simulink.SimulationInput('MalhaAberta');
    in = in.setVariable('Bancada', B);
    tic;  out = sim(in);  tsim = toc;
    r = analisa(out, B, Z, atraso);
    r.nome = cenarios{c, 1};  r.tsim = tsim;  r.out = out;
    res(c).r = r; %#ok<SAGROW>
    fprintf('cenário %-9s simulado em %5.1f s\n', r.nome, tsim);
end

%% Métricas
fprintf('\n=== VSI01: Vcc = %g V, Vp = %g V, fPWM = %g kHz, carga R = %.2f ohm, L = %.1f mH ===\n', ...
    Bancada.Vcc, Bancada.Vp, Bancada.fPWM/1e3, R, 1e3*L);
fprintf('índice de modulação m = 2Vp/Vcc = %.3f (linear até 1; até 1,155 com injeção de seq. zero)\n', 2*Bancada.Vp/Bancada.Vcc);
Iid = Bancada.Vp/abs(Z);
fprintf('teoria sem tempo morto: |I1| = %.4f A, fase em relação a va* = %.2f° (carga %.2f° + atraso de 1,5 Ts = %.2f°)\n', ...
    Iid, rad2deg(-angle(Z) - atraso), rad2deg(-angle(Z)), rad2deg(atraso));
fprintf('(tensões: médias exatas por período de PWM; fases em relação à referência va* = Vp sen(wt) da ISR)\n');
fprintf('\n%-9s %8s %8s %8s %8s %8s %8s %8s %8s %8s %8s\n', 'cenário', '|Van1|', 'teoria', '|Ia1|', 'teoria', ...
    'fase Ia', 'THD50 i', 'THDtot i', 'h5 Van', 'h7 Van', 'ripple');
fprintf('%-9s %8s %8s %8s %8s %8s %8s %8s %8s %8s %8s\n', '', '[V]', '[V]', '[A]', '[A]', '[°]', '[%]', '[%]', '[V]', '[V]', '[App]');
for c = 1:numel(res)
    r = res(c).r;
    fprintf('%-9s %8.4f %8.4f %8.4f %8.4f %8.2f %8.3f %8.3f %8.4f %8.4f %8.3f\n', r.nome, abs(r.Van1), abs(r.Van1teo), ...
        abs(r.Ia1), abs(r.Ia1teo), rad2deg(angle(r.Ia1)) + 90, r.THD50, r.THDtot, r.h5, r.h7, r.ripple);
end
r = res(1).r;
fprintf('\nTempo morto (nominal): |Van1| cai %.3f V em relação ao ideal (%.1f%%); |Ia1| cai %.2f%% (teoria %.2f%%)\n', ...
    abs(res(3).r.Van1) - abs(r.Van1), 100*(1 - abs(r.Van1)/abs(res(3).r.Van1)), ...
    100*(1 - abs(r.Ia1)/abs(res(3).r.Ia1)), 100*(1 - abs(r.Ia1teo)/abs(res(3).r.Ia1teo)));
fprintf('   erro de tensão por perna, 1a harmônica: (4/pi)*fPWM*tm*Vcc = %.3f V, em fase com a corrente\n', r.Vdt1);
fprintf('   equivale a uma resistência série de %.3f ohm por fase nesta corrente\n', r.Vdt1/abs(r.Ia1));
fprintf('Pico de corrente: %.2f A (placa: %g A nominal, OCP em %g A)\n', r.ipico, Bancada.Imax, Bancada.Iocp);
fprintf('Potência na carga: %.1f W (%.1f W por resistor)\n', 1.5*Bancada.Rc*abs(r.Ia1)^2, 0.5*Bancada.Rc*abs(r.Ia1)^2);
fprintf('Tensão de modo comum vnO: %.2f V rms\n', r.vnOrms);
fprintf('\nADC (amostra em CTR = 0):\n');
fprintf('   corrente: %.1f mA/LSB, |Ia1| = %.0f LSB; erro amostra-ADC vs corrente instantânea: média %+.1f mA, máx %.1f mA\n', ...
    1e3*r.lsbI, abs(r.Ia1)/r.lsbI, 1e3*r.erroIadcMed, 1e3*r.erroIadcMax);
fprintf('   amostra em CTR = 0 vs média da corrente no período: erro máx %.1f mA (ripple %.0f mA pp)\n', ...
    1e3*r.erroMediaMax, 1e3*r.ripple);
fprintf('   tensão VA: %.1f mV/LSB; fundamental medida/real = %.4f, atraso %.2f° (RC de %.0f Hz: %.2f°)\n', ...
    1e3*r.lsbV, abs(r.VAadc1)/abs(r.VaO1), rad2deg(angle(r.VaO1) - angle(r.VAadc1)), Bancada.fpTensao, ...
    rad2deg(atan(Bancada.f/Bancada.fpTensao)));

%% Figuras
set(groot, 'defaultAxesFontSize', 10, 'defaultLineLineWidth', 1);
out = res(1).r.out;
[t, i] = dados(out.iabc);

f1 = figure('Visible','off', 'Position',[0 0 900 420]);
for k = 1:3, plot(1e3*t, i(:,k), 'Color', cor(k,:)); hold on; end
grid on; xlabel('t [ms]'); ylabel('corrente de fase [A]');
legend('i_a','i_b','i_c', 'Location','southwest'); title('Partida em rampa e regime (cenário nominal)');
exportgraphics(f1, fullfile(figdir, 'correntes.png'), 'Resolution', 150);

% janela a passo cheio: 2 períodos de PWM no fim da simulação
[tj, J] = dados(out.log_janela);
sel = tj >= tj(end) - 2*Bancada.Ts;
tj = 1e6*(tj(sel) - tj(find(sel,1)));  J = J(sel,:);
f2 = figure('Visible','off', 'Position',[0 0 900 700]);
tl = tiledlayout(4,1, 'TileSpacing','compact');
nexttile; plot(tj, J(:,7), 'Color', cor(1,:)); grid on; ylabel('TBCTR'); title('Dois períodos de PWM (cenário nominal)');
nexttile; stairs(tj, J(:,1) + 1.2, 'Color', cor(1,:)); hold on; stairs(tj, J(:,2), 'Color', cor(2,:));
grid on; yticks([0 1 1.2 2.2]); yticklabels({'0','1','0','1'}); ylabel('portas fase a');
legend('A sup (EPWM1A)','A inf (EPWM1B)', 'Location','eastoutside');
nexttile; plot(tj, J(:,11), 'Color', cor(1,:)); hold on; plot(tj, J(:,14), 'Color', cor(2,:));
grid on; ylabel('tensão [V]'); legend('v_{aO}','v_{an}', 'Location','eastoutside');
nexttile; plot(tj, J(:,8), 'Color', cor(1,:)); grid on; ylabel('i_a [A]'); xlabel('t [\mus]');
exportgraphics(f2, fullfile(figdir, 'pwm.png'), 'Resolution', 150);

f3 = figure('Visible','off', 'Position',[0 0 900 420]);
r = res(1).r;
sel = r.fH <= 100e3 & r.Iia > 1e-5;
stem(r.fH(sel)/1e3, r.Iia(sel), 'Color', cor(1,:), 'Marker','none', 'BaseValue', 1e-5);
set(gca, 'YScale','log'); grid on; xlim([0 100]); ylim([1e-5 5]); xlabel('frequência [kHz]'); ylabel('amplitude de i_a [A]');
title('Espectro de i_a em regime (cenário nominal, 6 ciclos)');
exportgraphics(f3, fullfile(figdir, 'espectro.png'), 'Resolution', 150);

f4 = figure('Visible','off', 'Position',[0 0 900 420]);
[t0, i0] = dados(res(3).r.out.iabc);
s0 = t0 >= t0(end) - 1/Bancada.f;
for c = 1:2
    [t, i] = dados(res(c).r.out.iabc);
    plot(1e3*(t(s0) - t0(find(s0,1))), 1e3*(i(s0,1) - i0(s0,1)), 'Color', cor(c,:)); hold on;
end
[~, ii] = dados(res(3).r.out.iabc);
plot(1e3*(t0(s0) - t0(find(s0,1))), 100*ii(s0,1)/max(ii(s0,1)), ':', 'Color', [0.5 0.5 0.5]);
grid on; xlabel('t [ms]'); ylabel('i_a - i_a^{ideal} [mA]');
legend(sprintf('nominal (%.0f ns)', 1e9*Bancada.tMorto), '500 ns', 'i_a ideal (escala arbitrária)', 'Location','southwest');
title('Efeito do tempo morto em i_a: diferença para o caso sem tempo morto');
exportgraphics(f4, fullfile(figdir, 'tempo_morto.png'), 'Resolution', 150);

f5 = figure('Visible','off', 'Position',[0 0 900 500]);
r = res(1).r;
tiledlayout(2,1, 'TileSpacing','compact');
nexttile; plot(1e3*r.tA, 1e3*(r.iAdc - r.iReal), '.', 'Color', cor(1,:), 'MarkerSize', 6);
grid on; ylabel('erro de i_a [mA]'); title('Erro da medição pela placa (cenário nominal, amostra em CTR = 0)');
subtitle(sprintf('corrente: ADC - valor instantâneo (1 LSB = %.1f mA)', 1e3*r.lsbI));
nexttile; plot(1e3*r.tA, r.vaNadc - r.vaNreal, '.', 'Color', cor(1,:), 'MarkerSize', 6);
grid on; ylabel('erro de V_A [V]'); xlabel('t [ms]');
subtitle(sprintf('tensão VA: ADC (RC de %.0f Hz) - média no período (1 LSB = %.1f mV)', Bancada.fpTensao, 1e3*r.lsbV));
exportgraphics(f5, fullfile(figdir, 'adc.png'), 'Resolution', 150);
fprintf('\nFiguras em %s\n', figdir);

%% Funções
function [t, x] = dados(ts)
    t = ts.Time(:);
    x = squeeze(ts.Data);
    if size(x,1) ~= numel(t), x = x.'; end
end

function r = analisa(out, B, Z, atraso)
    w = 2*pi*B.f;  N = round(6/B.f/B.Tlog);          % 6 ciclos exatos
    [t, i] = dados(out.iabc);   i = i(end-N:end-1,:);   t = t(end-N:end-1);
    [~, vO] = dados(out.vabcO);  vO = vO(end-N:end-1,:);
    % tensões: média exata em cada período de PWM (integral a Tsim gravada a cada Ts); amostrar o PWM
    % a Tlog, síncrono com a portadora, quantiza as larguras de pulso e distorce a fundamental
    [tI, Iv] = dados(out.log_intv);
    vm = diff(Iv)/B.Ts;  tm = tI(1:end-1) + B.Ts/2;  M = round(6/B.f/B.Ts);
    vm = vm(end-M+1:end,:);  tm = tm(end-M+1:end);
    fasorM = @(x, h) 2/M*sum(x.*exp(-1j*h*w*tm));
    [~, vn] = dados(out.log_vnO);  vn = vn(end-N:end-1);
    fasor = @(x, h) 2/N*sum(x.*exp(-1j*h*w*t));
    r.Ia1 = fasor(i(:,1), 1);  r.Van1 = fasorM(vm(:,4), 1);
    % teoria: tensão média aplicada = Vp atrasada de 1,5 Ts; tempo morto = onda quadrada em fase com i
    Vref = B.Vp*exp(-1j*atraso);
    r.Vdt1 = 4/pi*B.fPWM*B.tMorto*B.Vcc;         % Vsd não entra: o modelo não o representa
    I = Vref/Z;
    for k = 1:50, I = (Vref - r.Vdt1*exp(1j*angle(I)))/Z; end
    r.Ia1teo = I;  r.Van1teo = Vref - r.Vdt1*exp(1j*angle(I)) - B.Ron*I;   % van inclui a queda na chave
    % espectro (resolução de 10 Hz; harmônica h no bin 6h)
    F = fft(i(:,1))/N*2;  nb = floor(N/2);
    r.fH = (0:nb-1)'/(N*B.Tlog);  r.Iia = abs(F(1:nb));
    h = 2:50;
    r.THD50  = 100*sqrt(sum(r.Iia(6*h+1).^2))/r.Iia(7);
    r.THDtot = 100*sqrt(sum(r.Iia(2:end).^2) - r.Iia(7)^2)/r.Iia(7);
    r.h5 = abs(fasorM(vm(:,4), 5));  r.h7 = abs(fasorM(vm(:,4), 7));
    nT = round(B.Ts/B.Tlog);
    imed = movmean(i(:,1), nT);
    r.ripple = max(i(:,1) - imed) - min(i(:,1) - imed);
    r.ipico = max(abs(i(:)));
    r.vnOrms = rms(vn);
    % ADC: códigos amostrados em kTs
    [tA, cod] = dados(out.log_adc);
    s = tA >= t(1) & tA <= t(end);  tA = tA(s);  cod = cod(s,:);
    r.lsbI = B.Vadc/2^B.nbits/(B.Gina*B.Rsh);  r.lsbV = B.VfsTensao/2^B.nbits;
    iAdc = (B.Vmeio - cod(:,1)*B.Vadc/2^B.nbits)/(B.Gina*B.Rsh);
    [tl, il] = dados(out.iabc);
    iReal = interp1(tl, il(:,1), tA, 'previous');
    r.erroIadcMed = mean(iAdc - iReal);  r.erroIadcMax = max(abs(iAdc - iReal));
    r.erroMediaMax = max(abs(iReal - interp1(t, movmean(i(:,1), nT), tA, 'nearest', 'extrap')));   % média no período centrado em kTs
    r.tA = tA - tA(1);  r.iReal = iReal;  r.iAdc = iAdc;
    vaNadc = cod(:,4)*r.lsbV;
    vaNmed = interp1(t, movmean(vO(:,1), nT), tA, 'nearest', 'extrap') + B.Vcc/2;
    r.vaNadc = vaNadc;  r.vaNreal = vaNmed;
    r.VAadc1 = 2/numel(tA)*sum((vaNadc - mean(vaNadc)).*exp(-1j*w*tA));
    r.VaO1 = fasorM(vm(:,1), 1);
end
