function [A, B] = edmd(Z, U, Zp)
% EDMD  Extended Dynamic Mode Decomposition com controle (minimos quadrados).
%   Zp ~ A*Z + B*U, com as colunas de Z, U e Zp = amostras dos observaveis,
%   das entradas e dos observaveis um passo adiante.
G = Zp / [Z; U];
n = size(Z, 1);
A = G(:, 1:n);  B = G(:, n+1:end);
end
