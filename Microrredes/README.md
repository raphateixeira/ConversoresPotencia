# MicroGrids — Microrredes

Repositório de pesquisa sobre microrredes (*microgrids*): arquiteturas CA/CC/híbridas,
conversores formadores e seguidores de rede, controle hierárquico (*droop*, secundário,
terciário), MPC e controle baseado em dados.

Site: <https://raphateixeira.github.io/ConversoresPotencia/Microrredes/> (publicado pelo workflow
reutilizável de `raphateixeira/.github`).

## Estrutura

```
index.qmd            página inicial do projeto (site Quarto, tema TemaRTx)
Notas/               apresentações (formato nova-revealjs)
  Nota01IntroducaoMicrorredes.qmd
  Nota02ControleDescentralizadoHierarquico.qmd   (rascunho; Guerrero et al., 2013)
  anims/             microrredes.js (diagramas SVG por fragmentos), microrredes-anim.js
                     (canvas com sliders: fasores, droop-partilha, secundario, raizes-droop),
                     nova-anim.js (base, cópia de NovaPresent/anims)
  _encerramento.qmd  slide final ({{< include _encerramento.qmd >}})
  imgs/              figuras das notas
_extensions/nova/    tema Nova (cópia de NovaPresent/_extensions/nova; citações no pé coladas ao rodapé)
Referencias.bib      bibliografia comum · apa.csl
```

## Preview local

```bash
../.github/scripts/atualizar-tema.sh   # baixa o TemaRTx.scss (não versionado)
quarto preview
```

Nova nota: crie `Notas/NotaXX....qmd` com `format: nova-revealjs` e `resources: [anims/*.js]`, acrescente-a em
`project.render` no `_quarto.yml` e um link em `index.qmd`. Se houver código
executável (`engine: knitr`, Python/MATLAB), ajuste `needs_python`/`needs_r` em
`.github/workflows/publish.yml`.
