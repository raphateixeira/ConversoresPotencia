function M = edmd_fcs(i, s)
% EDMD_FCS  EDMD com o dicionario z = [i(k); s(k-1)] e entrada s(k) (dados em alfa-beta).
k = 2:size(i, 2) - 1;
[M.A, M.B] = edmd([i(:, k); s(:, k-1)], s(:, k), [i(:, k+1); s(:, k)]);
end
