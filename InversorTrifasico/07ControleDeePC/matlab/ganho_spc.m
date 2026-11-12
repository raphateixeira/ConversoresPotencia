function C = ganho_spc(u, y, Tini, N, r)
% GANHO_SPC  Atalho: preditor por dados (SPC) + lei de controle (q = 1, peso r no esforco).
S = preditor_spc(u, y, Tini, N, 0);
C = ganho_mpc(S.F, S.Ku, N, size(y, 1), size(u, 1), 1, r);
end
