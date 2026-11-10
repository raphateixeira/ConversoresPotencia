function m = metricas(S, P)
% METRICAS  Erro medio e rms de corrente em regime (fora dos degraus), a partir do 2o periodo.
reg = [301:690, 901:1190, 1301:1690, 1801:2040];
per = size(S.ref, 2)/P.N;  k = [];
for p = 2:per, k = [k, reg + (p - 1)*P.N]; end %#ok<AGROW>
if per == 1, k = reg; end
e = S.ref(:, k) - S.idq(:, k);
m.erro = mean(e, 2)*1e3;                       % [mA], d e q
m.rms = sqrt(mean(sum(e.^2, 1)))*1e3;
m.fsw = S.fsw;
end
