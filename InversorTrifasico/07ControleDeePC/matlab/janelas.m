function [Zp, Uf, Yf, idx] = janelas(u, y, Tini, N, circular)
% JANELAS  Matrizes de Hankel dos dados em forma incremental (du, dy), uma coluna por instante k:
%   passado  Zp = [du(k-Tini..k-1); dy(k-Tini+1..k)]   (o que ja aconteceu quando se decide em k)
%   futuro   Uf = du(k..k+N-1),   Yf = dy(k+1..k+N)
%   circular = true (padrao): os dados sao um periodo de sinal periodico (media sincrona) e os
%   indices dao a volta. circular = false: registro comum, so as janelas que cabem inteiras.
if nargin < 5, circular = true; end
M = size(u, 2);  m = size(u, 1);  p = size(y, 1);
if circular
    du = u - circshift(u, 1, 2);  dy = y - circshift(y, 1, 2);
    c = @(k) mod(k - 1, M) + 1;  idx = 1:M;
else
    du = [zeros(m, 1), diff(u, 1, 2)];  dy = [zeros(p, 1), diff(y, 1, 2)];
    c = @(k) k;  idx = Tini + 2 : M - N;
end
J = numel(idx);
Zp = zeros(m*Tini + p*Tini, J);  Uf = zeros(m*N, J);  Yf = zeros(p*N, J);
for j = 1:J
    k = idx(j);
    Zp(:, j) = [reshape(du(:, c(k-Tini:k-1)), [], 1); reshape(dy(:, c(k-Tini+1:k)), [], 1)];
    Uf(:, j) = reshape(du(:, c(k:k+N-1)), [], 1);
    Yf(:, j) = reshape(dy(:, c(k+1:k+N)), [], 1);
end
end
