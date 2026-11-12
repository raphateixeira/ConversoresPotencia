%% d08_ruido_dados  Quanto ruido e quantos dados o controle direto aguenta? (Monte Carlo)
%  O ensaio de PRBS e repetido em simulacao com varios ruidos, e cada caminho constroi o seu
%  controle: direto (SPC, SPC causal, DeePC) x indireto (ARX; modelo fisico de 4 parametros).
%  Nota de cada controle: erro rms de rastreamento na malha fechada, relativo ao controle feito
%  com o modelo certo (oraculo). Na malha, sempre o ruido de medida da bancada (8,5 mA).
P = parametros();  [u, y, y1] = le_prbs(P);  warning('off', 'all');  NS = 20;
met = {'spc', 'spcc', 'deepc', 'arx', 'fisico'};
rot = {'SPC (direto)', 'SPC causal (direto)', 'DeePC, λ_g = 3 (direto)', 'ARX → MPC (indireto)', 'modelo físico → MPC (indireto)'};
cor = {P.cor.verde, P.cor.verde, P.cor.azul, P.cor.magenta, P.cor.magenta};  est = {'-s', ':s', '-o', '--^', ':^'};
Jo = desempenho(ganhos('oraculo', u, y, P), P).J;  fprintf('oraculo: J = %.2f mA\n', Jo);
nota = @(C) desempenho(C, P).J;

% 1. ruido nos dados (um periodo de PRBS, 2044 amostras)
sig = [0.5 1 2 4 8.5 16 32]*1e-3;  J1 = nan(numel(sig), numel(met), NS);
lgs = [0.3 1 3 10 30 100 300 1000 3000];  Jl = nan(numel(sig), numel(lgs), NS);
for a = 1:numel(sig), for s = 1:NS
    [ud, yd] = gera_dados(P, ruido = sig(a), media = 1, semente = 100 + s);
    for j = 1:numel(met), J1(a, j, s) = nota(ganhos(met{j}, ud, yd, P)); end
    for l = 1:numel(lgs), Jl(a, l, s) = nota(ganhos('deepc', ud, yd, P, lg = lgs(l))); end
end, end
Ml = 100*(median(Jl, 3, 'omitnan')/Jo - 1);  [melhor, il] = min(Ml, [], 2);
disp('ruido [mA] | melhor lambda_g | piora do DeePC com o melhor lambda_g [%]');  disp([sig'*1e3, lgs(il)', melhor]);
disp('piora mediana do DeePC [%] por lambda_g (colunas) e ruido (linhas):');  disp(round(Ml, 1));
R1 = 100*(J1/Jo - 1);  med1 = median(R1, 3, 'omitnan');  falha1 = mean(isnan(J1), 3);
disp('ruido [mA] | piora mediana sobre o oraculo [%]: spc spcc deepc arx fisico');  disp([sig'*1e3, med1]);
disp('fracao de controles instaveis ou inuteis:');  disp([sig'*1e3, falha1]);
real = [nota(ganhos('spc', u, y, P)), nota(ganhos('deepc', u, y, P)), nota(ganhos('arx', u, y, P)), nota(ganhos('fisico', u, y, P)); ...
        nota(ganhos('spc', u, y1, P)), nota(ganhos('deepc', u, y1, P)), nota(ganhos('arx', u, y1, P)), nota(ganhos('fisico', u, y1, P))];
disp('dados REAIS (linha 1: media 16; linha 2: 1 periodo) | piora sobre o oraculo [%]: spc deepc arx fisico');  disp(100*(real/Jo - 1));

% 2. quantidade de dados (registro comum, primeiras T amostras), ruido de 1 periodo e de media 16
Ts_ = [45 60 100 200 500 1000 2044];  sg2 = [8.5e-3, 8.5e-3/4];  m2 = [1 3 4 5];  J2 = nan(numel(Ts_), numel(m2), 2, NS);
for b = 1:2, for a = 1:numel(Ts_), for s = 1:NS
    [ud, yd] = gera_dados(P, ruido = sg2(b), media = 1, semente = 200 + s);  k = 1:Ts_(a);
    for j = 1:numel(m2)
        try, J2(a, j, b, s) = nota(ganhos(met{m2(j)}, ud(:, k), yd(:, k), P, circular = Ts_(a) == 2044)); catch, end
    end
end, end, end
R2 = 100*(J2/Jo - 1);  med2 = median(R2, 4, 'omitnan');  falha2 = mean(isnan(J2), 4);
disp('T | piora mediana [%] com 8,5 mA: spc deepc arx fisico | com 2,1 mA');  disp([Ts_', med2(:, :, 1), med2(:, :, 2)]);
disp('T | fracao de falhas com 8,5 mA | com 2,1 mA');  disp([Ts_', falha2(:, :, 1), falha2(:, :, 2)]);

% 3. quanto passado (Tini) com ruido: nota na malha fechada
Tis = 2:8;  J3 = nan(numel(Tis), 2, 2);
for a = 1:numel(Tis)
    J3(a, 1, 1) = nota(ganhos('spc', u, y, P, Tini = Tis(a)));    J3(a, 2, 1) = nota(ganhos('deepc', u, y, P, Tini = Tis(a)));
    J3(a, 1, 2) = nota(ganhos('spc', u, y1, P, Tini = Tis(a)));   J3(a, 2, 2) = nota(ganhos('deepc', u, y1, P, Tini = Tis(a)));
end
disp('Tini | J [mA] dados reais media 16: spc deepc | 1 periodo: spc deepc');  disp([Tis', J3(:, :, 1), J3(:, :, 2)]);

% 4. estrutura errada: a planta tem uma amostra a mais de atraso (3 no total)
casos = {'fisico', 2, 'modelo físico (supõe atraso 2)'; 'arx', 2, 'ARX (u(k−1), u(k−2))'; 'spc', 2, 'SPC, T_{ini} = 2'; 'spc', 3, 'SPC, T_{ini} = 3'; 'deepc', 3, 'DeePC, T_{ini} = 3'};
J4 = nan(size(casos, 1), NS);  Jo4 = desempenho(ganhos('oraculo', u, y, P, atraso = 1, Tini = 3), P, 'atraso', 1).J;
for s = 1:NS
    [ud, yd] = gera_dados(P, ruido = 8.5e-3/4, media = 1, semente = 300 + s, atraso = 1);
    for j = 1:size(casos, 1), J4(j, s) = desempenho(ganhos(casos{j, 1}, ud, yd, P, Tini = casos{j, 2}), P, 'atraso', 1).J; end
end
med4 = median(J4, 2, 'omitnan');  falha4 = mean(isnan(J4), 2);
fprintf('atraso de 3 amostras: oraculo J = %.2f mA\n', Jo4);
for j = 1:size(casos, 1), fprintf('  %-34s J mediana %6.2f mA (%+5.0f %%), falhas %.0f %%\n', casos{j, 3}, med4(j), 100*(med4(j)/Jo4 - 1), 100*falha4(j)); end
save(fullfile(P.res, 'd08.mat'), 'lgs', 'Ml', 'il', 'melhor', 'sig', 'R1', 'med1', 'falha1', 'real', 'Jo', 'Ts_', 'R2', 'med2', 'falha2', 'Tis', 'J3', 'J4', 'Jo4', 'med4', 'falha4', 'casos', 'met', 'rot');

% figuras
f = figure('Position', [0 0 1750 640]);  tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile;  hold on;
for j = [1 3 4 5]
    lo = prctile(R1(:, j, :), 10, 3);  hi = prctile(R1(:, j, :), 90, 3);
    fill([sig, fliplr(sig)]*1e3, [lo; flipud(hi)]', cor{j}, 'FaceAlpha', 0.10, 'EdgeColor', 'none', 'HandleVisibility', 'off');
    plot(sig*1e3, med1(:, j), est{j}, 'Color', cor{j}, 'MarkerSize', 9, 'MarkerFaceColor', 'w', 'LineWidth', 2.4);
end
xline(8.5/4, ':', 'média de 16', 'Color', P.cor.cinza, 'LineWidth', 1.6, 'FontSize', 14, 'LabelVerticalAlignment', 'top', 'HandleVisibility', 'off');
xline(8.5, ':', '1 período', 'Color', P.cor.cinza, 'LineWidth', 1.6, 'FontSize', 14, 'LabelVerticalAlignment', 'top', 'HandleVisibility', 'off');
plot(sig*1e3, melhor, ':o', 'Color', P.cor.azul, 'MarkerSize', 9, 'MarkerFaceColor', 'w', 'LineWidth', 2.4);
plot([8.5/4 8.5], 100*(real(:, 2)/Jo - 1), 'p', 'Color', 'k', 'MarkerFaceColor', P.cor.azul, 'MarkerSize', 18);
set(gca, 'XScale', 'log');  xticks([0.5 1 2 4 8.5 16 32]);  xlim([0.45 36]);  ylim([-10 100]);  yline(0, 'k-', 'HandleVisibility', 'off');
xlabel('ruído em cada amostra dos dados [mA rms]');  ylabel('piora sobre o controle com o modelo certo [%]');
legend([rot([1 3 4 5]), {'DeePC, melhor λ_g para cada ruído', 'DeePC (λ_g = 3) com os dados REAIS'}], 'Location', 'northwest', 'FontSize', 14);  title('ruído nos dados (2044 amostras)');
nexttile;  hold on;  e2 = {'-s', '-o', '--^', ':^'};  c2 = {P.cor.verde, P.cor.azul, P.cor.magenta, P.cor.magenta};
for j = 1:numel(m2), plot(Ts_, med2(:, j, 1), e2{j}, 'Color', c2{j}, 'MarkerSize', 9, 'MarkerFaceColor', 'w', 'LineWidth', 2.4); end
set(gca, 'XScale', 'log');  xticks(Ts_);  xlim([40 2300]);  ylim([-10 100]);  yline(0, 'k-');
xlabel('amostras de PRBS usadas (ruído de 8,5 mA, sem média)');  ylabel('piora sobre o controle com o modelo certo [%]');  title('quantidade de dados');
salva(f, P, 'd08_ruido.png');

f = figure('Position', [0 0 1750 600]);  tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile;  hold on;
plot(Tis, J3(:, 2, 1), '-o', 'Color', P.cor.azul, 'MarkerSize', 9, 'MarkerFaceColor', 'w');  plot(Tis, J3(:, 2, 2), '--o', 'Color', P.cor.azul, 'MarkerSize', 9, 'MarkerFaceColor', 'w');
plot(Tis, J3(:, 1, 1), '-s', 'Color', P.cor.verde, 'MarkerSize', 9, 'MarkerFaceColor', 'w');  plot(Tis, J3(:, 1, 2), '--s', 'Color', P.cor.verde, 'MarkerSize', 9, 'MarkerFaceColor', 'w');
yline(Jo, ':', 'modelo certo', 'Color', P.cor.magenta, 'LineWidth', 2, 'FontSize', 14);
xlabel('T_{ini} [amostras de passado]');  ylabel('erro rms de rastreamento [mA]');  ylim([9 15]);  title('dados reais: quanto passado usar');
legend({'DeePC (λ_g = 3), média de 16', 'DeePC (λ_g = 3), 1 período', 'SPC, média de 16', 'SPC, 1 período'}, 'Location', 'northeast', 'FontSize', 14);
nexttile;  hold on;  v = 100*(med4/Jo4 - 1);  v(falha4 > 0.5) = NaN;
b = barh(categorical(casos(:, 3), flipud(casos(:, 3))), flipud(min(v, 150)));  b.FaceColor = 'flat';
b.CData = flipud([P.cor.magenta; P.cor.magenta; P.cor.verde; P.cor.verde; P.cor.azul]);
for j = 1:numel(v)
    if isnan(v(j)), text(5, size(casos, 1) + 1 - j, 'instável', 'FontSize', 16, 'Color', P.cor.verm, 'FontWeight', 'bold');
    else, text(min(v(j), 150) + 0.3, size(casos, 1) + 1 - j, sprintf('%+.1f %%', v(j)), 'FontSize', 16); end
end
xlabel('piora sobre o controle com o modelo certo [%]');  xlim([-1 12]);  title('planta com 3 amostras de atraso (estrutura inesperada)');
salva(f, P, 'd08_estrutura.png');
