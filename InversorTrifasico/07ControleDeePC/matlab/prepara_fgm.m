function C = prepara_fgm(C, iteracoes)
% PREPARA_FGM  Matrizes para tratar o limite de tensao DENTRO da otimizacao com poucas contas:
%   variaveis = tensoes futuras u_f (N pares d, q); du_f = Dm u_f - Em u(k-1);
%   custo 1/2 du' H du - b' du;  restricao: cada par dentro do circulo |v| <= vmax (projecao simples).
%   Gradiente rapido projetado (Nesterov, passo 1/Lf, momento beta constante) com partida quente.
N = C.N;  D = eye(N) - diag(ones(N-1, 1), -1);
C.Dm = kron(D, eye(2));  C.Em = [eye(2); zeros(2*(N-1), 2)];
C.Hu = C.Dm'*C.H*C.Dm;  C.Hu = (C.Hu + C.Hu')/2;
ev = eig(C.Hu);  C.Lf = max(ev);  mu = min(ev);
C.beta = (sqrt(C.Lf) - sqrt(mu))/(sqrt(C.Lf) + sqrt(mu));  C.cond = C.Lf/mu;
C.fgm = iteracoes;
end
