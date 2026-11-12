function m = metricas(S, P, campo)
% METRICAS  Desempenho no ultimo periodo: subida 10-90 % e sobressinal do degrau em id
%   (curva sem ruido), erro medio e rms em regime (corrente verdadeira), |v| maximo.
if nargin < 3, campo = 'iv'; end
x = S.(campo);  M = size(x, 2);  k0 = M - P.N;
a = k0 + 200;  z = (x(1, a:a+300) - 0.15)/0.10;
t10 = find(z >= 0.1, 1);  t90 = find(z >= 0.9, 1);
if isempty(t10) || isempty(t90), m.subida = NaN; else, m.subida = (t90 - t10)*P.Ts*1e3; end
zs = movmean(z, 7);  m.sobre = max(0, (max(zs) - 1)*100);
fora = find(abs(zs - 1) > 0.05, 1, 'last');  if isempty(fora), fora = 0; end;  m.acomoda = fora*P.Ts*1e3;
reg = k0 + [301:690, 901:1190, 1301:1690, 1801:2040];
e = S.ref(:, reg) - x(:, reg);
m.erro = 1e3*mean(e, 2);  m.rms = 1e3*sqrt(mean(sum(e.^2, 1)));
b = k0 + 200 + (0:300);  m.interf = 1e3*max(abs(movmean(x(2, b), 7)));
if isfield(S, 'u'), m.vmax = max(vecnorm(S.u(:, k0+1:end))); else, m.vmax = NaN; end
end
