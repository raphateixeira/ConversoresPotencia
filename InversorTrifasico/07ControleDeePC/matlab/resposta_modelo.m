function y = resposta_modelo(Mo, u)
% RESPOSTA_MODELO  Resposta periodica, sem ruido, do modelo linear
%   y(k) = A1 y(k-1) + B1 u(k-1) + B2 u(k-2) (+ B3 u(k-3))   a uma entrada periodica u (2 x M).
%   Mo: struct com A1 e B (celula {B1, B2, ...}). Simula tres periodos e devolve o ultimo.
M = size(u, 2);  uu = [u u u];  y = zeros(2, 3*M);  nb = numel(Mo.B);
for k = nb+1:3*M
    y(:, k) = Mo.A1*y(:, k-1);
    for j = 1:nb, y(:, k) = y(:, k) + Mo.B{j}*uu(:, k-j); end
end
y = y(:, 2*M+1:end);
end
