function [R, L] = fisicos(M, P)
% FISICOS  R e L equivalentes de um modelo levantado z = [i; s(k-1)] (media dos dois eixos).
th1 = mean(diag(M.A(1:2, 1:2)));  th3 = mean(diag(M.B(1:2, :)));
R = P.Vdc*(1 - sqrt(th1))/th3;
L = -R*P.Ts/log(th1);
end
