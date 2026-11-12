function S = simula_dq(ctrl, P, opt)
% SIMULA_DQ  Inversor com carga RL e a temporizacao da placa: a tensao calculada em k vale de k+1
%   a k+2 (registrador de sombra), a corrente e lida no zero do contador com ruido (8,5 mA por
%   eixo) e resolucao do ADC; |v| <= 0,45 Vdc.
%   ctrl.tipo:
%     'mpc'     du(k) = G1 (r_f - 1 y(k)) - Kz z  (Tini; .previa = usa a referencia futura;
%               .qp = quadprog com octogono; .fgm = n iteracoes de gradiente rapido projetado)
%     'mpcabs'  preditor em valores absolutos (sem a forma incremental): ver GANHO_ABS
%     'pi'      kp, ki, desacopla, L (anti-windup: integra so sem saturar)
%     'ma'      malha aberta com a sequencia ctrl.u (2 x M): ensaios de identificacao
%   Opcoes da planta:
%     planta   'media' (modelo medio, ZOH exato em dq) | 'pwm' (chaveada: portadora triangular,
%              tres bracos, tempo morto tm, tensao constante em abc no periodo, corrente no zero)
%     R, L     carga;  troca = struct('k', k0, 'R', R2, 'L', L2) muda a carga na amostra k0
%     alfa     ganho da tensao aplicada (Vdc real / Vdc usado no calculo); escalar ou 1 x M
%     atraso   amostras a mais de atraso;  w  frequencia do referencial [rad/s]
%     dv       tensao de perturbacao em dq somada na carga, 2 x M [V]
arguments
    ctrl
    P
    opt.periodos = 3
    opt.ruido = P.ruido
    opt.semente = 1
    opt.R = P.R
    opt.L = P.L
    opt.ref = []
    opt.alfa = 1
    opt.atraso = 0
    opt.w = P.w
    opt.dv = []
    opt.planta = 'media'
    opt.tm = 100e-9
    opt.troca = []
    opt.limita = true
    opt.quantiza = true
end
rng(opt.semente);
ma = strcmp(ctrl.tipo, 'ma');
if ma, ref = zeros(2, size(ctrl.u, 2)); elseif isempty(opt.ref), ref = referencias(P, opt.periodos); else, ref = opt.ref; end
M = size(ref, 2);
refx = [ref, repmat(ref(:, end), 1, 64)];      % referencia futura (para a previa)
if ~isfield(ctrl, 'previa'), ctrl.previa = false; end
if ~isfield(ctrl, 'qp'), ctrl.qp = false; end
if ~isfield(ctrl, 'fgm'), ctrl.fgm = 0; end
if ctrl.qp                                     % octogono inscrito no circulo |v| <= vmax
    ang = (0:7)*pi/4;  Pol = [cos(ang') sin(ang')];  bpol = P.vmax*cos(pi/8)*ones(8, 1);
    Sm = kron(tril(ones(ctrl.N)), eye(2));     % u(k+j) = u(k-1) + soma dos du
    Aq = kron(eye(ctrl.N), Pol)*Sm;
    oq = optimoptions('quadprog', 'Display', 'off');
    H2 = (ctrl.H + ctrl.H')/2;
end
if ctrl.fgm > 0, uf = zeros(2*ctrl.N, 1); end
dv = opt.dv;  if isempty(dv), dv = zeros(2, M); end
R = opt.R;  L = opt.L;  [Phi, Gam] = zoh(R, L, opt.w, P.Ts);
pwm = strcmp(opt.planta, 'pwm');
rot = @(th) [cos(th) -sin(th); sin(th) cos(th)];           % dq -> alfa-beta
i = zeros(2, 1);  iab = zeros(2, 1);
u = zeros(2, M);  y = zeros(2, M);  iv = zeros(2, M);  integ = [0; 0];  sat = 0;  nit = 0;
if any(strcmp(ctrl.tipo, {'mpc', 'mpcabs'})), Tini = ctrl.Tini; else, Tini = 1; end
nd = 1 + opt.atraso;
for k = 1:M
    if ~isempty(opt.troca) && k == opt.troca.k
        R = opt.troca.R;  L = opt.troca.L;  [Phi, Gam] = zoh(R, L, opt.w, P.Ts);
    end
    th = opt.w*(k - 1)*P.Ts;
    if pwm, i = rot(th)'*iab; end
    % medida (no zero do contador)
    ym = i + opt.ruido*randn(2, 1);
    if opt.ruido > 0 && opt.quantiza, ym = round(ym/P.lsb)*P.lsb; end
    y(:, k) = ym;  iv(:, k) = i;
    % controle
    if ma
        v = ctrl.u(:, k);
    elseif k <= Tini + 2
        v = [0; 0];
    elseif strcmp(ctrl.tipo, 'mpc')
        du = u(:, k-Tini:k-1) - u(:, k-Tini-1:k-2);
        dy = y(:, k-Tini+1:k) - y(:, k-Tini:k-1);
        z = [du(:); dy(:)];
        if ctrl.previa
            rf = reshape(refx(:, k+1:k+ctrl.N), [], 1);    % y(k+1..k+N) contra r(k+1..k+N)
        else
            rf = repmat(ref(:, k), ctrl.N, 1);
        end
        if ctrl.qp
            e0 = rf - ctrl.um*ym - ctrl.TF*z;
            x = quadprog(H2, -ctrl.ThQ*e0, Aq, repmat(bpol, ctrl.N, 1) - kron(ones(ctrl.N, 1), Pol)*u(:, k-1), ...
                         [], [], [], [], [], oq);
            if isempty(x), x = zeros(2*ctrl.N, 1); end
            v = u(:, k-1) + x(1:2);
        elseif ctrl.fgm > 0                                 % tensoes futuras dentro do circulo |v| <= vmax
            b = ctrl.ThQ*(rf - ctrl.um*ym - ctrl.TF*z);
            g0 = ctrl.Dm'*(ctrl.H*(ctrl.Em*u(:, k-1)) + b);  % parte fixa do gradiente (com sinal trocado)
            uf = [uf(3:end); uf(end-1:end)];  ua = uf;      % partida quente: solucao anterior deslocada
            for it = 1:ctrl.fgm
                w = uf + ctrl.beta*(uf - ua);  ua = uf;
                uf = projeta(w - (ctrl.Hu*w - g0)/ctrl.Lf, P.vmax);
            end
            nit = nit + ctrl.fgm;
            v = uf(1:2);
        else
            v = u(:, k-1) + ctrl.G1*(rf - ctrl.um*ym) - ctrl.Kz*z;   % = G1 e0 (Kz = G1 T Fz)
        end
    elseif strcmp(ctrl.tipo, 'mpcabs')
        ua_ = u(:, k-Tini:k-1);  ya_ = y(:, k-Tini+1:k);
        rf = repmat(ref(:, k), ctrl.N, 1);
        v = ctrl.Ga*(rf - ctrl.Fa*[ua_(:); ya_(:)]) + ctrl.Gb*u(:, k-1);
    else
        e = ref(:, k) - ym;
        nova = integ + ctrl.ki*P.Ts*e;
        v = ctrl.kp*e + nova;
        if ctrl.desacopla, v = v + opt.w*ctrl.L*[-ym(2); ym(1)]; end
    end
    if opt.limita && norm(v) > P.vmax          % limite da modulacao (mesma direcao)
        v = v*P.vmax/norm(v);  sat = sat + 1;
    elseif strcmp(ctrl.tipo, 'pi') && k > Tini + 2
        integ = nova;                          % anti-windup: integra so sem saturar
    end
    u(:, k) = v;
    % planta: em [k, k+1] vale a tensao calculada em k - nd
    al = opt.alfa(min(k, end));  kc = k - nd;
    if kc >= 1, vap = u(:, kc); else, vap = [0; 0]; end
    if pwm
        thc = opt.w*(kc - 1)*P.Ts;             % a inversa de Park usa o angulo do instante do calculo
        iab = passo_pwm(iab, rot(thc)*vap, rot(th)*dv(:, k), P, R, L, al, opt.tm);
    else
        i = Phi*i + Gam*(al*vap + dv(:, k));
    end
end
S.y = y;  S.iv = iv;  S.u = u;  S.ref = ref;  S.sat = sat;  S.nit = nit;
end

function [Phi, Gam] = zoh(R, L, w, Ts)
A = [-R/L, w; -w, -R/L];  Phi = expm(A*Ts);  Gam = A \ ((Phi - eye(2))/L);
end

function x = projeta(x, vmax)
% Projecao de cada tensao futura (par d, q) no circulo de raio vmax.
X = reshape(x, 2, []);  n = max(vecnorm(X)/vmax, 1);  x = reshape(X./n, [], 1);
end

function iab = passo_pwm(iab, vab, eab, P, R, L, al, tm)
% Um periodo de PWM (zero a zero do contador) com os tres bracos chaveando. Saida A alta enquanto
% contador < CMPA: cada braco comeca ligado ao +, desce em d Ts/2 e volta a subir em Ts - d Ts/2.
% Tempo morto: com corrente saindo do braco (i > 0) a subida atrasa tm; com i < 0 a descida atrasa.
Ci = [1 0; -1/2 sqrt(3)/2; -1/2 -sqrt(3)/2];               % alfa-beta -> abc
Cd = (2/3)*[1 -1/2 -1/2; 0 sqrt(3)/2 -sqrt(3)/2];          % abc -> alfa-beta
d = min(max(0.5 + Ci*vab/P.Vdc, 0.05), 0.95);  iabc = Ci*iab;  Ts = P.Ts;
tt = [d*Ts/2 + tm*(iabc < -2e-3); Ts - d*Ts/2 + tm*(iabc > 2e-3)];
ev = [0; 0; 0; 1; 1; 1];  fase = [1; 2; 3; 1; 2; 3];
[tt, o] = sort(tt);  ev = ev(o);  fase = fase(o);
Sx = [1; 1; 1];  t0 = 0;
for j = 1:7
    if j <= 6, t1 = tt(j); else, t1 = Ts; end
    tau = t1 - t0;
    if tau > 0
        e = exp(-tau*R/L);
        iab = iab*e + (Cd*(al*P.Vdc*Sx) + eab)/R*(1 - e);
    end
    if j <= 6, Sx(fase(j)) = ev(j); end
    t0 = t1;
end
end
