%% k03_malha_fechada  De onde tirar os dados e o Koopman-FCS em malha fechada (simulacao)
%  Planta "verdadeira": carga da bancada (25,3 ohm; 9,8 mH), ruido de 8,5 mA e ADC de 7,32 mA,
%  mesma temporizacao do firmware. Compara os modelos do FCS e o ensaio de identificacao proposto.
P = parametros();  load(P.mat, 'Mfis', 'Mnom', 'Mcru', 'Mmed', 'tab');
N = P.N;  NP = 17;                                       % 1 periodo descartado + 16 na media

% 1. Ensaio de identificacao proposto: vetores pseudoaleatorios periodicos, em malha aberta
est1 = sequencia_vetores(N, 2);
Sid = simula_fcs([], P, estados = repmat(est1, 1, NP), ref = zeros(2, NP*N));
im = mean(reshape(Sid.i(:, N+1:end), 2, N, NP - 1), 3);  % media sincrona em alfa-beta
s1 = P.V(:, est1 + 1);
Mid = edmd_periodico(im, s1);                            % EDMD da media (proposto)
Mid1 = edmd_periodico(Sid.i(:, end-N+1:end), s1);        % um periodo so, sem media
fprintf('ensaio de identificacao simulado: |i| max %.2f A, rms %.0f mA\n', max(abs(Sid.iv(:))), 1e3*rms(Sid.iv(:)));

% 2. EDMD com dados de malha fechada simulados (como os ensaios reais)
Scl = simula_fcs(preditor_linear(Mfis, P), P, periodos = 2);
Mcl = edmd_fcs(Scl.i(:, N+1:end), Scl.s(:, N+1:end));

fontes = {'simulado: malha aberta periódica, média de 16', Mid
          'simulado: malha aberta, 1 período', Mid1
          'simulado: malha fechada, cru', Mcl
          'real: malha fechada, cru', Mcru
          'real: malha fechada, média de 16', Mmed};
RL = zeros(size(fontes, 1), 2);
fprintf('fonte dos dados | R [ohm], L [mH]\n');
for m = 1:size(fontes, 1)
    [RL(m, 1), l] = fisicos(fontes{m, 2}, P);  RL(m, 2) = l*1e3;
    fprintf('  %-48s %5.2f  %5.2f\n', fontes{m, 1}, RL(m, :));
end

% 3. Malha fechada: FCS com cada modelo (media de 16 periodos, como no ensaio)
casos = {'físico nominal (25 Ω; 10 mH)', Mnom, 'meio'
         'físico da bancada (25,3 Ω; 9,8 mH)', Mfis, 'meio'
         'EDMD real, malha fechada (L com viés)', Mmed, 'meio'
         'EDMD do ensaio proposto (simulado)', Mid, 'meio'
         'EDMD do ensaio proposto, custo em k+2', Mid, 'k2'};
fprintf('FCS com o modelo | erro medio d / q [mA] | rms [mA] | fsw [Hz]\n');
R = cell(size(casos, 1), 1);
for m = 1:size(casos, 1)
    hz = 1.5 + 0.5*strcmp(casos{m, 3}, 'k2');
    S = simula_fcs(preditor_linear(casos{m, 2}, P, casos{m, 3}), P, periodos = NP, horizonte = hz);
    R{m} = S;  q = metricas(S, P);
    fprintf('  %-40s %+5.1f / %+5.1f | %5.1f | %4.0f\n', casos{m, 1}, q.erro, q.rms, q.fsw);
end
save(P.mat, 'Mid', '-append');

% Figura 1: o ensaio de identificacao e L por fonte de dados
f = figure('Position', [0 0 1700 660]);  tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
nexttile;  k = 1:160;  t = (k - 1)*P.Ts*1e3;
plot(t, Sid.i(1, end-N+k)*1e3, '.', 'Color', P.cor.cinza, 'MarkerSize', 12);  hold on;
plot(t, im(1, k)*1e3, '-', 'Color', P.cor.azul, 'LineWidth', 2.5);
stairs(t, 100*s1(1, k) - 420, 'Color', P.cor.verm, 'LineWidth', 1.8);
xlabel('tempo [ms]');  ylabel('i_\alpha [mA]');  ylim([-520 420]);
legend({'um período (com ruído)', 'média de 16 períodos', 'vetor aplicado s_\alpha (escala à parte)'}, 'Location', 'northoutside');
nexttile;
nomes = {'sim.: aberta, média 16', 'sim.: aberta, 1 período', 'sim.: fechada, cru', 'real: fechada, cru', ...
         'real: fechada, média 16', 'real: RLS em linha', 'real: IV por predição', 'real: PRBS com PWM'};
Lb = [RL(:, 2); 9.0; 10.0; 9.74];
b = barh(Lb, 'FaceColor', 'flat');
b.CData = [repmat(P.cor.cinza, 3, 1); repmat(P.cor.azul, 5, 1)];  b.CData(1, :) = P.cor.verde;
set(gca, 'YTick', 1:numel(Lb), 'YTickLabel', nomes, 'YDir', 'reverse', 'XLim', [7 10.6]);
xline(P.L*1e3, 'k:', 'LineWidth', 2.5);  xlabel('L equivalente [mH]');
salva(f, P, 'k03_identificacao.png');

% Figura 2: resposta media de 16 periodos, Koopman-FCS simulado x FCS real (ControleFCS02)
Xr = le_dados3f(P.dados.fcs02, 8);
S = R{4};  idm = mean(reshape(S.idq(:, N+1:end), 2, N, NP - 1), 3);
f = figure('Position', [0 0 1700 660]);  tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
tt = (0:N-1)*P.Ts*1e3;  ref = referencias(P, 1);
nexttile;  plot(tt, Xr(:, 3)*1e3, 'Color', P.cor.cinza, 'LineWidth', 1.4);  hold on;
plot(tt, idm(1, :)*1e3, 'Color', P.cor.azul, 'LineWidth', 1.6);
plot(tt, Xr(:, 4)*1e3, 'Color', P.cor.cinza, 'LineWidth', 1.4);
plot(tt, idm(2, :)*1e3, 'Color', P.cor.verm, 'LineWidth', 1.6);
stairs(tt, ref'*1e3, ':', 'Color', P.cor.amar, 'LineWidth', 2);
xlabel('tempo [ms]');  ylabel('corrente [mA]');  xlim([0 102]);
legend({'FCS real (modelo físico)', 'i_d  Koopman-FCS (simulado)', '', 'i_q  Koopman-FCS (simulado)', 'referência'}, 'Location', 'northoutside', 'NumColumns', 2);
nexttile;  j = 181:281;  t2 = (j - 201)*P.Ts*1e3;
plot(t2, Xr(j, 3)*1e3, 'o', 'Color', P.cor.cinza, 'MarkerSize', 7, 'LineWidth', 1.5);  hold on;
plot(t2, idm(1, j)*1e3, '-', 'Color', P.cor.azul, 'LineWidth', 2.5);
stairs(t2, ref(1, j)*1e3, ':', 'Color', P.cor.amar, 'LineWidth', 2);
xlabel('tempo desde o degrau [ms]');  ylabel('i_d [mA]');
legend({'FCS real', 'Koopman-FCS (simulado)', 'referência'}, 'Location', 'southeast');
salva(f, P, 'k03_malha_fechada.png');
