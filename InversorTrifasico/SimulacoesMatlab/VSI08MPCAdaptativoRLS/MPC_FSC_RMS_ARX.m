function [sys, x0, str, ts] = MPC_FSC_RMS_ARX(Iab,Vab,Vcc,PQref)

    switch flag
        case 0 [P, theta, str, ts] = Inicio();
        case 1 theta = RLS(Iab,Vab,theta);
        case 2 Ip = ARX();
        case 3 [Sk, theta] = FSC(Ip);
        case {4,9} sys = [];
        otherwise error('Flag Inválido')
    end

function Inicio()
    na = 2;
    nb = 2
    nparams = 4;
    P = 1e5*eye(nparams);
    



        
        