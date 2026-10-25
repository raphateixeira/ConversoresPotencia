% Executa FonteControlada.m e salva todas as figuras geradas em PNG.
run('FonteControlada.m');

outdir = fullfile(fileparts(mfilename('fullpath')), 'figuras');
if ~exist(outdir, 'dir')
    mkdir(outdir);
end

figs = flipud(findobj('Type', 'figure'));
for i = 1:numel(figs)
    fh = figs(i);
    name = fh.Name;
    if isempty(name)
        name = sprintf('figura_%d', i);
    end
    safe = regexprep(name, '[^a-zA-Z0-9]+', '_');
    fname = fullfile(outdir, sprintf('%02d_%s.png', i, safe));
    exportgraphics(fh, fname, 'Resolution', 150);
    fprintf('Salvo: %s\n', fname);
end
