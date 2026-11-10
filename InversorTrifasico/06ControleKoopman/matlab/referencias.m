function ref = referencias(P, periodos)
% REFERENCIAS  Perfil dos ensaios: id* = 0,15 + 0,10 A (10-60 ms), iq* = 0 - 0,05 A (35-85 ms).
n = 0:P.N-1;
rd = 0.15 + 0.10*(n >= 200 & n < 1200);
rq = 0.00 - 0.05*(n >= 700 & n < 1700);
ref = repmat([rd; rq], 1, periodos);
end
