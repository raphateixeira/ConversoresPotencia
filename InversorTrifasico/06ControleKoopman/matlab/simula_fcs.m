function S = simula_fcs(pred2, P, opt)
% SIMULA_FCS  FCS-MPC de corrente com a temporizacao do firmware (corrente lida no zero k,
%   vetor aplicado do topo k+1/2 ao topo k+3/2), ruido de medida e resolucao do ADC.
%   pred2(im, sprev) devolve as correntes previstas no instante do custo (k + horizonte)
%   para os 8 estados (2 x 8).
arguments
    pred2
    P
    opt.periodos = 3
    opt.ruido = P.ruido
    opt.semente = 0
    opt.R = P.R                 % planta "verdadeira"
    opt.L = P.L
    opt.Isat = inf              % indutor saturavel: L(i) = L/(1 + (|i|/Isat)^2)
    opt.estados = []            % malha aberta: sequencia de estados 0..7 (sem decisao)
    opt.eps = 0                 % fracao de decisoes trocadas por um vetor aleatorio
    opt.ref = []                % referencia dq, 2 x M (padrao: perfil dos ensaios)
    opt.horizonte = 1.5         % instante do custo, em amostras a frente de k (1,5 ou 2)
end
rng(opt.semente);
if isempty(opt.ref), ref = referencias(P, opt.periodos); else, ref = opt.ref; end
M = size(ref, 2);  SUB = 20;  h = P.Ts/SUB;
af = exp(-opt.R*h/opt.L);  bf = (1 - af)/opt.R;
nb = [0 1 1 2 1 2 2 3];
i = [0; 0];  sprev = [0; 0];  est = 0;  com = 0;
S.i = zeros(2, M);  S.iv = zeros(2, M);  S.s = zeros(2, M);  S.est = zeros(1, M);
S.idq = zeros(2, M);  S.idqv = zeros(2, M);  S.vdq = zeros(2, M);  S.ref = ref;
for k = 1:M
    th = P.w*(k - 1)*P.Ts;  c = cos(th);  s = sin(th);
    im = i + opt.ruido*randn(2, 1);
    if opt.ruido > 0, im = round(im/P.lsb)*P.lsb; end
    S.i(:, k) = im;  S.iv(:, k) = i;
    S.idq(:, k) = [c s; -s c]*im;  S.idqv(:, k) = [c s; -s c]*i;
    if isempty(opt.estados)
        t2 = th + opt.horizonte*P.w*P.Ts;
        r = [cos(t2) -sin(t2); sin(t2) cos(t2)]*ref(:, k);
        g = sum((r - pred2(im, sprev)).^2, 1) + 1e-9*nb(bitxor(0:7, est) + 1);
        [~, m] = min(g);  novo = m - 1;
        if rand < opt.eps, novo = randi(8) - 1; end
    else
        novo = opt.estados(k);
    end
    com = com + nb(bitxor(novo, est) + 1);  est = novo;  snovo = P.V(:, est + 1);
    S.est(k) = est;  S.s(:, k) = snovo;
    t1 = th + P.w*P.Ts;
    S.vdq(:, k) = [cos(t1) sin(t1); -sin(t1) cos(t1)]*snovo*P.Vdc;
    for j = 1:SUB                                    % meio periodo com s(k-1), meio com s(k)
        if j <= SUB/2, v = P.Vdc*sprev; else, v = P.Vdc*snovo; end
        if isinf(opt.Isat)
            i = af*i + bf*v;
        else
            i = i + h*(v - opt.R*i)*(1 + (norm(i)/opt.Isat)^2)/opt.L;
        end
    end
    sprev = snovo;
end
S.fsw = com/6/(M*P.Ts);
end
