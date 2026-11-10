function D = prepara_fcs(arquivo, P)
% PREPARA_FCS  Registro do FCS (canais ... id iq vd vq iA iB) -> correntes e vetores em alfa-beta.
%   O angulo da Park sai das proprias correntes (alfa-beta x dq); o vetor aplicado, de (vd, vq).
X = le_dados3f(arquivo, 8);
id = X(:, 3);  iq = X(:, 4);  vd = X(:, 5);  vq = X(:, 6);
iA = X(:, 7);  iB = X(:, 8);  iC = -iA - iB;
ial = (2*iA - iB - iC)/3;  ibe = (iB - iC)/sqrt(3);
k = (0:P.N-1)';
th = angle((ial + 1j*ibe)./(id + 1j*iq));
th0 = angle(mean(exp(1j*(th - P.w*k*P.Ts))));
thk = th0 + P.w*k*P.Ts;
v = (vd + 1j*vq).*exp(1j*(thk + P.w*P.Ts));           % vetor escolhido em k, alfa-beta [V]
Vc = (P.V(1, :) + 1j*P.V(2, :))*P.Vdc;
[~, m] = min(abs(v - Vc), [], 2);
D.est = m' - 1;                                        % estado 0..7 (vetor nulo = 0)
D.s = P.V(:, m);                                       % vetor normalizado, 2 x N
D.i = [ial ibe]';                                      % correntes alfa-beta, 2 x N
D.idq = [id iq]';  D.vdq = [vd vq]';  D.th = thk';  D.X = X;
end
