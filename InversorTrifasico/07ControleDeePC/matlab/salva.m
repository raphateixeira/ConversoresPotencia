function salva(f, P, nome)
% SALVA  Grava a figura em imgs/ da apresentacao (PNG) e, se existir a pasta do artigo, em PDF vetorial.
exportgraphics(f, fullfile(P.imgs, nome), 'Resolution', 170);
if isfolder(P.artigo)
    [~, base] = fileparts(nome);
    exportgraphics(f, fullfile(P.artigo, [base '.pdf']), 'ContentType', 'vector');
end
close(f);
end
