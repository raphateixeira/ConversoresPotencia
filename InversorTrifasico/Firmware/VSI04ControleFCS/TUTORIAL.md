# VSI04ControleFCS: controle preditivo FCS-MPC da corrente (LINCE/UFPA)

LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (J1–J4), carga RL trifásica em estrela (25 Ω e 10 mH por
fase), barramento de 20 V. Base: `VSI03ControlePI` (mesmo hardware, medidas, calibração,
referências, proteção e gravação). O PI continua disponível (`modo` = 1) para comparar.

A cada 50 µs o FCS testa os 8 estados das chaves e aplica o de menor custo:

$$\hat i(k+\tfrac32) = a\,\big(a_h\, i(k) + b_h\, v_{\text{em vigor}}\big) + b\, v_e,
\qquad g_e = |i^* - \hat i|^2 + \lambda\, n_e$$

em αβ, com $a = e^{-RT_s/L}$, $b = (1-a)/R$ ($a_h$, $b_h$: o mesmo com $T_s/2$). As chaves mudam no
**topo** do contador (forçamento contínuo das saídas, com sombra) e a corrente é lida no **zero**.

## 1. Variáveis da Watch

| Variável | Padrão | Para quê |
|---|---|---|
| `habilita` | 0 | 1 liga, 0 desliga |
| `modo` | 2 | 2 = FCS-MPC; 1 = PI (como no VSI03); 0 = malha aberta |
| `referenciaD0`, `referenciaQ0`, `degrauD`, `degrauQ` | 0,15 A, 0, +0,10 A, −0,05 A | as mesmas referências do VSI03 |
| `resistencia`, `indutancia` | 25,3 Ω, 9,8 mH | modelo da predição (25,3 Ω: regime medido no ensaio do PI) |
| `lambdaComutacao` | 0 | peso das comutações no custo (ex.: 2e-4 reduz a frequência de chaveamento) |
| `correnteMaxima` | 0,8 A | proteção por software |
| `periodosMedia`, `grava` | 16, 0 | gravação, como no VSI03 |

Para ver: `estadoAtual` (bit 2 = A, 1 = B, 0 = C), `frequenciaChaveamento` (média por chave, janela
de 1 s; ≈ 3,4 kHz esperado), `custoMinimo`, `correnteD`, `correnteQ`, `tensaoDAgora`, `falha`.

## 2. Gravação: `Dados3F` (8 × 2044), igual ao VSI03

idRef, iqRef | id, iq (média) | vd, vq (vetor aplicado, em dq; média) | iA, iB (último período).
Com `periodosMedia` = 1 sai um registro cru (ondulação e chaveamento); com 16, a resposta média.

## 3. Ensaio

1. *Build* e *Debug* do **`VSI04ControleFCS`**; fonte em 20 V (limite 0,5 A); espere uns segundos.
2. `habilita = 1`: 110 ms a 50 % (calibração) e o FCS começa. Confira `correnteD` ≈ referência e
   `frequenciaChaveamento` ≈ 3 a 4 kHz.
3. `periodosMedia = 1`, `grava = 1`; exporte `Dados3F` (16352) → `DadosFCS01.csv`.
4. `periodosMedia = 16`, `grava = 1` → `DadosFCS16.csv`.
5. `modo = 1` (PI), `grava = 1` → `DadosPI16.csv` (mesmo dia, mesma carga).
6. Opcional: `lambdaComutacao = 2e-4`; fonte em 15 V (menos ondulação).
7. `habilita = 0`.

Esperado (simulação, `InversorTrifasico/Ensaios/ControleFCS/analise/simula_fcs.py`): resposta ao
degrau em ≈ 0,1 ms, ondulação de ± 30 mA, erro rms ≈ 16 mA a 20 V (12 mA a 15 V).
