%% d12_adaptativo  E se a carga mudar? SPC/DeePC que se refaz com os dados da malha fechada
%  Cenario (como o do RLS, etapa 05): o controle comeca com dados de uma carga ERRADA (35 ohm;
%  14 mH) na carga da bancada; no 5o periodo (0,41 s) a carga muda para 12 ohm; 2,5 mH (indutancia 4 vezes menor).
P = parametros();  warning('off', 'all');  NP = 8;  NS = 10;
[u0, y0] = gera_dados(P, R = 35, L = 14e-3);  troca = struct('k', 4*P.N + 1, 'R', 12, 'L', 2.5e-3);
[un, yn] = gera_dados(P);  [u2, y2] = gera_dados(P, R = 12, L = 2.5e-3);
ideal = [repmat(simula_adaptativo(P, un, yn, adapta = false, dither = 0, periodos = 2).J(2), 1, 4), ...
         repmat(simula_adaptativo(P, u2, y2, adapta = false, dither = 0, periodos = 2, R = 12, L = 2.5e-3).J(2), 1, 4)];
casos = {'ganhos fixos (dados da carga errada)', false, 0; 'adaptativo, sem excitação extra', true, 0; ...
         'adaptativo, excitação de ±0,2 V', true, 0.2; 'adaptativo, excitação de ±0,5 V', true, 0.5};
J = zeros(size(casos, 1), NP, NS);
for j = 1:size(casos, 1), for s = 1:NS
    J(j, :, s) = simula_adaptativo(P, u0, y0, adapta = casos{j, 2}, dither = casos{j, 3}, troca = troca, periodos = NP, semente = s).J;
end, end
Jm = median(J, 3);  disp('nota por periodo [mA] (mediana de 10 sementes); ultima linha: ganhos refeitos com um ensaio de PRBS na carga certa');
disp(round([Jm; ideal], 1));
fprintf('pior semente do adaptativo com 0,2 V: %.1f mA; sem excitacao: %.1f mA\n', max(J(3, :, :), [], 'all'), max(J(2, :, :), [], 'all'));
% alternativa: parar 10 ms e refazer o ensaio em malha aberta (200 amostras, sem media) na carga nova
Jr = zeros(1, NS);
for s = 1:NS
    [ud, yd] = gera_dados(P, R = 12, L = 2.5e-3, media = 1, semente = 50 + s);
    Jr(s) = desempenho(ganhos('spc', ud(:, 1:200), yd(:, 1:200), P, circular = false), P, 'R', 12, 'L', 2.5e-3, 'semente', s).J;
end
fprintf('re-ensaio de 10 ms (200 amostras, 8,5 mA de ruido) na carga nova: J mediana %.1f mA (de %.1f a %.1f)\n', median(Jr), min(Jr), max(Jr));
% memoria e periodo de recalculo
for mem = [500 2000 8000]
    Jx = simula_adaptativo(P, u0, y0, dither = 0.2, troca = troca, periodos = NP, memoria = mem).J;
    fprintf('memoria de %4d amostras: J por periodo %s\n', mem, mat2str(Jx, 3));
end
f = figure('Position', [0 0 1750 600]);  tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile;  hold on;  cor = {P.cor.laranja, P.cor.verde, P.cor.azul, P.cor.azul};  est = {'-s', '-^', '-o', ':o'};
t = (0.5:NP)*P.N*P.Ts*1e3;
for j = 1:4, plot(t, Jm(j, :), est{j}, 'Color', cor{j}, 'MarkerSize', 9, 'MarkerFaceColor', 'w', 'LineWidth', 2.4); end
plot(t(5:8), repmat(median(Jr), 1, 4), '-p', 'Color', P.cor.magenta, 'MarkerSize', 13, 'MarkerFaceColor', 'w', 'LineWidth', 2.4);
plot(t, ideal, 'k:', 'LineWidth', 2.2);  xline(4*P.N*P.Ts*1e3, '--', 'a carga muda', 'Color', P.cor.cinza, 'LineWidth', 1.6, 'FontSize', 15);
xlabel('tempo [ms] (um ponto por período de 102 ms)');  ylabel('erro rms de rastreamento [mA]');  ylim([0 inf]);
legend([casos(:, 1); {'re-ensaio de 10 ms em malha aberta após a troca'; 'ensaio completo na carga certa'}], 'Location', 'northwest', 'FontSize', 13);
nexttile;  hold on;  Sa = simula_adaptativo(P, u0, y0, dither = 0.2, troca = troca, periodos = NP);  Sf = simula_adaptativo(P, u0, y0, adapta = false, dither = 0, troca = troca, periodos = NP);
k = 4*P.N + (150:420);  tt = (k - 4*P.N - 201)*P.Ts*1e3;
plot(tt, 1e3*Sf.iv(1, k), '-', 'Color', P.cor.laranja, 'LineWidth', 1.8);  plot(tt, 1e3*Sa.iv(1, k), '-', 'Color', P.cor.azul, 'LineWidth', 1.8);
stairs(tt, 1e3*Sa.ref(1, k), 'k:', 'LineWidth', 1.6);  xlabel('tempo desde o degrau [ms]');  ylabel('i_d [mA]');
title('primeiro degrau depois da troca de carga');  legend({'ganhos fixos', 'adaptativo (±0,2 V)', 'referência'}, 'Location', 'southeast', 'FontSize', 15);
salva(f, P, 'd12_adaptativo.png');
save(fullfile(P.res, 'd12.mat'), 'Jm', 'ideal', 'casos', 'Jr');
