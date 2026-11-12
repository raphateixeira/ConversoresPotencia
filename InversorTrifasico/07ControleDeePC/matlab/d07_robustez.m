%% d07_robustez  O que acontece quando a bancada nao e mais a dos dados (simulacao no tempo)
%  (a) carga diferente da que gerou os dados, e o que muda ao refazer o ensaio de PRBS;
%  (b) queda de Vdc e perturbacao de tensao; (c) forma incremental x absoluta; (d) outra frequencia.
P = parametros();  [u, y] = le_prbs(P);  N = P.N;  warning('off', 'all');
Cd = ganhos('deepc', u, y, P);  Cm = ganhos('oraculo', u, y, P);  Cpi = P.pi;

% (a) cargas
cargas = [P.R P.L; 35 14e-3; 15 5e-3; 25.3 20e-3];  nc = size(cargas, 1);
rot = {'nominal: 25,3 Ω; 9,8 mH', '35 Ω; 14 mH', '15 Ω; 5 mH', '25,3 Ω; 20 mH'};
fprintf('carga | controle | subida [ms] | sobressinal | rms regime [mA] | J [mA] | rho\n');
Ja = zeros(nc, 4);  f = figure('Position', [0 0 1750 720]);  tiledlayout(2, nc, 'TileSpacing', 'compact', 'Padding', 'compact');
kk = N + (191:280);  tt = (kk - N - 201)*P.Ts*1e3;
for c = 1:nc
    R = cargas(c, 1);  L = cargas(c, 2);
    [un, yn] = gera_dados(P, R = R, L = L);  Cr = ganhos('deepc', un, yn, P);     % ensaio refeito na carga nova
    lista = {Cpi, 'PI 500 Hz', P.cor.cinza, '--'; Cm, 'MPC com o modelo nominal', P.cor.magenta, '--'; ...
             Cd, 'DeePC, dados da carga nominal', P.cor.azul, '-'; Cr, 'DeePC, ensaio refeito nesta carga', P.cor.verde, '-'};
    for j = 1:4
        d = desempenho(lista{j, 1}, P, 'R', R, 'L', L);  Ja(c, j) = d.J;
        rho = malha_linear(lista{j, 1}, P, R = R, L = L, completo = false).rho;
        fprintf('  %-22s | %-32s | %.2f | %3.0f %% | %4.1f | %5.1f | %.3f\n', rot{c}, lista{j, 2}, d.m.subida, d.m.sobre, d.m.rms, d.J, rho);
        Sx = simula_dq(lista{j, 1}, P, periodos = 2, ruido = 0, R = R, L = L);
        nexttile(c);  hold on;  plot(tt, 1e3*Sx.iv(1, kk), lista{j, 4}, 'Color', lista{j, 3}, 'LineWidth', 2.4);
        nexttile(nc + c);  hold on;  plot(tt, 1e3*Sx.iv(2, kk), lista{j, 4}, 'Color', lista{j, 3}, 'LineWidth', 2.4);
    end
    nexttile(c);  stairs(tt, 1e3*Sx.ref(1, kk), 'k:', 'LineWidth', 1.6);  title(rot{c});  ylim([140 275]);  if c == 1, ylabel('i_d [mA]'); end
    nexttile(nc + c);  ylim([-12 12]);  xlabel('tempo desde o degrau [ms]');  if c == 1, ylabel('i_q [mA]'); end
end
lg = legend(nexttile(1), [lista(:, 2); {'referência'}], 'Orientation', 'horizontal', 'FontSize', 15);  lg.Layout.Tile = 'north';
salva(f, P, 'd07_cargas.png');

% (b) queda de Vdc (ganho 1 -> 0,7 em 20 ms; volta em 45 ms) e perturbacao de 1,5 V em d (70-90 ms)
M = 2*N;  al = ones(1, M);  al(N + (400:900)) = 0.7;  dv = zeros(2, M);  dv(1, N + (1400:1800)) = 1.5;
ref = repmat([0.25; 0], 1, M);
lista = {Cpi, 'PI 500 Hz', P.cor.cinza, '--'; Cm, 'MPC com o modelo', P.cor.magenta, '--'; Cd, 'DeePC (dados reais)', P.cor.azul, '-'};
f = figure('Position', [0 0 1750 640]);  tiledlayout(1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
jan = {N + (390:460), N + (1390:1460), N + (1790:1860)};  tit = {'V_{dc} cai 30 %', 'entra 1,5 V de perturbação em d', 'sai a perturbação'};
for q = 1:3
    nexttile;  hold on;
    for j = 1:3
        Sx = simula_dq(lista{j, 1}, P, ref = ref, ruido = 0, alfa = al, dv = dv);
        plot((jan{q} - jan{q}(11))*P.Ts*1e3, 1e3*Sx.iv(1, jan{q}), lista{j, 4}, 'Color', lista{j, 3}, 'LineWidth', 2.6);
        dev = 1e3*(Sx.iv(1, jan{q}) - 0.25);  [pk, ip] = max(abs(dev));
        vol = find(abs(dev) > 0.1*pk, 1, 'last');
        fprintf('%-18s %-34s desvio max %5.1f mA, volta a 10 %% em %.2f ms\n', lista{j, 2}, tit{q}, pk, (vol - 11)*P.Ts*1e3);
    end
    yline(250, 'k:', 'LineWidth', 1.4);  xlabel('tempo desde o evento [ms]');  title(tit{q});  if q == 1, ylabel('i_d [mA]');  legend(lista(:, 2), 'Location', 'southeast', 'FontSize', 15); end
end
salva(f, P, 'd07_perturbacoes.png');

% (c) incremental x absoluta: dados da carga nominal, carga real com R 20 % maior
Ca = ganho_abs(u, y, P.Tini, P.Nh, P.q, P.ru);
f = figure('Position', [0 0 1750 560]);  tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
Rs = [P.R, 1.2*P.R];  tits = {'carga dos dados', 'R 20 % maior que nos dados'};
for c = 1:2
    nexttile;  hold on;  k = N + (150:500);  tt2 = (k - N - 201)*P.Ts*1e3;
    Sa = simula_dq(Ca, P, periodos = 2, ruido = 0, R = Rs(c));  Si = simula_dq(Cd, P, periodos = 2, ruido = 0, R = Rs(c));
    plot(tt2, 1e3*Sa.iv(1, k), '-', 'Color', P.cor.laranja, 'LineWidth', 2.6);  plot(tt2, 1e3*Si.iv(1, k), '-', 'Color', P.cor.azul, 'LineWidth', 2.6);
    stairs(tt2, 1e3*Si.ref(1, k), 'k:', 'LineWidth', 1.6);  xlabel('tempo desde o degrau [ms]');  title(tits{c});  ylim([130 270]);
    if c == 1, ylabel('i_d [mA]');  legend({'preditor em valores absolutos', 'preditor em incrementos (usado)', 'referência'}, 'Location', 'southeast', 'FontSize', 15); end
    fprintf('R x %.1f: erro em regime absoluto %+.1f mA, incremental %+.1f mA\n', Rs(c)/P.R, 1e3*(0.25 - mean(Sa.iv(1, N+(600:1100)))), 1e3*(0.25 - mean(Si.iv(1, N+(600:1100)))));
end
salva(f, P, 'd07_incremental.png');

% (d) outra frequencia fundamental (dados colhidos a 60 Hz)
fs = [0 30 60 120 240 400];  Jf = zeros(numel(fs), 3);  If = Jf;  rf = Jf;
for a = 1:numel(fs)
    for j = 1:3
        d = desempenho(lista{j, 1}, P, 'w', 2*pi*fs(a));  Jf(a, j) = d.J;  If(a, j) = d.m.interf;
        rf(a, j) = malha_linear(lista{j, 1}, P, w = 2*pi*fs(a), completo = false).rho;
    end
end
disp('frequencia [Hz] | J: PI, MPC, DeePC | interferencia d->q [mA]: PI, MPC, DeePC | rho');  disp([fs', Jf, If, rf]);
f = figure('Position', [0 0 1750 560]);  tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
dd = {Jf, If};  yl = {'erro rms de rastreamento [mA]', 'interferência d → q no degrau [mA]'};
for q = 1:2
    nexttile;  b = bar(categorical(string(fs)), dd{q});  for j = 1:3, b(j).FaceColor = lista{j, 3}; end
    xlabel('frequência fundamental na operação [Hz]');  ylabel(yl{q});
    if q == 1, legend(lista(:, 2), 'Location', 'northwest', 'FontSize', 15);  title('dados colhidos a 60 Hz'); end
end
salva(f, P, 'd07_frequencia.png');
save(fullfile(P.res, 'd07.mat'), 'Ja', 'cargas', 'Jf', 'If', 'fs');
