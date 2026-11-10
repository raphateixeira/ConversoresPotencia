function M = modelo_fisico(R, L, P)
% MODELO_FISICO  Modelo levantado z = [i(k); s(k-1)], em alfa-beta, da carga RL com a
%   temporizacao do FCS (corrente lida no zero k; vetor s(k) vale do topo k+1/2 ao k+3/2):
%   i(k+1) = th1 i(k) + th2 s(k-1) + th3 s(k),  s = vetor normalizado por Vdc.
a = exp(-R*P.Ts/L);  ah = exp(-R*P.Ts/(2*L));
th3 = P.Vdc*(1 - ah)/R;  th2 = ah*th3;
M.A = [a*eye(2), th2*eye(2); zeros(2, 4)];
M.B = [th3*eye(2); eye(2)];
end
