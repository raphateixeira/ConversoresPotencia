% Extraído de RLS_LIT.slx por scripts/extrai_blocos.py (não editar: edite o bloco no Simulink).

function [theta_A, theta_B] = RLS(ia, va, ib, vb)

    % Declara parâmetros ajustáveis como persistentes:
    persistent Pa Pb Ia Ib Va Vb Ka Kb lambda
    persistent theta_a theta_b

    % Inicializa parâmetros do RLS:
    if isempty(Pa)
        nA = 3;
        nB = 2;
        nparams = nA + 2*nB;
        Pa =  1e8*eye(nparams);
        Pb =  1e8*eye(nparams);
        lambda = 0.99;
        theta_a = zeros(nparams,1);
        theta_b = zeros(nparams,1);
        Ia = zeros(1,nA+1);
        Ib = zeros(1,nA+1);
        Va = zeros(1,nB+1);
        Vb = zeros(1,nB+1);
    end
    
    % Vetor de amostras das variáveis:
    Ia = [ia, Ia(1,1:end-1)];
    Ib = [ib, Ib(1,1:end-1)];
    Va = [va, Va(1,1:end-1)];
    Vb = [vb, Vb(1,1:end-1)];

    % Vetor de regressão 
    phi_a = [-Ia(1,2:end), Va(1,2:end), Vb(1,2:end)]';
    phi_b = [-Ib(1,2:end), Va(1,2:end), Vb(1,2:end)]';

    % Atualização do RLS para eixo alpha
    Ka = Pa*phi_a / (lambda + phi_a' * Pa * phi_a);
    theta_a = theta_a + Ka*(ia - phi_a'*theta_a);
    Pa = (Pa - Ka * phi_a' * Pa) / lambda;

    % Atualização do RLS para eixo alpha
    Kb = Pb * phi_b / (lambda + phi_b' * Pb * phi_b);
    theta_b = theta_b + Kb*(ib - phi_b'*theta_b);
    Pb = (Pb - Kb * phi_b' * Pb) / lambda;

    theta_A = theta_a;
    theta_B = theta_b;

end
