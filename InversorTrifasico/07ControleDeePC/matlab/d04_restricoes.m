%% d04_restricoes  Limite de tensao: cortar o comando x otimizar com a restricao (simulacao)
%  Degrau grande em id (0,05 -> 0,30 A): o transitorio pede mais que 9 V.
P = parametros();  [u, y] = le_prbs(P);  N = P.N;
n = 0:N-1;  ref = repmat([0.05 + 0.25*(n >= 200 & n < 1200); zeros(1, N)], 1, 2);
C = ganho_spc(u, y, 2, 10, 1e-3);  C.tipo = 'mpc';  C.Tini = 2;
Sc = simula_dq(C, P, ref = ref, ruido = 0);
Cq = C;  Cq.qp = true;  tic;  Sq = simula_dq(Cq, P, ref = ref, ruido = 0);  tqp = toc;
Cpi = P.pi;
Spi = simula_dq(Cpi, P, ref = ref, ruido = 0);
fprintf('QP: %.1f ms por amostra no MATLAB (quadprog)\n', 1e3*tqp/(2*N));
k = N + (180:330);  tt = (k - N - 201)*P.Ts*1e3;
casos = {'PI 500 Hz (anti-windup)', Spi, P.cor.cinza, '--'; 'DeePC: corta o comando', Sc, P.cor.azul, '-'; ...
         'DeePC: otimiza com a restrição', Sq, P.cor.verde, '-'};
for j = 1:3
    X = casos{j, 2};  id = X.iv(1, k);  z = (id - 0.05)/0.25;  t90 = (find(z(21:end) >= 0.9, 1) - 1)*P.Ts*1e3;
    fprintf('%-32s sobressinal %4.1f %%, t90 %.2f ms, |iq| max %.1f mA, |v| max %.2f V\n', casos{j, 1}, ...
        max(0, (max(id) - 0.30)/0.25*100), t90, 1e3*max(abs(X.iv(2, k))), max(vecnorm(X.u(:, k))));
end
f = figure('Position', [0 0 1750 600]);  tiledlayout(1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile;  hold on;  for j = 1:3, plot(tt, 1e3*casos{j, 2}.iv(1, k), casos{j, 4}, 'Color', casos{j, 3}, 'LineWidth', 2.6); end
stairs(tt, 1e3*ref(1, k), 'k:', 'LineWidth', 1.8);  ylabel('i_d [mA]');  xlabel('tempo desde o degrau [ms]');
legend([casos(:, 1); {'referência'}], 'Location', 'southeast', 'FontSize', 14);
nexttile;  hold on;  for j = 1:3, plot(tt, 1e3*casos{j, 2}.iv(2, k), casos{j, 4}, 'Color', casos{j, 3}, 'LineWidth', 2.6); end
ylabel('i_q [mA]');  xlabel('tempo desde o degrau [ms]');  title('o outro eixo');
nexttile;  hold on;  for j = 1:3, plot(tt, vecnorm(casos{j, 2}.u(:, k)), casos{j, 4}, 'Color', casos{j, 3}, 'LineWidth', 2.6); end
yline(P.vmax, 'r-', 'LineWidth', 2);  yline(P.vmax*cos(pi/8), 'r:', 'LineWidth', 2);
ylabel('|v| [V]');  xlabel('tempo desde o degrau [ms]');  title('limite de 9 V (octógono: pontilhado)');  ylim([0 10]);
salva(f, P, 'd04_restricoes.png');
