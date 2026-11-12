%% d00_superposicao  A ideia por tras do DeePC, com um exemplo de brinquedo (uma fase RL, sem ruido)
%  Tres ensaios gravados (entradas quaisquer) e uma entrada nova que e combinacao deles:
%  a saida nova e a MESMA combinacao das saidas gravadas. Nao foi preciso saber R nem L.
P = parametros();  a = exp(-P.R*P.Ts/P.L);  b = (1 - a)/P.R;
n = 60;  t = (0:n-1)*P.Ts*1e3;  rng(4);
resp = @(v) filter([0 0 b], [1 -a], v);           % i(k) = a i(k-1) + b v(k-2) (atraso de 2)
V = [6*(rand(1, n) > 0.5) - 3; 4*sin(2*pi*(0:n-1)/25); [zeros(1, 10), 5*ones(1, n-10)]];
I = [resp(V(1, :)); resp(V(2, :)); resp(V(3, :))];
g = [0.5; -1; 0.8];  vn = g'*V;  in = resp(vn);
f = figure('Position', [0 0 1750 680]);  tl = tiledlayout(2, 4, 'TileSpacing', 'compact', 'Padding', 'compact');
cores = {P.cor.azul, P.cor.verm, P.cor.verde};
for j = 1:3
    nexttile(j);  stairs(t, V(j, :), 'Color', cores{j}, 'LineWidth', 2.4);  title(sprintf('ensaio %d', j));  ylim([-6 7]);
    if j == 1, ylabel('tensão [V]'); end
    nexttile(4 + j);  plot(t, 1e3*I(j, :), 'Color', cores{j}, 'LineWidth', 2.6);  ylim([-200 200]);  xlabel('tempo [ms]');
    if j == 1, ylabel('corrente [mA]'); end
end
nexttile(4);  stairs(t, vn, 'k', 'LineWidth', 2.4);  ylim([-6 7]);
title(sprintf('nova = %.1f·(1) %+.1f·(2) %+.1f·(3)', g));
nexttile(8);  plot(t, 1e3*in, 'k', 'LineWidth', 3.5);  hold on;  plot(t, 1e3*(g'*I), '--', 'Color', P.cor.amar, 'LineWidth', 2.6);
ylim([-200 200]);  xlabel('tempo [ms]');  legend({'resposta da carga', 'mesma soma das gravadas'}, 'Location', 'southwest', 'FontSize', 14);
salva(f, P, 'd00_superposicao.png');
fprintf('superposicao: diferenca maxima %.2e A\n', max(abs(in - g'*I)));
