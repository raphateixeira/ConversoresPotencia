# CLAUDE.md

`ConversoresPotencia` (público, Pages em raphateixeira.github.io/ConversoresPotencia/) junta, desde
2026-10-25, `ControleBuck`, `ControleInversor3f`, `ControleVSI`, `MicroGrids` (cada um inteiro numa
subpasta, com histórico) e a parte Buck/inversor do `ProjetosCCS`. Os repositórios antigos foram
arquivados com redirecionamento. `ControleCC2CC` ficou de fora (IC com colaborador externo).

- Um único projeto Quarto na raiz: **não criar `_quarto.yml` em subpastas** (viraria outro projeto).
  Páginas novas entram em `project.render` e no menu do sistema em `website.navbar.right`.
- **Uma só página índice** (`index.qmd` da raiz), com uma seção por sistema e links diretos para o
  conteúdo; não criar índices por subpasta. Âncoras fixas usadas na navbar: `#buck`, `#firmware-buck`,
  `#inversor`, `#carga-rl`, `#firmware-inversor`, `#conectado-rede`, `#microrredes`.
- Caminhos para a raiz: tema `TemaRTx.scss` e `imgs/ufpa-colorido.png` com `../` conforme a profundidade.
- Bibliografia do Buck em `Buck/_metadata.yml`; as notas do ConectadoRede e do Microrredes declaram a sua.
- Firmware: `Buck/Firmware/` e `InversorTrifasico/Firmware/` são workspaces do CCS (`.theia/`); a numeração
  `VSINN` do firmware é a mesma das simulações em `InversorTrifasico/ConectadoRede/`.
  Detalhes técnicos dos projetos do CCS: ver o CLAUDE.md do `ProjetosCCS` (seções ProjetosVSI/ProjetosBuck).
- Detalhes das simulações: `InversorTrifasico/ConectadoRede/CLAUDE.md`.
- Visual: cabeçalho `.rtx-hero` e cartões `.categoria-card` do TemaRTx (não inventar paleta).
