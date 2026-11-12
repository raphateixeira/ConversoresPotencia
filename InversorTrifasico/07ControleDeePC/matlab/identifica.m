function Mo = identifica(tipo, u, y, P, opt)
% IDENTIFICA  Modelos parametricos para o caminho INDIRETO (identifica primeiro, controla depois):
%   'arx'      ARX MIMO sem estrutura: y(k) = A1 y(k-1) + B1 u(k-1) + B2 u(k-2)      (12 parametros)
%   'fisico'   estrutura da carga RL em dq com atraso de 2: y(k) = (a I + c J) y(k-1) + (b I + e J) u(k-2)  (4)
%   'oraculo'  o modelo verdadeiro da planta simulada (R, L dados), ZOH exato com atraso de 2
%   Dados periodicos (indices circulares). Devolve A1 e B = {B1, B2}.
arguments
    tipo; u; y; P
    opt.R = P.R
    opt.L = P.L
    opt.atraso = 0
    opt.circular = true
end
J = [0 1; -1 0];  s = @(x, n) circshift(x, n, 2);
if opt.circular, v = 1:size(u, 2); else, v = 3:size(u, 2); end   % registro comum: descarta o inicio
switch tipo
    case 'arx'
        Fi = [s(y, 1); s(u, 1); s(u, 2)];  Fi = Fi(:, v);
        Th = (y(:, v)*Fi') / (Fi*Fi');
        Mo.A1 = Th(:, 1:2);  Mo.B = {Th(:, 3:4), Th(:, 5:6)};
    case 'fisico'
        y1 = s(y, 1);  u2 = s(u, 2);  y1 = y1(:, v);  u2 = u2(:, v);  Jy = J*y1;  Ju = J*u2;  yv = y(:, v);
        X = [y1(:), Jy(:), u2(:), Ju(:)];  th = X \ yv(:);
        Mo.A1 = th(1)*eye(2) + th(2)*J;  Mo.B = {zeros(2), th(3)*eye(2) + th(4)*J};  Mo.th = th;
    case 'oraculo'
        A = [-opt.R/opt.L, P.w; -P.w, -opt.R/opt.L];
        Phi = expm(A*P.Ts);  Gam = A \ ((Phi - eye(2))/opt.L);
        Mo.A1 = Phi;  Mo.B = [repmat({zeros(2)}, 1, 1 + opt.atraso), {Gam}];
end
end
