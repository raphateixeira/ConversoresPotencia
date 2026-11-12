%% t00_confere  Testes de consistencia da infraestrutura (rodar depois de mexer no simulador)
P = parametros();  [u, y] = le_prbs(P);
% 1. malha_linear x simula_dq (sem ruido, sem saturacao): mesma resposta ao degrau
C = ganhos('spc', u, y, P);  Cpi = P.pi;
for c = {C, Cpi}
    S = simula_dq(c{1}, P, periodos = 1, ruido = 0, limita = false);
    Ml = malha_linear(c{1}, P);
    yl = lsim(Ml.sys(1:2, 1:2), S.ref', (0:P.N-1)*P.Ts)';
    k = 150:P.N;  fprintf('%-4s linear x simulacao: dif. max %.2e A (rho %.4f, Ms %.2f, banda %.0f Hz, MG %.1f dB, MF %.0f graus)\n', ...
        c{1}.tipo, max(abs(yl(:, k) - S.iv(:, k)), [], 'all'), Ml.rho, Ml.Ms, Ml.banda, Ml.mg, Ml.mf);
end
% 2. caminhos sem ruido dao o mesmo controle: oraculo = fisico = arx = spc com dados sem ruido
[us, ys] = gera_dados(P, ruido = 0, media = 1);
Co = ganhos('oraculo', us, ys, P);  So = simula_dq(Co, P, periodos = 1, ruido = 0);
for m = {'spc', 'spcc', 'arx', 'fisico', 'deepc'}
    Cm = ganhos(m{1}, us, ys, P, lg = 1e-9);  Sm = simula_dq(Cm, P, periodos = 1, ruido = 0);
    fprintf('sem ruido, %-7s: |Ke - Ke_oraculo| = %.1e; malha fechada x oraculo: dif. max %.1e A\n', m{1}, norm(Cm.Ke - Co.Ke), max(abs(Sm.iv - So.iv), [], 'all'));
end
% 3. planta chaveada (PWM) x modelo medio em malha aberta, sem tempo morto
[~, ym] = gera_dados(P, ruido = 0, media = 1);
[~, yp] = gera_dados(P, ruido = 0, media = 1, planta = 'pwm', tm = 0);
[~, yt] = gera_dados(P, ruido = 0, media = 1, planta = 'pwm', tm = 100e-9);
fprintf('PRBS: PWM x medio: rms %.2f mA; tempo morto de 100 ns x sem: rms %.2f mA\n', 1e3*rms(yp - ym, 'all'), 1e3*rms(yt - yp, 'all'));
fprintf('dados reais x medio: rms %.2f mA (d %.2f, q %.2f); dados reais x PWM: rms %.2f mA (d %.2f, q %.2f)\n', ...
    1e3*rms(y - ym, 'all'), 1e3*rms(y(1,:) - ym(1,:)), 1e3*rms(y(2,:) - ym(2,:)), 1e3*rms(y - yt, 'all'), 1e3*rms(y(1,:) - yt(1,:)), 1e3*rms(y(2,:) - yt(2,:)));
fprintf('medias: real id %.1f iq %.1f | medio %.1f %.1f | PWM %.1f %.1f mA\n', 1e3*mean(y, 2), 1e3*mean(ym, 2), 1e3*mean(yt, 2));
% 4. gradiente rapido: sem saturar, converge para a lei em forma fechada
n = 0:P.N-1;  Cf = prepara_fgm(C, 200);
S1 = simula_dq(C, P, periodos = 1, ruido = 0);  S2 = simula_dq(Cf, P, periodos = 1, ruido = 0);
fprintf('FGM 200 iteracoes x forma fechada: dif. max %.2e V (cond. %.0f, beta %.2f)\n', max(abs(S1.u - S2.u), [], 'all'), Cf.cond, Cf.beta);
