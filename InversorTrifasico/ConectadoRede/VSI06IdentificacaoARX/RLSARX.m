clear; clc; close all;

% Versão preliminar do RLS para estimação do
% modelo ARX das correntes alpha (ia) e beta (ib), que são geradas
% respectivamente pelas relações dinâmicas abaixo a partir das tensões va e
% vb. Os canais são poluídos pelos ruídos ea e eb.
%       Ba(q)         Ca(q)   
% ia =  ----- va   +  ----- vb + ea
%       Aa(q)         Aa(q)
%
%       Bb(q)         Cb(q)   
% ib =  ----- va   +  ----- vb + eb
%       Ab(q)         Ab(q)
% Estrutura para os polinômios:
% - Dinâmica da corrente ia:
% A(q) = 1 - a1*q^-1 - a2*q^-2
% B(q) = b1*q^-1 - b2*q^-2
% C(q) = c1*q^-1 - c2*q^-2
%
% Determinar os parâmetros do modelo ARX a partir do algoritmo RLS.


%% Parâmetros de simulação
N = 100;        % Número de amostras
lambda = 0.98;  % Fator de esquecimento 

%% Geração de sinais de entrada
va = randn(N, 1);  % Tensão alpha
vb = randn(N, 1);  % Tensão beta

%% Inicialização do modelo ARX nominal:
% theta_Ia =  [a1a, a2a, b1a, b2a, c1a, c2a]
% theta_Ib =  [a1b, a2b, b1b, b2b, c1b, c2b]
[a1a, a2a, b1a, b2a, c1a, c2a] = deal(0.7, -0.2, 0.5, -0.3, 0.4, -0.1);
[a1b, a2b, b1b, b2b, c1b, c2b] = deal(0.6, -0.1, 0.3, -0.4, 0.2, -0.2);

%% Geração das saídas usando os coeficientes reais
ia = zeros(N, 1);
ib = zeros(N, 1);

for k = 3:N
    ia(k) = a1a*ia(k-1) + a2a*ia(k-2) + b1a*va(k-1) + ...
            b2a*va(k-2) + c1a*vb(k-1) + c2a*vb(k-2) + 0.02*randn;

    ib(k) = a1b*ib(k-1) + a2b*ib(k-2) + b1b*va(k-1) + ...
            b2b*va(k-2) + c1b*vb(k-1) + c2b*vb(k-2) + 0.02*randn;
end

%% Inicialização do RLS
n_params = 6;                       % Número de coeficientes do ARX;
theta_ia = zeros(n_params, 1);      % Parâmetros do modelo de ia;
theta_ib = zeros(n_params, 1);      % Parâmetros do modelo de ib;

% Matriz de covariância inicial grande
Pa = 1000*eye(n_params);  
Pb = 1000*eye(n_params);

%% Vetores para armazenar os coeficientes estimados
theta_ia_hist = zeros(n_params, N);
theta_ib_hist = zeros(n_params, N);

%% Algoritmo RLS para estimar os coeficientes:

for k = 3:N
    % Vetor de regressores:
    phi_a = [-ia(k-1); -ia(k-2); va(k-1); va(k-2); vb(k-1); vb(k-2)];
    phi_b = [-ib(k-1); -ib(k-2); va(k-1); va(k-2); vb(k-1); vb(k-2)];
    
    % Ganho de Kalman:
    Ka = (Pa * phi_a) / (lambda + phi_a' * Pa * phi_a);
    Kb = (Pb * phi_b) / (lambda + phi_b' * Pb * phi_b);
    
    % Atualização dos coeficientes
    theta_ia = theta_ia + Ka*(ia(k) - phi_a' * theta_ia);
    theta_ib = theta_ib + Kb*(ib(k) - phi_b' * theta_ib);
    
    % Atualização da matriz de covariância
    Pa = (Pa - Ka * phi_a' * Pa) / lambda;
    Pb = (Pb - Kb * phi_b' * Pb) / lambda;
    
    % Armazenamento dos coeficientes estimados
    theta_ia_hist(:, k) = theta_ia;
    theta_ib_hist(:, k) = theta_ib;    
end

%% Gráficos dos coeficientes estimados
figure;
label_a = ["a_{1\alpha}", "a_{2\alpha}", "b_{1\alpha}",...
            "b_{2\alpha}", "c_{1\alpha}", "c_{2\alpha}"];
for i = 1:n_params
    subplot(2,3,i);
    plot(theta_ia_hist(i, :), 'b'); hold on;
    yline(theta_ia(i), 'r--', 'LineWidth', 1.5);
    xlabel('Amostra'); 
    ylabel([label_a(i)]);
    grid on;
end
sgtitle('Evolução dos Coeficientes Estimados para i_\alpha');

figure;
label_b = ["a_{1\beta}", "a_{2\beta}", "b_{1\beta}",...
            "b_{2\beta}", "c_{1\beta}", "c_{2\beta}"];
for i = 1:n_params
    subplot(2,3,i);
    plot(theta_ib_hist(i, :), 'b'); hold on;
    yline(theta_ib(i), 'r--', 'LineWidth', 1.5); 
    xlabel('Amostra'); 
    ylabel([label_b(i)]);
    grid on;
end
sgtitle('Evolução dos Coeficientes Estimados para i_\beta');