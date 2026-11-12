function [u, y] = gera_dados(P, opt)
% GERA_DADOS  Ensaio de identificacao SIMULADO, igual ao da placa (etapa 02): a mesma PRBS real
%   em vd e vq (5 +- 3 V e 0 +- 3 V, 2044 amostras), em malha aberta, com descarte do 1o periodo e
%   media sincrona de 'media' periodos. Serve para repetir o ensaio com outros ruidos e cargas.
arguments
    P
    opt.R = P.R
    opt.L = P.L
    opt.ruido = P.ruido
    opt.media = 16
    opt.semente = 1
    opt.planta = 'media'
    opt.tm = 100e-9
    opt.atraso = 0
    opt.u = []
end
if isempty(opt.u), u = le_prbs(P); else, u = opt.u; end
np = 1 + opt.media;
S = simula_dq(struct('tipo', 'ma', 'u', repmat(u, 1, np)), P, periodos = np, ruido = opt.ruido, ...
    semente = opt.semente, R = opt.R, L = opt.L, planta = opt.planta, tm = opt.tm, atraso = opt.atraso, limita = false);
y = squeeze(mean(reshape(S.y(:, P.N+1:end), 2, P.N, opt.media), 3));
end
