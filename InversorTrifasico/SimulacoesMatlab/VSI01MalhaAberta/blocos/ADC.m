% Extraído de MalhaAberta.slx por scripts/extrai_blocos.py (não editar: edite o bloco no Simulink).

function cod = ADC(iabc, vf, Bancada)
% Códigos do ADC (12 bits, 0 a 3,3 V) das medidas do BOOSTXL-3PHGANINV, amostradas em CTR = 0:
%  - correntes de fase: shunt em linha de 5 mohm + INA240 (ganho 20), ponto médio 1,65 V e
%    polaridade invertida (USER_M1_SIGN_CURRENT_SF = -1 no SDK): v = 1,65 - 0,1 i  (+-16,5 A)
%  - VA, VB, VC (em relação ao negativo do barramento) e VDC: divisor com fundo de escala de
%    81,5 V, já filtradas pelo RC (bloco FiltroRC)
%   cod = [IA; IB; IC; VA; VB; VC; VDC]
vi = Bancada.Vmeio - Bancada.Gina*Bancada.Rsh*iabc(:);
vv = vf(:)*Bancada.Vadc/Bancada.VfsTensao;
n = 2^Bancada.nbits;
cod = min(max(floor([vi; vv]/Bancada.Vadc*n), 0), n - 1);
