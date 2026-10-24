# CLAUDE.md

Contexto para sessões futuras do Claude Code neste repositório.

## O que é

`ControleVSI` (privado) reúne as simulações MATLAB/Simulink (R2024a, Specialized Power
Systems) do VSI trifásico de dois níveis conectado à rede por filtro L. É um satélite do hub
`raphateixeira.github.io`, mas **sem GitHub Pages** (repositório privado): o site Quarto é só
local. Tema `TemaRTx.scss`, compartilhado e não versionado; não inventar paleta própria.

## Organização

- Uma pasta por etapa, `VSINN<Etapa>/` (sem hífen), com **a mesma numeração** de
  `ProjetosCCS/ProjetosVSI/VSINN<Etapa>/` (firmware C2000). Etapa nova: criar a pasta, o
  `index.qmd` e a entrada no menu "Etapas" do `_quarto.yml` e na tabela do `index.qmd`.
- Cada `VSINN*/index.qmd` segue as seções: callout de status, objetivo/lei de controle,
  tabela **Arquivos**, **Como rodar** (se houver modelo), **Pendências**.
- `Comum/Parametros.m` é o único arquivo de parâmetros; os modelos leem as variáveis do
  workspace (não há callbacks `PreLoadFcn`/`InitFcn`). Não duplicar `Parametros.m` nas etapas.
- `VSI*/blocos/*.m` são **gerados** por `scripts/extrai_blocos.py` a partir dos `.slx`
  (versionados para que o diff mostre a lei de controle). Nunca editar à mão.
- Não renomear os `.slx`: o nome do modelo aparece em scripts (ex.: `'MPCFSCRL/AgenteFSC'`
  em `VSI09ControlePotenciaRL/AgenteRL.m`).
- Caches (`cache/`, `slprj/`, `*.slxc`) e PDFs de `Referencias/` são gitignorados.
- `Notas/NotaNN<Tema>.qmd`: apresentações em slides no tema Nova (`format: nova-revealjs`,
  extensão em `_extensions/nova/`, copiada de `GitRTx/NovaPresent`). Diagramas SVG em
  `Notas/anims/vsi.js`; figuras vêm de `VSI*/figuras/`. Nota nova: entrada no `index.qmd`
  (seção "Notas") e no menu "Notas" do `_quarto.yml`.
