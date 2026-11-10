function [M, c, fHz] = edmd_dq(idq, vdq, P)
% EDMD_DQ  EDMD com sinais complexos em dq (serve para a media sincrona de varios periodos):
%   i(k+1) = c1 i(k) + c2 v(k-1) + c3 v(k),  i = id + j iq,  v = (vd + j vq)/Vdc (angulo de k+1).
%   Em alfa-beta: th1 = c1 e^{j w Ts}, th2 = c2 e^{j w Ts}, th3 = c3 (matrizes de rotacao 2 x 2).
%   fHz = frequencia do referencial recuperada do angulo de c1 (supondo th1 real).
i = idq(1, :).' + 1j*idq(2, :).';  v = (vdq(1, :).' + 1j*vdq(2, :).')/P.Vdc;
k = (3:numel(i) - 1)';
c = [i(k), v(k-1), v(k)] \ i(k+1);
fHz = -angle(c(1))/(2*pi*P.Ts);
rot = exp(1j*P.w*P.Ts);
mc = @(x) [real(x) -imag(x); imag(x) real(x)];
M.A = [mc(c(1)*rot), mc(c(2)*rot); zeros(2, 4)];
M.B = [mc(c(3)); eye(2)];
end
