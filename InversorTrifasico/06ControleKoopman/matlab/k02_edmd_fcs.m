%% k02_edmd_fcs  EDMD com os dados reais do FCS (alfa-beta, sem modulador)
%  Dicionario: z = [i(k); s(k-1)], entrada s(k) = vetor do inversor (normalizado por Vdc).
%  Treinos: (a) registro cru em malha fechada (ControleFCS01);
%           (b) media sincrona de 16 periodos, sinais complexos em dq (ControleFCS02).
%  Validacao em outro ensaio, outro dia de bancada (DadosRLS02, cru).
P = parametros();
Dt = prepara_fcs(P.dados.fcs01, P);                    % treino (cru)
Dv = prepara_fcs(P.dados.rls02, P);                    % validacao (cru, outro ensaio)
Xm = le_dados3f(P.dados.fcs02, 8);                     % media de 16 periodos (dq)

Mfis = modelo_fisico(P.R, P.L, P);
Mnom = modelo_fisico(P.Rnom, P.Lnom, P);
Mcru = edmd_fcs(Dt.i, Dt.s);
[Mmed, c, fHz] = edmd_dq(Xm(:, 3:4)', Xm(:, 5:6)', P);

% dicionario com termos cubicos (|i|^2 i), para conferir a linearidade
Mcub = edmd_cubico(Dt.i, Dt.s);

modelos = {'físico nominal (25 Ω; 10 mH)', Mnom; 'físico da bancada (25,3 Ω; 9,8 mH)', Mfis
           'EDMD, registro cru', Mcru; 'EDMD, média de 16 períodos', Mmed};
fprintf('modelo | R, L equivalentes | erro de predicao na validacao: 1 passo, 10 passos [mA rms]\n');
tab = zeros(size(modelos, 1), 4);
for m = 1:size(modelos, 1)
    M = modelos{m, 2};  [R, L] = fisicos(M, P);
    e1 = erro_passos(M, Dv, 1);  e10 = erro_passos(M, Dv, 10);
    tab(m, :) = [R, L*1e3, e1, e10];
    fprintf('  %-36s %5.1f ohm, %5.2f mH | %5.2f, %5.2f\n', modelos{m, 1}, R, L*1e3, e1, e10);
end
fprintf('  EDMD cubico (|i|^2 i): 1 passo %.2f mA rms (linear: %.2f)\n', erro_cubico(Mcub, Dv), tab(3, 3));
fprintf('media de 16: c1 = %.4f%+.4fj; frequencia do referencial pelos dados = %.1f Hz\n', real(c(1)), imag(c(1)), fHz);
disp('A (EDMD, media) ='); disp(Mmed.A(1:2, :));  disp('B ='); disp(Mmed.B(1:2, :));
disp('A (EDMD, cru) =');   disp(Mcru.A(1:2, :));  disp('B ='); disp(Mcru.B(1:2, :));
save(P.mat, 'Mfis', 'Mnom', 'Mcru', 'Mmed', 'tab');

% Figura: predicao de 10 passos na validacao (trecho com o degrau de id)
h = 10;  M = Mmed;  n = size(M.A, 1);
k0 = 190:260;  ih = nan(2, numel(k0));
for q = 1:numel(k0)
    z = [Dv.i(:, k0(q)); Dv.s(:, k0(q) - 1)];
    for j = 0:h - 1, z = M.A*z + M.B*Dv.s(:, k0(q) + j); end
    ih(:, q) = z(1:2);
end
t = (k0 + h - 200)*P.Ts*1e3;
f = figure('Position', [0 0 1600 620]);  tl = tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
nomes = {'i_\alpha', 'i_\beta'};  cores = {P.cor.azul, P.cor.verm};
for e = 1:2
    nexttile;  plot(t, Dv.i(e, k0 + h)*1e3, 'o', 'Color', P.cor.cinza, 'MarkerSize', 7, 'LineWidth', 1.5);  hold on;
    plot(t, ih(e, :)*1e3, '-', 'Color', cores{e}, 'LineWidth', 2.5);
    xlabel('tempo desde o degrau [ms]');  ylabel([nomes{e} ' [mA]']);
    legend({'medida (outro ensaio)', 'previsão de 10 passos (0,5 ms)'}, 'Location', 'northoutside');
end
salva(f, P, 'k02_predicao.png');

function e = erro_passos(M, D, h)
% erro rms da predicao de h passos, com as entradas reais, sobre o registro inteiro [mA]
N = size(D.i, 2);  k0 = 2:N - h;  n = size(M.A, 1);
Z = [D.i(:, k0); D.s(:, k0 - 1)];
for j = 0:h - 1, Z = M.A*Z + M.B*D.s(:, k0 + j); end
e = sqrt(mean(sum((D.i(:, k0 + h) - Z(1:2, :)).^2, 1)))*1e3;
end

function M = edmd_cubico(i, s)
k = 2:size(i, 2) - 1;  q = sum(i(:, k).^2, 1)/0.04;       % |i|^2 em unidades de (0,2 A)^2
G = i(:, k + 1) / [i(:, k); q.*i(:, k); s(:, k - 1); s(:, k)];
M.G = G;
end

function e = erro_cubico(M, D)
k = 2:size(D.i, 2) - 1;  q = sum(D.i(:, k).^2, 1)/0.04;
ih = M.G*[D.i(:, k); q.*D.i(:, k); D.s(:, k - 1); D.s(:, k)];
e = sqrt(mean(sum((D.i(:, k + 1) - ih).^2, 1)))*1e3;
end
