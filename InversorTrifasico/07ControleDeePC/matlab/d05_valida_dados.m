%% d05_valida_dados  Validacao com dados reais que NAO entraram no projeto do controle
%  (a) O simulador reproduz a bancada? PI de 300 Hz medido (etapa 03) x simulado (modelo medio e PWM).
%  (b) O preditor tirado da PRBS preve outro ensaio? Previsao de 1 a 10 passos das correntes do
%      ensaio do PI (malha fechada, degraus) a partir das tensoes medidas nesse ensaio.
P = parametros();  [u, y, y1] = le_prbs(P);  N = P.N;
X = le_dados3f(P.piReal, 8);  rm = X(:, 1:2)';  im = X(:, 3:4)';  vm = X(:, 5:6)';     % idRef iqRef id iq vd vq

% (a) simulador x medido
Cpi = struct('tipo', 'pi', 'kp', 2*pi*300*9.8e-3, 'ki', 2*pi*300*26.2, 'desacopla', true, 'L', 9.8e-3);
Sa = simula_dq(Cpi, P, periodos = 2, ruido = 0);  ia = Sa.iv(:, N+1:end);  va = Sa.u(:, N+1:end);
Sp = simula_dq(Cpi, P, periodos = 2, ruido = 0, planta = 'pwm');  ip = Sp.iv(:, N+1:end);  vp = Sp.u(:, N+1:end);
fprintf('PI 300 Hz medido x simulado (rms no periodo): corrente medio %.2f mA, PWM %.2f mA; tensao medio %.3f V, PWM %.3f V\n', ...
    1e3*rms(im - ia, 'all'), 1e3*rms(im - ip, 'all'), rms(vm - va, 'all'), rms(vm - vp, 'all'));
reg = 301:690;
fprintf('regime (id* = 0,25 A): vd medido %.3f, medio %.3f, PWM %.3f V; vq medido %.3f, medio %.3f, PWM %.3f V\n', ...
    mean(vm(1, reg)), mean(va(1, reg)), mean(vp(1, reg)), mean(vm(2, reg)), mean(va(2, reg)), mean(vp(2, reg)));
f = figure('Position', [0 0 1750 760]);  tiledlayout(2, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
kk = 190:260;  tt = (kk - 201)*P.Ts*1e3;  nomes = {'i_d [mA]', 'i_q [mA]', 'v_d [V]', 'v_q [V]'};
dados = {1e3*im(1, :), 1e3*ia(1, :), 1e3*ip(1, :); 1e3*im(2, :), 1e3*ia(2, :), 1e3*ip(2, :); vm(1, :), va(1, :), vp(1, :); vm(2, :), va(2, :), vp(2, :)};
ordem = [1 2 4 5];
for j = 1:4
    nexttile(ordem(j));  hold on;
    plot(tt, dados{j, 2}(kk), '--', 'Color', P.cor.cinza, 'LineWidth', 2.2);
    plot(tt, dados{j, 3}(kk), '-', 'Color', P.cor.azul, 'LineWidth', 2.4);
    plot(tt, dados{j, 1}(kk), 'k.', 'MarkerSize', 13);
    ylabel(nomes{j});  if j > 2, xlabel('tempo desde o degrau de i_d [ms]'); end
    if j == 1, legend({'simulação: modelo médio', 'simulação: PWM chaveado', 'medido (média de 16)'}, 'Location', 'southeast', 'FontSize', 15); end
end
nexttile(3, [2 1]);  hold on;
b = bar(categorical({'corrente [mA]', 'tensão [×10 mV]'}), [1e3*rms(im - ia, 'all'), 1e3*rms(im - ip, 'all'); 100*rms(vm - va, 'all'), 100*rms(vm - vp, 'all')]);
b(1).FaceColor = P.cor.cinza;  b(2).FaceColor = P.cor.azul;  ylabel('erro rms no período inteiro');
legend({'modelo médio', 'PWM chaveado'}, 'Location', 'northwest', 'FontSize', 15);  title('simulado − medido');
salva(f, P, 'd05_simulador.png');

% (b) previsao do ensaio do PI com preditores tirados da PRBS
Nh = 10;  T = kron(tril(ones(Nh)), eye(2));
casos = {'SPC, T_{ini} = 2', 2, 'spc'; 'SPC, T_{ini} = 4', 4, 'spc'; 'SPC, T_{ini} = 6', 6, 'spc'; ...
         'modelo físico ajustado na PRBS (T_{ini} = 2)', 2, 'fis'; 'modelo físico ajustado (T_{ini} = 6)', 6, 'fis'};
E = zeros(size(casos, 1), Nh);  Mf = identifica('fisico', u, y, P);
for j = 1:size(casos, 1)
    Ti = casos{j, 2};
    if strcmp(casos{j, 3}, 'spc'), Sp = preditor_spc(u, y, Ti, Nh, 0); else, Sp = preditor_spc(u, resposta_modelo(Mf, u), Ti, Nh, 0, pinv = true); end
    [Zp, Uf, Yf] = janelas(vm, im, Ti, Nh);
    D = T*(Sp.F*Zp + Sp.Ku*Uf) - T*Yf;                 % erro em y(k+h) - y(k)
    for h = 1:Nh, E(j, h) = 1e3*rms(D(2*h-1:2*h, :), 'all'); end
    if j == 2, S2 = Sp;  Z2 = Zp;  U2 = Uf; end
end
piso = 1e3*rms(diff(im(:, reg), 1, 2), 'all')/sqrt(2);  % ruido por eixo das medidas (media de 16)
fprintf('previsao do ensaio do PI (rms por eixo, mA) em 1, 5 e 10 passos; ruido das medidas ~ %.1f mA (piso ~ %.1f)\n', piso, sqrt(2)*piso);
for j = 1:size(casos, 1), fprintf('  %-46s %5.2f %5.2f %5.2f\n', casos{j, 1}, E(j, [1 5 10])); end
% simulacao livre (so as tensoes medidas entram): tira o efeito do ruido na condicao inicial
yl = resposta_modelo(Mf, vm);  yn = resposta_modelo(identifica('oraculo', u, y, P, R = 25, L = 10e-3), vm);
Ma = identifica('arx', u, y, P);  ya = resposta_modelo(Ma, vm);
el = [rms(im - yl, 'all'), rms(im - yn, 'all'), rms(im - ya, 'all')]*1e3;
fit = @(yh) 100*(1 - norm(im - yh, 'fro')/norm(im - mean(im, 2), 'fro'));
fprintf('simulacao livre do ensaio do PI: fisico ajustado %.2f mA (FIT %.1f %%), nominal 25/10 %.2f mA (%.1f %%), ARX da PRBS %.2f mA (%.1f %%)\n', ...
    el(1), fit(yl), el(2), fit(yn), el(3), fit(ya));
fprintf('fisico ajustado: a %.4f c %.4f b %.5f e %.5f\n', Mf.th);
f = figure('Position', [0 0 1750 620]);  tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile;  hold on;  cores = {P.cor.azul, P.cor.azul, P.cor.azul, P.cor.magenta, P.cor.magenta};  est = {'-o', '-s', '-^', '--o', '--^'};
for j = 1:size(casos, 1), plot((1:Nh)*P.Ts*1e3, E(j, :), est{j}, 'Color', cores{j}, 'MarkerSize', 9, 'MarkerFaceColor', 'w'); end
yline(sqrt(2)*piso, ':', 'ruído das medidas', 'Color', P.cor.cinza, 'LineWidth', 2, 'FontSize', 15, 'LabelHorizontalAlignment', 'right', 'LabelVerticalAlignment', 'bottom');
xlabel('horizonte da previsão [ms]');  ylabel('erro rms de previsão [mA]');  ylim([0 10]);
legend(casos(:, 1), 'Location', 'northwest', 'FontSize', 14);  title('ensaio do PI previsto com o que se tirou da PRBS');
nexttile;  hold on;  k0 = 196;  kk = k0-6:k0+24;  tt = (kk - 201)*P.Ts*1e3;
plot(tt, 1e3*im(1, kk), 'k.-', 'MarkerSize', 16, 'LineWidth', 1.2);
for ks = k0:4:k0+12
    yh = im(:, ks) + reshape(T*(S2.F*Z2(:, ks) + S2.Ku*U2(:, ks)), 2, []);
    plot((ks + (0:Nh) - 201)*P.Ts*1e3, 1e3*[im(1, ks), yh(1, :)], '-', 'Color', P.cor.azul, 'LineWidth', 2.4);
    plot((ks - 201)*P.Ts*1e3, 1e3*im(1, ks), 'o', 'Color', P.cor.azul, 'MarkerSize', 10, 'LineWidth', 2);
end
xlabel('tempo desde o degrau de i_d [ms]');  ylabel('i_d [mA]');
legend({'medido (ensaio do PI)', 'previsões de 10 passos (SPC, T_{ini} = 4)'}, 'Location', 'southeast', 'FontSize', 15);  title('cada curva azul: previsão feita no círculo');
salva(f, P, 'd05_previsao_pi.png');
save(fullfile(P.res, 'd05.mat'), 'E', 'casos', 'el', 'piso');
