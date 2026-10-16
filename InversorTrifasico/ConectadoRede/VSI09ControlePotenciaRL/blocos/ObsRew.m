% Extraído de MPCFSCRL.slx por scripts/extrai_blocos.py (não editar: edite o bloco no Simulink).

function [obs, rew] = ObsRew(PQ_ref, V, I)
    % Definição dos pesos para a minimização dos erros de potência
    w_P = 1.0;  % Peso do erro de potência ativa
    w_Q = 1.0;  % Peso do erro de potência reativa

    % Extração das referências de potência ativa e reativa
    P_ref = PQ_ref(1);
    Q_ref = PQ_ref(2);

    % Extração das componentes alpha e beta das tensões e correntes
    V_alpha = V(1);
    V_beta  = V(2);
    I_alpha = I(1);
    I_beta  = I(2);

    % Cálculo da potência ativa e reativa medida
    P = V_alpha * I_alpha + V_beta * I_beta;  % Potência ativa real
    Q = V_beta * I_alpha - V_alpha * I_beta;  % Potência reativa real

    % Cálculo dos erros de potência
    e_P = P_ref - P;
    e_Q = Q_ref - Q;

    % Cálculo da recompensa (quanto menor o erro, maior a recompensa)
    rew = exp(- (w_P * e_P^2 + w_Q * e_Q^2));

    % Agrupamento das variáveis de estado em um único vetor de saída (observação)
    obs = [P_ref, Q_ref, V_alpha, V_beta, I_alpha, I_beta];
end
