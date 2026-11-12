%% d06_analise_linear  O DeePC sem restricoes e um controlador LINEAR: analise classica
%  (a) resposta em frequencia do controlador e da malha; (b) tabela de margens e ganhos de ruido;
%  (c) mapa de estabilidade em (R, L); (d) margem de ganho (erro de Vdc) e de atraso;
%  (e) compromisso rapidez x robustez x ruido, variando a sintonia (r_u no DeePC, banda no PI).
P = parametros();  [u, y] = le_prbs(P);  warning('off', 'all');
pi_fc = @(fc) struct('tipo', 'pi', 'kp', 2*pi*fc*9.8e-3, 'ki', 2*pi*fc*26.2, 'desacopla', true, 'L', 9.8e-3);
C.pi3 = pi_fc(300);  C.pi5 = pi_fc(500);
C.deepc = ganhos('deepc', u, y, P);  C.spc = ganhos('spc', u, y, P);  C.mod = ganhos('oraculo', u, y, P);
nome = struct('pi3', 'PI 300 Hz', 'pi5', 'PI 500 Hz', 'deepc', 'DeePC (dados reais)', 'spc', 'SPC (dados reais)', 'mod', 'MPC com o modelo');
cor = struct('pi3', P.cor.cinza, 'pi5', P.cor.cinza, 'deepc', P.cor.azul, 'spc', P.cor.verde, 'mod', P.cor.magenta);
est = struct('pi3', ':', 'pi5', '--', 'deepc', '-', 'spc', '-', 'mod', '--');
ks = fieldnames(C);
fprintf('controle | rho | banda [Hz] | Ms | MG disco [dB] | MF disco [graus] | ruido->i | ruido->v [V/A] | ordem\n');
for j = 1:numel(ks)
    L.(ks{j}) = malha_linear(C.(ks{j}), P);  m = L.(ks{j});
    fprintf('  %-22s %.3f | %4.0f | %.2f | %4.1f | %3.0f | %.2f | %5.1f | %d\n', nome.(ks{j}), m.rho, m.banda, m.Ms, m.mg, m.mf, m.ruido_i, m.ruido_u, order(minreal(m.ctrl, 1e-6, false)));
    T6(j, :) = [m.rho, m.banda, m.Ms, m.mg, m.mf, m.ruido_i, m.ruido_u];
end

% (a) resposta em frequencia
w = 2*pi*logspace(1, log10(9990), 400);  f = w/(2*pi);  mostra = {'pi5', 'mod', 'deepc'};
fg = figure('Position', [0 0 1750 800]);  tiledlayout(2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
tit = {'controlador: de i_d medida para v_d', 'malha fechada: de i_d^* para i_d', 'sensibilidade na entrada da planta: σ_{max}(S)', 'ruído de medida para a tensão: σ_{max}'};
for q = 1:4
    nexttile;  hold on;
    for j = 1:numel(mostra)
        m = L.(mostra{j});
        switch q
            case 1, g = abs(squeeze(freqresp(m.ctrl(1, 3), w)));
            case 2, g = abs(squeeze(freqresp(m.sys(1, 1), w)));
            case 3, g = squeeze(max(sigma(eye(2) + m.sys(5:6, 3:4), w), [], 1));
            case 4, g = squeeze(max(sigma(m.sys(3:4, 5:6), w), [], 1));
        end
        plot(f, g, est.(mostra{j}), 'Color', cor.(mostra{j}), 'LineWidth', 2.6);
    end
    set(gca, 'XScale', 'log', 'YScale', 'log');  xlim([10 1e4]);  title(tit{q});
    if q > 2, xlabel('frequência [Hz]'); end
    if q == 1, ylabel('ganho [V/A]');  legend(cellfun(@(k) nome.(k), mostra, 'UniformOutput', false), 'Location', 'southwest', 'FontSize', 15); end
    if q == 2, ylabel('ganho [A/A]');  ylim([0.05 2]);  yline(1/sqrt(2), ':', '−3 dB', 'Color', P.cor.cinza, 'FontSize', 14); end
    if q == 3, ylabel('|S|');  ylim([0.01 3]);  yline(1, ':', 'Color', P.cor.cinza); end
    if q == 4, ylabel('ganho [V/A]'); end
end
salva(fg, P, 'd06_frequencia.png');

% (c) mapa de estabilidade: carga diferente da que gerou os dados
fr = logspace(log10(0.15), log10(6), 49);  fl = logspace(log10(0.15), log10(6), 49);  mapas = {'deepc', 'mod', 'pi5'};
Rho = zeros(numel(fl), numel(fr), 3);
for a = 1:numel(fr), for b = 1:numel(fl), for j = 1:3
    Rho(b, a, j) = malha_linear(C.(mapas{j}), P, R = fr(a)*P.R, L = fl(b)*P.L, completo = false).rho;
end, end, end
fg = figure('Position', [0 0 1750 640]);  tl = tiledlayout(1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
for j = 1:3
    nexttile;  hold on;
    contourf(fr, fl, min(max(Rho(:, :, j), 0.801), 1.02), [0.80:0.04:1.0 1.02], 'LineColor', 'none');
    contour(fr, fl, Rho(:, :, j), [1 1], 'k', 'LineWidth', 3);
    set(gca, 'XScale', 'log', 'YScale', 'log', 'Layer', 'top');  clim([0.8 1.02]);  colormap(gca, flipud(sky(6)));
    xticks([0.2 0.5 1 2 5]);  yticks([0.2 0.5 1 2 5]);  xlabel('R / R_0');  if j == 1, ylabel('L / L_0'); end
    plot(1, 1, 'ko', 'MarkerFaceColor', 'w', 'MarkerSize', 12, 'LineWidth', 2);
    plot(35/P.R, 14e-3/P.L, 'k^', 'MarkerFaceColor', 'w', 'MarkerSize', 12, 'LineWidth', 2);
    plot(4.7/P.R, 6.8e-3/P.L, 'ks', 'MarkerFaceColor', 'w', 'MarkerSize', 12, 'LineWidth', 2);
    title(nome.(mapas{j}));  axis square;
    est_frac = mean(Rho(:, :, j) < 1, 'all');  fprintf('mapa %-20s: %.0f %% da grade estavel; L minimo estavel com R nominal: %.2f L0\n', nome.(mapas{j}), 100*est_frac, min(fl(Rho(:, fr == fr(find(fr >= 1, 1)), j) < 1)));
end
cb = colorbar;  cb.Layout.Tile = 'east';  cb.Label.String = 'raio espectral (≥ 1: instável)';  cb.FontSize = 16;
salva(fg, P, 'd06_mapa.png');

% (d) erro de ganho (Vdc) e atraso a mais
al = logspace(log10(0.2), log10(6), 120);  mostra = {'pi5', 'mod', 'deepc'};
fg = figure('Position', [0 0 1750 600]);  tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile;  hold on;
for j = 1:3
    r = arrayfun(@(a) malha_linear(C.(mostra{j}), P, alfa = a, completo = false).rho, al);
    plot(al, r, est.(mostra{j}), 'Color', cor.(mostra{j}), 'LineWidth', 2.6);
    lim = al(find(r >= 1 & al > 1, 1));  if isempty(lim), lim = NaN; end
    fprintf('%-20s: ganho maximo estavel %.2f (%.1f dB)\n', nome.(mostra{j}), lim, 20*log10(lim));
end
yline(1, 'k-', 'instável acima', 'LineWidth', 1.5, 'FontSize', 15);  set(gca, 'XScale', 'log');  xticks([0.25 0.5 1 2 4]);  ylim([0.7 1.2]);
xlabel('ganho real / ganho dos dados (erro de V_{dc})');  ylabel('raio espectral');  title('margem de ganho');
legend(cellfun(@(k) nome.(k), mostra, 'UniformOutput', false), 'Location', 'northwest', 'FontSize', 15);
nexttile;  hold on;  Ra = zeros(3, 4);
for j = 1:3, for a = 0:3, Ra(j, a+1) = malha_linear(C.(mostra{j}), P, atraso = a, completo = false).rho; end, end
b = bar(0:3, Ra');  for j = 1:3, b(j).FaceColor = cor.(mostra{j}); end
yline(1, 'k-', 'LineWidth', 1.5);  ylim([0.7 1.3]);  xlabel('amostras de atraso a mais (50 µs cada)');  ylabel('raio espectral');  title('margem de atraso');
disp('raio espectral x atraso extra (0..3):');  disp(Ra);
salva(fg, P, 'd06_margens.png');

% (e) compromisso: banda x margem x ruido
rs = logspace(-3.3, 0, 14);  fcs = logspace(log10(100), log10(1800), 14);
Dd = zeros(numel(rs), 4);  Dm = Dd;  Dp = zeros(numel(fcs), 4);
for j = 1:numel(rs)
    m = malha_linear(ganhos('deepc', u, y, P, r = rs(j)), P);  Dd(j, :) = [m.banda, m.mg, P.ruido*1e3*m.ruido_i, P.ruido*m.ruido_u];
    m = malha_linear(ganhos('oraculo', u, y, P, r = rs(j)), P);  Dm(j, :) = [m.banda, m.mg, P.ruido*1e3*m.ruido_i, P.ruido*m.ruido_u];
end
for j = 1:numel(fcs), m = malha_linear(pi_fc(fcs(j)), P);  Dp(j, :) = [m.banda, m.mg, P.ruido*1e3*m.ruido_i, P.ruido*m.ruido_u]; end
fg = figure('Position', [0 0 1750 600]);  tiledlayout(1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
rot = {'margem de ganho (disco) [dB]', 'ondulação da corrente pelo ruído [mA rms]', 'ondulação da tensão pelo ruído [V rms]'};
for q = 1:3
    nexttile;  hold on;
    plot(Dp(:, 1), Dp(:, q+1), '--', 'Color', P.cor.cinza, 'LineWidth', 2.6);
    plot(Dm(:, 1), Dm(:, q+1), '--', 'Color', P.cor.magenta, 'LineWidth', 2.6);
    plot(Dd(:, 1), Dd(:, q+1), '-', 'Color', P.cor.azul, 'LineWidth', 2.8);
    ponto = [T6(3, 4), P.ruido*1e3*T6(3, 6), P.ruido*T6(3, 7)];
    plot(L.deepc.banda, ponto(q), 'o', 'Color', P.cor.azul, 'MarkerFaceColor', 'w', 'MarkerSize', 12, 'LineWidth', 2.5, 'HandleVisibility', 'off');
    set(gca, 'XScale', 'log');  xlim([150 3000]);  xticks([200 500 1000 2000]);  xlabel('banda da malha fechada [Hz]');  ylabel(rot{q});
    if q == 1, legend({'PI (banda de projeto de 100 a 1800 Hz)', 'MPC com o modelo (r_u variando)', 'DeePC, dados reais (r_u variando)'}, 'Location', 'northeast', 'FontSize', 14); end
end
salva(fg, P, 'd06_compromisso.png');
save(fullfile(P.res, 'd06.mat'), 'T6', 'ks', 'Rho', 'fr', 'fl', 'Ra', 'Dd', 'Dm', 'Dp', 'rs', 'fcs');
