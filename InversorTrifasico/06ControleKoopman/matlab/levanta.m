function Z = levanta(x, u, k, nu, nx, nl)
% LEVANTA  Observaveis (dicionario) nos instantes k:
%   z = [x(k); x(k-1..k-nx); u(k-1..k-nu); monomios de grau 2 (nl >= 2) e 3 (nl >= 3) de x(k)].
%   Os monomios usam x/0,05 A (mesma ordem de grandeza dos outros observaveis).
Z = x(:, k);
for j = 1:nx, Z = [Z; x(:, k-j)]; end %#ok<AGROW>
for j = 1:nu, Z = [Z; u(:, k-j)]; end %#ok<AGROW>
a = x(1, k)/0.05;  b = x(2, k)/0.05;
if nl >= 2, Z = [Z; a.^2; a.*b; b.^2]; end
if nl >= 3, Z = [Z; a.^3; a.^2.*b; a.*b.^2; b.^3]; end
end
