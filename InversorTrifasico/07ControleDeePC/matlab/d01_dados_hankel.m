%% d01_dados_hankel  Dos dados reais as matrizes de Hankel e a previsao direta dos dados
%  Dados: ensaio real de identificacao (etapa 02): PRBS em vd e vq, id e iq medidas (media de 16).
P = parametros();  [u, y, y1] = le_prbs(P);  N = P.N;  t = (0:N-1)*P.Ts*1e3;

% Figura 1: janelas deslizantes sobre os dados -> colunas da matriz de Hankel
f = figure('Position', [0 0 1700 700]);  tl = tiledlayout(2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile(1);  k = 1:120;  stairs(t(k), u(1, k), 'Color', P.cor.azul);  ylabel('v_d [V]');  hold on;
nexttile(3);  plot(t(k), y(1, k)*1e3, 'Color', P.cor.verm);  ylabel('i_d [mA]');  xlabel('tempo [ms]');  hold on;
cores = {P.cor.verde, P.cor.amar, P.cor.cinza};  inicios = [10 40 70];  L = 12;
for j = 1:3
    a = inicios(j);  b = a + L - 1;
    for ax = [1 3]
        nexttile(ax);  yl = ylim;
        patch(t([a b b a]), yl([1 1 2 2]), cores{j}, 'FaceAlpha', 0.18, 'EdgeColor', cores{j}, 'LineWidth', 2);
    end
end
nexttile(2, [2 1]);
H = zeros(2*L, 90);
for j = 1:90, H(:, j) = [u(1, j:j+L-1)'/3; y(1, j:j+L-1)'/0.05]; end
imagesc(H);  colormap(gca, parula);  axis tight;  hold on;
for j = 1:3, xline(inicios(j), '-', 'Color', cores{j}, 'LineWidth', 4); end
yline(L + 0.5, 'w-', 'LineWidth', 3);
set(gca, 'YTick', [L/2, 1.5*L], 'YTickLabel', {'v_d (janela)', 'i_d (janela)'});
xlabel('coluna = início da janela');  title('matriz de Hankel: cada coluna é um pedaço da gravação');
salva(f, P, 'd01_hankel.png');

% Figura 2: valores singulares (quanta "informacao independente" ha nos dados)
Tini = 2;  Nh = 10;
[Zp, Uf, Yf] = janelas(u, y, Tini, Nh);
sv = svd([Zp; Uf; Yf]);  sv1 = svd([Zp; Uf]);
fprintf('Hankel [Zp; Uf; Yf]: %d linhas, %d colunas; posto numerico (1e-3) = %d\n', size([Zp; Uf; Yf], 1), size(Zp, 2), sum(sv > 1e-3*sv(1)));
fprintf('[Zp; Uf]: %d linhas, posto %d (excitacao persistente: todas as linhas independentes)\n', size([Zp; Uf], 1), sum(sv1 > 1e-6*sv1(1)));
f = figure('Position', [0 0 1500 600]);
semilogy(sv/sv(1), 'o-', 'Color', P.cor.azul, 'MarkerSize', 8, 'LineWidth', 2);  hold on;
nU = 2*(Tini + Nh);                                  % incrementos de entrada na janela: 2 eixos x 12 amostras
xline(nU + 0.5, ':', 'Color', P.cor.verm, 'LineWidth', 2.5);  xline(nU + 2.5, ':', 'Color', P.cor.verde, 'LineWidth', 2.5);
text(3, 0.12, {sprintf('%d direções: as entradas', nU), '(2 eixos × 12 amostras)'}, 'FontSize', 17, 'Color', P.cor.verm);
text(nU + 3, 0.05, {'+2: o "estado" da carga', '(a corrente em d e q)'}, 'FontSize', 17, 'Color', P.cor.verde);
text(32, 3e-3, 'resto: ruído', 'FontSize', 17, 'Color', P.cor.cinza);
xlabel('índice'); ylabel('valor singular (normalizado)');
title('os dados revelam a ordem do sistema');
salva(f, P, 'd01_singulares.png');

% Figura 3: previsao de 10 passos direto dos dados (ajuste numa metade, teste na outra)
h1 = 1:1022;  h2 = 1023:N;  Tv = [1 2 3 4];  err = zeros(size(Tv));
T = kron(tril(ones(Nh)), eye(2));
for q = 1:numel(Tv)
    [Zp, Uf, Yf] = janelas(u, y, Tv(q), Nh);
    K = Yf(:, h1)/[Zp(:, h1); Uf(:, h1)];
    yh = T*(K*[Zp(:, h2); Uf(:, h2)]);  yv = T*Yf(:, h2);
    err(q) = 1e3*rms(reshape(yv(end-1:end, :) - yh(end-1:end, :), 1, []));
end
fprintf('erro da previsao de 10 passos (0,5 ms) [mA rms] para Tini = %s: %s\n', mat2str(Tv), mat2str(err, 3));
Tini = 2;  [Zp, Uf, Yf] = janelas(u, y, Tini, Nh);  K = Yf(:, h1)/[Zp(:, h1); Uf(:, h1)];
D = K*[Zp; Uf];  dyh = T*D;                          % incrementos previstos, acumulados
ypred = zeros(2, N);  for j = 1:N, ypred(:, mod(j + Nh - 1, N) + 1) = y(:, j) + dyh(end-1:end, j); end
f = figure('Position', [0 0 1700 640]);  tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile;  k = 1300:1420;
plot(t(k), y(1, k)*1e3, 'o', 'Color', P.cor.cinza, 'MarkerSize', 6, 'LineWidth', 1.5);  hold on;
plot(t(k), ypred(1, k)*1e3, '-', 'Color', P.cor.azul, 'LineWidth', 2.5);
plot(t(k), y(2, k)*1e3, 's', 'Color', P.cor.cinza, 'MarkerSize', 6, 'LineWidth', 1.5);
plot(t(k), ypred(2, k)*1e3, '-', 'Color', P.cor.verm, 'LineWidth', 2.5);
xlabel('tempo [ms]');  ylabel('corrente [mA]');
legend({'i_d medida', 'i_d prevista 10 passos antes', 'i_q medida', 'i_q prevista'}, 'Location', 'northoutside', 'NumColumns', 2);
nexttile;  bar(Tv, err, 'FaceColor', P.cor.azul);  xlabel('T_{ini} (amostras do passado usadas)');
ylabel('erro da previsão de 0,5 ms [mA rms]');  title('quanto passado é preciso?');
salva(f, P, 'd01_previsao.png');
