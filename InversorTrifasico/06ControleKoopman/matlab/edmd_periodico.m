function M = edmd_periodico(i, s)
% EDMD_PERIODICO  EDMD de um registro periodico (indices circulares): z = [i(k); s(k-1)], entrada s(k).
%   E a mesma conta do EDMD embarcado no firmware VSI06ControleKoopman.
[M.A, M.B] = edmd([i; circshift(s, 1, 2)], s, [circshift(i, -1, 2); s]);
end
