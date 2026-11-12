function C = ganho_deepc(u, y, Tini, N, q, r, lg, lini, circular)
% GANHO_DEEPC  DeePC (forma incremental, sem restricoes) com regularizacao:
%   min_g  sum ||y(k+j) - r||^2 q + ||du_f||^2 r + lg ||g||^2 + lini ||Zp g - z||^2
%   com du_f = Uf g, dy_f = Yf g: g escolhe a combinacao das trajetorias gravadas.
%   A solucao otima fica no espaco das linhas dos dados (o resto de g so aumenta ||g||):
%   g = V c, com V da SVD economica de [Zp; Uf; Yf]. O problema em c e pequeno e bem condicionado.
%   A solucao e linear em (r - y(k)) e em z: calcula-se uma vez e vira matriz.
if nargin < 9, circular = true; end
[Zp, Uf, Yf] = janelas(u, y, Tini, N, circular);
p = size(y, 1);  m = size(u, 1);
[~, ~, V] = svd([Zp; Uf; Yf], 'econ');           % colunas de V: base do espaco das linhas
Zr = Zp*V;  Ur = Uf*V;  Yr = Yf*V;  nr = size(V, 2);
T = kron(tril(ones(N)), eye(p));  A = T*Yr;
H = q*(A'*A) + r*(Ur'*Ur) + lg*eye(nr) + lini*(Zr'*Zr);
U1 = Ur(1:m, :);                                % primeiro incremento de entrada: du(k) = U1 c
um = kron(ones(N, 1), eye(p));
C.Ke = U1*(H \ (q*A'*um));
C.Kz = -U1*(H \ (lini*Zr'));                    % du(k) = Ke e - Kz z  (mesma convencao de ganho_mpc)
C.G1 = U1*(H \ (q*A'));  C.um = um;               % (previa: du(k) = G1 (r_f - 1 y(k)) - Kz z)
C.N = N;  C.nr = nr;
end
