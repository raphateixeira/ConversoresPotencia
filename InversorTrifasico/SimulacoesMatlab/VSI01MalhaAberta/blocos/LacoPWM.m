% Extraído de MalhaAberta.slx por scripts/extrai_blocos.py (não editar: edite o bloco no Simulink).

function [cmpa, v] = LacoPWM(Bancada)
% Laço do PWM (ISR do ePWM1, a cada Ts): espelho de senoides.c + PWM2v (placa.c) do
% firmware ProjetosCCS/ProjetosVSI/VSI01MalhaAberta, em float de 32 bits como no C28x.
%   v    = [va; vb; vc]: tensões de fase desejadas, em relação ao ponto médio do barramento [V]
%   cmpa = CMPA dos ePWM 1, 2, 3 (d = 1/2 + v/Vcc, limitada a 0..1, truncada como no cast do C)
persistent theta kRampa
if isempty(theta)
    theta = single(0);
    kRampa = uint32(0);
end
DOIS_PI   = single(6.283185307);
DOIS_PI_3 = single(2.094395102);
Ts     = single(1)/single(Bancada.fPWM);
Vcc    = single(Bancada.Vcc);
Vp     = min(single(Bancada.Vp), Vcc/single(2));        % sem sobremodulação
dTheta = DOIS_PI*single(Bancada.f)*Ts;
nRampa = uint32(floor(single(Bancada.tRampa)/Ts + single(0.5)));
periodo = single(Bancada.TBPRD);

% Senoides()
V = Vp;
if kRampa < nRampa
    V = Vp*single(kRampa)/single(nRampa);
    kRampa = kRampa + uint32(1);
end
vs = [V*sin(theta); V*sin(theta - DOIS_PI_3); V*sin(theta + DOIS_PI_3)];
theta = theta + dTheta;
if theta >= DOIS_PI
    theta = theta - DOIS_PI;
end

% PWM2v()
d = single(0.5) + vs/Vcc;
d = min(max(d, single(0)), single(1));
cmpa = double(floor(d*periodo));
v = double(vs);
