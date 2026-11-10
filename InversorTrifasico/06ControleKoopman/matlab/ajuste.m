function f = ajuste(y, yh)
% AJUSTE  FIT = 100 (1 - NRMSE) [%], como o compare do MATLAB.
f = 100*(1 - norm(y - yh)/norm(y - mean(y)));
end
