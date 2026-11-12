%% principal  Roda o projeto 07ControleDeePC inteiro (figuras em ../apresentacoes/ControleDeePC/imgs)
%  t00: testes de consistencia do simulador e dos ganhos
%  d00: a ideia (superposicao de trajetorias gravadas)
%  d01: dos dados reais da PRBS a matriz de Hankel e a previsao direta dos dados
%  d02: DeePC/SPC em malha fechada (regularizacao; comparacao com PI e FCS)
%  d03: sintonia (peso r_u, horizonte N, passado Tini, dados com e sem media)
%  d04: limite de tensao (cortar x quadprog)
%  d05: validacao com dados reais fora do projeto (simulador x PI medido; previsao do ensaio do PI)
%  d06: a lei de controle como controlador linear (frequencia, margens, mapa de estabilidade)
%  d07: robustez no tempo (carga, Vdc, perturbacao, forma incremental, frequencia)
%  d08: ruido e quantidade de dados, direto x indireto (Monte Carlo)
%  d09: restricao com poucas iteracoes por amostra (gradiente rapido projetado)
%  d10: planta chaveada (PWM, tempo morto) e previsao do ensaio
%  d11: custo computacional, memoria e precisao simples
%  d12: adaptacao com dados da malha fechada e re-ensaio rapido
warning('off', 'all');
etapas = {'t00_confere', 'd00_superposicao', 'd01_dados_hankel', 'd02_malha_fechada', 'd03_sintonia', 'd04_restricoes', 'd05_valida_dados', ...
          'd06_analise_linear', 'd07_robustez', 'd08_ruido_dados', 'd09_restricoes_rapidas', 'd10_pwm', 'd11_custo', 'd12_adaptativo'};
for e = 1:numel(etapas), fprintf('\n===== %s =====\n', etapas{e});  executa(etapas{e}); end

function executa(nome)
% Cada etapa roda no seu proprio espaco de variaveis (as etapas reusam nomes como C e L).
eval(nome);
end
