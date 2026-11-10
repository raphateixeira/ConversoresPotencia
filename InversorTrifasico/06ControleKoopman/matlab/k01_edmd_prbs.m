%% k01_edmd_prbs  EDMD nos dados reais da identificacao (PRBS em vd e vq, PWM, eixos dq)
%  Pergunta: que observaveis o operador de Koopman precisa para prever id e iq?
%  Compara dicionarios pela simulacao livre na metade do registro nao usada no ajuste.
P = parametros();
X = le_dados3f(P.dados.prbs, 8);                       % vd vq id iq iA iB iC th
x = (X(:, 3:4) - mean(X(:, 3:4)))';                    % desvios de id, iq [A]
u = (X(:, 1:2) - mean(X(:, 1:2)))';                    % desvios de vd, vq [V]
N = P.N;  meio = N/2;

%            nome                          nu nx nl
dic = {'i(k)  (DMDc)',                      0, 0, 0
       'i(k), v(k-1)',                      1, 0, 0
       'i(k), v(k-1), v(k-2)',              2, 0, 0
       '... + i(k-1)',                      2, 1, 0
       '... + monômios de grau 2',          2, 0, 2
       '... + monômios de graus 2 e 3',     2, 0, 3};
nd = size(dic, 1);  FIT = zeros(nd, 2);  nobs = zeros(nd, 1);
fprintf('dicionario | observaveis | FIT d / q [%%] (validacao cruzada)\n');
for d = 1:nd
    [nu, nx, nl] = dic{d, 2:4};
    f = zeros(2, 2);
    for dobra = 1:2
        if dobra == 1, tr = 1:meio; va = meio+1:N; else, tr = meio+1:N; va = 1:meio; end
        [A, B] = ajusta(x, u, tr, nu, nx, nl);
        f(dobra, :) = valida(A, B, x, u, va, nu, nx, nl);
    end
    FIT(d, :) = max(mean(f, 1), 0);  nobs(d) = size(A, 1);
    fprintf('  %-32s %2d   %5.1f / %5.1f\n', dic{d, 1}, nobs(d), FIT(d, 1), FIT(d, 2));
end

% Modelo escolhido: i(k), v(k-1), v(k-2), com o registro inteiro
[A, B] = ajusta(x, u, 1:N, 2, 0, 0);
lam = eig(A);  [~, o] = sort(abs(lam), 'descend');  lam = lam(o);
s = log(lam(1))/P.Ts;
Gdc = [eye(2) zeros(2, 4)]*((eye(6) - A)\B);           % ganho estatico v -> i
Z = inv(Gdc);
fprintf('autovalores de Koopman: %s\n', mat2str(lam.', 4));
fprintf('  dominante: %.4f %+.4fj -> R/L = %.0f 1/s (tau = %.3f ms), f = %.1f Hz\n', ...
    real(lam(1)), imag(lam(1)), -real(s), -1e3/real(s), abs(imag(s))/(2*pi));
fprintf('  ganho estatico: R = %.2f ohm, X = %.2f ohm (wL fisico = %.2f)\n', ...
    (Z(1, 1) + Z(2, 2))/2, (Z(2, 1) - Z(1, 2))/2, P.w*P.L);
lamFis = exp(-P.R*P.Ts/P.L)*exp(1j*P.w*P.Ts*[1 -1]);

% Figura 1: FIT por dicionario
f1 = figure('Position', [0 0 1500 640]);
b = barh(FIT);  b(1).FaceColor = P.cor.azul;  b(2).FaceColor = P.cor.verm;
set(gca, 'YTick', 1:nd, 'YTickLabel', dic(:, 1), 'YDir', 'reverse', 'XLim', [0 108]);
xlabel('FIT na validação [%]');  legend({'eixo d', 'eixo q'}, 'Location', 'northoutside', 'NumColumns', 2);
for d = 1:nd, text(max(FIT(d, :)) + 1, d, sprintf('%d obs.', nobs(d)), 'FontSize', 16, 'Color', P.cor.cinza); end
salva(f1, P, 'k01_dicionarios.png');

% Figura 2: autovalores de Koopman x polo fisico
f2 = figure('Position', [0 0 1500 640]);
t = tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile;  tt = linspace(0, 2*pi, 400);  plot(cos(tt), sin(tt), 'Color', P.cor.cinza, 'LineWidth', 1.2);  hold on;
plot(real(lam), imag(lam), 'o', 'Color', P.cor.azul, 'MarkerSize', 12, 'LineWidth', 2.5);
plot(real(lamFis), imag(lamFis), 'x', 'Color', P.cor.verm, 'MarkerSize', 16, 'LineWidth', 3);
axis equal;  xlim([-1.1 1.1]);  ylim([-1.1 1.1]);  xlabel('Re');  ylabel('Im');  title('plano z');
nexttile;  plot(real(lam), imag(lam), 'o', 'Color', P.cor.azul, 'MarkerSize', 14, 'LineWidth', 2.5);  hold on;
plot(real(lamFis), imag(lamFis), 'x', 'Color', P.cor.verm, 'MarkerSize', 18, 'LineWidth', 3);
xlim([0.85 0.91]);  ylim([-0.03 0.03]);  xlabel('Re');  title('zoom no polo da carga');
legend({'autovalores do EDMD (dados)', 'e^{-RT_s/L} e^{\pm j\omega T_s} (25,3 \Omega; 9,8 mH)'}, 'Location', 'southoutside');
salva(f2, P, 'k01_autovalores.png');

function [A, B] = ajusta(x, u, faixa, nu, nx, nl)
k = faixa(1 + max(nu, nx)):faixa(end - 1);
[A, B] = edmd(levanta(x, u, k, nu, nx, nl), u(:, k), levanta(x, u, k + 1, nu, nx, nl));
end

function f = valida(A, B, x, u, faixa, nu, nx, nl)
% simulacao livre no espaco levantado: z(k+1) = A z(k) + B u(k), x = primeiras 2 linhas
k0 = faixa(1) + max(nu, nx);  z = levanta(x, u, k0, nu, nx, nl);
xh = nan(2, faixa(end));  xh(:, k0) = x(:, k0);
for k = k0:faixa(end) - 1
    z = A*z + B*u(:, k);  xh(:, k + 1) = z(1:2);
end
j = k0 + 40:faixa(end);
f = [ajuste(x(1, j), xh(1, j)), ajuste(x(2, j), xh(2, j))];
end
