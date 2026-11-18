# Arquitetura Realista: Indicadores Dark Pool (Feixes Lilás), NYSE $TICK / Correlação e Caixinha de Desequilíbrio Piscante no NinjaTrader 8

> **Princípio Inegociável do Projeto:** Zero dados artificiais ou simulados com números aleatórios. Este documento separa com **100% de transparência técnica** o que já existe em tempo real gratuito, o que funciona nativamente dentro do NinjaTrader 8 a 0ms de atraso e onde existe limitação estrutural de feeds gratuitos (e como resolver).

---

## Visão Geral dos 3 Novos Módulos Propostos para o NinjaTrader 8

| Módulo (C# NinjaScript + SharpDX) | Fonte dos Dados Reais | Latência Real | Como Aparece Visualmente no Gráfico |
| :--- | :--- | :--- | :--- |
| **1. `DarkPoolBeamsPro`** *(Feixes Lilás + Barra de Força)* | API do Dashboard (`/api/macro-darkpool` via HTTP a cada 15–30s): Blocos `1m` (SEC/FINRA SIP) + Tabela Oficial Diária FINRA Reg SHO | Blocos `1m` (~1 min) + FINRA Oficial Diário (pós-fechamento ET) | **Feixes de luz lilás/magenta luminescentes** (`LinearGradientBrush`) com brilho pulsante em prints recentes + Tag Dark Pool (`$M`, `Vol 1m`, `ASK ABSORPTION` / `BID SUPPORT`) + **Barra de força `% Buy/Long vs % Short`** + selo **`EXEMPT SPIKE` / `MEGA NOTIONAL`**. |
| **2. `NyseTickBreadthPro`** *(Correlação & Breadth ao Vivo)* | **Modo A:** Série nativa `$TICK` / `TICK-NYSE` do próprio NinjaTrader (se o feed do cliente incluir NYSE).<br>**Modo B:** API do Dashboard (`/api/market-context`) para `VIX`, `HYG`, `DXY`, `ZN`, `ES`, `NQ`, `YM`, `RTY` + Breadth Proxy ao vivo | **0ms** no Modo A (IQFeed/Kinetick); **~20s** no Modo B (Dashboard JSON) | Painel compacto multi-ativos sincronizado com o gráfico aberto + termômetro visual **`NYSE $TICK`** + aviso transparente da fonte (`Feed Nativo` vs `Proxy Cesta Ao Vivo`). |
| **3. `OrderFlowImbalanceFlash`** *(Caixinha Piscante Compra vs Venda + Níveis)* | **100% Nativo do NinjaTrader 8** (`OnMarketData`: `Last >= Ask` vs `Last <= Bid` tick a tick direto da corretora!) | **0ms — Tempo Real Puro (Tick-a-Tick)** em **QUALQUER** ativo! | **Caixinha HUD piscando em Verde Neon / Vermelho Neon** quando ocorre desequilíbrio agressivo na janela configurável (ex.: `5s` / `candle`), mostrando **Volume Ask vs Volume Bid**, **Saldo Delta**, **Ratio (`3.2x`)** e os **níveis de preço com Imbalance Diagonal ativo** marcados direto sobre os candles! |

---

## 1. Módulo `DarkPoolBeamsPro`: Correlação Real Por Ativo (Onde Funciona 100% Real vs. Exceções Honestas)

Quando você coloca o indicador em qualquer gráfico do NinjaTrader 8, o código em C# identifica automaticamente `Instrument.MasterInstrument.Name` e consulta a rota `/api/macro-darkpool` do seu Dashboard, selecionando **apenas os fluxos Dark Pool realmente correlacionados àquele mercado**:

### Mapa Exato de Ativos Suportados (`Correlação Real`)

| Ativo Aberto no NinjaTrader 8 | Proxy Dark Pool `1m` (Feixes Lilás com Conversão de Preço) | Contratos / Contexto FINRA Reg SHO Conectados | Precisão & Veredito Honesto |
| :--- | :--- | :--- | :--- |
| **`ES` / `MES`** *(S&P 500)* | **`SPY`** (`Preço ETF × (Spot ES ÷ Spot SPY)`) | `SPY`, `HYG`, `XLF`, `JPM`, `BAC`, `GS`, `AAPL`, `MSFT` | **Excelente (Grau A+).** `SPY` reflete 1:1 a carteira do `ES` e concentra o maior volume ETF do mundo; os níveis projetados no gráfico batem exatamente na zona de liquidez do `ES`/`MES`. |
| **`NQ` / `MNQ`** *(Nasdaq 100)* | **`QQQ`** (`Preço ETF × (Spot NQ ÷ Spot QQQ)`) | `QQQ`, `NVDA`, `SMH`, `INTC`, `AMD`, `AAPL`, `MSFT`, `AMZN`, `META`, `GOOGL`, `TSLA` | **Excelente (Grau A+).** Soma a precisão de conversão do `QQQ` com alertas no HUD sobre pressão vendedora ou `ASK ABSORPTION` em `NVDA` e `INTC`. |
| **`YM` / `MYM`** *(Dow Jones)* | **`DIA`** (`Preço ETF × (Spot YM ÷ Spot DIA)`) | `DIA`, `JPM`, `GS` (~7% Dow), `UNH` (Saúde Dow), `BAC`, `XLF`, `INTC` | **Excelente (Grau A).** `DIA` replica os 30 componentes do Dow, e `JPM` + `GS` + `UNH` explicam grande parte da força ou fraqueza financeira/industrial. |
| **`RTY` / `M2K`** *(Russell 2000)* | **`IWM`** (`Preço ETF × (Spot RTY ÷ Spot IWM)`) | `IWM`, `HYG`, `XLF` | **Excelente (Grau A+).** Como o futuro `RTY` tem book mais raso, quase toda a liquidez institucional de Small Caps está no `IWM`. |
| **`GC` / `MGC`** *(Ouro COMEX)* | **`GLD`** (`Preço ETF × (Spot GC ÷ Spot GLD)`) | `GLD`, `TLT` (Bonds inversos ao Yield), `DXY` (via `/api/market-context`) | **Muito Boa (Grau A).** `GLD` guarda ouro físico e replica perfeitamente as zonas institucionais do contrato `GC`/`MGC`. |
| **`ZB`** *(30Y US Treasury Bond)* | **`TLT`** (`Preço ETF × (Spot ZB ÷ Spot TLT)`) | `TLT`, `HYG` | **Muito Boa (Grau A).** O `TLT` acompanha títulos de `20+` anos — praticamente o mesmo duration e regiões técnicas do `ZB`. |
| **`ZN`** *(10Y US Treasury Note)* | *Melhoria recomendada no Backend:* adicionar ETF **`IEF` (7–10Y Treasury)** no `LIVE_PROXY_MAP` | `TLT` (referência macro de curva), e `IEF` (`7–10Y` específico para `ZN`) | **Atenção:** `TLT` (20+Y) tem beta maior que `ZN` (10Y). Adicionar `IEF` no backend garante escala de preço `1:1` fiel para o `ZN`. |
| **`CL` / `MCL`** *(Petróleo WTI)* | *Melhoria opcional:* adicionar **`USO`** (apenas intradiário do mesmo pregão) no `LIVE_PROXY_MAP` | **`USO`** (Petróleo) e **`XLE`** (Empresas de Energia) na tabela FINRA Reg SHO | **Regra Honesta sobre Contango:** como `USO` sofre efeito de rolagem entre vencimentos ao longo de meses, só vale projetar `USO × (CL / USO)` com razão ao vivo calculada **dentro do pregão atual**. Como contexto de fluxo (`% Short`, `Notional`, `BULLISH`/`BEARISH`), `USO + XLE` já funcionam de forma real! |
| **`NG`** *(Gás Natural NYMEX)* | **Sem proxy Dark Pool `1m` recomendado** | Nível GEX nativo + Order Flow próprio (`OrderFlowImbalanceFlash`) | O ETF de gás (`UNG`) tem distorção estrutural severa e baixo valor preditivo intraday no futuro `NG`. **Não forçar correlação artificial!** |
| **Ações/ETFs Diretos** (`SPY`, `QQQ`, `JPM`, `INTC`, `NVDA`, `IWM`, `TLT`, `GLD`) | **Próprio Ticker `1:1`** | Própria linha FINRA + `Mcap`, `Short Float`, `Inst Own %`, `Short Exempt` | **Precisão absoluta `1:1`** — o feixe lilás desenha exatamente no centavo do bloco `1m`. |

### Como Será o Visual "Feixe de Luz Lilás + Barra de Força" (SharpDX `OnRender`)
Ao contrário de linhas horizontais comuns (`Draw.Line`):
1. **Feixe de Luz Multicamada (`Aura Lilás`):** Para cada print `1m` (`$M` notável), desenhamos uma faixa vertical fina (`±1` a `±3` ticks do nível convertido) com `LinearGradientBrush` vertical transparente nas bordas (`Alpha 0 -> Alpha 110 -> Alpha 0` em roxo/lilás `#A855F7` / `#E879F9`) + núcleo brilhante de `1.5px`.
2. **Efeito Pulsante Somente em Prints Recentes:** Para não poluir ou distrair no gráfico todo, apenas o **print mais recente ou o print a menos de N ticks do preço atual** varia suavemente a intensidade do brilho (`Alpha` oscilando entre `55%` e `100%` com um *timer* leve de `250ms` ou a cada atualização de bar/tick). Prints antigos do dia ficam como "cicatrizes" estáticas discretas no gráfico!
3. **Tag Flutuante + Mini Barra de Força na Direita:**
   - Rótulo escuro com borda lilás:
     `DP SPY→ES | $288M (28.1x) | ASK ABSORPTION`
   - Logo abaixo ou dentro da tag, uma **Barrinha Bicolor de Força FINRA** (Verde = `% Buy/Long`, Vermelha = `% Short` + badge **`EXEMPT SPIKE`** / **`BEARISH`** / **`BULLISH`**) vinda diretamente dos registros oficiais da FINRA!

---

## 2. Módulo `NyseTickBreadthPro`: Como Ter `$TICK` + Correlação Real no NinjaTrader 8

Para manter **zero artificialidade**, o comportamento depende do provedor de dados que você usa dentro do NinjaTrader 8:

1. **Cenário 1 — Você usa feed multi-bolsa que inclui Índices NYSE (`IQFeed`, `Kinetick`, ou add-on Stocks/Indices):**
   - O indicador assina diretamente `AddDataSeries("$TICK", BarsPeriodType.Minute, 1)` (ou símbolo equivalente da sua corretora) dentro do NinjaTrader 8.
   - **Resultado:** Histograma e painel **`NYSE $TICK`** 100% real em **milissegundos**, destacando picos extremos **`> +800 / +1.000`** (compra institucional programada em cesta) e **`< -800 / -1.000`** (liquidação em cesta / fundo de exaustão na `Put Wall`).
2. **Cenário 2 — Você usa apenas corretora / mesa proprietária de Futuros CME (`Rithmic`, `Tradovate`, `NinjaTrader Brokerage Futures`):**
   - Contas CME-only **não** recebem o ticker oficial `$TICK` da bolsa de ações NYSE por bloqueio de licença entre bolsas.
   - **Como resolver de forma real sem inventar números:** o indicador conecta no endpoint `/api/market-context` do seu Dashboard a cada `15–20s` e mostra:
     - O painel **Correlação Ao Vivo** já adaptado ao ativo do gráfico (ex.: se o gráfico aberto for **`NQ`**, destaca **`ES`, `QQQ`, `HYG`, `VIX`, `ZN`, `NVDA`**; se for **`GC`**, destaca **`DXY`, `ZN`, `GLD`, `SI`, `EURUSD`, `USDJPY`**; se for **`ES`**, destaca **`HYG`, `VIX`, `NQ`, `YM`, `RTY`, `ZN`**).
     - O termômetro **`Breadth Tick Proxy`** calculado de verdade sobre as barras de 5m das 12 líderes reais (SPY, QQQ, IWM, DIA, HYG, Mag 7), sempre exibindo o selo transparente **`PROXY CESTA (~20s)`** para você nunca confundir com feed milissegundo direto da NYSE.

---

## 3. Módulo `OrderFlowImbalanceFlash` (Estilo Bookmap *Market Pulse*): Caixinha Piscante Real + Áudio Dinâmico por Velocidade e Volume

Sim — inspirado diretamente no conceito de **Market Pulse do Bookmap**: em vez de depender só de uma barra fixa por candle, o indicador mede em **tempo real contínuo** a **velocidade + aceleração do fluxo comprador vs. vendedor (`Trades/seg` e `Volume/janela`)** direto no livro real da corretora, traduzindo isso em uma caixinha piscante **Verde/Vermelha** e em pulsos sonoros não-vocais cujo ritmo e tom mudam conforme o apetite de agressão acelera!

Este módulo roda **100% local e em tempo real puro (0ms de atraso)** dentro do NinjaTrader 8 para **QUALQUER ativo do seu gráfico** (`ES`, `MES`, `NQ`, `MNQ`, `YM`, `RTY`, `GC`, `CL`, `NG`, `ZB`, `ZN`, `6E` ou ações) — sem depender de API externa!

### Por que ele é 100% Real (Não Estimado)?
Dentro do método `OnMarketData(MarketDataEventArgs e)` do NinjaTrader 8 (`Tick-by-Tick`):
- Quando chega um negócio real (`e.MarketDataType == MarketDataType.Last`):
  - Se `e.Price >= GetCurrentAsk()` → soma `e.Volume` no balde **Compra Agressiva (Ask)** do nível de preço `e.Price` e da janela móvel recente (ex.: últimos `10 segundos` ou candle atual).
  - Se `e.Price <= GetCurrentBid()` → soma `e.Volume` no balde **Venda Agressiva (Bid)** do nível de preço `e.Price` e da janela móvel.
  *(Nota importante do NinjaTrader: para calcular em histórico passado + tempo real sem perder ticks, usa `TickReplay` ligado ou começa a acumular em tempo real a partir do momento em que abre o gráfico!)*

### Como Funciona a "Caixinha Piscante" e os Níveis de Preço
1. **Janela Deslizante Ao Vivo (ex.: últimos `5s` a `15s` + Candle Atual):**
   - Mantém uma fila FIFO dos últimos negócios reais por timestamp.
   - Exibe uma **Caixinha HUD fixa** no canto escolhido (ex.: canto superior direito ou flutuando ao lado do último preço) com 4 linhas ultra-legíveis:
     - **`BUY (ASK):` `1.120` | `SELL (BID):` `310`**
     - **`DELTA JANELA:` `+810` (`Ratio 3.61x ASK`)**
     - **Mini Barra Horizontal Verde/Vermelha de Pressão Instantânea**
     - **Top 2 Níveis de Preço com Desequilíbrio Diagonal Ativo agora:**
       - `▲ BUY IMB @ 7.342,50 (340 vs 65)`
       - `▼ SELL IMB @ 7.348,25 (410 vs 90)`
2. **Lógica do "Piscar" Verde / Vermelho (Sem Poluição Visual):**
   - **Estado Neutro (Caixa Escura Discreta):** Quando `Buy` e `Sell` estão equilibrados (`Ratio < 2.5x`) ou o volume mínimo da janela (`MinVolume`, ex.: `150 ctrs` no `ES`, `80 ctrs` no `NQ`, `40 ctrs` no `GC`/`CL`) ainda não foi atingido.
   - **Alerta Comprador (Caixa Pisca em Verde Neon `#10B981`):** Quando `Volume Total >= MinVolume` e `Buy >= Ratio × Sell` (ex.: `>= 2.5x` ou `>= 3.0x`) — sinalizando explosão real de agressão compradora no *Ask* ou *Short Covering*!
   - **Alerta Vendedor (Caixa Pisca em Vermelho Neon `#F43F5E`):** Quando `Volume Total >= MinVolume` e `Sell >= Ratio × Buy` — sinalizando despejo agressivo no *Bid*!
   - *(Bônus de Desenho nos Candles)*: Sempre que um nível de preço atinge **Imbalance Diagonal (`Ask(p) >= 3× Bid(p-tick)` ou `Bid(p) >= 3× Ask(p+tick)`)**, o indicador marca um traço horizontal verde/vermelho curto exatamente naquele preço dentro do candle, permitindo enxergar **onde ocorreu a defesa/rompimento** junto dos **Feixes Lilás Dark Pool** e das linhas **GEX**!

### Sons Não-Vocais Proporcionais ao Volume & Velocidade (Estilo Bookmap *Market Pulse*)
Assim como o **Market Pulse do Bookmap**, você identifica explosões de compra ou venda **pelo ouvido sem tirar o olho dos candles** — sem voz sintética falando em cima do trade, usando **ritmo + altura do som** guiados pela velocidade e pelo volume líquido da janela:

| Nível de Intensidade (Volume + Velocidade vs. Linha de Base) | Compra Agressiva (`ASK` Dominante — Tom Agudo/Ascendente) | Venda Agressiva (`BID` Dominante — Tom Grave/Descendente) | Cadência Dinâmica (*Market Pulse*) & Anti-Travamento |
| :--- | :--- | :--- | :--- |
| **Nível 1: Pulso Inicial** (`>= 1× MinVolume` & `Ratio >= 2.5x`) | Clique tonal agudo suave (`660 Hz`, `40 ms`) | Clique tonal grave discreto (`330 Hz`, `45 ms`) | Cadência lenta (`~650–800 ms`): avisa o início do desequilíbrio sem cansar o ouvido. |
| **Nível 2: Pressão Forte** (`>= 2× MinVolume` & `Ratio >= 2.8x`) | Tom médio-agudo firme (`880 Hz`, `55 ms`) | Tom grave encorpado (`247 Hz`, `65 ms`) | Cadência acelera (`~400 ms`), mostrando que o ritmo (*Tape Speed*) e o volume continuam crescendo. |
| **Nível 3: Clímax / Sweep Institucional** (`>= 4× MinVolume`) | Duplo pulso cristalino agudo (`1175 Hz`, `70 ms`) | Pulso sub-grave pesado (`185 Hz`, `80 ms`) | Cadência rápida (`~200–250 ms`), funcionando igual ao **pulso acelerado do Market Pulse** no rompimento ou exaustão! |

- **Implementação Técnica Limpa em C# (.NET 4.8 no NinjaTrader 8):**
  - Nunca usar `Console.Beep()` no thread principal do gráfico (ele trava a renderização no Windows).
  - Em vez disso, gerar os buffers **WAV PCM senoidais em memória RAM (`MemoryStream`)** na inicialização (`OnStateChange`) com envoltória suave (*fade-in / fade-out* sem cliques) e disparar via **`System.Media.SoundPlayer` assíncrono com controle `Stopwatch` + botão de Mute rápido** — latência zero no `OnMarketData`!

---

## 4. Resumo: Como Tudo Se Conecta no Próximo Passo (Quando Você Quiser Construir em C#)

1. **Ajuste opcional no Dashboard Web (Passo rápido antes do C#):**
   - Incluir **`IEF`** (`7-10Y Treasury` para o futuro `ZN`) e **`USO`** (`Petróleo intradiário` para o futuro `CL`) na lista `LIVE_PROXY_MAP` do endpoint `/api/macro-darkpool`, elevando a cobertura `1m` de proxies reais para `ES, NQ, YM, RTY, GC, ZB, ZN e CL`!
2. **Atualização do `instalador_cloud2.0.py` (3 novos indicadores C# SharpDX):**
   - **`DarkPoolBeamsPro`**: consome `/api/macro-darkpool`, filtra automaticamente pelo contrato ativo no gráfico do NinjaTrader e renderiza feixes lilás pulsantes + barra de força FINRA + tags `$M`/`Short Exempt`.
   - **`NyseTickBreadthPro`**: lê `$TICK` nativo (se disponível no feed do usuário) ou consome `/api/market-context` para painel de correlação adaptativa por ativo + `Breadth Tick Proxy`.
   - **`OrderFlowImbalanceFlash`**: lê `OnMarketData` tick-a-tick real no NinjaTrader 8 e acende a caixinha piscante verde/vermelha com volumes Compra/Venda e marcações de níveis de preço com desequilíbrio diagonal.
