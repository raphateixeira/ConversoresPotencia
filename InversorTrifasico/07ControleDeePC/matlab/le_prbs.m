function [u, y, y1] = le_prbs(P)
% LE_PRBS  Ensaio real de identificacao (etapa 02): u = [vd; vq] comandadas [V],
%   y = [id; iq] media de 16 periodos [A], y1 = um periodo so (sem media). 2 x 2044 cada.
M = readmatrix(P.dados);
u = M(:, 1:2)';  y = M(:, 3:4)';  y1 = M(:, 5:6)';
end
