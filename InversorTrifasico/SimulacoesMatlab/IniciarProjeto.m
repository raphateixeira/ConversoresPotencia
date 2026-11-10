% Inicializa o ProjetoPowerMPC: rode uma vez por sessão do MATLAB.
% - Coloca a pasta Comum/ (Parametros.m) no path;
% - Centraliza os caches do Simulink (slprj/, *.slxc) em cache/,
%   evitando que eles se espalhem pelas pastas dos modelos.

raiz = fileparts(mfilename('fullpath'));
addpath(fullfile(raiz, 'Comum'));

Simulink.fileGenControl('set', ...
    'CacheFolder',   fullfile(raiz, 'cache'), ...
    'CodeGenFolder', fullfile(raiz, 'cache'), ...
    'createDir', true);

fprintf('ProjetoPowerMPC pronto. Rode Parametros antes de simular.\n');
