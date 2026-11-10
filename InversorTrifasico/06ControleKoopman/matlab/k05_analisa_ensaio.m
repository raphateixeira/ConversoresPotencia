%% k05_analisa_ensaio  Dados do firmware VSI06ControleKoopman (pasta ../dados)
%  Koopman01.csv  cenario 1: Dados3F = i_alfa, i_beta (media) | estado | ...  -> refaz o EDMD
%  Koopman02.csv  cenario 2: Koopman-FCS, media de 16 (idRef iqRef id iq vd vq iA iB)
%  Koopman03.csv  cenario 3: FCS com o modelo fisico, media de 16 (mesmo dia)
%  Koopman04.csv  cenario 4: Koopman-FCS, registro cru
%  Opcional: G.txt com os 12 valores de koopmanG copiados da Watch (confere o calculo da placa).
P = parametros();  D = fullfile(fileparts(fileparts(mfilename('fullpath'))), 'dados');
arq = @(n) fullfile(D, n);
if ~isfile(arq('Koopman01.csv'))
    fprintf('k05: sem dados do ensaio em %s (cenarios 1 a 4 do VSI06ControleKoopman)\n', D);
    return
end
X = le_dados3f(arq('Koopman01.csv'), 8);
i = X(:, 1:2)';  est = round(X(:, 3))';  s = P.V(:, est + 1);
M = edmd_periodico(i, s);  [R, L] = fisicos(M, P);
G = [M.A(1:2, :), M.B(1:2, :)];
fprintf('EDMD (MATLAB, dados da placa): R = %.2f ohm, L = %.2f mH\n', R, L*1e3);  disp(G);
if isfile(arq('G.txt'))
    Gp = reshape(readmatrix(arq('G.txt')), 6, 2)';
    fprintf('diferenca para o G calculado na placa: %.2e (max abs)\n', max(abs(Gp(:) - G(:))));
end
ref = referencias(P, 1);  reg = [301:690, 901:1190, 1301:1690, 1801:2040];
nomes = {'Koopman02.csv', 'Koopman-FCS (media 16)'; 'Koopman03.csv', 'FCS fisico (media 16)'; 'Koopman04.csv', 'Koopman-FCS (cru)'};
for m = 1:3
    if ~isfile(arq(nomes{m, 1})), continue; end
    Y = le_dados3f(arq(nomes{m, 1}), 8);
    e = ref(:, reg) - Y(reg, 3:4)';
    fprintf('%-24s erro medio d / q %+5.1f / %+5.1f mA, rms %.1f mA\n', nomes{m, 2}, 1e3*mean(e, 2), 1e3*sqrt(mean(sum(e.^2, 1))));
end
