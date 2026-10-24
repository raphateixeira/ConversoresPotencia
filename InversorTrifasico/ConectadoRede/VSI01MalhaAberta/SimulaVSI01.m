% SimulaVSI01 - simula a malha aberta do VSI01 e compara a corrente com a teoria.
%
%   MalhaAbertaSimples : PWM senoidal ideal, sem tempo morto nem atraso
%   MalhaAberta        : fiel ao firmware (ePWM, tempo morto, atraso de 1,5 Ts, ADC)
%
% Análise detalhada do modelo do firmware (tempo morto, ADC): AnaliseFirmwareVSI01.

% Parâmetros: sempre Comum/Parametros.m (começa com clear, por isso vem antes de tudo)
run(fullfile(fileparts(mfilename('fullpath')), '..', 'IniciarProjeto.m'))
run(fullfile(fileparts(mfilename('fullpath')), '..', 'Comum', 'Parametros.m'))

modelo = 'MalhaAbertaSimples';      % ou 'MalhaAberta'

pasta = fileparts(mfilename('fullpath'));
addpath(pasta);

Bancada.tRampa = 20e-3;             % só no MalhaAberta: rampa curta (L/R = 0,5 ms)

%% Simulação
out = sim(modelo);
[t, i] = sinal(out.iabc);
[~, v] = sinal(out.vabcn);

%% Regime: últimos 3 ciclos (o MalhaAbertaSimples simula só 6, a partir do repouso)
nc = 3;
w = 2*pi*Bancada.f;
N = round(nc/(Bancada.f*Bancada.Tlog));
k = numel(t)-N+1 : numel(t);
I1 = 2/N * sum(i(k,:) .* exp(-1j*w*t(k)));          % fasores da fundamental, fases a, b, c
F  = abs(fft(i(k,1))) * 2/N;                        % espectro de ia (harmônica h no bin nc*h+1)
THD = 100 * sqrt(sum(F(nc*(2:50)+1).^2)) / F(nc+1);

%% Teoria: carga RL + Ron, sem tempo morto
Z = Bancada.RLf + Bancada.Rc + Bancada.Ron + 1j*w*Bancada.Lf;
Iteo = Bancada.Vp / Z;
if strcmp(modelo, 'MalhaAberta')
    Iteo = Iteo * exp(-1.5j*w*Bancada.Ts);          % atraso da ISR + sombra do CMPA
end

resultado = table(abs(I1(1)), abs(Iteo), rad2deg(angle(I1(1))) + 90, rad2deg(angle(Iteo)), THD, ...
    'VariableNames', {'Ia1 [A]', 'teoria [A]', 'fase [°]', 'fase teoria [°]', 'THD ia [%]'});
fprintf('\n%s (fase em relação a va* = Vp sen(wt); teoria sem tempo morto)\n', modelo);
disp(resultado)
dmin = 0.5 - Bancada.Vp/Bancada.Vcc;  dmax = 0.5 + Bancada.Vp/Bancada.Vcc;
fprintf('Limites: d em [%.2f, %.2f] (permitido [%.2f, %.2f]); pico de corrente %.2f A (placa: %g A)\n\n', ...
    dmin, dmax, Bancada.dMin, Bancada.dMax, max(abs(i(k,1))), Bancada.Imax);

%% Figura
cor = [0.165 0.471 0.839; 0.922 0.408 0.204; 0.106 0.686 0.478];   % fases a, b, c
fig = figure('Position', [100 100 900 600]);
tiledlayout(2, 1, 'TileSpacing', 'compact');

nexttile;
s = t >= t(end) - 2/Bancada.f;                      % dois ciclos
for f = 1:3
    plot(1e3*t(s), i(s,f), 'Color', cor(f,:)); hold on;
end
grid on; ylabel('corrente [A]'); legend('i_a', 'i_b', 'i_c', 'Location', 'eastoutside');
title(sprintf('%s: regime', modelo));

nexttile;
s = t >= t(end) - 1/Bancada.f;                      % um ciclo
vmed = movmean(v(:,1), round(Bancada.Ts/Bancada.Tlog));    % média em um período de PWM
plot(1e3*t(s), v(s,1), 'Color', [cor(1,:) 0.25]); hold on;
plot(1e3*t(s), vmed(s), 'Color', cor(2,:), 'LineWidth', 1.5);
grid on; xlabel('t [ms]'); ylabel('v_{an} [V]');
legend('instantânea', 'média no período de PWM', 'Location', 'eastoutside');

exportgraphics(fig, fullfile(pasta, 'figuras', [modelo '.png']), 'Resolution', 150);

function [t, x] = sinal(ts)
% Tempo e dados de um timeseries gravado pelo To Workspace, com uma coluna por fase
    t = ts.Time(:);
    x = squeeze(ts.Data);
    if size(x, 1) ~= numel(t), x = x.'; end
end
