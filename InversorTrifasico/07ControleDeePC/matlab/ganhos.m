function C = ganhos(metodo, u, y, P, opt)
% GANHOS  Lei de controle preditivo (sem restricoes) por varios caminhos, todos com o mesmo custo:
%   diretos:   'spc' (minimos quadrados), 'spcc' (SPC causal), 'deepc' (DeePC regularizado, lg)
%   indiretos: 'arx', 'fisico' (identifica o modelo e deriva o preditor dele), 'oraculo' (modelo certo)
%   Devolve a struct pronta para SIMULA_DQ e MALHA_LINEAR (tipo 'mpc').
arguments
    metodo; u; y; P
    opt.Tini = P.Tini
    opt.N = P.Nh
    opt.q = P.q
    opt.r = P.ru
    opt.lg = P.lg
    opt.R = P.R
    opt.L = P.L
    opt.atraso = 0
    opt.circular = true
end
persistent ue
Tini = opt.Tini;  N = opt.N;
switch metodo
    case 'spc'
        S = preditor_spc(u, y, Tini, N, 0, circular = opt.circular);
    case 'spcc'
        S = preditor_spc(u, y, Tini, N, 0, causal = true, circular = opt.circular);
    case 'deepc'
        C = ganho_deepc(u, y, Tini, N, opt.q, opt.r, opt.lg, 1e6, opt.circular);
    case {'arx', 'fisico', 'oraculo'}
        Mo = identifica(metodo, u, y, P, R = opt.R, L = opt.L, atraso = opt.atraso, circular = opt.circular);
        if isempty(ue), ue = le_prbs(P); end          % o preditor do modelo sai da resposta dele a PRBS inteira
        S = preditor_spc(ue, resposta_modelo(Mo, ue), Tini, N, 0, pinv = true);
        C.modelo = Mo;
    otherwise
        error('metodo desconhecido: %s', metodo);
end
if ~strcmp(metodo, 'deepc')
    G = ganho_mpc(S.F, S.Ku, N, 2, 2, opt.q, opt.r);
    if exist('C', 'var'), G.modelo = C.modelo; end
    C = G;
end
C.tipo = 'mpc';  C.Tini = Tini;  C.metodo = metodo;
end
