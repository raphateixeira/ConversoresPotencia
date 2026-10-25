% Extraído de MPCFSCRLS.slx por scripts/extrai_blocos.py (não editar: edite o bloco no Simulink).

function [Sk,tta,ttb]   = RLS2ARX2FSC(Vcc, PQref, Vg, Ig)
    
    %Separa as referências P e Q
    Pr = PQref(1);
    Qr = PQref(2);
    
    %Juntando na forma complexa as componentes
    VG = Vg(1)+1j*Vg(2);
    ia = Ig(1);
    ib = Ig(2);
    va = Vg(1);
    vb = Vg(2);


    %% Algoritmo RLS:
    % Declara parâmetros ajustáveis como persistentes:
    persistent Pa Pb Ia Ib Va Vb Ka Kb lambda
    persistent theta_a theta_b
    persistent Aa Ab Ba Bb xa xb nA nB

    % Inicializa parâmetros do RLS:
    if isempty(Pa)
        nA = 3;
        nB = 2;
        nparams = nA + 2*nB;
        Pa =  1e6*eye(nparams);
        Pb =  1e6*eye(nparams);
        lambda = 0.99;
        theta_a = [-1.4157, 0.054, 0.4103, -6.51e-5, 5.29e-5, -1.87e-6,4.87e-4]';
        theta_b = [-1.4157, 0.054, 0.4103, -6.51e-5, 5.29e-5, -1.87e-6,4.87e-4]';
        Aa = [0,1,0;
              0,0,1;
              0,0,0];
        Ba = zeros(nA,2);
        Ab = Aa;
        Bb = Ba;
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
    xa = Ia(1,1:end-1)';
    xb = Ib(1,1:end-1)';
    % Vetor de regressão 
    phi_a = [-Ia(1,2:end), Va(1,2:end), Vb(1,2:end)]';
    phi_b = [-Ib(1,2:end), Va(1,2:end), Vb(1,2:end)]';

    % Atualização do RLS para eixo alpha
    Ka = Pa*phi_a / (lambda + phi_a' * Pa * phi_a);
    theta_a = theta_a + Ka*(ia - phi_a'*theta_a);
    Pa = (Pa - Ka * phi_a' * Pa) / lambda;

    % Atualização do RLS para eixo beta
    Kb = Pb * phi_b / (lambda + phi_b' * Pb * phi_b);
    theta_b = theta_b + Kb*(ib - phi_b'*theta_b);
    Pb = (Pb - Kb * phi_b' * Pb) / lambda;
    
    tta = theta_a;
    ttb = theta_b;
    %% Converter para representação de estados:
    Aa(:,1) = -theta_a(1:nA)';
    Ba(1:nB,1) =  theta_a(nA+1:nA+nB)';
    Ba(1:nB,2) =  theta_a(nA+nB+1:end)';
    Ab(:,1) = -theta_b(1:nA)';
    Bb(1:nB,1) =  theta_b(nA+1:nA+nB)';
    Bb(1:nB,2) =  theta_b(nA+nB+1:end)';
    
    %Tabela de posições das chaves
    S = [0 0 0; 1 0 0; 1 1 0; 0 1 0; 0 1 1; 0 0 1; 1 0 1; 1 1 1];

    %Matriz de conversão do sistema 3phi para o sistema alfa-beta
    a = exp(1j*2*pi/3);
    Tab = (2/3)*[1; a; a^2];
    
    %Possíveis valores para o vetor de saídas do conversor
    V = Vcc*(S*Tab);
    Ipa = zeros(8,1);
    Ipb = zeros(8,1);
    for n = 1:numel(Ipa)
        u = [real(V(n)-VG); imag(V(n)-VG)];
        xap = Aa*xa + Ba*u;
        xbp = Ab*xb + Bb*u;

        Ipa(n) = xap(1);
        Ipb(n) = xbp(1);
    end
    
    % Calcula-se os possíveis valores de potência ativa e reativa
    Pp = (3/2)*real(VG*conj(complex(Ipa,Ipb)));
    Qp = (3/2)*imag(VG*conj(complex(Ipa,Ipb)));

    % 3 - Calcula-se os possíveis valores da função custo
    g = abs(Pr-Pp) + abs(Qr-Qp);
    % 4 - Minimiza a função custo
    [~,IO] = min(g);
    % 5 - Gera os estados das chaves no conversor
    Sa = [S(IO,1) ~S(IO,1)]; % Chaves da fase A
    Sb = [S(IO,2) ~S(IO,2)]; % Chaves da fase B
    Sc = [S(IO,3) ~S(IO,3)]; % Chaves da fase C
    Sk = [Sa Sb Sc];

end
