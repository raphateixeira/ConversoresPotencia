function C = ganho_mpc(Fz, Ku, N, p, m, q, r)
% GANHO_MPC  Controle preditivo a partir de um preditor incremental dy_f = Fz z + Ku du_f.
%   Saidas previstas: y_f = 1 y(k) + T dy_f (T soma os incrementos).
%   Custo: sum_j ||y(k+j) - r(k+j)||^2 q + ||du(k+j-1)||^2 r.
%   Sem restricoes: du_f = G e0, e0 = r_f - 1 y(k) - T Fz z, e so o primeiro du e aplicado.
%   Resultado: du(k) = Ke (r - y(k)) - Kz z  (referencia constante no horizonte), ou, com a
%   referencia futura conhecida (previa), du(k) = G1 (r_f - 1 y(k)) - Kz z. Uma conta fixa.
%   Para o caso com restricoes guarda H e Theta'Q (problema quadratico por amostra).
T = kron(tril(ones(N)), eye(p));
Theta = T*Ku;  Q = q*eye(p*N);  Rm = r*eye(m*N);
H = Theta'*Q*Theta + Rm;
G = H \ (Theta'*Q);
C.G1 = G(1:m, :);                             % primeiro passo
C.um = kron(ones(N, 1), eye(p));
C.Ke = C.G1*C.um;                             % ganho do erro atual
C.Kz = C.G1*T*Fz;                             % ganho do passado (du e dy recentes)
C.TF = T*Fz;  C.H = H;  C.ThQ = Theta'*Q;  C.N = N;  C.m = m;
end
