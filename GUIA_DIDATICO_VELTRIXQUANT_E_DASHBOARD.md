# Guia Didático de Engenharia & Programação — Suite **VeltrixQuant** (NT8 + Web TradingView Studio)

> **Para Alan (trilha de aprendizado em Engenharia & Quant Dev):** este guia explica, passo a passo e sem "caixa-preta", **por que cada ajuste foi feito**, **quais conceitos de programação foram usados** (React/Next.js, Lightweight Charts v5, C#/.NET Framework 4.8, HTTP/TLS, parser JSON manual, síntese de áudio PCM WAV em memória e GPU SharpDX) e **como o NinjaTrader 8 organiza pastas, classes e templates**.

---

## 1. Dúvida Importante: O Paper Trading da Web loga em alguma corretora?

**Não.** O Paper Trading do Dashboard Web é um **simulador 100% local no seu navegador** (gerenciado pelo hook `usePaperAccount` em [usePaperAccount.ts](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/lib/paper/usePaperAccount.ts)):
- **Saldo inicial virtual:** **`$50,000.00`** salvos no `localStorage` do seu navegador.
- **Execução das ordens:** quando você clica em Compra/Venda a Mercado, Ordem Limite, Stop ou Bracket OCO / Trailing Stop na Boleta, a engine verifica em tempo real os **candles gratuitos do Yahoo Finance** (delay regulatório ~10–15 min em futuros CME / near real-time em ETFs) para acionar stops, alvos e calcular P&L — **zero conexão com Tradovate, Rithmic, Interactive Brokers ou corretora real**, e **zero risco financeiro real**.
- **Onde você opera em corretora Demo/Prop Firm?** No **NinjaTrader 8** conectado à sua conta **Tradovate Demo** (ou Rithmic/IQFeed no futuro), usando a suíte **`VeltrixQuant`**.

---

## 2. Melhorias no Dashboard Web (`gex-dashboard`)

### 2.1. Fim do Reload/Piscada Visual a Cada 1 Minuto (`app/page.tsx`)
- **Por que acontecia antes?** Toda vez que o cronômetro de `60s` disparava o fetch de atualização em segundo plano, a função chamava `setLoading(true)`, o que desmontava o gráfico (`TradingViewGexChart`), a curva GEX e os painéis até os novos dados chegarem — zerando o visual a cada minuto.
- **Como foi resolvido (Padrão Stale-While-Revalidate):**
  - Introduzida uma referência mutável `hasInitialLoadRef` (que guarda `false` na primeira carga e vira `true` assim que os primeiros dados carregam) combinada com o estado `isRefreshing`.
  - Nos ciclos automáticos de 1 minuto (ou troca suave em segundo plano), `isRefreshing` apenas gira discretamente o ícone do botão de atualização **sem desmontar nenhum gráfico** — mantendo seu zoom, arraste, boleta aberta e templates intactos.

### 2.2. Templates Salvos, Cores & Fundo do TradingView (`TradingViewGexChart.tsx`)
- O estado visual divide-se em dois objetos tipados (`CandleThemeConfig` e `IndicatorConfig`) gravados no `localStorage`:
  - `gex_tv_templates_v1`: lista com todos os seus templates nomeados (além dos presets built-in como `Quant Neon Dark`, `Institutional Clean + Dark Pool` e `Modo Claro / Alto Contraste`).
  - `gex_tv_default_template_v1`: ID do template marcado com estrela (**★ Padrão**). Quando você abre ou recarrega o navegador, `loadInitialTvSetup()` restaura automaticamente esse template antes mesmo do gráfico renderizar.
- **Todos os indicadores configuráveis em cores/espessuras:** Candles, fundo, grade, linhas GEX (`Call Wall`, `Put Wall`, `GEX Flip`, `0DTE`, `POC`), barras de estrutura (`TradingViewProfileOverlay`), `VWAP` + Desvios (`vwapWidth` 1–3px), `Daily OHLC`, `Globex Range`, `Expected Move`, **`MoneyRiskPro`**, **`DeltaCumulativePro`** e clusters **`DarkPool`**.

### 2.3. Sub-Painel Real do `DeltaCumulativePro` + `MoneyRiskPro` + Barra `$TICK*`
- **`DeltaCumulativePro` (`BaselineSeries` no Pane 1):** Na biblioteca `lightweight-charts` v5, passar `paneIndex = 1` como terceiro argumento de `chart.addSeries(BaselineSeries, ..., 1)` cria automaticamente um **sub-painel exclusivo abaixo dos candles** (com linha de base em `0`, preenchimento verde acima e vermelho abaixo), calculado por `computeCandleDeltaFlow(candles)`.
- **`MoneyRiskPro` na Web:** Plota diretamente sobre os candles os 3 níveis automáticos baseados no ATR e risco máximo configurável (`moneyRiskMaxUsd`): **`RISK STOP`**, **`ALVO 1:1`** e **`ALVO 2:1`**, além do HUD **`MONEY RISK PRO`** com Stop Ideal (pts), Alvo 2:1 e Stop Estático em USD.
- **Faixa `Pulso Macro & NYSE $TICK*`:** Agora permanece visível assim que ativada, exibindo estado de sincronização/reconexão com `/api/market-context` em vez de desaparecer silenciosamente se uma requisição demorar.

### 2.4. Relatório Profissional de Performance (`PaperPerformanceModal.tsx`)
- Cada fechamento no `usePaperAccount` agora grava também `openedAt`, `plannedStopLoss`, `plannedTakeProfit`, `plannedRiskUsd`, `realizedRR` e `pointValue` (até 500 trades no histórico).
- O modal **Relatório de Performance** calcula em tempo real: **Saldo Líquido & Retorno %**, **Win Rate %**, **Profit Factor**, **Payoff / R:R Médio Realizado**, **Expectancy ($/trade)**, **Max Drawdown ($ e %)**, **Sequências Máximas de Gains/Losses**, **Contagem por Motivo (`Take Profit` vs `Stop Loss` vs `Trailing Stop` vs `Manual/Flatten`)**, **Curva de Equity em SVG** e **Exportação CSV**.

---

## 3. Pasta da Marca `VeltrixQuant` no NinjaTrader 8 (`instalador_cloud2.0.py`)

### Como o NinjaTrader 8 organiza Pastas vs. Menu `Ctrl+I` vs. Templates Salvos
1. **Pasta Física (`Custom/Indicators/VeltrixQuant/`):** Organização visual no **NinjaScript Editor** (`F5`). Ao mover os `.cs` para dentro de `VeltrixQuant/`, **removemos obrigatoriamente cópias soltas da raiz** para evitar erro de compilação duplicada (`CS0101`/`CS0102`), e **nunca tocamos** nos arquivos nativos `@*.cs` do próprio NinjaTrader.
2. **`namespace` C# mantido intacto (`NinjaTrader.NinjaScript.Indicators`):** O compilador do NinjaTrader exige que indicadores herdem e compilem dentro desse namespace raiz; subpastas no disco funcionam sem mudar o namespace.
3. **Nome da Classe (`ClassName`) vs. Nome Exibido (`Name`):**
   - **Chart Templates (`.xml`) e Estratégias** salvam o **ClassName** (ex.: `NiveisEstruturaPro`, `VWAPInstitucionalPro`, `FluentliWatchdog`). Preservando os nomes de classe originais, **nenhum gráfico ou bot existente quebra**.
   - **Lista de Indicadores (`Ctrl+I`)** ordena pela propriedade **`Name = "VeltrixQuant - ..."`** definida em `State.SetDefaults`. Assim, todos os **13 indicadores** ficam agrupados juntos sob a letra `V`.

---

## 4. Engenharia dos 3 Novos Indicadores no NinjaTrader 8

### 4.1. `DarkPoolBeamsPro` — Feixes de Luz Lilás + Barra de Força FINRA
- **Sem DLL Externa (Zero Erro no `F5`):** O NinjaTrader 8 não referencia `System.Web.Extensions.dll` nem `Newtonsoft.Json` por padrão. Para garantir compilação com **1 clique (`F5`)**, embutimos um parser JSON recursivo puro em C# (`VeltrixJsonParser`, usando `CultureInfo.InvariantCulture` para que o Windows em português com vírgula `,` não quebre decimais com ponto `.`).
- **Conexão HTTPS Moderna:** `VeltrixTimeoutWebClient` força TLS 1.2 (`(SecurityProtocolType)3072`) e descompressão GZip/Deflate com timeout de `7000ms` em uma `Thread`/Timer separada — a rede nunca trava a thread da UI/candles.
- **Correlação Automática Multi-Ativos:** A função `ResolveTargetBasket()` extrai o token raiz do instrumento (`ES/MES -> SPY`, `NQ/MNQ -> QQQ`, `RTY/M2K -> IWM`, `YM/MYM -> DIA`, `GC/MGC -> GLD`, `ZB -> TLT`, `ZN -> IEF` com fallback `TLT`, `CL/MCL -> USO`) usando divisão por delimitadores (evitando bugs como `"AMZN".Contains("ZN")`).
- **Feixes Luminosos em SharpDX (`LinearGradientBrush`):** Desenhados em 3 camadas (aura externa + degradê horizontal transparente-para-lilás/esmeralda/magenta + filamento laser central pulsante) com **etiquetas anti-colisão** e micro-barra de força interna proporcional ao `AbsorptionScore`, mais o card **FINRA Reg SHO** (`% Compra/Non-Short vs % Short`).

### 4.2. `NyseTickBreadthPro` — Híbrido **Modo A Automático** (`$TICK` + Correlação)
- **Detecção Segura em `State.Configure`:** Verifica por Reflection as conexões ativas (dando prioridade a `TICK.Z` se **IQFeed** estiver conectado; caso contrário `^TICK`, `$TICK`, `TICK-NYSE`) e só chama `AddDataSeries(...)` se `Instrument.GetInstrument(...)` retornar instrumento válido — zero risco de travar com erro em conta **Tradovate Demo** / **Rithmic** sem feed Cash Index.
- **Árbitro Híbrido em Tempo Real (`IsModoAActiveNow`):**
  - Se houver feed nativo vivo recebendo ticks reais -> exibe **`MODO A · FEED NATIVO`**.
  - Se estiver na Tradovate Demo sem `$TICK` nativo -> alterna transparentemente para **`MODO B · PROXY WEB (~15s)`** via `/api/market-context` e ainda mostra `TICKQ`, `ADD`, `VIX` e a matriz de correlação adaptada ao ativo aberto (`ES` ou `NQ`).

### 4.3. `OrderFlowImbalanceFlash` — Estilo Bookmap *Market Pulse* + Áudio PCM Binário
- **Fluxo de 0ms em `OnMarketData`:** Classifica cada execução (`MarketDataType.Last`) contra `Ask`/`Bid` reais em tempo real dentro de uma janela deslizante (`Queue<TradeSample>`) usando estritamente o mesmo relógio do evento (`e.Time`) para inserir e expirar amostras.
- **Botão `[SOM: ON/MUTE]` DPI-Aware:** Converte as coordenadas do clique via `ChartingExtensions.ConvertToHorizontalPixels(..., ChartControl.PresentationSource)` para funcionar perfeitamente mesmo em monitores 4K ou Windows com escala `125%` / `150%`.
- **Síntese de Áudio Não-Vocal em Memória (`PcmToneSynthesizer`):**
  - Gera 6 arquivos `.wav` binários em RAM (`MemoryStream` + cabeçalho RIFF/PCM 16-bit mono 22050Hz) carregados em 6 `System.Media.SoundPlayer`:
    - **Compra (Agudos Ascendentes):** `L1` (`784->880Hz`), `L2` (`988->1244Hz`), `L3 Clímax` (`1175->1568Hz`).
    - **Venda (Graves Descendentes):** `L1` (`349->311Hz`), `L2` (`294->220Hz`), `L3 Clímax` (`220->146.8Hz`).
  - **Cadência Progressiva com `Stopwatch`:** À medida que o volume/desequilíbrio sobe de L1 para L3, o cooldown cai (`700ms -> 360ms -> 210ms`), criando o efeito sonoro acelerado sem usar fala humana (`SAPI`) nem travar a UI.

---

## 5. Arrastar Stop Loss / Take Profit com o Mouse & Feeds em Tempo Real (`gex-dashboard`)

### 5.1. Drag & Drop no Gráfico (`TradingViewGexChart.tsx` + `PaperTradingBoleta.tsx` + `usePaperAccount.ts`)
- A biblioteca `lightweight-charts` não possui arraste nativo embutido em `IPriceLine`. Para criar essa interação a 60 fps:
  1. As linhas de `OCO TP`, `OCO SL`, `TRAILING SL` e `Ordens Pendentes` são indexadas em `draggableLinesRef`.
  2. Um listener na **fase de captura (`{ capture: true }`)** intercepta `pointerdown` antes do canvas interno do gráfico. Ao clicar dentro de `±11px` da linha (`priceToCoordinate`), travamos temporariamente `handleScroll` / `handleScale`, convertemos o Y do mouse em preço (`coordinateToPrice`), alinhamos ao tick exato do ativo (`snapToInstrumentTick`: `0.25` para ES/NQ, `0.1` para RTY/GC, `0.01` para ETFs/CL/Ações) e mostramos uma pílula flutuante com o novo preço e P&L estimado em dólares.
  3. Ao soltar o mouse (`pointerup`), liberamos o zoom/pan e persistimos no `localStorage` via `updateOpenPositionOco` ou `updatePendingOrderPrice`. Na Boleta Paper, os botões **`+ Criar TP` / `+ Criar SL`** permitem criar proteção com 1 clique caso a posição esteja sem ela.

### 5.2. Corretora Demo em Tempo Real vs. Atraso CME & Alternativas Gratuitas Legítimas (`$0/mês`)
- **Por que nenhuma corretora americana de futuros (Tradovate / Rithmic / AMP) oferece conta demo gratuita infinita com o mesmo Gmail?** A própria bolsa **CME Group** impõe licença mensal de dados Level 1 e restringe trials gratuitos de simulador a **14 dias**. Contas Paper permanentes exigem uma conta real financiada (ex.: *Interactive Brokers* ou *AMP Futures*) ou avaliação ativa de Prop Firm. *(Por política de segurança/compliance, nunca automatizamos criação em massa nem contorno de limite de trial).*
- **O que entregamos agora, de graça (`$0/mês`) e legítimo no Web Dashboard:**
  1. **Cripto (`BTC-USD`, `ETH-USD`) a 0ms nativo:** conecta direto no **WebSocket público da Binance** no navegador.
  2. **ETFs & Ações dos EUA (`SPY`, `QQQ`, `IWM`, `DIA`, `GLD`, `USO`, `TLT`, `NVDA`):** stream SSE acelerado para **2 segundos** (`app/api/candles/stream/route.ts`) + opção no botão **`API Feed Grátis ($0)`** para colar sua própria chave permanente e gratuita do **Finnhub** (`finnhub.io`), ativando **WebSocket em sub-segundo** salvo só no seu navegador.
  3. **Botão 1-Clique em Futuros (`Operar s/ Delay em SPY / QQQ / ...`):** pula instantaneamente do futuro CME com atraso regulatório de 15 min para o ETF americano equivalente mantendo Paper Trade, VWAP, Dark Pool e indicadores ativos.
  4. **Aba `TradingView Oficial` ([TradingViewOfficialWidget.tsx](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/components/TradingViewOfficialWidget.tsx)):** incorpora o widget oficial da `TradingView.com` (padrão `OANDA:SPX500USD`, `OANDA:NAS100USD`, `NASDAQ:QQQ`, `BINANCE:BTCUSDT`) para conferência visual lado a lado; ordens da Boleta Paper e drag de SL/TP operam na aba **Studio Quant** devido à isolação *cross-origin* de iframes do TradingView.
