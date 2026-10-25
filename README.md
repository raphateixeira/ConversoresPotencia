# ConversoresPotencia

Modelagem, identificação e controle de conversores de potência na plataforma LAUNCHXL-F28379D —
Prof. Dr. Raphael Teixeira (UFPA, Campus de Tucuruí). Site: <https://raphateixeira.github.io/ConversoresPotencia/>.

Reúne, desde 2026-10-25, os antigos repositórios `ControleBuck`, `ControleInversor3f`, `ControleVSI` e
`MicroGrids` e a parte de conversor Buck e inversor trifásico do `ProjetosCCS`, com o histórico de commits
de cada um.

| Pasta | Conteúdo | Origem |
|---|---|---|
| `Buck/` | IC do conversor Buck (Kauã): modelagem, fonte controlada, apresentações | ControleBuck |
| `Buck/Ensaios/`, `Buck/Firmware/` | identificação na placa; projetos do CCS | ProjetosCCS |
| `InversorTrifasico/CargaRL/` | IC do inversor com carga RL (Alessandra) | ControleInversor3f |
| `InversorTrifasico/ConectadoRede/` | simulações MATLAB/Simulink, etapas VSI01–VSI09 | ControleVSI |
| `InversorTrifasico/Ensaios/`, `InversorTrifasico/Firmware/` | malha aberta e controle de corrente na placa; projetos do CCS | ProjetosCCS |
| `Microrredes/` | notas em slides (tema Nova) | MicroGrids |

- Tema `TemaRTx.scss` compartilhado (raphateixeira/.github), não versionado; extensão de slides Nova em `_extensions/nova/`.
- `scripts/empacota_projetos.py` (pre-render) gera `downloads/<Projeto>.zip` de cada `*/Firmware/<Projeto>/`.
- As pastas `*/Firmware/` são *workspaces* do Code Composer Studio: abrir com *File → Open Folder* e fazer Clean + Rebuild.
- PDFs de terceiros ficam só na máquina local (gitignorados).

```bash
sh ../.github/scripts/atualizar-tema.sh   # baixa o tema
quarto preview
```
