function M = malha_linear(ctrl, P, opt)
% MALHA_LINEAR  A malha fechada como sistema linear (sem ruido nem saturacao), para analisar a lei
%   de controle com as ferramentas classicas. Vale para 'mpc' (referencia constante no horizonte)
%   e 'pi'. Planta: i(k+1) = Phi i(k) + Gam (alfa u(k-nd) + dv(k)), nd = 1 + atraso.
%   Entradas do sistema M.sys: r (2), dv (2, perturbacao de tensao), n (2, ruido de medida).
%   Saidas: i (2, corrente verdadeira), u (2, comando), w (2, tensao aplicada = alfa u(k-nd)).
%   Tambem devolve: rho (raio espectral), Ms e Mt (picos de S e T na entrada da planta), margem
%   de disco (ganho e fase simultaneos nas duas entradas), banda r -> i e ganhos de ruido (H2).
arguments
    ctrl
    P
    opt.R = P.R
    opt.L = P.L
    opt.alfa = 1
    opt.atraso = 0
    opt.w = P.w
    opt.completo = true
end
A = [-opt.R/opt.L, opt.w; -opt.w, -opt.R/opt.L];
Phi = expm(A*P.Ts);  Gam = A \ ((Phi - eye(2))/opt.L);
nd = 1 + opt.atraso;  I2 = eye(2);
if strcmp(ctrl.tipo, 'mpc')
    Ti = ctrl.Tini;  nU = max(Ti + 1, nd);
    % pilhas: Up = [u(k-1); ...; u(k-nU)],  Yp = [y(k-1); ...; y(k-Ti)]
    DU = zeros(2*Ti, 2*nU);  DYp = zeros(2*Ti, 2*Ti);  DY0 = zeros(2*Ti, 2);
    for idx = 1:Ti
        li = 2*idx - 1 : 2*idx;
        j = Ti + 1 - idx;                       % du(k-j) = u(k-j) - u(k-j-1)
        DU(li, 2*j-1:2*j) = I2;  DU(li, 2*j+1:2*j+2) = -I2;
        j = Ti - idx;                           % dy(k-j) = y(k-j) - y(k-j-1)
        if j == 0, DY0(li, :) = I2; else, DYp(li, 2*j-1:2*j) = I2; end
        DYp(li, 2*j+1:2*j+2) = -I2;
    end
    Kzu = ctrl.Kz(:, 1:2*Ti);  Kzy = ctrl.Kz(:, 2*Ti+1:end);
    Fu = [I2, zeros(2, 2*(nU-1))] - Kzu*DU;  Fy = -Kzy*DYp;  Fr = ctrl.Ke;  F0 = -ctrl.Ke - Kzy*DY0;
    nx = 2 + 2*nU + 2*Ti;  ii = 1:2;  iu = 2 + (1:2*nU);  iy = 2 + 2*nU + (1:2*Ti);
    % u(k) = Fu Up + Fy Yp + Fr r + F0 y,  y = i + n
    Cu = zeros(2, nx);  Cu(:, iu) = Fu;  Cu(:, iy) = Fy;  Cu(:, ii) = F0;
    Du = [Fr, zeros(2), F0];
    Cy = zeros(2, nx);  Cy(:, ii) = I2;  Dy = [zeros(2, 4), I2];
    Sel = zeros(2, nx);  Sel(:, iu(2*nd-1:2*nd)) = I2;       % u(k-nd)
    Ac = zeros(nx);  Bc = zeros(nx, 6);
    Ac(ii, :) = Phi*Cy(:, 1:nx) + opt.alfa*Gam*Sel;  Bc(ii, 3:4) = Gam;
    Ac(iu(1:2), :) = Cu;  Bc(iu(1:2), :) = Du;
    Ac(iu(3:end), iu(1:end-2)) = eye(2*nU - 2);
    Ac(iy(1:2), :) = Cy;  Bc(iy(1:2), :) = Dy;
    if Ti > 1, Ac(iy(3:end), iy(1:end-2)) = eye(2*Ti - 2); end
    % o controlador sozinho: entradas (r, y), saida u, estado [Up; Yp]
    nc = 2*nU + 2*Ti;  Aq = zeros(nc);  Bq = zeros(nc, 4);  ku = 1:2*nU;  ky = 2*nU + (1:2*Ti);
    Cq = [Fu, Fy];  Dq = [Fr, F0];
    Aq(ku(1:2), :) = Cq;  Bq(ku(1:2), :) = Dq;  Aq(ku(3:end), ku(1:end-2)) = eye(2*nU - 2);
    Bq(ky(1:2), 3:4) = I2;  if Ti > 1, Aq(ky(3:end), ky(1:end-2)) = eye(2*Ti - 2); end
    M.ctrl = ss(Aq, Bq, Cq, Dq, P.Ts);
else                                             % PI: X = [i; integ; Up(nd)]
    nx = 4 + 2*nd;  ii = 1:2;  ig = 3:4;  iu = 4 + (1:2*nd);
    Jd = zeros(2);  if ctrl.desacopla, Jd = opt.w*ctrl.L*[0 -1; 1 0]; end
    % e = r - y;  integ+ = integ + ki Ts e;  u = kp e + integ+ + Jd y
    Cg = zeros(2, nx);  Cg(:, ig) = I2;  Cg(:, ii) = -ctrl.ki*P.Ts*I2;  Dg = ctrl.ki*P.Ts*[I2, zeros(2), -I2];
    Cu = Cg;  Cu(:, ii) = Cu(:, ii) - ctrl.kp*I2 + Jd;  Du = Dg + [ctrl.kp*I2, zeros(2), -ctrl.kp*I2 + Jd];
    Sel = zeros(2, nx);  Sel(:, iu(2*nd-1:2*nd)) = I2;
    Ac = zeros(nx);  Bc = zeros(nx, 6);
    Ac(ii, ii) = Phi;  Ac(ii, :) = Ac(ii, :) + opt.alfa*Gam*Sel;  Bc(ii, 3:4) = Gam;
    Ac(ig, :) = Cg;  Bc(ig, :) = Dg;
    Ac(iu(1:2), :) = Cu;  Bc(iu(1:2), :) = Du;
    if nd > 1, Ac(iu(3:end), iu(1:end-2)) = eye(2*nd - 2); end
    kT = ctrl.ki*P.Ts;                           % o controlador sozinho: estado = integrador
    M.ctrl = ss(I2, kT*[I2, -I2], I2, [(ctrl.kp + kT)*I2, -(ctrl.kp + kT)*I2 + Jd], P.Ts);
end
M.A = Ac;  M.rho = max(abs(eig(Ac)));
if ~opt.completo, return; end
Ci = zeros(2, nx);  Ci(:, 1:2) = I2;
M.sys = ss(Ac, Bc, [Ci; Cu; opt.alfa*Sel], [zeros(2, 6); Du; zeros(2, 6)], P.Ts);
M.estavel = M.rho < 1;
if M.estavel
    Si = eye(2) + M.sys(5:6, 3:4);               % S na entrada da planta: w = -T (w + dv)
    M.Ms = norm(Si, inf);  M.Mt = norm(M.sys(5:6, 3:4), inf);
    a = 1/norm(Si - 0.5*eye(2), inf);  M.disco = a;
    M.mg = 20*log10((2 + a)/(2 - a));  M.mf = 2*atand(a/2);       % margem de ganho [dB] e de fase [graus]
    M.banda = bandwidth(M.sys(1, 1))/(2*pi);     % r_d -> i_d, -3 dB [Hz]
    M.ruido_i = norm(M.sys(1:2, 5:6), 2)/sqrt(2);   % rms da corrente por eixo / rms do ruido por eixo
    M.ruido_u = norm(M.sys(3:4, 5:6), 2)/sqrt(2);   % rms da tensao por eixo [V/A]
else
    [M.Ms, M.Mt, M.disco, M.mg, M.mf, M.banda, M.ruido_i, M.ruido_u] = deal(NaN);
end
end
