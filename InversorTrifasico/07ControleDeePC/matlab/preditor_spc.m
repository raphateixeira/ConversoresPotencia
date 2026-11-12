function S = preditor_spc(u, y, Tini, N, lambda, opt)
% PREDITOR_SPC  Preditor por subespaco (SPC) direto dos dados, forma incremental:
%   dy_f = F zp + Ku du_f,  [F Ku] = Yf [Zp; Uf]^+  (minimos quadrados com regularizacao lambda)
%   Nenhum modelo e escolhido: F e Ku sao so uma "tabela" tirada das matrizes de Hankel.
%   opt.causal: cada passo futuro j usa so as entradas ate j (Ku triangular inferior por blocos),
%   o que tira parametros que so ajustariam ruido. opt.pinv: pseudo-inversa (dados sem ruido,
%   em que [Zp; Uf] tem linhas dependentes). opt.circular: ver JANELAS.
arguments
    u; y; Tini; N
    lambda = 0
    opt.causal = false
    opt.pinv = false
    opt.circular = true
end
[Zp, Uf, Yf] = janelas(u, y, Tini, N, opt.circular);
m = size(u, 1);  p = size(y, 1);  nz = size(Zp, 1);
if opt.pinv
    K = Yf*pinv([Zp; Uf], 1e-9*norm([Zp; Uf]));
elseif opt.causal
    K = zeros(p*N, nz + m*N);
    for j = 1:N
        W = [Zp; Uf(1:m*j, :)];  li = (j-1)*p + (1:p);
        K(li, 1:nz + m*j) = (Yf(li, :)*W') / (W*W' + lambda*eye(size(W, 1)));
    end
else
    W = [Zp; Uf];
    K = (Yf*W') / (W*W' + lambda*eye(size(W, 1)));
end
S.F = K(:, 1:nz);  S.Ku = K(:, nz+1:end);  S.Tini = Tini;  S.N = N;
end
