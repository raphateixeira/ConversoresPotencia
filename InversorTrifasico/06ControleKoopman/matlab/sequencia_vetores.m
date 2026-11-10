function est = sequencia_vetores(N, segura)
% SEQUENCIA_VETORES  Sequencia pseudoaleatoria de estados do inversor (0..7), igual a do firmware:
%   LFSR de Galois de 16 bits (semente 0xACE1, mascara 0xB400), 3 deslocamentos por simbolo,
%   estado = 3 bits de baixo; cada simbolo dura "segura" amostras. Recomeca a cada periodo.
if nargin < 2, segura = 2; end
r = uint16(hex2dec('ACE1'));  est = zeros(1, N);
for k = 1:N
    if mod(k - 1, segura) == 0
        for j = 1:3
            b = bitand(r, 1);  r = bitshift(r, -1);
            if b, r = bitxor(r, uint16(hex2dec('B400'))); end
        end
        e = double(bitand(r, 7));
    end
    est(k) = e;
end
end
