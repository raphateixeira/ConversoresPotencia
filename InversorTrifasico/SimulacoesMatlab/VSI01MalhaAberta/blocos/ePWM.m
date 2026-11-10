% Extraído de MalhaAberta.slx por scripts/extrai_blocos.py (não editar: edite o bloco no Simulink).

function [g, ctr] = ePWM(cmpa, Bancada)
% ePWM 1, 2, 3 do F28379D configurados como em placa.c (VSI01), emulados contagem a contagem:
%  - contador sobe e desce, 0 -> TBPRD -> 0 (período 2*TBPRD contagens de EPWMCLK);
%  - CMPA com sombra: o valor escrito pela ISR só vale a partir do próximo CTR = 0;
%  - AQ: saída A vai a 0 em CTR = CMPA subindo e a 1 em CTR = CMPA descendo;
%  - banda morta: EPWMxA = A com a subida atrasada de nMorto (RED);
%    EPWMxB = A invertida, com a subida atrasada de nMorto (FED, polaridade ativa baixa).
% Cada passo de Tsim avança k = Tsim*EPWMCLK contagens; os eventos caem no primeiro passo
% em que o contador cruza CMPA (erro de até k-1 contagens).
%   g   = [AH AL BH BL CH CL]: comando das chaves (1 = ligada)
%   ctr = TBCTR do ePWM1
persistent pos A desde ativo
P   = round(Bancada.TBPRD);
k   = round(Bancada.Tsim*Bancada.EPWMCLK);
nDB = round(Bancada.tMorto*Bancada.EPWMCLK);
if isempty(pos)
    pos = -1;                    % primeira chamada: estado inicial em t = 0
    A = false(3,1);              % AQ parte com a saída A em 0
    desde = nDB*ones(3,1);       % contagens desde a última transição de A
    ativo = floor(P/2)*ones(3,1);   % CMPA inicial (d = 1/2)
end
if pos < 0
    pos = 0;
    ctrAnt = 0;
    subindo = true;
else
    ctrAnt = pos;
    if pos > P
        ctrAnt = 2*P - pos;
    end
    subindo = pos < P;
    pos = mod(pos + k, 2*P);
end
ctr = pos;
if pos > P
    ctr = 2*P - pos;
end
for i = 1:3
    C = ativo(i);
    if subindo && ctrAnt < C && ctr >= C && A(i)
        A(i) = false;
        desde(i) = ctr - C;
    elseif ~subindo && ctrAnt > C && ctr <= C && ~A(i)
        A(i) = true;
        desde(i) = C - ctr;
    else
        desde(i) = desde(i) + k;
    end
end
if pos == 0
    ativo = cmpa(:);             % carga da sombra em CTR = 0
end
g = zeros(6,1);
for i = 1:3
    passou = desde(i) >= nDB;
    g(2*i-1) = double(A(i) && passou);
    g(2*i)   = double(~A(i) && passou);
end
