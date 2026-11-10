function salva(f, P, nome)
% SALVA  Grava a figura em imgs/ da apresentacao.
exportgraphics(f, fullfile(P.imgs, nome), 'Resolution', 110);
close(f);
end
