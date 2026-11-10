% Extraído de MalhaAberta.slx por scripts/extrai_blocos.py (não editar: edite o bloco no Simulink).

function y = FiltroRC(u, Bancada)
% Filtro RC de 1a ordem das tensões medidas pelo BOOSTXL (VA, VB, VC, VDC), polo em fpTensao,
% discretizado por invariância ao degrau no passo Tsim.
persistent x
if isempty(x)
    x = zeros(4,1);
end
a = 1 - exp(-2*pi*Bancada.fpTensao*Bancada.Tsim);
x = x + a*(u - x);
y = x;
