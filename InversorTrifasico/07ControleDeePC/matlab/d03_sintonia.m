%% d03_sintonia  O que cada botao do DeePC/SPC faz (simulacao)
%  r: peso do esforco de controle (velocidade x ruido); N: horizonte; Tini: passado usado;
%  dados: media de 16 periodos x um periodo so (mais ruido nos dados).
P = parametros();  [u, y, y1] = le_prbs(P);  NP = 3;
rodar = @(uu, yy, Tini, N, r) metricas(simula_dq(setfield(setfield(ganho_spc(uu, yy, Tini, N, r), 'tipo', 'mpc'), 'Tini', Tini), P, periodos = NP), P);

rs = [1e-3 3e-3 1e-2 3e-2 1e-1];  A = zeros(numel(rs), 2);
for j = 1:numel(rs), m = rodar(u, y, 2, 10, rs(j));  A(j, :) = [m.subida, m.rms]; end
Ns = [3 5 10 20 40];  B = zeros(numel(Ns), 2);
for j = 1:numel(Ns), m = rodar(u, y, 2, Ns(j), 1e-2);  B(j, :) = [m.subida, m.rms]; end
Ts_ = [1 2 3 4];  Cc = zeros(numel(Ts_), 2);
for j = 1:numel(Ts_), m = rodar(u, y, Ts_(j), 10, 1e-2);  Cc(j, :) = [m.subida, m.rms]; end
m16 = rodar(u, y, 2, 10, 1e-2);  m1 = rodar(u, y1, 2, 10, 1e-2);
fprintf('r: %s\n subida %s\n rms %s\n', mat2str(rs), mat2str(A(:, 1)', 3), mat2str(A(:, 2)', 3));
fprintf('N: %s\n subida %s\n rms %s\n', mat2str(Ns), mat2str(B(:, 1)', 3), mat2str(B(:, 2)', 3));
fprintf('Tini: %s\n subida %s\n rms %s\n', mat2str(Ts_), mat2str(Cc(:, 1)', 3), mat2str(Cc(:, 2)', 3));
fprintf('dados media 16: subida %.2f rms %.1f erro %+.1f | 1 periodo: subida %.2f rms %.1f erro %+.1f\n', m16.subida, m16.rms, m16.erro(1), m1.subida, m1.rms, m1.erro(1));
D3 = [m16.subida m16.rms; m1.subida m1.rms];

f = figure('Position', [0 0 1750 760]);  tiledlayout(2, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
xs = {rs, Ns, Ts_};  Ms = {A, B, Cc};  rot = {'peso r_u do esforço', 'horizonte N [amostras]', 'T_{ini} [amostras de passado]'};
tit = {'r_u: rapidez × ruído', 'N: quanto olhar à frente', 'T_{ini}: quanto passado'};
for l = 1:2, for c = 1:3
    nexttile;  plot(xs{c}, Ms{c}(:, l), 'o-', 'Color', P.cor.azul, 'MarkerSize', 9, 'MarkerFaceColor', 'w', 'LineWidth', 2.4);
    if c < 3, set(gca, 'XScale', 'log');  xticks(xs{c}); end
    if l == 1, ylim([0 1.2]);  title(tit{c});  if c == 1, ylabel('subida 10–90 % [ms]'); end
    else, ylim([0 8]);  xlabel(rot{c});  if c == 1, ylabel('desvio rms em regime [mA]'); end, end
end, end
salva(f, P, 'd03_sintonia.png');
save(fullfile(P.res, 'd03.mat'), 'rs', 'A', 'Ns', 'B', 'Ts_', 'Cc', 'D3');
