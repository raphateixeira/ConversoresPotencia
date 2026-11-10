# VSI03ControlePI: ensaio do controle de corrente PI em dq (LINCE/UFPA)

LAUNCHXL-F28379D + BOOSTXL-3PHGANINV (J1–J4), carga RL trifásica em estrela (25 Ω e 10 mH por
fase), barramento de 20 V. Base: `VSI02IdentificacaoARX`. PWM, pinos, ADC, leitura das correntes
(zero/topo), zero dos sensores medido chaveando e gravação na matriz `Dados3F` são os mesmos. No
lugar da PRBS, um PI por eixo segue referências de corrente:

$$v_{d,q} = k_p\,e + k_i T_s \textstyle\sum e, \qquad k_p = 2\pi f_c L,\quad k_i = 2\pi f_c R$$

com desacoplamento ($v_d \mathrel{-}= \omega L\, i_q$, $v_q \mathrel{+}= \omega L\, i_d$) e limite
$|v| \le 0{,}45\,V_{dc}$ (9 V com 20 V), com anti-windup (o integrador para quando satura).
R e L são os identificados (26,2 Ω e 9,8 mH; apresentação *Identificação ARX: dados reais*).

## 1. Variáveis da Watch

| Variável | Padrão | Para quê |
|---|---|---|
| `habilita` | 0 | 1 liga o inversor, 0 desliga |
| `modo` | 1 | 1 = PI; 0 = malha aberta (`tensaoD0`, `tensaoQ0`) |
| `referenciaD0`, `referenciaQ0` | 0,15 A, 0 A | ponto de operação das correntes |
| `degrauD`, `degrauQ` | +0,10 A, −0,05 A | degraus: d de 10 a 60 ms, q de 35 a 85 ms, em cada período de 102 ms |
| `bandaPI` | 300 Hz | banda f~c~ da malha; 500 Hz depois de validar |
| `resistencia`, `indutancia` | 26,2 Ω, 9,8 mH | modelo usado nos ganhos |
| `desacopla` | 1 | 1 = desacoplamento ωL ligado; 0 = desligado (para comparar) |
| `correnteMaxima` | 0,8 A | proteção por software (pico de fase) |
| `periodosMedia` | 16 | períodos na média síncrona |
| `grava` | 0 | 1 grava; 2 gravando; 3 calculando a média; 0 pronto |

Para ver: `correnteD`, `correnteQ`, `referenciaD`, `referenciaQ`, `tensaoDAgora`, `tensaoQAgora`,
`kp`, `ki` (calculados), `saturacoes`, `falha`, `tensaoBarramento`, `calibrando`, `periodoAtual`.

## 2. O que é gravado: `Dados3F` (8 × 2044 amostras de 50 µs = 102 ms)

| Linha | Variável | Conteúdo |
|---|---|---|
| 0–1 | idRef, iqRef | referências [A] |
| 2–3 | id, iq | correntes medidas [A] (média síncrona) |
| 4–5 | vd, vq | sinais de controle aplicados [V] (média síncrona) |
| 6–7 | iA, iB | correntes das fases [A], último período (iC = −iA − iB) |

O perfil de referências se repete a cada 102 ms; a gravação descarta o primeiro período e faz a
média dos `periodosMedia` seguintes (ruído ÷ 4 com 16). Exportar: *Graph - Time* com `Dados3F`,
float de 32 bits, tamanho **16352**, ou *Memory > Save Memory* (32704 palavras).

## 3. Ensaio

1. *Build* e *Debug* do **`VSI03ControlePI`**.
2. Fonte em 20 V (limite de 0,5 A); `tensaoBarramento` ≈ 20 V. Espere uns segundos com
   `habilita = 0` (zero dos sensores).
3. `habilita = 1`: 110 ms a 50 % (`calibrando` = 1) e o PI começa. Confira `correnteD` seguindo
   `referenciaD` (0,15 / 0,25 A) e `correnteQ` seguindo `referenciaQ` (0 / −0,05 A).
4. `grava = 1`; espere voltar a 0 (≈ 1,7 s). Pause e exporte `Dados3F`.
5. Repita com `desacopla = 0` e depois com `bandaPI = 500`, gravando cada um.
6. `habilita = 0`. Se `falha` = 1, a proteção desligou: veja `correnteAgora` e o zero.

Análise e simulação do ensaio esperado: `InversorTrifasico/03ControlePI/apresentacoes/ControlePIDados/analise/simula_pi.py`
(`python3 simula_pi.py arquivo.csv` sobrepõe os dados medidos à simulação). Esperado (300 Hz):
subida de ≈ 1 ms, sem sobressinal, |v| até ≈ 6,7 V, interferência em i~q~ de ≈ 2 mA com
desacoplamento e ≈ 6 mA sem.
