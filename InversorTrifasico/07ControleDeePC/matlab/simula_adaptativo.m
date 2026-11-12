function S = simula_adaptativo(P, u0, y0, opt)
% SIMULA_ADAPTATIVO  SPC/DeePC que refaz os ganhos com os dados da propria malha fechada.
%   Guarda so as matrizes de Gram (G = soma de w w', Hy = soma de y_f w'), com esquecimento, a
%   partir dos dados iniciais (u0, y0). A cada 'refaz' amostras: K = Hy / G -> ganhos novos.
%   'dither': amplitude [V] de uma PRBS somada a tensao para manter a excitacao.
%   'troca': struct k, R, L (muda a carga). 'adapta' = false: ganhos fixos (referencia).
arguments
    P; u0; y0
    opt.periodos = 8
    opt.dither = 0.3
    opt.refaz = 200
    opt.memoria = 2000
    opt.adapta = true
    opt.troca = []
    opt.R = P.R
    opt.L = P.L
    opt.semente = 1
end
rng(opt.semente);  Ti = P.Tini;  N = P.Nh;  m = 2;  p = 2;  nz = Ti*(m + p);  nw = nz + m*N;
ref = referencias(P, opt.periodos);  M = size(ref, 2);  lam = 1 - 1/opt.memoria;
[Zp, Uf, Yf] = janelas(u0, y0, Ti, N);  W = [Zp; Uf];  G = W*W';  Hy = Yf*W';
C = lei(G, Hy, nz, N, P);
R = opt.R;  L = opt.L;  [Phi, Gam] = zoh(R, L, P);
i = [0; 0];  ul = [0; 0];  u = zeros(2, M);  y = zeros(2, M);  iv = zeros(2, M);  S.trocas = [];
dit = opt.dither*sign(randn(2, M));  dit = repelem(dit(:, 1:ceil(M/4)), 1, 4);  dit = dit(:, 1:M);
for k = 1:M
    if ~isempty(opt.troca) && k == opt.troca.k, R = opt.troca.R;  L = opt.troca.L;  [Phi, Gam] = zoh(R, L, P); end
    ym = round((i + P.ruido*randn(2, 1))/P.lsb)*P.lsb;  y(:, k) = ym;  iv(:, k) = i;
    if k <= Ti + 2
        v = [0; 0];
    else
        du = u(:, k-Ti:k-1) - u(:, k-Ti-1:k-2);  dy = y(:, k-Ti+1:k) - y(:, k-Ti:k-1);
        ul = ul + C.Ke*(ref(:, k) - ym) - C.Kz*[du(:); dy(:)];      % a lei acumula so a sua parte
        v = ul + dit(:, k);                                         % a excitacao entra por fora, sem acumular
    end
    if norm(v) > P.vmax, v = v*P.vmax/norm(v);  ul = v - dit(:, k); end
    u(:, k) = v;
    kd = k - N;                                   % janela mais nova ja completa: decisao em kd
    if opt.adapta && kd - Ti - 1 >= 1
        dU = diff(u(:, kd-Ti-1:k-1), 1, 2);  dY = diff(y(:, kd-Ti:k), 1, 2);     % du(kd-Ti..k-1), dy(kd-Ti+1..k)
        w = [reshape(dU(:, 1:Ti), [], 1); reshape(dY(:, 1:Ti), [], 1); reshape(dU(:, Ti+1:end), [], 1)];
        yf = reshape(dY(:, Ti+1:end), [], 1);
        G = lam*G + w*w';  Hy = lam*Hy + yf*w';
        if mod(k, opt.refaz) == 0, C = lei(G, Hy, nz, N, P);  S.trocas(end+1) = k; end
    end
    if k > 1, i = Phi*i + Gam*u(:, k-1); end
end
e = reshape(sum((ref - iv).^2, 1), P.N, []);  S.J = 1e3*sqrt(mean(e, 1));     % nota por periodo [mA]
S.iv = iv;  S.u = u;  S.ref = ref;  S.C = C;
end

function C = lei(G, Hy, nz, N, P)
K = Hy / (G + 1e-9*trace(G)/size(G, 1)*eye(size(G, 1)));
C = ganho_mpc(K(:, 1:nz), K(:, nz+1:end), N, 2, 2, P.q, P.ru);
end

function [Phi, Gam] = zoh(R, L, P)
A = [-R/L, P.w; -P.w, -R/L];  Phi = expm(A*P.Ts);  Gam = A \ ((Phi - eye(2))/L);
end
