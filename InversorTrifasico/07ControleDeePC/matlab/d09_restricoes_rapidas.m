%% d09_restricoes_rapidas  Limite de tensao dentro da otimizacao com poucas contas por amostra
%  Gradiente rapido projetado (FGM) nas tensoes futuras, cada par (vd, vq) projetado no circulo
%  |v| <= 0,45 Vdc, partida quente. Quantas iteracoes bastam? Comparado com cortar o comando.
P = parametros();  [u, y] = le_prbs(P);  N = P.N;  n = 0:N-1;  warning('off', 'all');
C = ganhos('spc', u, y, P, r = 1e-3);                        % sintonia agressiva: satura nos degraus
ref = repmat([0.05 + 0.25*(n >= 200 & n < 1200); -0.10*(n >= 200 & n < 1200)], 1, 2);   % degrau em d e q juntos
its = [1 2 3 5 10 20 50];  k = N + (195:400);
custo = @(S) sum(P.q*sum((S.ref(:, k) - S.iv(:, k)).^2, 1)) + 1e-3*sum(sum(diff(S.u(:, k(1)-1:k(end)), 1, 2).^2, 1));
Sc = simula_dq(C, P, ref = ref, ruido = 0);  Se = simula_dq(prepara_fgm(C, 400), P, ref = ref, ruido = 0);
Jc = custo(Sc);  Je = custo(Se);  Jk = zeros(size(its));  Sk = cell(size(its));
for j = 1:numel(its), Sk{j} = simula_dq(prepara_fgm(C, its(j)), P, ref = ref, ruido = 0);  Jk(j) = custo(Sk{j}); end
t90 = @(S) (find((S.iv(1, N+201:N+400) - 0.05)/0.25 >= 0.9, 1) - 1)*P.Ts*1e3;
tq90 = @(S) (find(S.iv(2, N+201:N+400)/(-0.10) >= 0.9, 1) - 1)*P.Ts*1e3;
fprintf('cortar: custo %+.1f %% sobre o otimo, t90 d %.2f ms, q %.2f ms\n', 100*(Jc/Je - 1), t90(Sc), tq90(Sc));
for j = 1:numel(its), fprintf('FGM %2d iteracoes: custo %+.2f %%, t90 d %.2f ms, q %.2f ms\n', its(j), 100*(Jk(j)/Je - 1), t90(Sk{j}), tq90(Sk{j})); end
fprintf('otimo (400 iteracoes): t90 d %.2f ms, q %.2f ms\n', t90(Se), tq90(Se));
Cf = prepara_fgm(C, 1);  nv = 2*C.N;
fprintf('por iteracao: %d multiplicacoes e somas (matriz %d x %d) + %d projecoes; condicionamento %.0f, momento %.2f\n', nv*nv + 2*nv, nv, nv, C.N, Cf.cond, Cf.beta);
% com o ruido da bancada: o corte e o FGM de 3 iteracoes na nota de sempre
d1 = desempenho(C, P, 'ref', ref);  d3 = desempenho(prepara_fgm(C, 3), P, 'ref', ref);
fprintf('com ruido: cortar J = %.2f mA; FGM 3 it. J = %.2f mA\n', d1.J, d3.J);
f = figure('Position', [0 0 1750 620]);  tiledlayout(1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
kk = N + (195:260);  tt = (kk - N - 201)*P.Ts*1e3;
lista = {Sc, 'cortar o comando', P.cor.laranja, '-'; Sk{2}, 'otimizar: 2 iterações', P.cor.verde, '-'; Sk{4}, 'otimizar: 5 iterações', P.cor.azul, '-'; Se, 'ótimo com a restrição', [0 0 0], ':'};
for q = 1:2
    nexttile;  hold on;
    for j = 1:4, plot(tt, 1e3*lista{j, 1}.iv(q, kk), lista{j, 4}, 'Color', lista{j, 3}, 'LineWidth', 2.6); end
    stairs(tt, 1e3*ref(q, kk), ':', 'Color', P.cor.cinza, 'LineWidth', 1.4);  xlabel('tempo desde o degrau [ms]');
    if q == 1, ylabel('i_d [mA]');  legend(lista(:, 2), 'Location', 'southeast', 'FontSize', 15); else, ylabel('i_q [mA]'); end
end
nexttile;  hold on;
plot(its, 100*(Jk/Je - 1), '-o', 'Color', P.cor.azul, 'MarkerSize', 10, 'MarkerFaceColor', 'w', 'LineWidth', 2.6);
yline(100*(Jc/Je - 1), '--', 'cortar o comando', 'Color', P.cor.laranja, 'LineWidth', 2.4, 'FontSize', 15);
set(gca, 'XScale', 'log');  xticks(its);  ylim([-1 8]);  xlabel('iterações por amostra');  ylabel('custo a mais sobre o ótimo [%]');  title('quanto custa parar cedo');
text(1.1, 7.3, sprintf('1 iteração: %+.0f %%', 100*(Jk(1)/Je - 1)), 'FontSize', 15, 'Color', P.cor.verm);
salva(f, P, 'd09_restricoes.png');
save(fullfile(P.res, 'd09.mat'), 'its', 'Jk', 'Je', 'Jc');
