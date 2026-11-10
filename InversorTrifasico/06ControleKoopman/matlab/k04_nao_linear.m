%% k04_nao_linear  E se a carga nao fosse linear? (simulacao; hipotese, nao observada na bancada)
%  Indutor que satura: L(i) = L0 / (1 + (|i|/Isat)^2), Isat = 0,3 A (em 0,25 A, L cai a 59 %).
%  Dicionarios: linear z = [i; s(k-1)] e levantado [i; |i|^2 i; s(k-1); |i|^2 s(k-1)], com a
%  entrada tambem multiplicada por |i|^2 (modelo bilinear na entrada).
%  Dados de treino: (a) ensaio em malha aberta com vetores pseudoaleatorios (media de 16);
%                   (b) malha fechada na regiao de operacao, com 30 % de vetores aleatorios.
P = parametros();  N = P.N;  NP = 9;  Isat = 0.3;  V = P.V;

est1 = sequencia_vetores(N, 2);  s1 = V(:, est1 + 1);
Sid = simula_fcs([], P, estados = repmat(est1, 1, 17), ref = zeros(2, 17*N), Isat = Isat);
im = mean(reshape(Sid.i(:, N+1:end), 2, N, 16), 3);
Mab = edmd_periodico(im, s1);                                   % linear, malha aberta
Gab = circshift(im, -1, 2) / feat(im, circshift(s1, 1, 2), s1); % levantado, malha aberta

Sc = simula_fcs(preditor_linear(Mab, P), P, periodos = 4, Isat = Isat, eps = 0.3, semente = 5);
k = N+2:4*N-1;  I = Sc.i(:, k);  Sp = Sc.s(:, k-1);  S = Sc.s(:, k);  Ip = Sc.i(:, k+1);
Glf = Ip / [I; Sp; S];  Gfe = Ip / feat(I, Sp, S);              % linear e levantado, malha fechada
Mfe.A = [Glf(:, 1:4); zeros(2, 4)];  Mfe.B = [Glf(:, 5:6); eye(2)];

% predicao em dados de validacao sem ruido (correntes verdadeiras, malha fechada)
Sv = simula_fcs(preditor_linear(Mab, P), P, periodos = 2, ruido = 0, Isat = Isat);
iv = Sv.iv(:, N+1:end);  sv = Sv.s(:, N+1:end);  k0 = 2:N-10;
pred = {@(i, sp, s) Mab.A(1:2, :)*[i; sp] + Mab.B(1:2, :)*s, @(i, sp, s) Gab*feat(i, sp, s), ...
        @(i, sp, s) Glf*[i; sp; s],                          @(i, sp, s) Gfe*feat(i, sp, s)};
nomes = {'linear, malha aberta', 'levantado, malha aberta', 'linear, região de operação', 'levantado, região de operação'};
E = zeros(4, 2);
for m = 1:4
    E(m, :) = 1e3*[erro_h(pred{m}, iv, sv, k0, 1), erro_h(pred{m}, iv, sv, k0, 10)];
    fprintf('%-32s erro de predicao: 1 passo %.2f mA, 10 passos %.2f mA rms\n', nomes{m}, E(m, :));
end

% malha fechada (custo em k+3/2; o levantado refaz os observaveis a cada passo)
ctrl = {'linear, malha aberta', preditor_linear(Mab, P); 'linear, região de operação', preditor_linear(Mfe, P)
        'levantado, região de operação', @(im_, sp) meio(Gfe, im_, sp, V)};
C = zeros(3, 2);
for m = 1:3
    S_ = simula_fcs(ctrl{m, 2}, P, periodos = NP, Isat = Isat);  q = metricas(S_, P);
    C(m, :) = [norm(q.erro), q.rms];
    fprintf('FCS %-30s erro medio d / q %+5.1f / %+5.1f mA, rms %.1f mA, fsw %.0f Hz\n', ctrl{m, 1}, q.erro, q.rms, q.fsw);
end

f = figure('Position', [0 0 1700 640]);  tiledlayout(1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile;  ii = linspace(0, 0.4, 100);
plot(ii*1e3, P.L*1e3./(1 + (ii/Isat).^2), 'k', 'LineWidth', 2.5);  hold on;
xline([150 255], ':', 'Color', P.cor.amar, 'LineWidth', 2.5);
xlabel('|i| [mA]');  ylabel('L(i) [mH]');  title('indutor que satura (hipótese)');
nexttile;  b = bar(E);  b(1).FaceColor = P.cor.azul;  b(2).FaceColor = P.cor.verm;
set(gca, 'XTickLabel', {'linear', 'levantado', 'linear', 'levantado'});  ylabel('erro de predição [mA rms]');
xline(2.5, 'k:');  text(1.5, max(E(:))*1.06, {'treino:', 'malha aberta'}, 'HorizontalAlignment', 'center', 'FontSize', 15);
text(3.5, max(E(:))*1.06, {'treino: região', 'de operação'}, 'HorizontalAlignment', 'center', 'FontSize', 15);
legend({'1 passo', '10 passos'}, 'Location', 'northoutside', 'NumColumns', 2);  ylim([0 max(E(:))*1.2]);
nexttile;  b = bar(C(:, 1));  b.FaceColor = P.cor.cinza;
set(gca, 'XTickLabel', {'linear (aberta)', 'linear (oper.)', 'levantado (oper.)'});  ylabel('|erro médio| em regime [mA]');
title('FCS em malha fechada');  ylim([0 6]);
salva(f, P, 'k04_nao_linear.png');

function F = feat(i, sp, s)
% observaveis e entradas do modelo levantado; q = |i|^2 em unidades de (0,2 A)^2
q = sum(i.^2, 1)/0.04;
F = [i; q.*i; sp; q.*sp; s; q.*s];
end

function e = erro_h(pred, i, s, k0, h)
x = i(:, k0);
for j = 0:h - 1, x = pred(x, s(:, k0 + j - 1), s(:, k0 + j)); end
e = rms(vecnorm(i(:, k0 + h) - x));
end

function Im = meio(G, im, sp, V)
% i(k+3/2) ~ media de i(k+1) e i(k+2), refazendo os observaveis em k+1 (8 vetores de uma vez)
i1 = G*feat(repmat(im, 1, 8), repmat(sp, 1, 8), V);
i2 = G*feat(i1, V, V);
Im = (i1 + i2)/2;
end
