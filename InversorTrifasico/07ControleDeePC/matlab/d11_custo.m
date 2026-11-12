%% d11_custo  Quanto custa: contas por amostra, calculo dos ganhos, memoria e precisao simples
P = parametros();  [u, y] = le_prbs(P);  warning('off', 'all');  m = 2;  p = 2;
fprintf('lei de controle por amostra (multiplicacoes e somas):\n');
for c = [2 10; 4 10; 6 10; 2 20]'
    Ti = c(1);  N = c(2);  nz = Ti*(m + p);
    fprintf('  Tini %d, N %2d: sem previa %3d; com previa %3d; memoria dos ganhos %d floats\n', Ti, N, m*p + m*nz, m*p*N + m*nz, m*p*N + m*nz);
end
Ti = P.Tini;  N = P.Nh;  nz = Ti*(m + p);  nw = nz + m*N;  ny = p*N;  T = P.N;
gram = nw*(nw + 1)/2 + ny*nw;
fprintf('ganhos na placa: Gram por coluna %d contas x %d colunas = %.2f milhoes; Cholesky %d x %d ~ %.0f mil; memoria das matrizes %d floats (os dados nao precisam ser guardados)\n', ...
    gram, T, gram*T/1e6, nw, nw, (nw^3/3 + 2*ny*nw^2 + (m*N)^3/3)/1e3, nw*nw + ny*nw);
% tempos no MATLAB (mediana)
tt = zeros(3, 30);
for k = 1:30
    tic;  ganhos('spc', u, y, P);  tt(1, k) = toc;  tic;  ganhos('deepc', u, y, P);  tt(2, k) = toc;  tic;  ganhos('arx', u, y, P);  tt(3, k) = toc;
end
fprintf('MATLAB neste computador: SPC %.1f ms, DeePC (SVD) %.1f ms, ARX indireto %.1f ms\n', 1e3*median(tt, 2));
% precisao simples: Gram + Cholesky em float de 32 bits, como seria na placa
[Zp, Uf, Yf] = janelas(u, y, Ti, N);  W = [Zp; Uf];
G = single(0)*zeros(nw, 'single');  Hy = zeros(ny, nw, 'single');
for k = 1:T, w = single(W(:, k));  G = G + w*w';  Hy = Hy + single(Yf(:, k))*w'; end
Rc = chol(G);  Ks = (Hy / Rc) / Rc';  Kd = (Yf*W') / (W*W');
Cs = ganho_mpc(double(Ks(:, 1:nz)), double(Ks(:, nz+1:end)), N, p, m, P.q, P.ru);  Cs.tipo = 'mpc';  Cs.Tini = Ti;
Cd = ganhos('spc', u, y, P);
fprintf('precisao simples: cond(W W'') = %.1e; erro relativo do preditor %.1e; dos ganhos %.1e; J simples %.3f x dupla %.3f mA\n', ...
    cond(W*W'), norm(double(Ks) - Kd, 'fro')/norm(Kd, 'fro'), norm([Cs.Ke Cs.Kz] - [Cd.Ke Cd.Kz], 'fro')/norm([Cd.Ke Cd.Kz], 'fro'), desempenho(Cs, P).J, desempenho(Cd, P).J);
% ganhos arredondados (float de 32 bits) e sensibilidade a erro nos ganhos
for e = [1e-3 1e-2 5e-2]
    Jr = zeros(1, 20);  for s = 1:20, rng(s);  Cx = Cd;  Cx.Kz = Cd.Kz.*(1 + e*randn(size(Cd.Kz)));  Cx.G1 = Cd.G1.*(1 + e*randn(size(Cd.G1)));  Cx.Ke = Cx.G1*Cx.um;  Jr(s) = desempenho(Cx, P).J; end
    fprintf('erro relativo de %.1f %% em cada ganho: J de %.2f a %.2f mA\n', 100*e, min(Jr), max(Jr));
end
