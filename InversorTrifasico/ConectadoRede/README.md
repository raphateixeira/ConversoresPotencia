# ControleVSI

Simulações MATLAB/Simulink do **inversor fonte de tensão (VSI) trifásico conectado à rede**:
controle PI, MPC-FSC, identificação ARX/RLS, MPC adaptativo e aprendizagem por reforço.
Prof. Dr. Raphael Barros Teixeira (UFPA-CAMTUC-FEE). Repositório privado, com site Quarto só
local (`quarto preview`).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `Comum/` | `Parametros.m`: parâmetros do VSI usados por todos os modelos |
| `VSI01MalhaAberta/` … `VSI09ControlePotenciaRL/` | uma pasta por etapa: modelos `.slx`, scripts `.m`, `blocos/` (código extraído dos blocos MATLAB Function) e `index.qmd` |
| `scripts/extrai_blocos.py` | regenera `VSI*/blocos/*.m` a partir dos `.slx` |
| `Referencias/` | PDFs (artigo base e datasheet), **não versionados** |
| `IniciarProjeto.m` | põe `Comum/` no path e manda os caches do Simulink para `cache/` |

A numeração das etapas é a mesma dos projetos de firmware em
[ProjetosCCS/ProjetosVSI](https://github.com/raphateixeira/ProjetosCCS/tree/main/ProjetosVSI).

## Uso

```matlab
IniciarProjeto
Parametros
open_system('VSI05ControlePotenciaMPC/MPCFSC.slx')
```

Depois de editar um bloco MATLAB Function: `python3 scripts/extrai_blocos.py`.

Origem: pasta `~/Pesquisa/ProjetoPowerMPC`, migrada em 2026-10-16. Os estudos de Koopman foram
para `DataDrivenControl/Codigos/Koopman/`.
