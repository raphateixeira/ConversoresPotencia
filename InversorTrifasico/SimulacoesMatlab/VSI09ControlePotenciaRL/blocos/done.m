% Extraído de MPCFSCRL.slx por scripts/extrai_blocos.py (não editar: edite o bloco no Simulink).

function d = done()
    % Obtém o tempo atual da simulação no Simulink
    sim_time = get_param(bdroot, 'SimulationTime');

    % Definição do tempo máximo do episódio
    max_time = 0.04;  % Tempo limite para o episódio (40ms)

    % Condição para encerrar o episódio
    if sim_time >= max_time
        d = 1;  % O episódio terminou
    else
        d = 0;  % O episódio continua
    end
end
