function f = preditor_linear(M, P, custo)
% PREDITOR_LINEAR  Predicao do FCS com um modelo levantado linear, para os 8 vetores (2 x 8).
%   'meio' (padrao): i(k+3/2) ~ media das previsoes de k+1 e k+2 (fim do intervalo do vetor);
%                    usar com horizonte = 1,5 em simula_fcs.
%   'k2':            i(k+2) com o vetor mantido (algoritmo do VSI05); horizonte = 2.
%   i(k+1) = C A z + C B s;  i(k+2) = C A^2 z + C (A B + B) s.
if nargin < 3, custo = 'meio'; end
n = size(M.A, 1);  C = [eye(2), zeros(2, n - 2)];
P1 = C*M.A;  M1 = C*M.B;  P2 = C*M.A*M.A;  M2 = C*(M.A*M.B + M.B);
if strcmp(custo, 'k2')
    f = @(im, sprev) P2*[im; sprev] + M2*P.V;
else
    Pm = (P1 + P2)/2;  Mm = (M1 + M2)/2;
    f = @(im, sprev) Pm*[im; sprev] + Mm*P.V;
end
end
