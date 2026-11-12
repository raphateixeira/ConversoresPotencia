function F = fcs_referencia(P, periodos)
% FCS_REFERENCIA  FCS-MPC (modelo fisico, custo em k+3/2) simulado com o simulador da etapa 06,
%   na mesma planta (25,3 ohm; 9,8 mH), mesmo ruido e mesmas referencias. Devolve iv (corrente
%   verdadeira em dq), ref e a frequencia media de chaveamento.
aqui = pwd;  cd(P.fcs);  limpa = onCleanup(@() cd(aqui));
P6 = parametros();                                % (funcoes da pasta 06)
M = modelo_fisico(P6.R, P6.L, P6);
S = simula_fcs(preditor_linear(M, P6), P6, periodos = periodos);
F.iv = S.idqv;  F.ref = S.ref;  F.fsw = S.fsw;  F.vdq = S.vdq;
end
