function C = ganho_abs(u, y, Tini, N, q, r)
% GANHO_ABS  O mesmo controle preditivo por dados, mas com o preditor em VALORES ABSOLUTOS
%   (y_f = F z + Ku u_f, com u e y e nao du e dy). Serve so para mostrar por que a forma
%   incremental e usada: se a carga muda, este preditor erra um valor constante e sobra erro
%   em regime. Custo: q ||y_f - r_f||^2 + r ||du_f||^2 (mesmo peso no esforco).
M = size(u, 2);  c = @(k) mod(k - 1, M) + 1;
Zp = zeros(4*Tini, M);  Uf = zeros(2*N, M);  Yf = zeros(2*N, M);
for k = 1:M
    Zp(:, k) = [reshape(u(:, c(k-Tini:k-1)), [], 1); reshape(y(:, c(k-Tini+1:k)), [], 1)];
    Uf(:, k) = reshape(u(:, c(k:k+N-1)), [], 1);  Yf(:, k) = reshape(y(:, c(k+1:k+N)), [], 1);
end
W = [Zp; Uf];  K = (Yf*W') / (W*W');  F = K(:, 1:4*Tini);  Ku = K(:, 4*Tini+1:end);
D = kron(eye(N) - diag(ones(N-1, 1), -1), eye(2));  E = [eye(2); zeros(2*(N-1), 2)];
Hi = inv(q*(Ku'*Ku) + r*(D'*D));
Ga = Hi*(q*Ku');  Gb = Hi*(r*D'*E);
C.Ga = Ga(1:2, :);  C.Gb = Gb(1:2, :);  C.Fa = F;  C.N = N;  C.Tini = Tini;  C.tipo = 'mpcabs';
end
