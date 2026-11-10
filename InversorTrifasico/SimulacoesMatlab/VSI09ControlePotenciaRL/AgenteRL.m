clear; clc;

% Parâmetros do Sistema
Ts = 10e-6; % Período de amostragem de 10µs
f = 60;
Vg = 110;
Vcc = 350;
Rs = 0.1;
R = 0.1;
Ls = 10e-3;
C = 1000e-6;

A = (2/3)*[1 -1/2 -1/2; 0 sqrt(3)/2 -sqrt(3)/2];

%% 🔹 Carregar Modelo Simulink do Ambiente
modelName = 'MPCFSCRL';  % Nome correto do modelo Simulink
load_system(modelName);  % Carregar o modelo no MATLAB

%% 🔹 Definição do Espaço de Observação e Ação
obsDim = [6 1]; % Dimensão das observações (6 variáveis)
numActions = 8; % Número total de ações possíveis do inversor

% Criar espaço de observação e ação do ambiente Simulink
obsInfo = rlNumericSpec(obsDim, 'LowerLimit', -inf, 'UpperLimit', inf);
actInfo = rlFiniteSetSpec(1:numActions); % Espaço discreto de ações

%% 🔹 Criar Ambiente de Aprendizado no Simulink
env = rlSimulinkEnv(modelName, 'MPCFSCRL/AgenteFSC', obsInfo, actInfo);
env.ResetFcn = @(in) resetFunction(in);

%% 🔹 Definição da Rede Neural do Agente DQN
% A rede agora possui apenas **uma saída escalar**, compatível com rlQValueFunction
criticNet = [
    featureInputLayer(obsDim(1), "Normalization", "none", "Name", "stateInput");
    fullyConnectedLayer(24, "Name", "fc1");
    reluLayer("Name", "relu1");
    fullyConnectedLayer(24, "Name", "fc2");
    reluLayer("Name", "relu2");
    fullyConnectedLayer(1, "Name", "output") % Apenas **um único valor Q** por entrada
];

% Criar a função Q-value corretamente
critic = rlQValueFunction(layerGraph(criticNet), obsInfo, actInfo, ...
    "ObservationInputNames", "stateInput");

%% 🔹 Configuração do Agente DQN
agentOptions = rlDQNAgentOptions(...
    "SampleTime", Ts, ... 
    "DiscountFactor", 0.99, ...
    "MiniBatchSize", 32, ...
    "ExperienceBufferLength", 1e5);

AgenteFSC = rlDQNAgent(critic, agentOptions);

%% 🔹 Configuração do Treinamento
trainingOptions = rlTrainingOptions(...
    "MaxEpisodes", 1000, ...
    "MaxStepsPerEpisode", 200, ...
    "StopTrainingCriteria", "AverageReward", ...
    "StopTrainingValue", 195, ...
    "SaveAgentCriteria", "EpisodeCount", ...
    "SaveAgentValue", 100, ...
    "Verbose", true);

%% 🔹 Iniciar Treinamento
trainingStats = train(AgenteFSC, env, trainingOptions);

%% 🔹 Salvar Agente Treinado
save('AgenteFSC.mat', 'AgenteFSC');

%% 🔹 Configuração para o Simulink
rlAgentBlock = 'MPCFSCRL/AgenteFSC';
rlSetAgent(rlAgentBlock, AgenteFSC);

%% 🔹 Função de Reset do Ambiente
function in = resetFunction(~)
    in = Simulink.SimulationInput('MPCFSCRL'); 
end
