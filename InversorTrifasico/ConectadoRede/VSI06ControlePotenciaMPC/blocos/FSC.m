% Extraído de MPCFSC.slx por scripts/extrai_blocos.py (não editar: edite o bloco no Simulink).

function Sk = FSC(Vcc, PQref, Vg, Ig, Ls, Rs, Ts)

%Separa as referências P e Q
Pr = PQref(1);
Qr = PQref(2);

%Juntando na forma complexa as componentes
IG = Ig(1)+1j*Ig(2);
VG = Vg(1)+1j*Vg(2);

%Tabela de posições das chaves
S = [0 0 0;1 0 0;1 1 0;0 1 0;0 1 1;0 0 1;1 0 1;1 1 1];
%Matriz de conversão do sistema 3phi para o sistema alfa-beta

a = exp(1j*2*pi/3);
A = (2/3)*[1; a; a^2];

%Possíveis valores para o vetor de saídas do conversor
V = Vcc*(S*A);

%Otimização do Sinal de Controle

% 1 - Predição dos possíveis valores de corrente
Ip = (1-(Rs*Ts)/Ls)*IG + (Ts/Ls)*(-VG + V);
% Utilizar modelo ARX e RLS (para estimar os parametros do modelo ARX)

% 2 - Calcula-se os possíveis valores de potência ativa e reativa
Pp = (3/2)*real(VG*conj(Ip));
Qp = (3/2)*imag(VG*conj(Ip));
% 3 - Calcula-se os possíveis valores da função custo
g = abs(Pr-Pp) + abs(Qr-Qp);
% 4 - Minimiza a função custo
[~,IO] = min(g);
% 5 - Gera os estados das chaves no conversor
Sa = [S(IO,1) ~S(IO,1)]; % Chaves da fase A
Sb = [S(IO,2) ~S(IO,2)]; % Chaves da fase B
Sc = [S(IO,3) ~S(IO,3)]; % Chaves da fase C
Sk = [Sa Sb Sc];
