function X = le_dados3f(arquivo, canais)
% LE_DADOS3F  Le a matriz Dados3F exportada pelo Graph do CCS (CSV "Sample,Value").
%   X(:, c) = canal c (2044 amostras de 50 us).
if nargin < 2, canais = 8; end
M = readmatrix(arquivo, 'NumHeaderLines', 2);
v = M(:, end);
X = reshape(v(1:2044*canais), 2044, canais);
end
