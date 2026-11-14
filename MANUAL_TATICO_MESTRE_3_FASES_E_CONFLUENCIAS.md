# 🎯 Manual Tático Mestre: As 3 Fases do Mercado, Matriz Quant Engine V8, Barras de Estrutura GEX e Confluência Total (9 Indicadores + MZPack Footprint + Jigsaw DOM + Volume/Market Profile)

> **Documento Operacional Completo (Teoria + Prática de Execução Institucional)**
> Integração dos **9 Indicadores do `instalador_cloud2.0.py`** (`NiveisGammaPro`, `NiveisEstruturaPro`, `MoneyRiskPro`, `DailyOHLCPro`, `GlobexRangePro`, `VolatilidadeImplicitaPro`, `FluentliExpectedMove`, `VWAPInstitucionalPro`, `DeltaCumulativePro`) + **Fluxo de Ordens Profissional (`MZPack Footprint`, `Jigsaw DOM / SuperDOM`, `MZPack Volume Profile` e `MZPack Market Profile TPO`)**.

---

## 📌 Parte 1: Leitura das Barras do `NiveisEstruturaPro` (Verde vs. Vermelha, Mercado Subindo vs. Caindo e Valores em `$M` / `$B`)

### 1.1 O Valor Financeiro (`$1M`, `$145M`, `$1.2B`) Significa Dinheiro Parado Lá? É Relevante?

- **O que o número realmente representa:** O valor ao lado da barra (ex.: `$145.2M` ou `-$170.0M`) **não é lote de ordens limitadas esperando no Book (DOM)**. Ele é a **Exposição Financeira Nocional de Gamma dos Dealers (Market Makers)** naquele strike, calculada por:
  $$\text{Notional GEX (\$)} = \text{Open Interest} \times \Gamma \times \text{Multiplicador do Contrato} \times \text{Spot}$$
- **O que isso significa na prática:** Mostra **quantos milhões ou bilhões de dólares em contratos futuros (`ES`, `NQ`, etc.) os Market Makers são obrigados matematicamente a comprar ou vender** para manterem seu *Delta-Hedge* neutro quando o preço passa por aquele strike.
- **Relevância da Magnitude (`$1M` vs. `$100M+` / `$1B`):**
  - **Barra de `$1M` a `$10M` (No ES/NQ):** **Baixa relevância (Barra `Light` / Ruído).** É facilmente rompida por qualquer fluxo institucional no Footprint/DOM.
  - **Barra de `$50M` a `$250M+` (Barra `Heavy`):** **Altíssima relevância institucional.** Os Dealers terão que descarregar centenas ou milhares de contratos futuros naquele nível.
  - **Barra de `$500M` a `$1B+` (Em dias de OPEX / `0DTE` + `7DTE` alinhados):** **Muralha Institucional Suprema ("Concreto Armado").** Gera absorções gigantescas no Jigsaw DOM e raramente é rompida no primeiro toque sem um catalisador macroeconômico.

---

### 1.2 Matriz das Barras VERDES (`+Net GEX` = Gamma Positivo / Amortecedor)

Na barra **VERDE (`+Net GEX`)**, os Dealers estão **Comprados em Gamma (*Long Gamma*)**. A obrigação matemática deles é **operar CONTRA o movimento do preço** (*vender quando sobe e comprar quando cai*):

| Posição da Barra Verde | Movimento do Preço | O que os Dealers Fazem? | É COMPRA ou VENDA? (Como Operar) |
|---|---|---|---|
| **Barra Verde Grande ACIMA do Preço** | **Mercado SUBINDO** em direção à barra verde | Os Dealers **VENDEM futuros** contra a alta para zerar o Delta positivo das Calls. | **ALVO DE COMPRA / GATILHO DE VENDA (Reversão de Topo):** Realize o lucro de compras ao tocar na barra verde. Se o **Footprint (MZPack)** + **Jigsaw DOM** mostrarem absorção no Ask (Iceberg segurando a subida e candle fechando com pavio superior), **VENDA** buscando retorno à `VWAP` / `POC`. |
| **Barra Verde Grande ABAIXO do Preço** | **Mercado CAINDO** em direção à barra verde | Os Dealers **COMPRAM futuros** na queda, criando um colchão de liquidez institucional. | **ALVO DE VENDA / GATILHO DE COMPRA (Reversão de Fundo ou Pullback):** Realize o lucro de vendas ao tocar na barra verde. Se o **Footprint** + **Jigsaw DOM** mostrarem absorção passiva no Bid (vendedores batendo sem deslocar o preço e candle revertendo para cima), **COMPRE** com stop abaixo da barra verde. |

---

### 1.3 Matriz das Barras VERMELHAS (`-Net GEX` = Gamma Negativo / Acelerador)

Na barra **VERMELHA (`-Net GEX`)**, os Dealers estão **Vendidos em Gamma (*Short Gamma*)**. A obrigação matemática deles é **operar A FAVOR do movimento do preço** (*vender mais futuros quando cai e recomprar futuros no pânico quando sobe*):

| Posição da Barra Vermelha | Movimento do Preço | O que os Dealers Fazem? | É COMPRA ou VENDA? (Como Operar) |
|---|---|---|---|
| **Barra Vermelha Grande ABAIXO do Preço** | **Mercado CAINDO** em direção à barra vermelha | À medida que o preço cai rumo à barra vermelha, o Delta negativo das Puts explode e obriga os Dealers a **VENDEREM FUTUROS A MERCADO**. | **1º) VENDA DE CONTINUIDADE (Ímã de Queda):** Antes de tocar na barra vermelha, ela funciona como um **ímã acelerador de baixa** — opere **VENDIDO** a favor da queda até ela.<br>**2º) AO TOCAR NA BARRA VERMELHA (`PUT WALL`):** Se entrar **Absorção Extrema (Iceberg Comprador no DOM + Divergência no Footprint)**, os fundos realizam lucro das Puts e geram **COMPRA de repique (*Put Squeeze*)**. Porém, se **não houver absorção** e o candle rasgar a barra vermelha com *Stacked Selling Imbalances*, **VENDA O ROMPIMENTO** (queda livre). |
| **Barra Vermelha Grande ACIMA do Preço** | **Mercado SUBINDO** em direção à barra vermelha | À medida que o preço sobe e invade a barra vermelha, as Puts daquele strike perdem Delta rapidamente (*Vanna/Charm*), obrigando os Dealers que estavam vendidos em futuros a **RECOMPRAREM FUTUROS A MERCADO**. | **COMPRA DE CONTINUIDADE / *SHORT SQUEEZE DE ALTA*:** Quando o mercado está **subindo** rumo a uma grande barra vermelha (ou rompendo-a para cima), ela **não freia o preço como a barra verde** — ela **acelera a subida**! Opere **COMPRADO** a favor do rompimento/pullback de alta. Só pense em venda se o preço falhar abaixo dela com forte rejeição vendedora no Footprint/DOM. |

---

## 🛡️ Parte 2: Como Interpretar o Painel `🛡️ QUANT ENGINE V8` (Compra, Venda, Lateral ou Ficar de Fora)

| Cor do Painel (`REGIME`) | Etiqueta do `RATIO` (`|Put GEX| / Call GEX`) | `CALL/PUT VOLUME BALANCE` | Diagnóstico Institucional do Mercado | Ação Tática Recomendada (Comprar, Vender, Lateral ou Ficar de Fora) |
|---|---|---|---|---|
| 🟢 **VERDE (`LONG GAMMA`)** | **`[NEUTRAL]`** (`0.80` a `1.20`) | Equilibrado / Misto | **Mercado Lateral Amortecido (*Mean Reversion*):** Dealers comprados em Gamma freiam tanto esticadas de alta quanto de baixa. | **OPERAR LATERALIZAÇÃO (FADE NAS BORDAS):** **Compre** nos suportes (`0DTE Put Wall`, `Put Wall`, `VAL`, `-1 SD`) e **Venda** nas resistências (`0DTE Call Wall`, `Call Wall`, `VAH`, `+1 SD`) buscando a `VWAP` / `POC` / `MAX PAIN`. **Proibido operar rompimento seco.** |
| 🟢 **VERDE (`LONG GAMMA`)** | **`[CALL DOMINANT]`** (`< 0.80`) | **`BULLISH`** | **Tendência de Alta Estável (*Slow Grind Up*):** Estoque positivo de Calls sustenta o mercado e amortece quedas. | **PRIORIZAR COMPRA EM PULLBACK:** Compre recuos até a `VWAPInstitucionalPro`, `GEX FLIP`, linha roxa `BLOCK/MAX VOL` ou `0DTE PUT WALL`, com alvo na `0DTE CALL WALL` e `CALL WALL` Macro. |
| 🟢 **VERDE (`LONG GAMMA`)** | **`[PUT DOMINANT]`** (`> 1.20`) | **`BEARISH`** | **Alerta de Transição / Conflito:** Carteira macro ainda positiva, mas fluxo pesado de Puts pressionando para baixo. | **FICAR DE FORA NO MIOLO / CAUTELA:** Não compre no meio do range. Opere apenas venda de rejeição na `CALL WALL` ou aguarde: se perder a linha branca do `GEX FLIP`, vire a mão para **Venda**. |
| 🔴 **VERMELHO (`SHORT GAMMA`)** | **`[PUT DOMINANT]`** (`> 1.20`) | **`BEARISH`** | **Liquidação Direcional / Cascata de Baixa:** Dealers vendidos em Gamma são forçados a vender futuros conforme o preço cai. | **VENDA DE ROMPIMENTO E PULLBACK DE BAIXA:** **Proibido caçar fundo no escuro.** Venda a perda do `GEX FLIP` ou o repique até a `VWAP` / `GEX FLIP` mirando `0DTE PUT WALL` → `PUT WALL` → `AlvoDown` (`-1 SD` / `-2 SD`). |
| 🔴 **VERMELHO (`SHORT GAMMA`)** | **`[CALL DOMINANT]`** (`< 0.80`) | **`BULLISH`** | **Explosão Compradora (*Gamma Squeeze de Alta*):** Fluxo agressivo de Calls em ambiente volátil força recompra de futuros pelos Dealers. | **COMPRA DE ROMPIMENTO / PULLBACK CURTO DE ALTA:** Se o preço romper acima do `GEX FLIP` ou da `PUT WALL` com *Stacked Buying Imbalances* no Footprint, **Compre** mirando `MAX PAIN` e `CALL WALL`. |
| ⚪ **QUALQUER COR** | Preço em cima do `GEX FLIP` sem direção ou Paredes Invertidas (`CW < PW`) no miolo | Baixo giro / Indefinido | **Zona de Ninguém (*Chop Zone*):** Hedge trocando de sinal a cada tick ou compressão entre paredes invertidas. | **FICAR 100% DE FORA:** Aguarde o preço sair da zona morta e confirmar direção com agressão real no Footprint e Jigsaw DOM. |

---

## ⚔️ Parte 3: Manual Tático das 3 Fases do Mercado (9 Indicadores + MZPack Footprint + Jigsaw DOM + Volume Profile + Market Profile TPO)

### FASE 1: ROMPIMENTO E CONTINUIDADE DE MOVIMENTO (ALTA E BAIXA)

#### 1A. Rompimento e Continuidade de ALTA (*Breakout & Bullish Trend Continuation*)
1. **Contexto nos 9 Indicadores (`instalador_cloud2.0.py`):**
   - **`NiveisGammaPro`:** O preço rompe para cima a linha branca do `GEX FLIP` (ou rompe a `0DTE CALL WALL` amarela / linha roxa `BLOCK/MAX VOL`).
   - **`NiveisEstruturaPro`:** O preço sai de um bloqueio e entra em uma faixa de barras pequenas (`Light`) ou avança sobre uma barra vermelha (`-Net GEX`) que força recompra dos Dealers.
   - **`VWAPInstitucionalPro`:** Preço acima da `VWAP` central e caminhando sobre a banda `+1 SD` (bandas abrindo inclinadas para cima).
   - **`GlobexRangePro` / `DailyOHLCPro`:** Rompimento da Máxima do Globex (`ONH`) ou da Máxima do Dia Anterior (`PDH`).
   - **`DeltaCumulativePro`:** Fazendo topos e fundos ascendentes em sincronia com o preço (agressão compradora real sustentando o rompimento).
2. **Contexto no MZPack Volume Profile + Market Profile (TPO):**
   - O preço rompe o topo da Área de Valor (**`VAH`**) ou a máxima do *Initial Balance* (**`IBH`**), deixando **Single Prints compradores** no TPO e entrando em um **LVN (*Low Volume Node* / Vácuo de Liquidez)** no Volume Profile (região onde o preço corre rápido sem resistência histórica).
3. **Gatilho Exato de Entrada no MZPack Footprint + Jigsaw DOM:**
   - **Footprint (MZPack):** O candle de rompimento (ou o candle de retomada após o micro-pullback no nível rompido) apresenta **Stacked Buying Imbalances** (3 ou mais níveis diagonais consecutivos com desequilíbrio comprador $\ge 300\%$), `POC` da barra posicionada no terço superior e fechamento cheio próximo à máxima.
   - **DOM (Jigsaw):** Aumento nítido da velocidade da fita (*Tape Speed*), lotes grandes na coluna do **Ask** sendo consumidos rapidamente por ordens a mercado e recarga imediata de lotes limitados na coluna do **Bid** (*Bid Reloading* sustentando o preço).
4. **Gestão de Risco, Saída, Alvo e Amplitude do Movimento:**
   - **Lote e Stop (`MoneyRiskPro`):** Calcule o número de contratos pelo painel do `MoneyRiskPro`; posicione o Stop Loss técnico `1 a 2 pontos` abaixo da base do *Stacked Buying Imbalance* (ou abaixo da linha rompida).
   - **Amplitude e Escada de Alvos (Saídas):**
     - **Parcial 1 (50% da mão):** Na próxima linha da escada temporal do `NiveisGammaPro` (`0DTE CALL WALL` → `1DTE CALL WALL` → `2DTE CALL WALL`).
     - **Alvo Final (Amplitude Máxima):** Na **`CALL WALL` Macro (ciano sólida)** em confluência com a banda superior **`1 SD` / `2 SD` do `VolatilidadeImplicitaPro`** e a **nuvem vermelha superior do `FluentliExpectedMove`** (ou quando o Jigsaw DOM mostrar absorção passiva pesada no Ask).

---

#### 1B. Rompimento e Continuidade de BAIXA (*Breakout & Bearish Trend Continuation*)
1. **Contexto nos 9 Indicadores (`instalador_cloud2.0.py`):**
   - **`NiveisGammaPro`:** Painel `🛡️ QUANT ENGINE V8` em **`SHORT GAMMA` (vermelho)** com `RATIO > 1.20 [PUT DOMINANT]`. O preço perde a linha branca do `GEX FLIP` ou rompe para baixo a `0DTE PUT WALL` (laranja) / linha roxa `BLOCK/MAX VOL`.
   - **`NiveisEstruturaPro`:** Presença de **Grande Barra Vermelha (`-Net GEX`)** abaixo do preço atuando como ímã acelerador de queda.
   - **`VWAPInstitucionalPro`:** Preço abaixo da `VWAP` central e deslizando abaixo da banda `-1 SD`.
   - **`GlobexRangePro` / `DailyOHLCPro`:** Perda da Mínima do Globex (`ONL`) ou da Mínima do Dia Anterior (`PDL`).
   - **`DeltaCumulativePro`:** Barras vermelhas em queda livre (mínimas cada vez menores).
2. **Contexto no MZPack Volume Profile + Market Profile (TPO):**
   - Rompimento para baixo da **`VAL` (*Value Area Low*)** e da mínima do *Initial Balance* (**`IBL`**), abrindo **Single Prints vendedores** no TPO e caindo dentro de um **LVN (vácuo de volume)**.
3. **Gatilho Exato de Entrada no MZPack Footprint + Jigsaw DOM:**
   - **Footprint (MZPack):** **Stacked Selling Imbalances** (3 ou mais desequilíbrios diagonais vendedores consecutivos na coluna do Bid), Delta da barra fortemente negativo e fechamento na mínima do candle.
   - **DOM (Jigsaw):** *Bid Pulling* (compradores cancelando ordens limitadas no Bid ao verem a agressão) combinado com lotes pesados de venda a mercado varrendo vários níveis de preço para baixo.
4. **Gestão de Risco, Saída, Alvo e Amplitude do Movimento:**
   - **Lote e Stop (`MoneyRiskPro`):** Stop técnico `1 a 2 pontos` acima do topo do *Stacked Selling Imbalance* (ou acima do nível perdido).
   - **Amplitude e Escada de Alvos (Saídas):**
     - **Parcial 1:** Na `0DTE PUT WALL` (laranja) ou `1DTE PUT WALL` (roxa).
     - **Alvo Final (Amplitude Máxima):** Na **`PUT WALL` Macro (magenta sólida)** e no limite inferior **`AlvoDown` (`-1 SD` / `-2 SD` do `VolatilidadeImplicitaPro` + nuvem verde inferior do `FluentliExpectedMove`)**.

---

### FASE 2: REVERSÃO DE MOVIMENTO (ALTA PARA BAIXA NO TOPO E BAIXA PARA ALTA NO FUNDO)

#### 2A. Reversão de BAIXA no Topo (Mercado Subindo Esticado → Venda na Muralha)
1. **Onde Buscar (Confluência de Exaustão Máxima nos 9 Indicadores):**
   - O preço chega esticado na **`CALL WALL` Macro (ciano)** ou na **Super-Confluência `0DTE + 7DTE CALL WALL`**;
   - No **`NiveisEstruturaPro`**, há uma **Grande Barra Verde (`+Net GEX` de `$100M+` / `$1B`)** naquele nível;
   - O preço toca simultaneamente a banda **`+1 SD` ou `+2 SD` do `VolatilidadeImplicitaPro`**, entra na **nuvem vermelha superior do `FluentliExpectedMove`** e atinge a banda **`+2 SD` ou `+3 SD` da `VWAPInstitucionalPro`**.
2. **Confirmação no MZPack Volume Profile + Market Profile (TPO):**
   - Teste de um **HVN (*High Volume Node*)** de resistência superior ou falha de rompimento acima da `VAH` / `PDH`, deixando **Excess High (cauda de pavio/TPO no topo)** e voltando para dentro da área de valor.
3. **Gatilho Exato de Entrada no MZPack Footprint + Jigsaw DOM:**
   - **1º) Absorção Passiva no Topo (Armadilha Compradora / *Buying Trap*):** No **Footprint**, você vê um cluster enorme de contratos comprados no Ask exatamente na linha da `CALL WALL` (`POC` do candle presa no pavio superior), mas o candle **não sobe mais e fecha vermelho ou com longo pavio superior** (**Delta da barra Positivo + Preço fechando para baixo**).
   - **2º) Divergência no `DeltaCumulativePro`:** O `DeltaCumulativePro` faz uma máxima mais alta (compradores tardios agredindo no topo), mas o preço no gráfico faz um topo igual ou mais baixo (os Dealers absorveram tudo vendendo futuros).
   - **3º) Leitura no Jigsaw DOM:** Um lote institucional oculto (**Iceberg Order no Ask**) renova contratos sem parar no mesmo preço da `CALL WALL`; logo em seguida, os compradores cansam e entram agressões vendedoras no Bid (*Selling Imbalance* no Footprint).
4. **Saída, Alvo e Amplitude da Reversão de Baixa:**
   - **Entrada e Stop:** Venda na perda da mínima do candle de absorção (lote pelo `MoneyRiskPro`), com stop curto `4 a 8 ticks` acima da máxima do pavio/Iceberg.
   - **Alvos de Saída:** **Alvo 1:** Banda `+1 SD` da `VWAP` / `VAH` do Volume Profile → **Alvo 2:** Linha central da **`VWAPInstitucionalPro`** e **`POC`** do Volume Profile → **Alvo 3 (Amplitude Completa):** Linha dourada do **`MAX PAIN`** ou linha branca do **`GEX FLIP`**.

---

#### 2B. Reversão de ALTA no Fundo (Mercado Caindo Esticado → Compra na Muralha)
1. **Onde Buscar (Confluência de Exaustão Máxima nos 9 Indicadores):**
   - O preço cai esticado até a **`PUT WALL` Macro (magenta)** ou **`0DTE + 7DTE PUT WALL`**;
   - O nível coincide com a banda inferior **`-1 SD` ou `-2 SD` do `VolatilidadeImplicitaPro`**, a **nuvem verde inferior do `FluentliExpectedMove`** e o desvio **`-2 SD` / `-3 SD` da `VWAPInstitucionalPro`** (ou mínima do `GlobexRangePro` / `DailyOHLCPro`).
2. **Confirmação no MZPack Volume Profile + Market Profile (TPO):**
   - Falso rompimento (*Spring* de Wyckoff) abaixo da `VAL`, da `ONL` ou da `PDL` que rejeita rapidamente e volta para cima da `VAL`, deixando **Excess Low (cauda compradora no TPO)**.
3. **Gatilho Exato de Entrada no MZPack Footprint + Jigsaw DOM:**
   - **1º) Absorção Passiva no Fundo (*Selling Trap*):** No **Footprint**, milhares de contratos são vendidos no Bid em cima da `PUT WALL` (`POC` da barra presa na mínima do pavio), mas o candle **fecha positivo/verde acima da `PUT WALL`** (**Delta da barra Negativo + Fechamento de Alta**).
   - **2º) Divergência no `DeltaCumulativePro`:** O preço faz um micro-fundo duplo na `PUT WALL`, enquanto o `DeltaCumulativePro` já faz um fundo mais alto (exaustão vendedora).
   - **3º) Leitura no Jigsaw DOM:** **Iceberg Comprador no Bid** segurando toda a pancada vendedora na `PUT WALL`, seguido de agressão compradora limpando os primeiros níveis do Ask (*Buying Imbalance* de virada no Footprint).
4. **Saída, Alvo e Amplitude da Reversão de Alta:**
   - **Entrada e Stop:** Compra na superação da máxima do candle de absorção, com stop técnico `4 a 8 ticks` abaixo da mínima do pavio.
   - **Alvos de Saída:** **Alvo 1:** `VAL` / `-1 SD` da `VWAP` → **Alvo 2:** **`VWAPInstitucionalPro`** central e **`POC`** do Volume Profile → **Alvo 3 (Amplitude Completa):** **`MAX PAIN`** (dourada), **`GEX FLIP`** (branca) ou **`0DTE CALL WALL`**.

---

### FASE 3: LATERALIZAÇÃO (RANGE) E PULLBACK DE COMPRA OU VENDA

#### 3A. Operacional de Lateralização (*Range Rotation* em `LONG GAMMA`)
1. **Como Identificar que o Dia é Lateral:**
   - Painel `🛡️ QUANT ENGINE V8` **Verde (`LONG GAMMA`)** com **`RATIO [NEUTRAL]`**;
   - `VWAPInstitucionalPro` caminhando **horizontalmente (achatada)** no centro do gráfico;
   - Volume Profile e Market Profile (TPO) desenhando uma curva de sino simétrica (**Perfil `D-Shape`**), com a `POC`, a `VWAP` e o `MAX PAIN` agrupados no meio do canal entre a `0DTE PUT WALL` e a `0DTE CALL WALL`.
2. **Regra de Ouro da Lateralização:**
   - **PROIBIDO clicar no meio do canal (`POC` / `VWAP` / `MAX PAIN`).** Ali o risco/retorno é `1:1` e você será violinado.
   - **Venda na Borda Superior:** Quando o preço subir até a `VAH` do Volume Profile + `0DTE CALL WALL` (ou `+1 SD` da `VWAP` / barra verde do `NiveisEstruturaPro`), espere a absorção no Footprint/DOM e **venda** com alvo na `POC` / `VWAP` / `MAX PAIN`.
   - **Compre na Borda Inferior:** Quando o preço cair até a `VAL` do Volume Profile + `0DTE PUT WALL` (ou `-1 SD` da `VWAP` / barra verde inferior), espere a absorção no Footprint/DOM e **compre** com alvo na `POC` / `VWAP` / `MAX PAIN`.

---

#### 3B. Operacional de Pullback de COMPRA e Pullback de VENDA (A Favor da Tendência)
1. **Pullback de COMPRA (Em Tendência de Alta — Perfil `P-Shape`):**
   - **Zona de Espera do Pullback:** O mercado está em tendência de alta (acima do `GEX FLIP` e da `VWAP`). Aguarde o preço recuar até testar de cima para baixo uma zona de confluência dupla/tripla: **`VWAPInstitucionalPro`** (ou banda `+1 SD`) + **`GEX FLIP`** + linha roxa **`BLOCK/MAX VOL`** + **Barra Verde (`+Net GEX`)** no `NiveisEstruturaPro` + **`VAH` / `POC`** do Volume Profile.
   - **Gatilho no Footprint + DOM:** Durante o recuo, o volume no Footprint diminui (correção sem pressão institucional) e no Jigsaw DOM as agressões de venda secam; assim que tocar no suporte e surgir o primeiro candle com **Buying Imbalance** no Footprint e retomada do `DeltaCumulativePro` para cima, **COMPRE** com stop abaixo do suporte e alvo na `0DTE CALL WALL` / `CALL WALL` Macro / `1 SD Superior`.
2. **Pullback de VENDA (Em Tendência de Baixa — Perfil `b-Shape`):**
   - **Zona de Espera do Pullback:** O mercado está em tendência de baixa (painel `SHORT GAMMA` vermelho, abaixo do `GEX FLIP` e da `VWAP`). Aguarde o repique técnico de baixo para cima até a **`VWAPInstitucionalPro`** (ou banda `-1 SD`) + **`GEX FLIP` perdido** + linha roxa **`BLOCK/MAX VOL`** + **`VAL` / `POC`** do Volume Profile.
   - **Gatilho no Footprint + DOM:** O repique comprador perde força no Jigsaw DOM (compras a mercado batem em ordens passivas no Ask sem subir mais) e surge um candle com **Selling Imbalance** no Footprint virando o `DeltaCumulativePro` novamente para baixo. **VENDA** com stop acima do pivô do pullback e alvo na `0DTE PUT WALL` / `PUT WALL` Macro / `AlvoDown`.

---

## 🧭 Parte 4: Guia Tático das 7 Situações Especiais por Nível (`GEX Flip`, `Call Wall`, `Put Wall`, Rompimentos, `Max Pain` e `Block Order`)

### 1. Quando o Preço se Aproxima do `GEX FLIP (Zero Gamma)` (Linha Branca Pontilhada)
- **O que é:** É o divisor de águas onde os Dealers mudam de comportamento (acima dele amortecem o preço; abaixo dele aceleram o movimento).
- **Preço caindo de cima para o `GEX FLIP`:** No primeiro teste, se o painel estiver em `LONG GAMMA` e o Footprint/DOM mostrarem absorção compradora no Bid, opere **Compra de Pullback** defendendo a manutenção do regime positivo. Porém, se o preço **perder o `GEX FLIP` com *Stacked Selling Imbalances***, zere qualquer compra imediatamente e opere **Venda no reteste por baixo da linha branca**.
- **Preço subindo de baixo para o `GEX FLIP`:** Vindo do `SHORT GAMMA`, o `GEX FLIP` atua como o primeiro teto. Se rejeitar no Footprint/DOM, dá **Venda de Pullback** de volta à `PUT WALL`; mas se **romper o `GEX FLIP` para cima com força**, os Dealers recompram futuros e o preço busca a `CALL WALL` (opere **Compra no pullback sobre a linha branca**).

### 2. Quando o Preço Chega na `CALL WALL` ou na `PUT WALL`
- **Na `CALL WALL`:** É o alvo obrigatório para realizar lucros de posições compradas. Para abrir uma nova **Venda de Reversão**, exija o tripé: **Barra Verde (`+Net GEX`)** no `NiveisEstruturaPro` + **Absorção/Iceberg no Ask** pelo Jigsaw DOM + **Candle de rejeição/divergência** no Footprint e `DeltaCumulativePro`.
- **Na `PUT WALL`:** É o alvo obrigatório para realizar lucros de posições vendidas. Para abrir uma nova **Compra de Reversão**, exija **Absorção/Iceberg no Bid** pelo Jigsaw DOM + **Candle de rejeição compradora** no Footprint.

### 3. Quando o Preço ROMPE a `PUT WALL` ou ROMPE a `CALL WALL`
- **Rompimento da `CALL WALL` para Cima:** Quando o mercado fecha candles cheios acima da `CALL WALL` com *Stacked Buying Imbalances* no Footprint, o teto virou **piso institucional**. Os Dealers precisam comprar futuros adicionais para cobrir o Delta das Calls que ficaram profundamente dentro do dinheiro (ITM). **Tática:** Compre o pullback de cima para baixo na `CALL WALL` rompida mirando o próximo degrau DTE (`1DTE` / `2DTE` / `7DTE CALL WALL`) ou a banda de `+2 SD` do `VolatilidadeImplicitaPro`.
- **Rompimento da `PUT WALL` para Baixo:** É o movimento mais explosivo e perigoso do mercado (*Liquidation Cascade*). Abaixo da `PUT WALL`, não há mais suporte estrutural de opções naquela série e os Dealers vendem futuros em efeito bola de neve. **Tática:** **Proibido comprar.** Opere **Venda de Continuidade / Pullback por baixo da `PUT WALL` rompida** mirando a parede do próximo DTE inferior ou as bandas de `-2 SD` e `-3 SD` do `VolatilidadeImplicitaPro`.

### 4. Quando o Mercado Está em `POSITIVE GAMMA (+Net GEX)` na Mesma Linha da `CALL WALL` ou da `PUT WALL`
- **O que significa:** No `NiveisEstruturaPro`, a linha da `CALL WALL` (ou até mesmo o strike da suporte/parede inferior) exibe uma **Barra Verde (`+Net GEX`)** e o regime está em `LONG GAMMA`.
- **Como operar:** É a **Parede de Concreto Amortecedora**. Os Dealers estão operando **contra** o teste da linha (vendendo futuros na parede superior e comprando futuros na parede inferior). Opere **Reversão (Fade)** a favor da defesa dos Dealers assim que o Footprint confirmar a absorção.

### 5. Quando a `PUT WALL` ou `CALL WALL` Estão Próximas ou Cravadas no `NEGATIVE GAMMA (-Net GEX)`
- **O que significa:** A parede coincide com uma **Grande Barra Vermelha (`-Net GEX`)** e o preço está abaixo do `GEX FLIP` em `SHORT GAMMA`.
- **Como operar:** Cuidado redobrado! Enquanto o preço se aproxima dessa parede, o Gamma Negativo **puxa e acelera o preço como um ímã** até bater na linha (excelente para segurar um trade a favor da tendência até lá). Ao tocar na linha, **não coloque ordem apregoada cega ( pedra na mão )**: como o Gamma ali é negativo, os Dealers só param de vender futuros se os fundos começarem a realizar o lucro das Puts no DOM. Portanto, **espere o candle fechar e confirmar o Iceberg no Jigsaw DOM + virada de Delta no Footprint** antes de operar contra; se não houver defesa no DOM, opere a favor do rompimento!

### 6. Como Interpretar e Operar o `MAX PAIN` (Linha Tracejada Dourada — Entrada vs. Saída)
- **Para SAÍDA e ALVO (Uso Principal — 80% das vezes):** O `MAX PAIN` é o preço magnético para onde os lançadores de opções tentam conduzir o mercado até o encerramento da sessão (especialmente após as **13:30–14:00 ET** e em vencimentos `0DTE` / sextas-feiras). Se você entrou comprado na `PUT WALL` ou vendido na `CALL WALL`, use a linha dourada do **`MAX PAIN` como seu Alvo de Realização de Lucro**.
- **Para ENTRADA (Uso Secundário — 20% das vezes):** Só utilize o `MAX PAIN` como gatilho de entrada quando ele estiver **cravado junto com a `VWAPInstitucionalPro` ou com a `POC` do Volume Profile** servindo como suporte/resistência de **Pullback** a favor da tendência do dia. Se o preço já estiver lateralizado em cima do `MAX PAIN` no fim da tarde, **fique de fora** (*Pinning* = mercado travado).

### 7. Como Interpretar e Operar o `BLOCK ORDER / MAX OPTION VOLUME` (`DP` — Linha Sólida Roxa Grossa) e Outras Linhas
- **O que é:** A linha roxa grossa (`MAX OPTION VOLUME`) marca exatamente o strike onde ocorreu o **maior volume de contratos negociados no dia** (o "bloco institucional" vivo da sessão).
- **Como operar para Entrada:** Ela funciona como o **Pivô de Defesa do Grande Player do Dia**:
  - **Preço acima da Linha Roxa (`DP`):** Se o mercado recuar de cima para baixo até a linha roxa e o Footprint/DOM mostrarem absorção compradora no Bid, o player institucional está defendendo seu preço médio — **Compre o pullback** com stop logo abaixo da linha roxa.
  - **Preço abaixo da Linha Roxa (`DP`):** Se o mercado perder a linha roxa com agressão vendedora e falhar no reteste de baixo para cima, o grande bloco virou resistência — **Venda o pullback** mirando a `0DTE PUT WALL`.
  - **Super-Confluência (`BLOCK/MAX VOL` em cima da `CALL WALL` ou `PUT WALL`):** Quando a linha roxa grossa cai exatamente sobre uma Wall, significa que além do maior estoque histórico de Open Interest, o maior fluxo de dinheiro novo de hoje também entrou naquele mesmo strike — **é a barreira mais forte do pregão**.
  - **Outras Linhas de Confluência (`GlobexRangePro` ONH/ONL e `DailyOHLCPro` PDH/PDL/PDC):** Quando uma `CALL WALL` ou `PUT WALL` coincide a poucos ticks da Máxima/Mínima do Globex (`ONH`/`ONL`) ou da Máxima/Mínima do Dia Anterior (`PDH`/`PDL`), a taxa de acerto da reversão/absorção supera **80%+**, pois une os algoritmos de opções aos traders de Price Action/ICT que operam liquidez de máximas e mínimas diárias.
