%% d10_pwm  O controle na planta CHAVEADA (portadora, tres bracos, tempo morto, rotacao no atraso)
%  O controle e o mesmo dos dados reais da bancada; a planta agora e a simulacao chaveada, que
%  reproduz a bancada melhor que o modelo medio (d05). E a melhor previsao disponivel do ensaio.
P = parametros();  [u, y] = le_prbs(P);  N = P.N;  warning('off', 'all');
Cd = ganhos('spc', u, y, P);  Cm = ganhos('oraculo', u, y, P);  Cpi = P.pi;
lista = {Cpi, 'PI 500 Hz', P.cor.cinza, '--'; Cm, 'MPC com o modelo médio', P.cor.magenta, '--'; Cd, 'SPC/DeePC, dados reais', P.cor.azul, '-'};
tms = [0 100 500 1000]*1e-9;  T = zeros(3, numel(tms), 4);
for j = 1:3, for a = 1:numel(tms)
    d = desempenho(lista{j, 1}, P, 'planta', 'pwm', 'tm', tms(a));
    S0 = simula_dq(lista{j, 1}, P, periodos = 2, ruido = 0, planta = 'pwm', tm = tms(a));
    reg = N + [301:690, 901:1190, 1301:1690, 1801:2040];  e0 = S0.ref(:, reg) - S0.iv(:, reg);
    T(j, a, :) = [d.J, d.m.subida, d.m.interf, 1e3*sqrt(mean(sum(e0.^2, 1)))];
end, end
for j = 1:3
    fprintf('%-24s J [mA] por tempo morto (0, 100, 500, 1000 ns): %s | ondulacao sem ruido [mA]: %s | subida %.2f ms, interf. %.1f mA (100 ns)\n', ...
        lista{j, 2}, mat2str(T(j, :, 1), 3), mat2str(T(j, :, 4), 2), T(j, 2, 2), T(j, 2, 3));
end
% previsao do ensaio: mesmas metricas da tabela principal, planta PWM com 100 ns e ruido
Cdp = Cd;  Cdp.previa = true;  casos = {Cpi, 'PI 500 Hz'; Cd, 'SPC/DeePC'; Cdp, 'SPC/DeePC + previa'};
fprintf('previsao do ensaio (PWM, 100 ns, ruido 8,5 mA): controle | subida | t50 | sobressinal | rms regime | interf | J\n');
for j = 1:3
    d = desempenho(casos{j, 1}, P, 'planta', 'pwm');  z = (d.S.iv(1, N + (201:500)) - 0.15)/0.10;
    fprintf('  %-20s %.2f | %.2f | %2.0f %% | %.1f | %.1f | %.1f\n', casos{j, 2}, d.m.subida, (find(z >= 0.5, 1) - 1)*P.Ts*1e3, d.m.sobre, d.m.rms, d.m.interf, d.J);
end
f = figure('Position', [0 0 1750 620]);  tiledlayout(1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
kk = N + (191:280);  tt = (kk - N - 201)*P.Ts*1e3;
for q = 1:2
    nexttile;  hold on;
    for j = 1:3
        S0 = simula_dq(lista{j, 1}, P, periodos = 2, ruido = 0, planta = 'pwm');
        plot(tt, 1e3*S0.iv(q, kk), lista{j, 4}, 'Color', lista{j, 3}, 'LineWidth', 2.6);
    end
    xlabel('tempo desde o degrau de i_d [ms]');
    if q == 1, ylabel('i_d [mA]');  legend(lista(:, 2), 'Location', 'southeast', 'FontSize', 15);  title('planta chaveada, tempo morto de 100 ns'); else, ylabel('i_q [mA]');  title('o outro eixo'); end
end
nexttile;  hold on;
for j = 1:3, plot(tms*1e9, T(j, :, 4), [lista{j, 4} 'o'], 'Color', lista{j, 3}, 'MarkerSize', 10, 'MarkerFaceColor', 'w', 'LineWidth', 2.6); end
xlabel('tempo morto [ns]');  ylabel('ondulação em regime, sem ruído [mA rms]');  title('distorção do tempo morto');  ylim([0 inf]);
salva(f, P, 'd10_pwm.png');
save(fullfile(P.res, 'd10.mat'), 'T', 'tms');
