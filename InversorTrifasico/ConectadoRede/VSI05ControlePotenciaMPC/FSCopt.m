function Sk = FSCopt(Vcc,PQref,Vs, Is, Rs, Ls, Ts)

% Separa as referências P e Q:

Pr = PQref(1);
Qr = PQref(2);

% Juntando na forma comlpexa as componentes de coorente e tensão:

Ik = Is(1) + 1j*Is(2);
VS = Vs(1) + 1j*Vs(2);

% Tabela de posições das chaves [Sa, Sb, Sc]:

S = [0 0 0;
     1 0 0;
     1 1 0;
     0 1 0;
     0 1 1;
     0 0 1;
     1 0 1;
     1 1 1];

% Matriz de conversão de abc para alpha-beta:

a = exp(1j*2*pi/3);
A = 2/3*[1; a; a^2];

% Possíveis valores para a saída do conversor:

V = Vcc*(S*A);

% Otimização do sinal de controle:

    % 1 - Predição dos possíveis valores de corrente na rede: 
    % Ip -> I(k+1);

    Ip = (1- (Rs*Ts)/Ls)*Ik + (Ts/Ls)*(-Vs + V);
    
    % Predição das potencias:

    Pp = (3/2)*real(VS*conj(Ip));
    Qp = (3/2)*imag(VS*conj(Ip));

    % Aplica função de custo:
    g = abs(Pr - Pp) + abs(Qr - Qp);

    % Minimiza o custo:
    [~,IO] = min(g);

    % Gera estados das chaves:
    Sa = [S(IO,1) ~S(IO,1)]; % Fase a
    Sb = [S(IO,2) ~S(IO,2)]; % Fase b
    Sc = [S(IO,3) ~S(IO,3)]; % Fase c
    Sk = [Sa, Sb, Sc];

end

