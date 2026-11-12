%% d02_malha_fechada  DeePC e SPC em malha fechada (simulacao) x PI e FCS
%  Controladores construidos so com os dados reais da PRBS (etapa 02). Planta simulada: carga da
%  bancada (25,3 ohm; 9,8 mH), PWM de 20 kHz com atraso de 2 amostras, ruido e ADC, |v| <= 9 V.
P = parametros();  [u, y] = le_prbs(P);  N = P.N;  NP = 3;
Tini = 2;  Nh = 10;  q = 1;  r = 1e-2;
warning('off', 'MATLAB:nearlySingularMatrix');

% 1. regularizacao do DeePC (lambda_g): pouco -> usa o ruido; muito -> lento
Sp = preditor_spc(u, y, Tini, Nh, 0);  Cs = ganho_mpc(Sp.F, Sp.Ku, Nh, 2, 2, q, r);  Cs.tipo = 'mpc';  Cs.Tini = Tini;
ms = metricas(simula_dq(Cs, P, periodos = NP), P);
lgs = [1e-2 3e-2 0.1 0.3 1 3 10 30 100 300 1000];  M1 = zeros(numel(lgs), 3);
fprintf('lambda_g | subida [ms] | rms [mA] | erro medio d [mA]\n');
for j = 1:numel(lgs)
    D = ganho_deepc(u, y, Tini, Nh, q, r, lgs(j), 1e6);  D.tipo = 'mpc';  D.Tini = Tini;
    m = metricas(simula_dq(D, P, periodos = NP), P);
    M1(j, :) = [m.subida, m.rms, abs(m.erro(1))];
    fprintf('  %7.2g | %5.2f | %6.1f | %+6.1f\n', lgs(j), m.subida, m.rms, m.erro(1));
end
fprintf('SPC (mesmos pesos): subida %.2f ms, rms %.1f mA\n', ms.subida, ms.rms);
f = figure('Position', [0 0 1750 600]);  tiledlayout(1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile;  loglog(lgs, M1(:, 3), 'o-', 'Color', P.cor.azul, 'MarkerSize', 9, 'MarkerFaceColor', 'w');  hold on;
xregion(1e-2, 0.2, 'FaceColor', P.cor.verm, 'FaceAlpha', 0.08);
xlabel('\lambda_g');  ylabel('|erro médio em i_d| [mA]');  title('pouca regularização: falha');
text(0.012, 50, {'o controle "usa o ruído"', 'e não segue a referência'}, 'FontSize', 16, 'Color', P.cor.verm);
nexttile;  semilogx(lgs, M1(:, 1), 'o-', 'Color', P.cor.azul, 'MarkerSize', 9, 'MarkerFaceColor', 'w');  hold on;
yline(ms.subida, ':', 'SPC', 'Color', P.cor.verde, 'LineWidth', 2.4, 'FontSize', 15);  ylim([0 3]);  xlim([0.2 1000]);
xlabel('\lambda_g');  ylabel('subida 10–90 % [ms]');  title('muita regularização: lento');
nexttile;  semilogx(lgs, M1(:, 2), 'o-', 'Color', P.cor.azul, 'MarkerSize', 9, 'MarkerFaceColor', 'w');  hold on;
yline(ms.rms, ':', 'SPC', 'Color', P.cor.verde, 'LineWidth', 2.4, 'FontSize', 15);  ylim([0 15]);  xlim([0.2 1000]);
xlabel('\lambda_g');  ylabel('desvio rms em regime [mA]');  title('na faixa boa: igual ao SPC');
salva(f, P, 'd02_regularizacao.png');

% 2. comparacao: PI (500 Hz), FCS, DeePC/SPC e DeePC com previa da referencia
Cpi = P.pi;
Spi = simula_dq(Cpi, P, periodos = NP);
D = ganho_deepc(u, y, Tini, Nh, q, r, 3, 1e6);  D.tipo = 'mpc';  D.Tini = Tini;
Sd = simula_dq(D, P, periodos = NP);
Dp = D;  Dp.previa = true;  Sdp = simula_dq(Dp, P, periodos = NP);
F = fcs_referencia(P, NP);
casos = {'PI 500 Hz', Spi; 'FCS-MPC', F; 'DeePC', Sd; 'DeePC + prévia', Sdp};
fprintf('controle | subida [ms] | t50 [ms] | sobressinal | erro medio d/q | rms [mA] | interf. [mA] | |v| max\n');
tab = zeros(4, 6);
for j = 1:4
    X = casos{j, 2};  m = metricas(X, P);
    z = (X.iv(1, (NP-1)*N + (201:500)) - 0.15)/0.10;  t50 = (find(z >= 0.5, 1) - 1)*P.Ts*1e3;
    tab(j, :) = [m.subida, t50, m.sobre, m.rms, m.interf, m.vmax];
    fprintf('  %-15s %5.2f | %5.2f | %3.0f %% | %+5.1f / %+5.1f | %5.1f | %5.1f | %5.2f\n', casos{j, 1}, m.subida, t50, m.sobre, m.erro, m.rms, m.interf, m.vmax);
end
fprintf('FCS: chaveamento medio %.0f Hz (PI e DeePC: 20 kHz fixos)\n', F.fsw);
save(fullfile(P.res, 'd02.mat'), 'tab', 'M1', 'lgs');

% figura: degraus (corrente verdadeira, ultimo periodo)
k0 = (NP-1)*N;  t = (0:N-1)*P.Ts*1e3;  cores = {P.cor.cinza, P.cor.laranja, P.cor.azul, P.cor.verde};
estilos = {'--', '-', '-', '-'};  ab = 'dq';
f = figure('Position', [0 0 1700 760]);  tiledlayout(2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
for e = 1:2
    nexttile;  hold on;
    for j = [2 1 3 4]
        plot(t, 1e3*casos{j, 2}.iv(e, k0+1:k0+N), estilos{j}, 'Color', cores{j}, 'LineWidth', 1.2 + 0.6*(j > 2));
    end
    stairs(t, 1e3*Sd.ref(e, k0+1:k0+N), ':', 'Color', 'k', 'LineWidth', 1.8);
    ylabel(sprintf('i_%s [mA]', ab(e)));  xlim([0 102]);
    if e == 1, legend({'FCS-MPC', 'PI 500 Hz', 'DeePC', 'DeePC + prévia', 'referência'}, 'Location', 'northoutside', 'NumColumns', 5); end
end
xlabel('tempo [ms]');
for e = 1:2
    nexttile;  hold on;  kk = (195:260);  tt = (kk - 201)*P.Ts*1e3;
    if e == 2, kk = kk + 500; end
    for j = [2 1 3 4]
        plot(tt, 1e3*casos{j, 2}.iv(e, k0+kk), estilos{j}, 'Color', cores{j}, 'LineWidth', 1.6 + 0.8*(j > 2));
    end
    stairs(tt, 1e3*Sd.ref(e, k0+kk), ':', 'Color', 'k', 'LineWidth', 1.8);
    ylabel(sprintf('i_%s [mA]', ab(e)));  title(sprintf('zoom no degrau de i_%s', ab(e)));
end
xlabel('tempo desde o degrau [ms]');
salva(f, P, 'd02_comparacao.png');

% figura: tensoes aplicadas e resumo (t50 e desvio rms)
f = figure('Position', [0 0 1750 560]);  tiledlayout(1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
kk = 185:280;  tt = (kk - 201)*P.Ts*1e3;
nexttile;  plot(tt, movmean(F.vdq(1, k0+kk), 9), 'Color', P.cor.laranja, 'LineWidth', 1.6);  hold on;
plot(tt, Spi.u(1, k0+kk), '--', 'Color', P.cor.cinza, 'LineWidth', 2.2);  plot(tt, Sd.u(1, k0+kk), 'Color', P.cor.azul, 'LineWidth', 2.6);
plot(tt, Sdp.u(1, k0+kk), 'Color', P.cor.verde, 'LineWidth', 2.6);
ylabel('v_d [V]');  xlabel('tempo desde o degrau [ms]');  title('tensão no degrau de i_d');
legend({'FCS (média de 9 vetores)', 'PI 500 Hz', 'DeePC', 'DeePC + prévia'}, 'Location', 'southeast', 'FontSize', 15);
nomes = categorical({'PI 500 Hz', 'FCS-MPC', 'DeePC', 'DeePC + prévia'}, {'PI 500 Hz', 'FCS-MPC', 'DeePC', 'DeePC + prévia'});
cb = [P.cor.cinza; P.cor.laranja; P.cor.azul; P.cor.verde];
nexttile;  b = bar(nomes, tab(:, 2), 'FaceColor', 'flat');  b.CData = cb;  ylabel('t_{50} [ms]');  title('atraso até meio degrau');
nexttile;  b = bar(nomes, tab(:, 4), 'FaceColor', 'flat');  b.CData = cb;  ylabel('desvio rms [mA]');  title('ondulação em regime');
salva(f, P, 'd02_tensoes.png');
