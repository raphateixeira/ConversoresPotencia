function d = desempenho(ctrl, P, varargin)
% DESEMPENHO  Uma nota so para comparar controles: erro rms de rastreamento no periodo inteiro
%   (degraus e regime, corrente verdadeira, soma dos dois eixos) [mA], com o ruido de medida da
%   bancada na malha. Tambem devolve as metricas classicas (METRICAS) e o numero de saturacoes.
%   Argumentos extras vao para SIMULA_DQ (R, L, alfa, planta...).
S = simula_dq(ctrl, P, 'periodos', 2, varargin{:});
k = P.N + 1 : 2*P.N;  e = S.ref(:, k) - S.iv(:, k);
d.J = 1e3*sqrt(mean(sum(e.^2, 1)));  d.m = metricas(S, P);  d.sat = S.sat;  d.S = S;
if any(~isfinite(e(:))) || d.J > 500, d.J = NaN; end
end
