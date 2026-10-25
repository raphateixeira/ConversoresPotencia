# CLAUDE.md

Contexto para sessões futuras do Claude Code neste repositório.

## O que é

Pasta `InversorTrifasico/ConectadoRede/` do `ConversoresPotencia` (ex-repositório `ControleVSI`) reúne as simulações MATLAB/Simulink (R2024a, Specialized Power
Systems) do VSI trifásico de dois níveis conectado à rede por filtro L. Publicada no site do `ConversoresPotencia`. Tema `TemaRTx.scss`, compartilhado e não versionado; não inventar paleta própria.

## Organização

- Uma pasta por etapa, `VSINN<Etapa>/` (sem hífen), com **a mesma numeração** de
  `InversorTrifasico/Firmware/VSINN<Etapa>/` (firmware C2000). Etapa nova: criar a pasta, o
  `index.qmd` e a entrada em `project.render`/menu "Inversor Trifásico" do `_quarto.yml` da raiz e na tabela do `index.qmd`.
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
  extensão em `_extensions/nova/` da raiz, copiada de `GitRTx/NovaPresent`). Diagramas SVG em
  `Notas/anims/vsi.js`; figuras vêm de `VSI*/figuras/`. Nota nova: entrada no `index.qmd`
  (seção "Notas") e no menu "Inversor Trifásico" do `_quarto.yml` da raiz.
