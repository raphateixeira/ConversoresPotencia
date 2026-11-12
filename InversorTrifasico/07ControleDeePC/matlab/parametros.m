function P = parametros()
% PARAMETROS  Constantes da bancada (carga RL, PWM de 20 kHz) e estilo das figuras.
%   Projeto 07ControleDeePC: controle preditivo direto dos dados (DeePC / SPC).
aqui = fileparts(mfilename('fullpath'));
etapa = fileparts(aqui);
raiz = fileparts(etapa);                      % .../InversorTrifasico
P.Ts = 50e-6;  P.N = 2044;  P.f = 60;  P.w = 2*pi*60;
P.Vdc = 19.85;  P.vmax = 0.45*P.Vdc;           % limite de tensao de fase (razao 5-95 %) [V]
P.R = 25.3;  P.L = 9.8e-3;                     % carga da bancada (planta "verdadeira" das simulacoes)
P.ruido = 8.5e-3;  P.lsb = 7.32e-3;            % ruido de medida e resolucao do ADC [A]
P.dados = fullfile(etapa, 'dados', 'prbs_dq.csv');     % PRBS real: vd vq id iq (media 16) id iq (1 periodo)
P.imgs = fullfile(etapa, 'apresentacoes', 'ControleDeePC', 'imgs');
P.fcs = fullfile(raiz, '06ControleKoopman', 'matlab');  % simulador do FCS (comparacao)
P.fcsReal = fullfile(raiz, '04ControleFCS', 'dados', 'ControleFCS02.csv');
P.piReal = fullfile(raiz, '03ControlePI', 'dados', 'DadosControlePI01.csv');
% Cores: uma por entidade, fixas em todas as figuras (paleta conferida para daltonismo):
%   DeePC/SPC (dados, direto) = azul; FCS = laranja; DeePC com previa ou 2a variante = verde;
%   MPC por modelo / indireto = magenta (tracejado); PI = cinza (tracejado); alerta = verm.
P.cor.azul = [31 95 191]/255;  P.cor.laranja = [213 94 0]/255;  P.cor.verde = [0 158 115]/255;
P.cor.magenta = [194 64 154]/255;  P.cor.cinza = [108 117 125]/255;  P.cor.verm = [214 40 40]/255;
P.cor.amar = [200 164 0]/255;  P.cor.preto = [0.1 0.1 0.1];
P.res = fullfile(aqui, 'resultados');  if ~isfolder(P.res), mkdir(P.res); end
P.artigo = fullfile(getenv('HOME'), 'Artigos', 'ArtigoDeePC', 'figures');   % copia em PDF, se a pasta existir
P.pi = struct('tipo', 'pi', 'kp', 2*pi*500*9.8e-3, 'ki', 2*pi*500*26.2, 'desacopla', true, 'L', 9.8e-3);  % PI 500 Hz
P.Tini = 2;  P.Nh = 10;  P.q = 1;  P.ru = 1e-2;  P.lg = 3;        % sintonia de referencia do DeePC
set(groot, 'defaultAxesFontSize', 20, 'defaultLineLineWidth', 2.2, 'defaultFigureColor', 'w', ...
    'defaultAxesXGrid', 'on', 'defaultAxesYGrid', 'on', 'defaultAxesBox', 'off', ...
    'defaultLegendBox', 'off', 'defaultAxesGridAlpha', 0.18, 'defaultAxesTickDir', 'out', 'defaultAxesLineWidth', 1.0, 'defaultFigureVisible', 'off');
end
