# Manual Técnico e Operacional dos Indicadores NinjaTrader 8 (Ecossistema Quant V9)

Este documento reúne a explicação **Teórica e Prática** dos novos indicadores incorporados ao ecossistema (`VolatilidadeImplicitaPro`, `FluentliExpectedMove`, `DeltaCumulativePro` e `VWAPInstitucionalPro`) e sua integração direta com `instalador_cloud2.0.py` e `gex_profile_v7_cloud.py`.

> **Nota:** Estes 4 módulos (junto com `NiveisEstruturaPro`, `NiveisGammaPro`, `MoneyRiskPro`, `DailyOHLCPro`, `GlobexRangePro` e `GEX Cloud Engine`) também foram adicionados com diagramas `.svg` interativos e suporte a leitura em voz na **Biblioteca do Dashboard Web** (`gex-dashboard/public/ebooks/`).

---

## 1. `VolatilidadeImplicitaPro` (Embutido em `instalador_cloud2.0.py`)

### A. Teoria e Extração de Dados
- **Origem dos Dados (`gex_profile_v7_cloud.py`):** O coletor extrai da API interna do Barchart a **Volatilidade Implícita (IV) e as gregas reais por strike** (`volatility,delta,gamma,theta,vega`), calcula a IV representativa At-The-Money (`IV_Real_ATM`) e grava em `AlvosVolatilidade_{ATIVO}.csv` (coluna 4 = `IV%`, coluna 13 = `IVSource`).
- **Ancoragem na Abertura:** Na primeira barra da sessão (`Bars.IsFirstBarOfSession`), o indicador fixa `sessionAnchorPrice = Open[0]` e calcula o desvio-padrão diário pela anualização de 252 dias úteis (`sqrt(252) ≈ 16`):
  $$\text{dem} = \text{sessionAnchorPrice} \times \frac{\text{currentIV}}{1600}$$
- **As 6 Bandas Estatísticas:**
  - `1 SD (+68%)` e `-1 SD (-68%)`: `Open ± 1 × dem` (tracejadas verde e vermelha).
  - `2 SD (+95%)` e `-2 SD (-95%)`: `Open ± 2 × dem` (sólidas verde escura e vermelha escura).
  - `3 SD (+99% MAX)` e `-3 SD (-99% MAX)`: `Open ± 3 × dem` (sólidas magenta grossas).
- **Melhorias V9:** Leitura com `FileShare.ReadWrite` sem apagar `ivVal` durante a sincronização do Dropbox (zero piscada), suporte a todos os Micro Futuros (`MES`, `MNQ`, `M2K`, `MYM`, `MCL`, `MGC`, `MNG`/`QG`) e exibição do preço exato no texto de cada linha.

### B. Aplicação Prática
- **Em `LONG GAMMA`:** Quando a `1 SD (+68%)` ou `-1 SD (-68%)` coincide com a `Call Wall` ou `Put Wall` do `NiveisGammaPro`, opere reversão de volta para a `VWAPInstitucionalPro`.
- **Em `SHORT GAMMA`:** O rompimento com aceitação além da `1 SD` abre alvo direto até a banda de `2 SD (+95% / -95%)`, onde `95,4%` dos movimentos diários se esgotam e exigem realização de lucro.

---

## 2. `FluentliExpectedMove` (Embutido em `instalador_cloud2.0.py`)

### A. Teoria e Funcionamento
- **Por que Nuvens (`Draw.Rectangle`):** Em vez de uma linha única, projeta duas zonas acolchoadas de liquidez com espessura configurável em ticks (`raio = (EspessuraNuvem * TickSize) / 2.0`) em torno de `upperBand` (**Nuvem de Venda / Topo**, vermelha) e `lowerBand` (**Nuvem de Compra / Fundo**, azul).
- **Motor Híbrido (Dropbox 9 Ativos + Yahoo VIX):**
  - Carrega sincronamente na abertura a IV de `AlvosVolatilidade_{ATIVO}.csv` do Dropbox para todos os 9 ativos e seus Micros (`ES/MES`, `NQ/MNQ`, `GC/MGC`, `CL/MCL`, `ZB`, `ZN`, `YM/MYM`, `RTY/M2K`, `NG/QG`).
  - No `ES/MES`, também consulta assincronamente o `^VIX` no Yahoo Finance e recalcula imediatamente as nuvens em `OnBarUpdate()` assim que `VixInterno` é atualizado (`Math.Abs(VixInterno - ultimoVixCalculado) > 1e-6`).
  - Opacidade corrigida (aplicada uma única vez em `Draw.Rectangle`) e HUD posicionado em `BottomLeft` para não colidir com outros indicadores.

### B. Aplicação Prática
- **Gatilho na Nuvem Azul (Compra):** Aguarde o preço entrar na Nuvem Azul inferior, deixar pavio de rejeição com absorção confirmada no `DeltaCumulativePro` e fechar um candle saindo acima da borda superior da nuvem. Stop técnico logo abaixo da borda externa da nuvem.
- **Gatilho na Nuvem Vermelha (Venda):** Aguarde exaustão compradora dentro da Nuvem Vermelha superior e feche venda quando o candle perder a borda inferior da nuvem.

---

## 3. `DeltaCumulativePro` (`DeltaCumulativePro.py`)

### A. Teoria e Cálculo Tick-by-Tick (`OnMarketData`)
- **O que mede:** Saldo acumulado de agressão a mercado (`sessionDelta`) desde a abertura da sessão (`Bars.IsFirstBarOfSession`).
- **Como funciona no código:**
  - Adiciona internamente uma série de 1 Tick (`AddDataSeries(BarsPeriodType.Tick, 1)`) para ler cada negócio real (`MarketDataType.Last`).
  - Negócio executado no `Ask` (`price >= e.Ask`) = **Agressão Compradora** (`sessionDelta += volume`).
  - Negócio executado no `Bid` (`price <= e.Bid`) = **Agressão Vendedora** (`sessionDelta -= volume`).
  - Negócio no spread = desempate comparando com `Close[0]`.
  - Plota barras em **Azul (`DodgerBlue`)** quando o saldo da sessão é comprador (`>= 0`) e **Vermelho (`Red`)** quando vendedor (`< 0`).

### B. Aplicação Prática com o GEX
1. **Absorção na `Put Wall` (Compra):** O preço toca na `Put Wall`, o `DeltaCumulativePro` faz uma nova mínima mais funda (vendedores batendo a mercado), mas o candle de preço **não renova a mínima** e fecha positivo. Prova que os Dealers absorveram toda a venda passivamente.
2. **Absorção na `Call Wall` (Venda):** O preço bate na `Call Wall`, o `DeltaCumulativePro` faz topo mais alto, mas o candle trava na parede e perde a mínima (*Trapped Buyers*).
3. **Validação de Rompimento (`GEX Flip`):** Só opere rompimento do `GEX Flip` quando preço e `DeltaCumulativePro` caminharem juntos na direção do rompimento.

---

## 4. `VWAPInstitucionalPro` (`vwap.py`)

### A. Teoria e Matemática da Variância Ponderada por Volume
- **Cálculo Incremental:** Em cada tick (`Calculate.OnEachTick`), calcula o preço típico `P = (High + Low + Close) / 3` e o incremento de volume `volumeDelta = Volume[0] - lastBarVolume`, acumulando desde o início da sessão:
  - `sumPV += P * volumeDelta`
  - `sumVol += volumeDelta`
  - `sumP2V += P² * volumeDelta`
- **Fórmula da VWAP e Desvio-Padrão (`StdDev`):**
  $$\text{VWAP} = \frac{\text{sumPV}}{\text{sumVol}}, \qquad \text{StdDev} = \sqrt{\max\left(0,\; \frac{\text{sumP2V}}{\text{sumVol}} - \text{VWAP}^2\right)}$$
- **As 9 Linhas Plotadas:**
  - **Linha Central Amarela Grossa (`VWAP`):** Preço justo institucional da sessão.
  - **`Top/Bot SD1` (Azul Pontilhada):** Borda da área de valor normal (`±1σ`).
  - **`Top/Bot SD2` (Ciano Tracejada):** Zona de valor extremo (`±2σ`).
  - **`Top/Bot SD3` (Laranja Sólida):** Zona de exaustão intradiária (`±3σ`).
  - **`Top/Bot SD4` (Vermelha Sólida Grossa):** Ponto de reversão extrema / *Crash-Boom* (`±4σ`).

### B. Aplicação Prática com os Regimes GEX
1. **Em Regime `LONG GAMMA` (Painel Verde):** A linha amarela da `VWAP` funciona como **ímã central e alvo principal**. Compre rejeições em `Put Wall + Bot SD2/SD3` mirando retorno até a `VWAP` central; venda rejeições em `Call Wall + Top SD2/SD3` mirando retorno até a `VWAP`.
2. **Em Regime `SHORT GAMMA` (Painel Vermelho):** Quando o preço perde o `GEX Flip` com força, ele caminha entre a banda `SD1` (azul) e `SD2` (ciano). Use o toque de pullback na `SD1` (ou na `VWAP`) para entrar a favor da tendência até `SD2/SD3`.
3. **Realização Obrigatória em `SD3` e `SD4`:** Ao tocar nas bandas laranja (`SD3`) ou vermelha (`SD4`), realize lucros de tendência e jamais abra novas ordens a favor do rompimento esticado.
