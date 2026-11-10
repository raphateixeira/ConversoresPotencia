function P = parametros()
% PARAMETROS  Constantes da bancada do inversor (carga RL) e estilo das figuras.
%   Projeto 06ControleKoopman: EDMD / operador de Koopman com os dados reais.
aqui = fileparts(mfilename('fullpath'));
etapa = fileparts(aqui);                      % .../06ControleKoopman
raiz = fileparts(etapa);                      % .../InversorTrifasico

P.Ts = 50e-6;  P.N = 2044;                    % amostragem (20 kHz) e registro (102 ms)
P.f = 60;      P.w = 2*pi*60;                 % referencial dq
P.Vdc = 19.85;                                % barramento medido nos ensaios [V]
P.R = 25.3;    P.L = 9.8e-3;                  % carga da bancada (regime do PI; ARX)
P.Rnom = 25;   P.Lnom = 10e-3;                % valores nominais (etiqueta)
P.ruido = 8.5e-3;  P.lsb = 7.32e-3;           % ruido de medida e resolucao do ADC [A]

P.dados.prbs  = fullfile(raiz, '02IdentificacaoARX', 'dados', 'Dados01A.csv');       % vd vq id iq iA iB iC th
P.dados.fcs01 = fullfile(raiz, '04ControleFCS', 'dados', 'ControleFCS01.csv');       % idRef iqRef id iq vd vq iA iB (cru)
P.dados.fcs02 = fullfile(raiz, '04ControleFCS', 'dados', 'ControleFCS02.csv');       % idem, media de 16 periodos
P.dados.rls02 = fullfile(raiz, '05FCSAdaptativoRLS', 'dados', 'DadosRLS02.csv');     % th1 th3 id iq vd vq iA iB (cru)
P.dados.rls03 = fullfile(raiz, '05FCSAdaptativoRLS', 'dados', 'DadosRLS03.csv');     % idem, media de 16
P.dados.rls04 = fullfile(raiz, '05FCSAdaptativoRLS', 'dados', 'DadosRLS04.csv');     % idem, cru (IV)
P.imgs = fullfile(etapa, 'apresentacoes', 'ControleKoopman', 'imgs');
P.firmware = fullfile(etapa, 'firmware', 'VSI06ControleKoopman');
P.mat = fullfile(aqui, 'modelos.mat');

% Vetores do inversor normalizados por Vdc: coluna e+1 = estado e (bit 2 = A, 1 = B, 0 = C)
e = 0:7;  sa = bitand(bitshift(e, -2), 1);  sb = bitand(bitshift(e, -1), 1);  sc = bitand(e, 1);
P.V = [2/3*(sa - (sb + sc)/2); (sb - sc)/sqrt(3)];

P.cor.azul = [31 95 191]/255;  P.cor.verm = [214 40 40]/255;  P.cor.verde = [42 157 58]/255;
P.cor.cinza = [108 117 125]/255;  P.cor.amar = [200 164 0]/255;
set(groot, 'defaultAxesFontSize', 20, 'defaultLineLineWidth', 2.2, 'defaultFigureColor', 'w', ...
    'defaultAxesXGrid', 'on', 'defaultAxesYGrid', 'on', 'defaultAxesBox', 'off', ...
    'defaultLegendBox', 'off', 'defaultAxesGridAlpha', 0.25, 'defaultFigureVisible', 'off');
end
