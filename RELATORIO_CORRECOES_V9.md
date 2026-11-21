# Relatório de Refatoração, Auditoria Quantitativa e Histórico Cronológico (V9)

Este documento segue o padrão oficial definido em [regras.md](file:///C:/Users/alanb/source/gex_profile_v7/gex_profile_v7/regras.md), registrando **Data (`dd/MM/aaaa`)**, **Horário (`HH:mm`)**, **Arquivo**, **Commit** e **Descrição Técnica** de todas as alterações realizadas nos repositórios `gex_profile_v7` e `gex-dashboard`.

---

## 1. Registro Cronológico de Modificações por Data e Horário

### A. Modificações de HOJE — `14/11/2026`

| Data e Horário | Repositório / Arquivo | Commit / Status | O Que Foi Alterado |
|---|---|---|---|
| **`14/11/2026 10:45`** | `VWAPInstitucionalPro.cs`, `DeltaCumulativePro.cs`, `FluentliQuantBot_V1.cs`, `vwap.py`, `DeltaCumulativePro.py` e `instalador_cloud2.0.py` | Commit `65c9a8d` | **1.** Corrigido o erro `CS1955: Non-invocable member 'VWAPInstitucionalPro' cannot be used like a method` na linha 46 de `FluentliQuantBot_V1.cs`: o arquivo `VWAPInstitucionalPro.cs` gerado pelo `vwap.py` antigo não continha o bloco `#region NinjaScript generated code` que expõe o método `Strategy.VWAPInstitucionalPro(...)` (tanto sem parâmetros quanto com a sobrecarga `(4, true, true, 3.0)` chamada pela estratégia).<br>**2.** Atualizado `VWAPInstitucionalPro.cs` (em `Documents\NinjaTrader 8\bin\Custom\Indicators\`, em `vwap.py` e dentro do `instalador_cloud2.0.py`) com as propriedades `NumBandas`, `MostrarBandas`, `ResetDiario`, `DesvioMaximo` e o bloco `#region NinjaScript generated code` completo.<br>**3.** Embutidos `VWAPInstitucionalPro.cs` e `DeltaCumulativePro.cs` v2.0 diretamente no `instalador_cloud2.0.py` (que agora instala os **9 indicadores** de uma vez) e atualizado `LerIVDoEngine()` em `FluentliQuantBot_V1.cs` para ler automaticamente a pasta `Dropbox\RoboGexNinjaV1` (`AlvosVolatilidade_{s}.csv` e `NiveisGamma_{s}.csv`). |
| **`14/11/2026 11:34`** | `instalador_cloud2.0.py`, `Documents\NinjaTrader 8\bin\Custom\Indicators\*.cs`, `public/ebooks/niveisestruturapro/*`, `public/ebooks/niveisgammapro/*` e `MANUAL_TATICO_MESTRE_3_FASES_E_CONFLUENCIAS.md` | Commit `d3f1dcb` / `96ec834` | **1.** Corrigido o caminho padrão do Dropbox (`@"C:\Users\alanb\Dropbox\Dropbox\Aplicativos\RoboGexNinjaV1"`) em `NiveisGammaPro`, `MoneyRiskPro`, `VolatilidadeImplicitaPro`, `FluentliExpectedMove` e `FluentliQuantBot_V1` (que estavam com apenas um `\Dropbox\`, causando o aviso `GEX: arquivo de niveis indisponivel` ao tentar carregar os arquivos salvos de ontem com o mercado fechado).<br>**2.** Documentada em `niveisestruturapro/teoria.md` e `pratica.md` a leitura completa das barras verdes (`+Net GEX`) e vermelhas (`-Net GEX`) quando o mercado está subindo ou caindo (acima e abaixo do preço) e o significado financeiro de `$1M` vs. `$100M+`/`$1B` (*Notional Dealer Gamma Exposure*).<br>**3.** Documentada em `niveisgammapro/teoria.md`, `niveisgammapro/pratica.md` e no novo `MANUAL_TATICO_MESTRE_3_FASES_E_CONFLUENCIAS.md` a Matriz de Decisão do `🛡️ QUANT ENGINE V8` (`LONG GAMMA` verde vs. `SHORT GAMMA` vermelho × `[NEUTRAL]`, `[CALL DOMINANT]`, `[PUT DOMINANT]`) e o **Manual Tático das 3 Fases do Mercado (1. Rompimento/Continuidade, 2. Reversão Alta/Baixa, 3. Lateralização/Pullback)** somando os 9 indicadores do pacote + `MZPack Footprint` + `Jigsaw DOM` + `MZPack Volume Profile` + `MZPack Market Profile (TPO)` em todos os níveis (`GEX Flip`, `Call Wall`, `Put Wall`, Rompimentos das Walls, `Positive Gamma` na Wall, Walls próximas do `Negative Gamma`, `Max Pain` e `Block Order / Max Option Volume`). |
| **`14/11/2026 13:39`** | `public/ebooks/manualtaticomestre/*`, `public/ebooks/manualtaticomestre/imagens/*.svg` e `app/biblioteca/page.tsx` | Commit `3994155` / `e8f448b` | Criada a pasta dedicada `public/ebooks/manualtaticomestre/` contendo o `MANUAL_TATICO_MESTRE_3_FASES_E_CONFLUENCIAS.md` formatado no padrão da Biblioteca, os capítulos `teoria.md` e `pratica.md` (registrados como o 11º módulo no topo de `app/biblioteca/page.tsx`) e **4 diagramas vetoriais institucionais (`.svg`)** em `public/ebooks/manualtaticomestre/imagens/` (`barras_estrutura_e_quant_engine.svg`, `fase1_rompimento_e_continuidade.svg`, `fase2_reversao_topo_e_fundo.svg` e `fase3_lateralizacao_pullback_e_7_niveis.svg`) ilustrando visualmente cada estratégia do manual. |
| **`14/11/2026 13:51`** | `gex-dashboard/app/biblioteca/page.tsx` e `app/globals.css` | Commit `90b83cc` / `3bc5097` | **1. Lightbox de Ampliação + Lupa Interativa (`🔍 Clique para ampliar` + `✕ Fechar`):** Todas as imagens dos 22 e-books agora abrem em tela cheia ao clicar, com controles de zoom (`80%` a `300%`), botão **`🔍 Ativar Lupa`** (lente circular de alta precisão que segue o mouse) e botão **`✕ Fechar`** (ou tecla `ESC`).<br>**2. Motor de Voz Neural Bilíngue (`normalizeTradingSpeechPtBr` + Fix de Acentos `pt-BR`):** Corrigido o bug onde `utterance.lang` herdava `en-US` da voz `Andrew Multilingual` (o que quebrava todos os acentos do português), priorizadas as vozes Neurais Naturais (`Microsoft Thalita Multilingual Online (Natural)`, `Francisca Online (Natural)` e `Antonio Online (Natural)`) com `utterance.lang = "pt-BR"` fixo, seletor de velocidade (`0.9x` a `1.25x`) e dicionário fonético completo para pronunciar termos em inglês (`Heatmap`, `Call Wall`, `Put Wall`, `GEX Flip`, `0DTE`, `Short Squeeze`, `Pullback`, `Footprint`, `Stacked Imbalances`, `Iceberg`, `VWAP`, `POC`, `$145M`, etc.) com fluidez humana natural e 100% grátis. |
| **`14/11/2026 13:56`** | `gex-dashboard/app/globals.css` e `.vscode/settings.json` | Commit `52249b3` / `a164bf2` | Corrigido o aviso/erro `Unknown at rule @theme css(unknownAtRules)` na linha 8 de `app/globals.css` (substituído `@theme inline` por variáveis padrão `:root` e configurado `"css.lint.unknownAtRules": "ignore"` no VS Code). |
| **`14/11/2026 14:17`** | `public/ebooks/manualtaticomestre/imagens/*.svg` | Atualizados às `14:17` | Redesenhados e auditados geometricamente os 4 diagramas `.svg` (`barras_estrutura_e_quant_engine.svg`, `fase1_rompimento_e_continuidade.svg`, `fase2_reversao_topo_e_fundo.svg` e `fase3_lateralizacao_pullback_e_7_niveis.svg`) separando as etiquetas de níveis em pílulas opacas à esquerda, os candles/curvas ao centro e as caixas de gatilho à direita, eliminando 100% dos cortes de borda e sobreposições de texto. |

---

### B. Modificações de `13/11/2026`

| Data e Horário | Repositório / Arquivo | Commit / Status | O Que Foi Alterado |
|---|---|---|---|
| **`13/11/2026 12:49`** | `gex_profile_v7/gex_profile_v7_cloud.py` | Commit `5b826a7` (Enviado) | **1.** Inclusão de `Monthly Options` (3ª sexta-feira ou data real da página para commodities) e `EOM Options` (último dia útil) em `extract_futures_expiration_options` e `parse_futures_expiration_options`, com limite de **21 dias corridos** (`MAX_SHORT_DTE_CALENDAR_DAYS = 21`) e fallback para `7DTE`.<br>**2.** Extração de **IV real e gregas por strike** (`volatility,delta,gamma,theta,vega`) da API interna do Barchart (`/proxies/core-api/v1/quotes/get`), calibração de IV via `implied_vol_from_gamma()` quando o feed retorna `raw.gamma`, aplicação do *Volatility Skew* real em `cgex`, `pgex` e `find_gex_flip` e exportação de `IVSource = "IV real por strike (Barchart)"`.<br>**3.** Injeção explícita de `api.expirationDate = expirationToken` nas rotas de ETF (`RTY` via `IWM`) para que `0DTE`, `1DTE`, `2DTE` e `7DTE` busquem cadeias distintas. |
| **`13/11/2026 12:49`** | `gex_profile_v7/test_gex_profile_v7_cloud.py` | Commit `5b826a7` (Enviado) | Suíte expandida de 31 para **49 testes unitários** (`Ran 49 tests in 10.319s — OK`), validando OPEX mensal/EOM, limite de 21 dias, IV/Gamma reais por strike, filtro de ruído numérico de gamma (`MIN_RELEVANT_GAMMA_X_SPOT`) e injeção de `expirationDate` no `IWM`/`RTY`. |
| **`13/11/2026 12:55`** | `gex-dashboard/app/page.tsx` | Commit `6e58290` (Enviado) | Em `fetchDataset`, priorizada a chamada a `buildApiUrl(dteFilter, dataset)` (`/api/gamma-data`) **antes** dos links estáticos do Dropbox (`getStaticLink`), eliminando atrasos de cache em `ALL`, `1DTE` e `7DTE`. |
| **`13/11/2026 13:12`** | `gex_profile_v7/instalador_cloud2.0.py` | Atualizado às `13:12` (`SYNTAX_OK`) | **1.** Embutidos diretamente dentro do instalador os códigos C# completos e auditados de `VolatilidadeImplicitaPro` (`CODE_VOLATILIDADE`) e `FluentliExpectedMove` (`CODE_EXPECTED_MOVE`, usando delimitador `r'''` para compatibilidade com `@"""regularMarketPrice""`). Agora o instalador grava todos os **7 indicadores** no NinjaTrader 8 sem depender de arquivos `.cs` soltos.<br>**2.** Mapeamento dos micro futuros `M2K` → `RTY` e `QG` → `NG` em `NiveisEstruturaPro`, `NiveisGammaPro` e `MoneyRiskPro`.<br>**3.** Leitura da coluna 13 (`p[12]`, `dashIvSource`) no `NiveisGammaPro` para exibir no painel `🛡️ QUANT ENGINE V8` se a IV é `"IV REAL POR STRIKE (BARCHART)"` ou `"IV BASE ASSUMIDA"`. |
| **`13/11/2026 13:34`** | `gex-dashboard/public/ebooks/gexcloudengine/imagens/*.svg` | Criados às `13:34` | Criados 4 diagramas vetoriais institucionais em tema escuro (`#0f172a`):<br>1. `curva_gex_regimes.svg` (Ondas `+Net GEX`, barrigas `-Net GEX`, `Call Wall`, `Put Wall` e `GEX Flip`).<br>2. `heatmap_espelho_leitura.svg` (Comparação entre Muralha Direcional Desbalanceada `-$170M vs +$3M` e Zona de Pinning/Straddle `8.000 Calls vs 8.000 Puts`).<br>3. `playbook_gatilhos_operacionais.svg` (Candles de Compra por Absorção na Put Wall, Venda de Pullback abaixo do Flip e Compra de Gamma Squeeze acima da Call Wall).<br>4. `escada_dte_volatilidade.svg` (Escada `0DTE -> 1DTE -> 2DTE -> 7DTE / OPEX Mensal` e impacto da IV Baixa vs. IV Alta no stop/lote). |
| **`13/11/2026 13:36`** | `gex-dashboard/public/ebooks/gexcloudengine/teoria.md` e `pratica.md` | Atualizados às `13:36` | Reescritos e unificados sem duplicidades, sem marcadores de conflito de merge e sem avisos antigos superados. Formatados 100% no padrão exigido pelo parser `markdownToHtml` de `app/biblioteca/page.tsx` (parágrafos e itens `- ` em linha única, sem tabelas cruas ou LaTeX quebrado), integrando os exemplos dos strikes `7705`, `7645`, `7650`, `7550` e `7600` com o Playbook de 4 cenários e os 4 diagramas `.svg`. |
| **`13/11/2026 13:36`** | `gex-dashboard/app/biblioteca/page.tsx` | Atualizado às `13:36` | Normalização de quebras de linha Windows (`\r\n` → `\n`) e exclusão de `<figure>` do agrupamento `<p>` em `markdownToHtml`, garantindo renderização limpa das listas `<ul>` e dos diagramas `.svg`. |
| **`13/11/2026 13:38`** | `regras.md` (em ambos os repositórios) | Commit `ebe707e` / `63e3dfa` | Criado documento de regras permanentes exigindo registro de data e horário (`dd/MM/aaaa HH:mm`) em todas as alterações futuras e documentando o padrão de formatação dos e-books da Biblioteca. |
| **`13/11/2026 14:13`** | `gex_profile_v7/.github/workflows/main.yml` | Commit `94394dc` (Enviado) | Corrigida a inconstância dos agendamentos do GitHub Actions: alterado `cron` de 20 min (`7,27,47`) para **30 min (`12,42 13-20 * * 1-5`) + coleta de fechamento às `18:15 BRT` (`15 21 * * 1-5`)**, cobrindo das **10h da manhã até o fechamento das opções** sem colisão de fila; adicionados `concurrency` (`cancel-in-progress: false`) e disparo automático em `push` na `main`. |
| **`13/11/2026 14:22`** | `gex-dashboard/public/ebooks/*` e `app/biblioteca/page.tsx` | Commit `aeb39c5` | Reescritos `teoria.md` e `pratica.md` + criados diagramas `.svg` para `niveisestruturapro`, `niveisgammapro` e `moneyriskpro` (documentando as 16 linhas Multi-DTE, painel `QUANT ENGINE V8`, IV Real por Strike e correção de unidade `$M/$B`), além de criados os novos livros completos (`teoria.md`, `pratica.md` e `.svg`) para `volatilidadeimplicitapro`, `fluentliexpectedmove`, `deltacumulativepro` e `vwapinstitucionalpro` (totalizando 10 módulos / 20 e-books na Biblioteca). |
| **`13/11/2026 14:23`** | `gex_profile_v7/MANUAL_INDICADORES_NT8_V9.md` | Commit `94394dc` (Enviado) | Criado manual consolidado em Markdown explicando a teoria e a prática de `VolatilidadeImplicitaPro`, `FluentliExpectedMove`, `DeltaCumulativePro.py` e `vwap.py` integrados ao Motor V9. |
| **`13/11/2026 14:32`** | `gex_profile_v7/.github/workflows/main.yml` | Commit `b8fcd82` (Enviado) | Removido `cache: 'pip'` do passo `actions/setup-python@v5` pois o repositório instala pacotes diretamente via `pip install pandas selenium dropbox tzdata` sem arquivo `requirements.txt`, o que havia causado falha no passo `Configurar Python com Cache` da run `#265`. |
| **`13/11/2026 15:24`** | `gex_profile_v7/gex_profile_v7_cloud.py` e `test_gex_profile_v7_cloud.py` | Atualizados às `15:24` | **1.** Ajustado `MIN_TIME_TO_EXPIRY_SECONDS = 86400.0` (1 dia = `1/365` anos, convenção do Barchart e SpotGamma para `0DTE`) e `effective_T = max(T, 1/365)` em `resolve_strike_vols`: evita que no `0DTE` a gaussiana do Black-Scholes vire uma agulha de 5 pontos em torno do spot (o que zerava as paredes reais e impedia a calibração de `IV real por strike (Barchart)` a partir de `raw.gamma`).<br>**2.** Garantido que `resolve_strike_vols` **jamais descarte o `gamma_api` real do Barchart** mesmo em strikes de asa onde `implied_vol_from_gamma` não encontre raiz analítica.<br>**3.** Adicionada proteção estrutural em `select_walls` para evitar que um strike residual ITM faça a `Call Wall` aparecer abaixo da `Put Wall` (ex.: `7545 < 7550` visto no print do `ES 0DTE`), validada pelo 50º teste unitário (`test_select_walls_prevents_inverted_call_wall_below_put_wall`). |
| **`13/11/2026 15:24`** | `gex-dashboard/app/page.tsx` | Commit `ba7e28d` | **1.** Criado `focusedChartData` para remover automaticamente as caudas distantes onde `|ng| ≈ 0` (strikes de `±15%` sem gamma no `0DTE` que esmagavam a curva no centro do gráfico), preservando `Call Wall`, `Put Wall`, `GEX Flip` e paredes `0DTE` com folga lateral.<br>**2.** Atualizado o rótulo de `GEX FLIP (estimado)` para `GEX FLIP (Zero Gamma)` / `GEX Flip` e destacado `IV real por strike (Barchart)` em verde esmeralda no cabeçalho. |
| **`13/11/2026 15:56`** | `gex_profile_v7/gex_profile_v7_cloud.py` | Atualizado às `15:56` | Refinado `select_walls(df)` com limiar institucional de `50%` (`>= 0.50`): se `Call Wall < Put Wall` seria causada por resíduo ITM menor (quando há parede no lado normal com `>= 50%` do Net GEX), promove a parede normal (`PW < CW`); porém, se a parede invertida for estruturalmente dominante (`> 2x` qualquer alternativa), preserva a leitura real de **Paredes Invertidas (*Crossed Gamma Zone*)**. |
| **`13/11/2026 15:56`** | `gex_profile_v7/instalador_cloud2.0.py` | Atualizado às `15:56` | **1.** `NiveisGammaPro`: adicionada leitura sempre ativa de `NiveisGamma_{ATIVO}_0DTE.csv` para plotar também a 17ª linha **`0DTE GEX FLIP`** (`ZG0DTE`, Dourada Pontilhada) junto com `0DTE CALL WALL` e `0DTE PUT WALL`, além de remover `"ESTIMADO"` dos rótulos.<br>**2.** `NiveisEstruturaPro`, `MoneyRiskPro`, `VolatilidadeImplicitaPro` e `FluentliExpectedMove`: adicionada a propriedade **`Vencimento DTE`** (`"ALL"`, `"0DTE"`, `"1DTE"`, `"2DTE"`, `"7DTE"`, padrão `"ALL"`, com fallback automático `0DTE -> 1DTE -> ALL`) e atualização contínua a cada 5s da IV do Dropbox no `FluentliExpectedMove`. |
| **`13/11/2026 15:56`** | `gex-dashboard/public/ebooks/gexcloudengine/*` e `niveisgammapro/*` | Commit `7fc2b05` | Documentado em `teoria.md` e `pratica.md` (de `gexcloudengine` e `niveisgammapro`, além do seletor `Vencimento DTE` em `niveisestruturapro` e `moneyriskpro`) o fenômeno de **Paredes Invertidas (`Call Wall < Put Wall`, ex.: `CW 7545` abaixo de `PW 7550`)**, quando ele ocorre no mercado real e o Playbook de 3 zonas (Quando Ficar de Fora entre `7545–7550`, Gatilho de Venda abaixo de `7545` e Gatilho de Compra / Put Squeeze acima de `7550`). |
| **`13/11/2026 17:09`** | `gex-dashboard/public/ebooks/gexcloudengine/*` e `niveisgammapro/*` | Atualizados às `17:09` | Adicionado estudo de caso real completo (Teoria e Prática) com os **2 prints reais de `0DTE` (`2026-11-13`) e `7DTE / OPEX Mensal` (`2026-11-20`)** (`confluencia_0dte_7650_7500.jpg` e `confluencia_7dte_7650_7500.png`) explicando a **Super-Confluência Temporal (Muralha Dupla em `7650` e `7500` com GEX Flips distintos `7622.2` vs. `7668.41`)**, o efeito *Friday-to-Friday Roll* / *Big Figures* (`00` e `50`) e o Playbook operacional integrando Order Flow (`DeltaCumulativePro`), `VWAPInstitucionalPro`, `NiveisEstruturaPro`, `VolatilidadeImplicitaPro`, `FluentliExpectedMove` e `MoneyRiskPro`. |

---

### B. Modificações de ONTEM — `12/11/2026` (Já Enviadas ao GitHub)

| Data e Horário | Repositório / Arquivo | Commit / Status | O Que Foi Alterado |
|---|---|---|---|
| **`12/11/2026 21:20`** | `gex_profile_v7/gex_profile_v7_cloud.py` | Commit `2fa12e8` (Enviado) | Correção das anomalias estruturais: **1.** `select_walls()` por saldo líquido (`ng > 0` máx. para Call Wall e `ng < 0` mín. para Put Wall, evitando `CW == PW`); **2.** `_dte_target_date()` por dias úteis para `1DTE` e `2DTE` não duplicarem sexta-feira; **3.** Exportação dedicada de `_0DTE.csv`; **5.** `STRIKE_ROUNDING` restrito aos índices; **6.** `apply_proxy_scaling()` nas fatias DTE do `RTY`; **7.** Piso `MIN_TIME_TO_EXPIRY_SECONDS = 300.0`, `effective_session_date` após 16h NY e resiliência por ativo/DTE; **Extra.** `parse_treasury_price()` para `ZN`/`ZB`. |
| **`12/11/2026 21:20`** | `gex_profile_v7/.github/workflows/main.yml` | Commit `2fa12e8` (Enviado) | `timeout-minutes` ampliado de `18` para `35`. |
| **`12/11/2026 21:20`** | `gex_profile_v7/instalador_cloud2.0.py` | Commit `2fa12e8` (Enviado) | Correção de `FormatVal(n.NetGamma)` sem `* 100 * Close[0]` no `NiveisEstruturaPro` (que inflava o histograma em ~760.000x) e atualização do painel `🛡️ QUANT ENGINE V8` no `NiveisGammaPro`. |
| **`12/11/2026 21:23`** | `gex-dashboard/app/api/gamma-data/route.ts` | Commit `4eed2ae` (Enviado) | Suporte unificado a `ALL`, `0DTE` (com fallback automático para `1DTE` em HTTP 409), `1DTE`, `2DTE` e `7DTE`, cache em memória do token OAuth do Dropbox (`cachedAccessToken`) e cabeçalhos `Cache-Control: no-store` + `X-Resolved-DTE`. |
| **`12/11/2026 21:23`** | `gex-dashboard/app/page.tsx` | Commit `4eed2ae` (Enviado) | Suporte ao filtro `0DTE`, `<XAxis dataKey="strike" type="number" domain={['dataMin', 'dataMax']} />` contínuo e inclusão das `<ReferenceLine>` de `Call Wall`, `Put Wall` e `GEX Flip` na `Curva GEX` e no `Heatmap`. |
| **`12/11/2026 21:37`** | `VolatilidadeImplicitaPro.cs` e `FluentliExpectedMove.cs` | Auditados em `12/11 21:37` e embutidos no instalador em `13/11 13:12` | Correção do sumiço das bandas durante sincronização do Dropbox, suporte a todos os micro futuros (`MES`, `MNQ`, `MCL`, `MGC`, `MYM`, `M2K`, `MNG`/`QG`), correção da condição de corrida assíncrona (`Task.Run`) no `FluentliExpectedMove`, leitura automática da IV do Dropbox para os 9 ativos, correção da opacidade duplicada em `Draw.Rectangle` e ajuste de posição do HUD (`BottomLeft`). |

---

## 2. Comandos Finais de Sincronização Git (`13/11/2026`)

### Repositório 1: `gex-dashboard` (branch `master`)
```powershell
cd C:\Users\alanb\source\gex-dashboard\gex-dashboard
git add app/biblioteca/page.tsx public/ebooks/gexcloudengine/teoria.md public/ebooks/gexcloudengine/pratica.md public/ebooks/gexcloudengine/imagens/ regras.md
git commit -m "docs(biblioteca): unify GEX Cloud Engine V9 manuals, add 4 SVG diagrams and rules"
git pull --rebase origin master
git push origin master
```

### Repositório 2: `gex_profile_v7` (branch `main`)
```powershell
cd C:\Users\alanb\source\gex_profile_v7\gex_profile_v7
git rm -f --ignore-unmatch VolatilidadeImplicitaPro.cs FluentliExpectedMove.cs
git add instalador_cloud2.0.py RELATORIO_CORRECOES_V9.md regras.md
git commit -m "docs(quant-v9): embed 7 NT8 indicators in installer and add timestamped audit log & rules"
git push origin main
```


---

## 9. Expansão Completa da Academia Quant (Opções Iniciante/Intermediário/Avançado, Estatística V9, Arquitetura DevOps e Engenharia C# nos 9 Indicadores) (14/11/2026 15:18)

### 9.1. Trilha Completa de Opções Aplicadas aos 9 Futuros (`public/ebooks/opcoes_*`)
- **`public/ebooks/opcoes_iniciante/`**: Criados `teoria.md`, `pratica.md`, `DICIONARIO_OPCOES_INICIANTE.md` e `imagens/opcoes_iniciante_seguro_e_paredes.svg` (Metáforas para leigos, 4 Pontas Call/Put Comprada e Vendida, Paradoxo da `Call Wall` como Resistência e `Put Wall` como Suporte via *Dynamic Delta-Hedging*, e Comparativo Completo de Liquidez e Personalidade dos 9 Ativos: `ES`, `NQ`, `GC`, `CL`, `ZN`, `ZB`, `RTY`, `YM`, `NG`).
- **`public/ebooks/opcoes_intermediario/`**: Criados `teoria.md`, `pratica.md`, `DICIONARIO_OPCOES_INTERMEDIARIO.md` e `imagens/opcoes_intermediario_gregas_estrategias.svg` (As 5 Gregas de 1ª Ordem `Delta`, `Gamma`, `Theta`, `Vega`, `Rho`, `IV vs. HV`, `Volatility Skew` de Índices vs. Commodities e Estratégias Institucionais `Straddle`, `Strangle`, `Collar JHEQX`, `Iron Condor` e `Butterfly`).
- **`public/ebooks/opcoes_avancado/`**: Criados `teoria.md`, `pratica.md`, `DICIONARIO_OPCOES_AVANCADO.md` e `imagens/opcoes_avancado_dealer_hedging_vanna_charm.svg` (Nomenclaturas oficiais institucionais `Dynamic Delta-Hedging`, `Cross-Asset Gamma Hedging`, `Dispersion Trading`, Gregas de 2ª e 3ª Ordem `Vanna`, `Charm / Delta Bleed`, `Vomma / Volga`, `Speed`, `Color`, `Zomma` e Matriz de Correlação Intermercados dos 9 Futuros + `VIX` + `Yields`).

### 9.2. Pasta `public/ebooks/estatistica/` (Do Básico ao Avançado em `gex_profile_v7_cloud.py` e `instalador_cloud2.0.py`)
- Criados `teoria.md`, `pratica.md` e `imagens/estatistica_motor_v9_pipeline.svg` explicando para leigos e avançados:
  - Curva Normal de Gauss (`68,2% / 95,4% / 99,7%`) e a Regra da Raiz de 252 (`\sqrt{252} \approx 16`).
  - Metodologia de Scraping em 2 Etapas (Sessão Autenticada `XSRF-TOKEN` + API JSON interna `/proxies/core-api/v1/quotes/get` da Barchart), `parse_treasury_price` (32 avos de `ZN`/`ZB`), Calendário de Dias Úteis `_dte_target_date` e Fallback `IWM x 10` para `RTY`.
  - Matemática de Black-Scholes (`bs_gamma`), Inversão de IV por Busca Binária de 60 iterações (`implied_vol_from_gamma`), Piso `0DTE` (`MIN_TIME_TO_EXPIRY_SECONDS = 86400.0`), Interpolação Linear (`find_gex_flip`), Filtro Anti-Inversão 50% (`select_walls`) e `calculate_max_pain`.

### 9.3. Pasta `public/ebooks/arquitetura_devops/` + Engenharia de Código Individual nos 9 Indicadores
- Criados `teoria.md`, `pratica.md` e `imagens/arquitetura_cloud_github_dropbox_vercel_nt8.svg` detalhando a ponte `GitHub Actions Cron` -> `gex_profile_v7_cloud.py` -> `Dropbox OAuth2 Refresh Token` -> `Vercel Next.js /api/gamma-data (Cache RAM 10s)` + `NinjaTrader 8 (FileShare.ReadWrite + Cache 5s)`.
- Adicionada a seção **"Engenharia de Código e Matemática (Do Básico ao Avançado — `instalador_cloud2.0.py`)"** em cada uma das 9 pastas de indicadores (`niveisgammapro`, `niveisestruturapro`, `moneyriskpro`, `volatilidadeimplicitapro`, `fluentliexpectedmove`, `vwapinstitucionalpro`, `deltacumulativepro`, `dailyohlcpro`, `globexrangepro`) e registrados os **16 módulos / 32 ebooks** em `app/biblioteca/page.tsx`.


---

## 10. Comentários Didáticos Linha a Linha em Todos os Blocos de Código C#, Python e TypeScript nos Ebooks (14/11/2026 15:44)
- **Escopo:** Adicionados comentários explicativos linha por linha (`// ...` e `# ...`) detalhando a função exata de cada instrução e coluna (`cols[0]` a `cols[11]`, `FileShare.ReadWrite`, `StreamReader`, cálculos de variância $O(1)$, Black-Scholes, interpolação de `GEX Flip`, `parse_treasury_price` e OAuth2) em todos os blocos de código de `niveisgammapro/teoria.md`, `niveisestruturapro/teoria.md`, `moneyriskpro/teoria.md`, `volatilidadeimplicitapro/teoria.md`, `fluentliexpectedmove/teoria.md`, `vwapinstitucionalpro/teoria.md`, `deltacumulativepro/teoria.md`, `dailyohlcpro/teoria.md`, `globexrangepro/teoria.md`, `estatistica/teoria.md`, `estatistica/pratica.md` e `arquitetura_devops/teoria.md`.


---

## 11. Criação do Plano Mestre de Vida, Carreira STEM nos EUA e Blindagem em Mesas Proprietárias (14/11/2026 16:11)
- **Arquivos criados:**
  - `C:\Users\alanb\source\gex_profile_v7\gex_profile_v7\PLANO_MESTRE_RECOMECO_37_ANOS_STEM_EUA_E_MESAS_PROP.md`
  - `C:\Users\alanb\source\gex-dashboard\gex-dashboard\public\ebooks\plano_carreira_stem_eua\teoria.md`
  - `C:\Users\alanb\source\gex-dashboard\gex-dashboard\public\ebooks\plano_carreira_stem_eua\pratica.md`
  - `C:\Users\alanb\source\gex-dashboard\gex-dashboard\public\ebooks\plano_carreira_stem_eua\PLANO_MESTRE_RECOMECO_37_ANOS_STEM_EUA_E_MESAS_PROP.md`
  - `C:\Users\alanb\source\gex-dashboard\gex-dashboard\public\ebooks\plano_carreira_stem_eua\imagens\roadmap_stem_eua_e_mesas_prop.svg`
- **Registrado na Biblioteca (`app/biblioteca/page.tsx`):** Adicionado como primeiro módulo em destaque (`Plano Mestre: STEM EUA & Prop ($60k)`, totalizando `17 módulos / 34 ebooks`).


---

## 12. Auditoria do `instalador_cloud2.0.py`, Formatação Decimal da IV no `NiveisGammaPro` e Documentação de `PW/CW` Sem DTE vs. Com DTE vs. Barras Sem Sigla (14/11/2026 16:55)
- **Auditoria do `instalador_cloud2.0.py`:** Todos os 9 indicadores verificados. Adicionado arredondamento limpo (`ToString("F1")`) no campo `dashIv` do `NiveisGammaPro` (linhas 378-383) para exibir `15.2%` em vez de `15.200833333333334%` no painel `🛡️ QUANT ENGINE V8`.
- **Atualização nos Ebooks (`niveisgammapro/teoria.md`, `niveisestruturapro/teoria.md`, `manualtaticomestre/MANUAL_TATICO_MESTRE_3_FASES_E_CONFLUENCIAS.md` e `manualtaticomestre/pratica.md`):** Documentada a diferença entre:
  1. `PUT WALL | -$22.34M | 7630` e `CALL WALL | $9.88M | 7690` **sem DTE** (Muralhas Macro Principais `ALL` em linha sólida grossa de 5px).
  2. Siglas amarelas curtas `PW -$22,3M` e `CW $9,9M` na ponta da barra do `NiveisEstruturaPro` vs. barras secundárias sem sigla (ex.: `$5,1M` em branco no `7640`, que representam sub-paredes/alvos intermediários).
  3. Linhas tracejadas **com DTE** (`0DTE`, `1DTE`, `2DTE`, `7DTE`) e o comportamento de inversão de polaridade quando uma `Call Wall` fica abaixo do preço ou abaixo de uma `Put Wall`.


---

## 13. Etiquetas Anti-Colisão (`renderReferenceBadge`), Formatação de Contratos sem `.00` (`pt-BR`) e Barra Inferior de Esticar/Juntar no Dashboard Web + HUD do `NiveisGammaPro` (15/11/2026 19:06)
- **Etiquetas Anti-Colisão em `app/page.tsx` (`renderReferenceBadge`):** Substituídos os rótulos internos do Recharts (`insideTopLeft`/`insideBottomRight`) por pílulas institucionais SVG com fundo escuro sólido (`#090d16`) e borda colorida posicionadas em faixas verticais independentes acima da área de plotagem (`margin.top = 72`: `GEX Flip` no andar 0, `Call Wall` no andar 1 apontando para o lado oposto da Put Wall, e `Put Wall` no andar 2), eliminando 100% a sobreposição de texto em cima das linhas verticais ou das curvas/barras.
- **Formatação Visual de Contratos Inteiros (`15.810 contratos` em vez de `15810.00`):**
  - Mantido o formato numérico bruto padrão (`InvariantCulture` com ponto decimal e sem separador de milhar) dentro dos CSVs gerados pelo `gex_profile_v7_cloud.py` para garantir zero risco de erro de leitura ou cálculo no Python, C# e TypeScript.
  - Em `app/page.tsx` (Tooltip do Heatmap), removido o `.toFixed(2)` que adicionava `.00` artificial na contagem inteira de contratos de `Open Interest` e `Volume`, aplicando `Math.round(Math.abs(Number(value))).toLocaleString('pt-BR') + ' contratos'` (ex.: `15.810 contratos`, `3.240 contratos`, `191.436 contratos`).
  - Em `instalador_cloud2.0.py` (`NiveisGammaPro`), aplicada formatação visual `ToString("N0", new CultureInfo("pt-BR"))` apenas nas strings de exibição `optionVolume` (`326.488 ctrs`) e `dashFlowVal` (`24.990`) após o parse seguro via `InvariantCulture`.
- **Barra Inferior de Zoom Horizontal ("Esticar e Juntar Gráfico") em `app/page.tsx`:** Adicionada barra interativa no rodapé do card gráfico com botões `Esticar (+)` e `Juntar (-)`, controle deslizante contínuo (`range slider`) e atalhos rápidos (`Super Esticado ±1.5%`, `Ideal ±3.5%`, `Médio ±7%`, `Amplo ±15%` e `Tudo 100%`), iniciando por padrão em `±3.5%` para que as barras e curvas fiquem bem espaçadas e legíveis.


---

## 14. Central de Correlação Multi-Ativos (`/correlacao`), Mapa de Calor em Tempo Real, Adição de Dinheiro Novo (`Vol > OI`), Perfil de Volume 0DTE, Inclusão de `$NDX` e Novos Manuais (15/11/2026 20:24)
- **Central de Correlação Macro & Heatmap em Tempo Real (`app/correlacao/page.tsx` e `app/api/market-context/route.ts`):**
  - Criado menu dedicado `/correlacao` separado por classes de ativos (**Futuros CME**, **Índices Cash & Volatilidade `SPX/NDX/VIX`**, **ETFs `SPY/QQQ/TQQQ/HYG/VXX/UVXY/GLD/USO`**, **Bonds `ZB/ZN/TLT`**, **Forex `DXY/EURUSD/USDJPY/GBPUSD/AUDUSD`**, **Market Internals `ADD/TICK/TICKQ`** e **Mag 7 `NVDA/AAPL/MSFT`**).
  - Gráfico multi-linhas interativo com seletor individual de cores (Roxa, Rosa, Ciano, Verde, Amarela, Laranja, Vermelha) e modo `Espelhar Inversos (× -1)` para comparar `ES/NQ` contra `VIX, VXX, UVXY, HYG, ZB, ZN, ADD, TICK, DXY e USD/JPY`.
  - Mapa de Calor em tempo real com indicador explícito **`🟢 CORRELAÇÃO DIRETA`** vs. **`🔴 CORRELAÇÃO INVERSA`**, medidor de coeficiente de Pearson ($r$) e radar automático de divergência (`ES vs HYG`, `ES vs VIX`, `NQ vs ZN/DXY`).
- **Adição de Dinheiro Novo (`NEW_MONEY`) e Perfil de Volume 0DTE (`VOL_PROFILE`) em `app/page.tsx` e `instalador_cloud2.0.py`:**
  - Adicionadas as abas **`✨ DINHEIRO NOVO (FLOW)`** (identificando strikes onde $\text{Volume} > \text{Open Interest}$) e **`📊 PERFIL VOLUME 0DTE`** (com `POC Volume` e `Zero Gamma`) + Auto-Refresh a cada 60s.
  - Em `instalador_cloud2.0.py` (`NiveisEstruturaPro`), adicionado suporte aos modos `GAMMA`, `VOLUME` e `NEW_MONEY` com etiqueta `[NEW$]` e fundo escuro de alto contraste via Direct2D GPU.
  - Em `gex_profile_v7_cloud.py`, adicionado `$NDX` (`strike_mult: 1`, `gex_correcao: 5`) ao grupo agregado do `NQ` junto com `NQ*0` e `QQQ` (`strike_mult: 40`).
- **Novos Manuais e Dicionários na Biblioteca (`19 módulos / 38 ebooks`):**
  - `public/ebooks/correlacao_macro_fluxo/` (`teoria.md`, `pratica.md`, `DICIONARIO_CORRELACAO_MACRO.md`, `imagens/correlacao_direta_inversa_ecossistema.svg`)
  - `public/ebooks/perfil_volume_0dte_dinheiro_novo/` (`teoria.md`, `pratica.md`, `imagens/dinheiro_novo_e_perfil_0dte.svg`)


---

## 15. Correção de Layout & SVGs, Nomenclatura Oficial EUA (`Opening Flow / UOA`), Famílias Irmãos vs. Lados Opostos em `/correlacao` e Central Unificada `/macro` (Macro + Notícias + Finviz + Dark Pool Ao Vivo + Trader OS) (16/11/2026 00:15)
- **Biblioteca & SVGs (`app/biblioteca/page.tsx`, `app/globals.css`, `public/ebooks/*`):**
  - Melhorado `markdownToHtml` para renderizar tabelas responsivas (`.table-wrap`), links clicáveis, referências locais compactas (sem URLs cruas vazando da margem), citações e listas mistas; adicionado `overflow-wrap: anywhere` em `.markdown-body`.
  - Redimensionados os 3 diagramas SVG (`correlacao_direta_inversa_ecossistema.svg`, `dinheiro_novo_e_perfil_0dte.svg` e `arquitetura_macro_darkpool.svg`) para canvas `1360px` com folga lateral rígida (`0 issues` na auditoria de largura).
- **Nomenclatura Oficial EUA (`app/page.tsx`, `instalador_cloud2.0.py`, ebooks):**
  - Renomeado "Dinheiro Novo (`Vol > OI`)" para os termos reais usados nos EUA: **`Opening Flow (Vol>OI)`** / **`Fresh Positioning (BTO/STO)`** / **`UOA`** (mantendo compatibilidade retroativa com `"NEW_MONEY"` no `NiveisEstruturaPro` e adotando tag **`[OPEN$]`**).
- **Irmãos vs. Lados Opostos (`app/correlacao/page.tsx`, `app/api/market-context/route.ts`):**
  - Adicionados filtros `🟢 Andam Juntos (+)` vs. `🔴 Lados Opostos (-)`, placar instantâneo dos **4 Futuros Irmãos (`ES + NQ + RTY + YM`)**, preset **`🤝 Kit Irmãos CME`**, inclusão das ETFs `IWM` e `DIA` (completando as 11 ETFs líquidas) e ajuste de `GC`/`SI`/`GLD` para `DIRETA`.
- **Central Macro & Dark Pool Automática (`app/macro/page.tsx`, `app/api/macro-darkpool/route.ts`, `INDICADORES MACROECONOMICOS/*`):**
  - Unificados automaticamente na nuvem (zero VS Code): FRED API / CSV Público (`FEDFUNDS`, `CPI`, `PCE`, `UNRATE`, `PAYEMS`, Curva `10Y-2Y`), Termômetro Global, Agenda USD com Alerta Prop 5 min, Scanner Finviz/Yahoo Short Squeeze, **FINRA Reg SHO Dark Pool direto (`cdn.finra.org`) + Detector Ao Vivo 5m de Absorção (`ETF → Futuro CME`)** e **Quant Trader OS** (Regra do 16 com IV Real + Auditor CSV com parser US/BR corrigido + Diário `localStorage`).
  - Corrigidos também localmente `criador_dashboard_macro.py` (remoção do path fixo `NOTEBOOK`, `--auto`, fallback CSV público opcional e inclusão de `HYG`/`DXY` simétrico), `dashboard_trader.py` (parse CSV `$1,250.50` e Regra do 16 usando `iv_atual`) e criado `INICIAR_PAINEL_MACRO_AUTOMATICO.bat`.
  - Criado o Módulo #20 na Biblioteca (`public/ebooks/indicadores_macro_darkpool/`: `teoria.md`, `pratica.md`, `DICIONARIO_MACRO_DARKPOOL.md`, `imagens/arquitetura_macro_darkpool.svg`), totalizando `20 módulos / 40 ebooks`.


---

## 16. Upgrade do Rastreador Dark Pool para Velas 1m (Zero Displacement + Valor Nocional `$M`), Filtro `Cum. net profit` no Auditor CSV e Expansão Didática "Por Quês" para Leigos (`16/11/2026 01:19`)
- **`gex-dashboard/app/api/macro-darkpool/route.ts` & `app/macro/page.tsx`:**
  - Aprimorado `fetchIntradayProxyBlocks()` de velas `5m` para **`1m` (`interval=1m&range=1d`)** usando mediana diária como linha de base (evitando distorção do leilão de abertura), cálculo do **Valor Nocional em `$M`** por minuto (`typicalPrice × volume`) e classificação **`DARK POOL PRINT / ABSORÇÃO 1m`** quando `rangePct <= 0.12%` com `RVOL >= 2.5x`.
  - Corrigido o detector de coluna no **Auditor NinjaTrader CSV** (em `app/macro/page.tsx` e `INDICADORES MACROECONOMICOS/dashboard_trader.py`) para priorizar `Profit`/`Lucro` e excluir `Cum. net profit` (lucro acumulado), exibindo na interface o caminho exato no NinjaTrader 8 (`Trade Performance > Trades > Export (.csv)`).
- **`public/ebooks/indicadores_macro_darkpool/` (`teoria.md`, `pratica.md`, `DICIONARIO_MACRO_DARKPOOL.md`, `arquitetura_macro_darkpool.svg`):**
  - Detalhamento completo para leigos explicando **todos os "por quês"**: corte de juros vs. inflação/corte bom vs. corte de recessão, gangorra `^TNX vs. ZN/ZB`, mecânica completa de *Short Squeeze* ("carro alugado"), por que o OpenBB não oferece feed gratuito superior ao `cdn.finra.org`, assinatura SEC/FINRA TRF em até 10s nas velas `1m` e guia exato das colunas exportadas pelo NinjaTrader 8.


---

## 17. Restauração Integral + Fusão Expandida dos Ebooks (`teoria.md` e `pratica.md`) Sem Remoção de Tabelas ou Explicações (`16/11/2026 01:57`)
- **`public/ebooks/indicadores_macro_darkpool/` (`teoria.md` e `pratica.md`):**
  - Restauradas 100% das seções, tabela de 5 colunas do FRED/Termômetro Global, cenários `Actual vs. Forecast`, regra do 1º candle de 5m, watchlist/regras do Finviz & Squeeze, todas as 3 camadas do Dark Pool (`FINRA Reg SHO`, feeds SIP pagas vs. gratuitos, e Proxy ETF → Futuro CME), nota `STOCK Act` (45 dias) do Capitol Trades, fórmula da Regra do 16 (`√252 ≈ 16`) e rotinas pré-mercado/automação local `.bat` + `shell:startup` da versão anterior (`1e57ba0`).
  - Mantido e expandido 100% do conteúdo didático para leigos adicionado em `3cdbf8e`: todos os "por quês" de corte de juros/inflação/recessão, gangorra `^TNX vs. ZN/ZB`, verdade sobre o OpenBB (`openbb-stockgrid`), mecanismo SEC/FINRA 10s em velas `1m` (`>= 2.5x` mediana, `rangePct <= 0.12%`, `$M` nocional), veredito de confluência no Day Trade, analogia do "carro alugado" no *Short Squeeze*, automação em nuvem Vercel e guia exato de exportação CSV do NinjaTrader 8 (`Control Center > New > Trade Performance > Trades > Export (.csv)`).
- **`public/ebooks/correlacao_macro_fluxo/` e `public/ebooks/perfil_volume_0dte_dinheiro_novo/` (`teoria.md` e `pratica.md`):**
  - Auditados contra o snapshot anterior (`f554bfa`) e restaurados todos os detalhes, exemplos práticos (`7690`, `7500`, `15–20 pts POC`, `20–40 pts Delta Unwind`), coluna `Nome Oficial` na tabela das 11 ETFs, fórmula matemática do `Opening Flow (Vol > OI)`, combinação `GEX OI + GEX Vol + Δ Delta` (*Straddle Pinning* e migração de parede) e passo-a-passo completo dos setups e modos `GAMMA / VOLUME / OPENING_FLOW` no `NiveisEstruturaPro` sem expor URLs quebrando o layout.


---

## 18. Persistência de Áudio Padrão (Voz + Velocidade) em Todos os E-Books (`Teoria` e `Prática`) (`16/11/2026 14:40`)
- **`gex-dashboard/app/biblioteca/page.tsx` & `app/globals.css`:**
  - Removido o `key={`${selected.id}-${kind}`}` do componente `AudioReader` (que reiniciava a voz e a velocidade escolhidas toda vez que o usuário trocava de módulo ou alternava entre `Teoria` e `Prática`).
  - Implementada persistência permanente via `localStorage` (`gex-biblioteca-audio-default-v1`) + `useSyncExternalStore`, salvando `voiceURI`, `voiceName` (fallback resiliente caso o `voiceURI` varie entre reinicializações do navegador) e velocidade (`0.85x` a `1.4x`) automaticamente em todos os 20 módulos (`40 ebooks`), mesmo após fechar e reabrir o navegador.
  - Adicionados rótulo **`Áudio Padrão`**, botão **`⭐ Fixar / Padrão`** com confirmação visual (`Salvo!`), botão **`↺ Restaurar Automático`** (volta à seleção recomendada `PT-BR Neural, 1.0x`), cancelamento seguro ao trocar de capítulo/aba sem perder o padrão, tratamento de tabelas Markdown na leitura (`|` → pausa limpa) e adaptação de `utterance.lang` caso o usuário escolha vozes em outro idioma.


---

## 19. Auditoria Sênior Quantitativa, Ajustes Cirúrgicos e Validação Final (`16/11/2026 17:41`)

### 19.1. Erros Encontrados (Antes) vs. Correções / Melhorias Aplicadas (Depois)

| Módulo / Arquivo | Erro que Existia (Antes) | Correção / Melhoria Aplicada (Depois) |
|---|---|---|
| **`NiveisEstruturaPro`** (embutido em `gex_profile_v7/instalador_cloud2.0.py`) | **1.** `GammaProfile_*.csv` é exportado por `gex_profile_v7_cloud.py` na ordem `strike, ng, c_vol, p_vol, coi, poi`, mas o C# lia `ln[2..3]` como `coi/poi` e `ln[4..5]` como `cvol/pvol` — invertendo `VOLUME` (plotava OI), `OPENING_FLOW`/`NEW_MONEY` (calculava `OI > Vol`) e `[OPEN$]`.<br>**2.** `NiveisGamma_*.csv` e `GammaProfile_*.csv` eram abertos com `File.ReadAllText` / `new StreamReader(path)` sem `FileShare.ReadWrite`. | **1.** Corrigida a extração posicional (`ln[2]=cvol`, `ln[3]=pvol`, `ln[4]=coi`, `ln[5]=poi`).<br>**2.** Leitura migrada para `FileStream(..., FileMode.Open, FileAccess.Read, FileShare.ReadWrite)` com guarda contra linhas vazias, eliminando falhas durante sync do Dropbox. |
| **`NiveisGammaPro`** (embutido em `gex_profile_v7/instalador_cloud2.0.py`) | `File.ReadAllText(...)` nos CSVs `macro`, `0DTE`, `1DTE`, `2DTE`, `7DTE` e `Alvos` abria sem `FileShare.ReadWrite`, causando exceções de bloqueio e apagão temporário das linhas quando o Dropbox gravava. | Adicionado o helper `LerTextoCompartilhado` com `FileStream(..., FileShare.ReadWrite)` e proteção contra strings vazias transitórias. |
| **`MoneyRiskPro`** (embutido em `gex_profile_v7/instalador_cloud2.0.py`) | `LerDadosCSV()` usava `File.ReadAllText` sem `FileShare.ReadWrite` e zerava `currentIV = 0` antes mesmo de verificar o arquivo, fazendo o indicador cair para ATR durante sync do Dropbox. | Leitura atualizada para `FileStream(..., FileShare.ReadWrite)`, preservando `currentIV` e `currentRegime` caso o arquivo esteja momentaneamente vazio durante sincronização. |
| **`GlobexRangePro`** (embutido em `gex_profile_v7/instalador_cloud2.0.py` e espelho `gex_profile_v7/DAILYOLHC.PY`) | `HoraInicio = 1800` e `HoraFim = 930` (`HHmm`) eram comparados diretamente com `ToTime(Time[0])`, que no NinjaTrader 8 retorna `HHmmss` (`180000` / `93000`) — erro de escala 100x que disparava a sessão às `00:18` / `00:09`. | Convertidos `ToTime(Time[0]) / 100` e `ToTime(Time[1]) / 100` para comparar `HHmm` com `HoraInicio` e `HoraFim` corretamente. |
| **`DeltaCumulativePro`** (embutido em `gex_profile_v7/instalador_cloud2.0.py` e espelho `gex_profile_v7/DeltaCumulativePro.py`) | **1.** Com `Calculate.OnEachTick`, `if (Bars.IsFirstBarOfSession)` zerava `sessionDelta` em todo tick da primeira barra da sessão.<br>**2.** `OnMarketData` com `AddDataSeries(Tick, 1)` só checava `BarsInProgress == 0` no ramo `else` do spread, podendo duplicar volume em negócios no Bid/Ask. | **1.** Adicionado controle `sessionStartBar != CurrentBar` (igual ao `VWAPInstitucionalPro`) para resetar uma única vez por sessão.<br>**2.** Adicionado `if (BarsInProgress != 0) return;` no início de `OnMarketData`. |
| **Correlação de Pearson ($r$)** (`gex-dashboard/app/api/market-context/route.ts`) | `fetchYahooSymbol` descartava `result.timestamp` e reamostrava por índice `0..N-1`, correlacionando futuros 23h (`ES=F`/`NQ=F` desde `18:00 ET`) contra ETFs/índices RTH (`SPY`/`QQQ`/`^VIX` `09:30–16:00 ET`), além de poder correlacionar ativo ao vivo com curva determinística caso `ES`/`NQ` falhassem. | `fetchYahooSymbol` agora preserva `result.timestamp`, alinha `chartPoints` à janela RTH (`09:30–16:15 America/New_York`) quando disponível e indexa barras em buckets de 15m (`pointsByBucket`); `computePearsonCorrelationByBucket` calcula $r$ somente em timestamps coincidentes e apenas quando ativo e referência (`ES`/`NQ`) estão ao vivo. |

> **Nota para instalação no NinjaTrader 8:** Todas as correções dos indicadores C# (`NiveisEstruturaPro`, `NiveisGammaPro`, `MoneyRiskPro`, `GlobexRangePro` e `DeltaCumulativePro`) estão **embutidas diretamente dentro de `gex_profile_v7/instalador_cloud2.0.py`** (além de espelhadas em `DAILYOLHC.PY` e `DeltaCumulativePro.py`). Basta executar `instalador_cloud2.0.py` e pressionar **F5** no NinjaScript Editor.

### 19.2. Escopo Auditado e Preservado Sem Alteração (Regra de Ouro)
- **`gex_profile_v7/gex_profile_v7_cloud.py`:** `black_scholes_gamma`, `implied_vol_from_gamma`, `resolve_strike_vols`, `find_gex_flip`, `total_gex_at_spot`, `select_walls`, `calculate_max_pain`, escalas de proxies (`$SPX`, `SPY`, `$NDX`, `QQQ`, `DIA`, `IWM`, `NG`) e `ATIVOS_AGREGADOS`.
- **`gex_profile_v7/instalador_cloud2.0.py` (sem bugs):** `VWAPInstitucionalPro` (variância $O(1)$ e reset único), `FluentliExpectedMove`, `VolatilidadeImplicitaPro` e `DailyOHLCPro`.
- **`gex-dashboard` e `INDICADORES MACROECONOMICOS/`:** `app/page.tsx` (`DEX`, `GEX Vol`, `GEX OI`, `Opening Flow Vol > OI`), `app/correlacao/page.tsx` (espelhamento `× -1`), `app/macro/page.tsx`, `app/api/gamma-data/route.ts`, `app/api/macro-darkpool/route.ts`, `criador_dashboard_macro.py` e `dashboard_trader.py`.

### 19.3. Validações Executadas Após as Correções e Status dos Commits Git (`16/11/2026 17:41`)
- **Testes Python:** `python -m unittest -v test_gex_profile_v7_cloud.py` → **51/51 OK** (`4.567s`); `python -m unittest -v test_criador_dashboard_macro.py` → **6/6 OK** (`0.069s`).
- **Compilação / Sintaxe:** `py_compile` OK em `instalador_cloud2.0.py`, `gex_profile_v7_cloud.py`, `DAILYOLHC.PY` e `DeltaCumulativePro.py` (balanço `{`/`}` = `0` nos 9 códigos C#); `npx tsc --noEmit` (**0 erros**) e `npx eslint app/api/market-context/route.ts` (**0 erros/avisos**).
- **Commits Git:**
  - **`gex-dashboard` (branch `master`) — Commit `d843155` (`16/11/2026 17:41`):** `fix(correlacao): align Yahoo 15m timestamps and RTH window for Pearson correlation` (`app/api/market-context/route.ts`). *(Alterações locais prévias não relacionadas à auditoria em `app/biblioteca/page.tsx`, `app/globals.css` e o PDF não rastreado em `public/ebooks/` foram preservados fora do commit.)*
  - **`gex_profile_v7` (branch `main`) — Commit local desta rodada (`16/11/2026 17:41`):** `instalador_cloud2.0.py`, `DAILYOLHC.PY`, `DeltaCumulativePro.py` e `RELATORIO_CORRECOES_V9.md` *(caches `__pycache__/*.pyc` excluídos do commit conforme `regras.md`)*.
  - **Push remoto:** aguardando execução manual do usuário (`git push origin main` / `git push origin master`).


---

## 20. Correção de Acurácia `%` Diária (`chartPreviousClose`), Filtro Anti-Glitch Dark Pool `1m`, Expansão por Categorias e Escala `Z-Score σ` / Granularidade `5m` (`17/11/2026 09:48`)

### 20.1. Diagnóstico das Anomalias Reportadas em `/macro` e `/correlacao`

| Sintoma Observado nos Prints | Causa Raiz Técnica Comprovada no Código | Correção Cirúrgica Implementada |
|---|---|---|
| **Termômetro Macro (`ES -2.26%`, `NQ -3.46%`) e Raio-X (`NVDA -30.65%`, `AAPL +15.31%`) muito divergentes de `/correlacao` (`+0.16%`) e TradingView (`+0.08%`)** | Em `gex-dashboard/app/api/macro-darkpool/route.ts`, `fetchYahooChart()` priorizava `meta.chartPreviousClose` antes de `meta.previousClose`. Na API do Yahoo Finance, `chartPreviousClose` representa o fechamento **anterior à janela inteira** (`5 dias` no Termômetro; `3 meses` no Raio-X!). | `fetchYahooChart()` passou a priorizar `meta.previousClose` e só aceitar `chartPreviousClose` quando `range === "1d"`; nos ranges maiores (`3mo`, `1d` diário), compara a data de Nova York (`regularMarketTime` vs última barra diária) para obter o fechamento exato de 1 dia atrás; `buildThermometerAndBias()` também passou a consultar `("1d", "5m")` (com fallback `("5d", "1d")`) para leitura 1D exata. |
| **Cards Dark Pool `1m` exibindo `$22.923,8M` (`361.73x`) em `SPY`, `$18.692,3M` (`399.36x`) em `QQQ` e `16:45 BRT` enquanto em Brasília era `09:26`** | **1.** Algumas barras isoladas do feed gratuito `1m` do Yahoo Finance emitem o **volume acumulado da sessão inteira** (~50% do dia) em uma única barra de 1m.<br>**2.** Às `09:26 BRT` (`07:26 ET` em novembro, UTC-5 vs UTC-3 = +2h), NYSE/NASDAQ ainda está fechada (abre às `09:30 ET = 11:30 BRT`), logo `SPY/QQQ/GLD/IWM/DIA` trazem o último pregão sem exibir a data. | **1.** Adicionado filtro sequencial anti-glitch em `fetchIntradayProxyBlocks()` (`cumValidVol * 0.55`, `> 28%` de `lastVol` e `> 150x` mediana após abertura), preservando leilões reais (`09:30`/`15:59`, `$61M–$288M`) e eliminando falsos `$22B`. Adicionado também `TLT -> ZB / ZN (Bonds)`.<br>**2.** Adicionados `dateLabel` (`dd/MM`) e `isTodaySession` nos cards + aviso claro quando NYSE está fechada antes das `11:30 BRT`. |
| **Linhas `ES`, `NQ` e `ZN` parecendo "laterais / achatadas" em `/correlacao` junto com `VXX` / `VIX`, e eixo X travado em `09:30..16:15` com velas `15m`** | **1.** Plotar `VXX (+9.77%)` / `VIX (-2.23%)` no mesmo eixo Y percentual bruto que `ES (+0.08%)` / `ZN (+0.01%)` comprime `ES/NQ/ZN` em ~4 pixels perto de `0%`.<br>**2.** `fetchYahooSymbol()` usava `15m`, sem incluir o último ponto ao vivo `regularMarketPrice`, e `GET()` rotulava horários como `09:30–16:15` mesmo durante Globex. | **1.** Criada a alternância **Escala Normalizada (`Z-Score σ`) vs. `% Bruto`** em `app/correlacao/page.tsx` (Tooltip continua mostrando o `%` real + `Z-Score`).<br>**2.** `market-context/route.ts` atualizado para velas **`5m` (`bucket 300s`, mínimo 5 pontos coincidentes no Pearson)**, ponta ao vivo com `regularMarketPrice`, `timeLabels` reais da sessão (`ES`) e selo por card (`GLOBEX` / `Pregão RTH` / `Últ. Pregão dd/MM HH:mm ET`).<br>**3.** Auto-refresh reduzido de **`60s` para `20s`** em `/macro` e `/correlacao`. |
| **Poucas opções de Commodities, Índices, Bonds, Forex e Setores em Termômetro Macro e Raio-X Finviz** | Listas fixas com apenas `11` ativos no Termômetro e `10` ativos no Raio-X. | Termômetro expandido para **`64` instrumentos** em `THERMOMETER_DEFS` (`INDICES`, `COMMODITIES`, `BONDS`, `FOREX_CRIPTO`, `ACOES_SETORES`) e Raio-X para **`57` ativos** em `SQUEEZE_WATCHLIST` (`PRINCIPAIS`, `MAG7_TECH`, `SETORES`, `ETFS_BONDS`, `COMMODITIES_ETFS`, `FINANCEIRO_SAUDE_ENERGIA`, `ALTO_SHORT`, `ALL`), mantendo a visão padrão limpa em **Principais** + seletor por setinha (`<select>`) e sem inflar o rate-limit do Finviz (`?squeezeCat=...`). |

### 20.2. Adições Preservação-Only aos E-books & Transparência sobre Provedores Gratuitos
- **`gex-dashboard/public/ebooks/indicadores_macro_darkpool/teoria.md` & `pratica.md`:**
  - Conteúdo original **100% preservado sem remoção**; adicionadas as Seções **7 e 8 (`teoria.md`)** e **Seção 6 (`pratica.md`)** explicando cada elemento dos cards Dark Pool `1m` (`SPY → ES/MES`, `RVOL 1m` + filtro anti-glitch, `Nível` projetado, `ETF $` e data/hora `BRT vs ET`, `DARK POOL PRINT / ABSORÇÃO 1m`, `$M` nocional), uso operacional em **Localização, Contexto, Confluência e Entrada**, diferenças de horário `Globex vs RTH`, escala `Z-Score σ` e delay padrão CME (`10–15 min` em feeds gratuitos como Yahoo Finance e TradingView `[D]`).
- **Nota honesta sobre provedores gratuitos vs. delay de 15 min:**
  - Os módulos `/macro` e `/correlacao` consomem **Yahoo Finance** (cotações e candles gratuitos sem chave), **FINRA (`cdn.finra.org`)**, **ForexFactory**, **FRED** e **Finviz**. Por regra da própria bolsa **CME**, **nenhum provedor público gratuito sem autenticação entrega futuros CME (`ES`, `NQ`, `YM`, `RTY`, `GC`, `CL`, `ZN`, `ZB`) sem delay regulatório de 10–15 min** (mesmo selo `[D]` visto no TradingView). Já ações/ETFs à vista no Yahoo Finance durante RTH (`11:30–18:00 BRT`) atualizam com cache leve (~1–5s), e o painel agora consulta candles **`5m`** e atualiza a cada **`20s`**.

### 20.3. Validações e Commits desta Atualização (`17/11/2026 09:48`)
- **`gex-dashboard` (branch `master`) — Commit `2d660a1`:**
  - Arquivos commitados: `app/api/macro-darkpool/route.ts`, `app/api/market-context/route.ts`, `app/macro/page.tsx`, `app/correlacao/page.tsx`, `public/ebooks/indicadores_macro_darkpool/teoria.md`, `public/ebooks/indicadores_macro_darkpool/pratica.md` *(preservando intactos `app/biblioteca/page.tsx`, `app/globals.css` e o PDF externo).*
  - **`npx tsc --noEmit`:** **exit code `0`** (**0 erros de tipagem**).
  - **`npx eslint app/api/macro-darkpool/route.ts app/api/market-context/route.ts app/macro/page.tsx app/correlacao/page.tsx`:** **exit code `0`** (**0 erros / 0 avisos**).
  - **Push remoto:** aguardando execução manual do usuário (`git push origin main` no `gex_profile_v7` e `git push origin master` no `gex-dashboard`).


---

## 21. Curva de Juros Institucional da Tesouraria EUA em Tempo Real (`Par + Bootstrapped Spot Zero + 5y5y Forward`) e Guia Visual Completo (`17/11/2026 10:12`)

- **Esclarecimento Técnico sobre Calendário Econômico USD (Sem Alterar `app/api/macro-darkpool`):**
  - A pasta `gex-dashboard/app/api/macro-darkpool/` foi mantida **100% intacta**. A rota existente já consulta `https://nfs.faireconomy.media/ff_calendar_thisweek.json` (**ForexFactory / FairEconomy**, não `sslecal2.forexprostools.com` do Investing.com). Para feeds estilo **MetaStock XENITH** (wire institucional Refinitiv em milissegundos), exige-se assinatura paga profissional; como alternativa gratuita com API REST oficial JSON e chave gratuita opcional, destaca-se **Finnhub Economic Calendar** (`/calendar/economic`).
- **Novo Motor Dedicado `gex-dashboard/app/api/yield-curve/route.ts`:**
  - Integra a curva oficial completa de **11 vértices do Departamento do Tesouro dos EUA** (`home.treasury.gov` XML: `1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y`), fallback **St. Louis FRED CSV** (`DGS3MO..DGS30`) e sobreposição ao vivo intraday (`5m`) via **Yahoo/CME** (`^IRX`, `2YY=F`, `^FVX`, `^TNX`, `^TYX`, com normalização segura de escala `/ 10` se `> 18`).
  - Executa **Bootstrapping Semestral padrão de Renda Fixa** para extrair a curva **Zero-Cupom Spot (`z(t)`)** (`DF_k = (1 - (c_k / 2) * Sum(DF_j)) / (1 + c_k / 2)`), calcula **`Forward 5y5y`**, **`Spread 2s10s`**, **`10Y - 3M` (Modelo Fed)**, **`5s30s`** e **`Butterfly 2s5s10s`** (`2*5Y - 2Y - 10Y`), além de classificar automaticamente os **4 Regimes Intraday** (`BULL_STEEPENING`, `BEAR_STEEPENING`, `BULL_FLATTENING`, `BEAR_FLATTENING`) com impacto direcional em **Índices (`ES/NQ/RTY`)**, **Bonds (`ZT/ZN/ZB`)** e **Commodities/Dólar (`GC/CL/HG/DXY`)**.
- **Interface & E-book (`app/macro/page.tsx`, `teoria.md`, `pratica.md`, `curva_juros_institucional.svg`):**
  - Integrado gráfico de 3 linhas (*Par Yield Tempo Real* vs *Spot Zero Bootstrapped* vs *Fechamento Anterior*) + cards de *Spreads*, *Butterfly*, *5y5y Forward* e impacto direcional dentro do bloco **Banco Central / FRED Oficial** de `/macro`.
  - Adicionados diagrama SVG (`curva_juros_institucional.svg`), **Seção 9 em `teoria.md`** (fórmulas, regimes e exemplos reais de mercado em alta/baixa) e **Seção 7 em `pratica.md`** (rotina de 4 passos antes das ordens), sem apagar conteúdo anterior.
- **Validações & Commits (`17/11/2026 10:12`):**
  - `npx tsc --noEmit`: **exit code `0`** (**0 erros**).
  - `npx eslint app/api/yield-curve/route.ts app/macro/page.tsx`: **exit code `0`** (**0 erros / 0 avisos**).
  - **`gex-dashboard` (`master`) — Commit `158d521`:** `app/api/yield-curve/route.ts`, `app/macro/page.tsx`, `public/ebooks/indicadores_macro_darkpool/imagens/curva_juros_institucional.svg`, `teoria.md`, `pratica.md` (`app/api/macro-darkpool` preservado intacto).
  - **`gex_profile_v7` (`main`) — Commit desta atualização:** `RELATORIO_CORRECOES_V9.md`. *(Push remoto aguardando usuário.)*


---

## 22. `NiveisGammaPro`: Correção de Tags Invisíveis em Footprint (`barsAgo = -10/-60`), Sistema Anti-Colisão 2D e Dicionário Separado (`17/11/2026 12:26`)

### 22.1. Diagnóstico & Correção no C# do NinjaTrader 8 (`gex_profile_v7/instalador_cloud2.0.py`)
- **Erro encontrado (Tags `TxtDP`, `TxtMP`, `TxtCW`, `TxtPW`, `TxtZG` e DTEs sumindo ou se sobrepondo):**
  1. `Desenhar()` e `DesenharNivelDte()` chamavam `Draw.Text(..., barsAgo = -10)` e `-60` (deslocados `10` a `60` candles futuros para a direita do candle atual). Em gráficos com velas largas (**Volumetric / Footprint**) ou sem extensa margem direita, esses rótulos caíam **totalmente fora da área visível à direita da escala de preço**.
  2. Quando dois ou mais níveis coincidiam em strikes próximos (ou próximos às barras de `NiveisEstruturaPro` na borda direita), vários textos com o mesmo `barsAgo` sobrepunham uns aos outros.
- **Correção aplicada (`CODE_GAMMA` em `instalador_cloud2.0.py`):**
  - Mantidas todas as linhas horizontais via `Draw.HorizontalLine` e limpas as antigas tags legadas `Txt*` via `RemoveDrawObject`.
  - Implementado **`OnRender(ChartControl, ChartScale)` com Direct2D / SharpDX** desenhando todas as tags visíveis (`MAX OPTION VOLUME`, `CALL WALL`, `PUT WALL`, `GEX FLIP`, `MAX PAIN`, `0DTE/1DTE/2DTE/7DTE`) em caixa escura de alto contraste com **algoritmo anti-colisão 2D**: tenta 3 colunas horizontais (`0`, `-310px`, `-620px`) no `Y` exato da linha e degraus verticais de `±26px` até encontrar espaço livre (evitando o painel `QUANT ENGINE V8` no topo esquerdo e o histograma `NiveisEstruturaPro` na borda direita via nova propriedade ajustável **`Margem Direita Tags (px)`**, padrão `190`), traçando fio conector pontilhado até a linha correspondente sempre que deslocado; todos os recursos Direct2D/DirectWrite são descartados em `OnRenderTargetChanged()`.
- **Definição confirmada de `MAX OPTION VOLUME` (`Tag: DP` / `TxtDP`):**
  - Gerado por `dp = df_levels.loc[df_levels["vol"].idxmax()]` em `gex_profile_v7_cloud.py`, identifica o strike que recebeu o **maior volume total de contratos de opções negociados na sessão** (Calls + Puts, por exemplo `253.785 contracts [26400]` no NQ agregado), atuando como pivô de liquidez institucional intradiário.

### 22.2. Dicionário Separado (`gex-dashboard/public/ebooks/niveisgammapro/DICIONARIO_NIVEIS_GAMMA_PRO.md`)
- Criado arquivo dedicado **separado de `teoria.md` e `pratica.md`** contendo a definição completa de todas as 17 linhas horizontais, explicação detalhada da diferença entre `CW`/`PW` sem DTE (`ALL` / Macro) vs. `0DTE`/`1DTE`/`2DTE`/`7DTE`, siglas do `NiveisEstruturaPro` (`CW`, `PW`, `ZG`, `[OPEN$]`), explicação de `MAX OPTION VOLUME | 253785 contracts [26400]`, glossário do painel `🛡️ QUANT ENGINE V8` e explicação do novo sistema anti-colisão.

### 22.3. Validações & Commits (`17/11/2026 12:26`)
- **`py_compile instalador_cloud2.0.py` & balanço `{`/`}`:** OK em todos os 9 blocos `CODE_*` (diferença `0`).
- **`python -m unittest -v test_gex_profile_v7_cloud.py`:** **51/51 OK** (`9.850s`).
- **`gex-dashboard` (`master`) — Commit `2bcde91`:** `public/ebooks/niveisgammapro/DICIONARIO_NIVEIS_GAMMA_PRO.md`.
- **`gex_profile_v7` (`main`) — Commit desta atualização:** `instalador_cloud2.0.py` e `RELATORIO_CORRECOES_V9.md`. *(Lembrete: executar `instalador_cloud2.0.py` e pressionar **F5** no NinjaScript Editor do NinjaTrader 8 para recompilar o indicador; push remoto aguardando usuário.)*

---

## 23. Glossário Macro/Portunhol, Correção SVG da Curva de Juros & E-book Completo de Microestrutura, MBO e Contratos CME/Globais (`17/11/2026 14:29`)

### 23.1. Correção Visual SVG (`curva_juros_institucional.svg`)
- Corrigido o vazamento de texto à direita em **`(expectativa estrutural)`** na caixa das 4 métricas institucionais de `gex-dashboard/public/ebooks/indicadores_macro_darkpool/imagens/curva_juros_institucional.svg`: largura da caixa ampliada (`x=48`, `width=596`), `Spot Zero Bootstrapped + Forward 5y5y` quebrado em duas linhas com `font-size="10.2"` / `"10"`. Validado via `xml.etree.ElementTree.parse` (`XML=OK`, `backticks=0`).

### 23.2. Glossário de Siglas e Termos Macro + "Portunhol de Tela" (`Deflação vs. Inflação`)
- **`c:\Users\alanb\source\gex-dashboard\DOCUMENTACAO_TRADING\INDICADORES_MACROECONOMICOS\GLOSSARIO_SIGLAS_TERMOS_PAINEL_MACRO.md`:** Arquivo separado na pasta `INDICADORES_MACROECONOMICOS` explicando em linguagem direta `Mag 7`, `Beta Alto`, `Proxy`, `RVOL`, `Short Float/Ratio/Squeeze`, `Bull/Bear Flattening & Steepening`, `5y5y Forward`, `Spot Zero`, `Butterfly 2s5s10s`, `bps`, `Inflação / Desinflação / Deflação / Estagflação`, `Hawkish/Dovish`, `QE/QT`, `CPI/PCE/PPI/NFP`, `DXY`, `VIX/VXX/UVXY`, `HYG/LQD`, `Market Internals ($ADD/$TICK)`, `FINRA Reg SHO/TRF/Condition Code D`, `MOC` e `Regra do 16`. *(Observação: a pasta pai `c:\Users\alanb\source\gex-dashboard` não é repositório Git — arquivo salvo diretamente em disco.)*
- **`gex-dashboard/public/ebooks/indicadores_macro_darkpool/pratica.md` (Seção 8 adicionada sem apagar conteúdo anterior):** Explicação prática da diferença entre **Inflação**, **Desinflação**, **Deflação** e **Estagflação**, mais lista rápida "Portunhol de Tela".

### 23.3. Novo E-book Completo: `gex-dashboard/public/ebooks/microestrutura_mercados_cme/`
- **`teoria.md`:** Microestrutura completa do `CLOB / DOM` CME (`FIFO` em `ES/NQ/GC/CL` vs. `Pro-Rata` em Treasuries curtos), **`MBO` (*Market-By-Order*, feed CME MDP 3.0)** vs. **`MBP` (*Level 2*)**, leitura de lotes individuais, **Icebergs Nativos CME**, *Pulling vs. Absorption*, ranking de liquidez global, participantes reais com nomes e objetivos (**Market Makers / Primary Dealers / HFTs:** Citadel, Virtu, Jane Street, Optiver, SIG, IMC, Jump, HRT, DRW, XTX, JPM, Goldman; **Market Takers / Fundos / Hedgers:** Bridgewater, Millennium, BlackRock, PIMCO, CTAs, Exxon, Vitol, Cargill, ADM, JBS), arbitragens (*Soybean Crush* `ZS/ZM/ZL`, *3:2:1 Crack Spread* `CL/RB/HO`, *EFP* `GC/SI`, *Index Arb* & *Delta-Hedging GEX*), conexões intermercados e ponte cultural EUA ↔ **B3 (`WIN/IND`, `WDO/DOL`, `DI1`, `EWZ`)**.
- **`pratica.md`:** Precificação de índices (`Fair Value` e Mini vs. Micro `1/10`) + **Tabelas completas A–F** cobrindo **Índices (`ES/MES`, `NQ/MNQ`, `YM/MYM`, `RTY/M2K`)**, **Metais (`GC/MGC/1OZ`, `SI/SIL`, `PL`, `PA`, `HG/MHG`)**, **Energia (`CL/MCL`, `BZ`, `RB`, `HO`, `NG/QG/MNG`)**, **Grãos (`ZC/XC`, `ZS/XK`, `ZL`, `ZM`, `ZW/XW`, `ZO`, `ZR`)**, **Pecuária (`LE`, `GF`, `HE`)**, **Treasuries CBOT em 32 avos (`UB`, `ZB`, `ZN`, `ZF`, `ZT`)**, **Moedas CME (`6E/M6E`, `6J/M6J`, `6B/M6B`, `6A/M6A`, `6C`, `6S`, `6L`) + Micro Cripto (`MBT/MET`)**, **SOFR (`SR3`)**, **Softs globais na ICE (`KC`, `SB`, `CC`, `CT`)** e **B3 (`IND/WIN`, `DOL/WDO`, `DI1`)**, além de regras práticas com **`MBO`**, `MoneyRiskPro`, `DeltaCumulativePro` e `NiveisGammaPro`.
- **Recursos Visuais (4 arquivos em `imagens/`):** `market_makers_vs_takers.jpg`, `cme_ativos_ilustrados.jpg`, `fluxograma_conexao_mercados.svg` e `ilustracao_contratos_cme.svg` (todos os SVGs validados via `xml.etree.ElementTree.parse` e todas as referências de imagem conferidas em disco).

### 23.4. Commits & Observação sobre `/biblioteca` (`17/11/2026 14:29`)
- **`gex-dashboard` (`master`) — Commit `f0df1ff`:** `public/ebooks/indicadores_macro_darkpool/imagens/curva_juros_institucional.svg`, `public/ebooks/indicadores_macro_darkpool/pratica.md` e toda a pasta `public/ebooks/microestrutura_mercados_cme/` (8 arquivos no commit).
- **Observação:** Em seguida, o usuário autorizou restaurar `app/biblioteca/page.tsx` para o `HEAD` (`82c57de`, eliminando 2 erros de ESLint da cópia local desatualizada) e registrar **`microestrutura_mercados_cme`** no menu lateral (**Commit `e96d046`**, `21 módulos / 42 ebooks`, ESLint `0 erros` e `tsc --noEmit` `0 erros`).
- **`gex_profile_v7` (`main`) — Commit anterior `393d8da` (`14:40`).**

---

## 24. Upgrade Visual `Neon Glow 3D` Ultra-Leve no `NiveisEstruturaPro` (`instalador_cloud2.0.py`) (`17/11/2026 14:39`)

### 24.1. Problema Identificado & Meta de Hardware (`Vivobook Ryzen 5 7520U / 8GB RAM / 486MB VRAM`)
- As barras horizontais do **`NiveisEstruturaPro`** eram desenhadas como retângulos chapados (`FillRectangle`, `3.5px–7px`), sem gradiente, com bordas amarelas rígidas nas barras fortes e sem proteção anti-colisão nas etiquetas de texto (`-$4,8M [OPEN$]`, `-$4,4M [OPEN$]`).
- Como o notebook executa o **NinjaTrader 8 + MZPack Footprint** com **7,28 GB de RAM utilizáveis e 486 MB de VRAM compartilhada Radeon**, efeitos pesados de shader GPU (`GaussianBlur`, timers a 60fps ou alocação de `Brush` por barra a cada tick) causariam travamentos.

### 24.2. Melhorias Gráficas & Otimizações Aplicadas no `NiveisEstruturaPro` (`CODE_ESTRUTURA`)
- **Degradê Horizontal em GPU Pré-Cacheado (`LinearGradientBrush` + `GradientStopCollection`):** 4 gradientes cacheados fora do loop (Calls regulares, Calls fortes `>65%`/Walls, Puts regulares e Puts fortes), variando de base profunda translúcida na escala direita até ponta **Ciano-Menta Neon** (Calls) ou **Magenta-Rosa Neon** (Puts). Como todas as barras compartilham a âncora à direita (`canvasRight`), **nenhum brush é recriado por frame** (apenas `.StartPoint` / `.EndPoint` são atualizados se a largura do painel mudar).
- **Efeito Neon Glow em Camadas Geométricas (Zero Shader VRAM):** `FillRoundedRectangle` com cantos arredondados (`RadiusX/Y`) + sub-camada halo translúcida atrás das barras dominantes + **filete specular Glass 3D (`1.25px`)** no topo + **ponta luminosa (*Leading Edge Cap*)** na extremidade esquerda (em **Âmbar/Ouro** automático quando `[OPEN$]`).
- **Pílulas Arredondadas & Anti-Colisão Vertical:** Etiquetas `CW`/`PW`/`ZG`/`-$X.XM [OPEN$]` agora usam pílulas escuras arredondadas com faixa lateral colorida e verificação `TagColide` (`usedTagRects`), deslocando apenas a etiqueta com linha guia quando strikes ficam colados — mantendo as barras sempre travadas no preço exato do strike.
- **Throttle Inteligente de I/O & VRAM:**
  - `LerTudo()` agora checa os timestamps UTC de `NiveisGamma_*.csv` e `GammaProfile_*.csv` (`File.GetLastWriteTimeUtc`), retornando `false` (sem reler CSV, sem alocar listas e sem chamar `ForceRefresh()`) quando os arquivos não mudaram.
  - `SharpDX.DirectWrite.Factory` agora é único e cacheado, descartado corretamente em `LimparRecursos()` tanto em `OnRenderTargetChanged()` quanto em `State.Terminated`.
- **Novas Propriedades em `Propriedades -> Visual`:**
  - **`EfeitoVisual`**: `"NEON_GLOW"` (padrão, com fallback seguro mesmo para templates antigos salvos no NT8), `"GLASS_3D"` (gradiente + brilho sem halo) ou `"ECO"` (ultra-leve reto para economia máxima de bateria/GPU).
  - **`EspessuraMax`**: espessura máxima da barra dominante em pixels (padrão `10 px`, escalando proporcionalmente de `4.4px` a `10px`).

### 24.3. Validações & Commits (`17/11/2026 14:39`)
- **`py_compile instalador_cloud2.0.py`:** **OK** (`PY_COMPILE_OK`).
- **Balanço de chaves `{`/`}` em todos os 9 blocos C# (`CODE_*`):** **OK** (`CODE_ESTRUTURA` 450 linhas, `{=107 }=107`, `diff=0`; todos os 9 blocos com `diff=0`).
- **`python -m unittest -v test_gex_profile_v7_cloud.py`:** **51/51 OK** em `4.792s`.
- **`gex_profile_v7` (`main`) — Commit `393d8da`:** `instalador_cloud2.0.py` e `RELATORIO_CORRECOES_V9.md`.

---

## 25. Correções `NiveisEstruturaPro` (`$k` + `[OPEN$]`), Redesign `NiveisGammaPro` Laser SharpDX (Sem Linha Cortando Texto) & Correção Matemática Welford no `VWAPInstitucionalPro` (`17/11/2026 15:19`)

### 25.1. `NiveisEstruturaPro` — Por que `CW` ficava sem valor e diferença real de `[OPEN$]`
- **`FormatVal(v)` corrigido para incluir milhares (`$k`):** Antes retornava `""` abaixo de `$1.000.000`, deixando paredes menores (como `CALL WALL | $318.493 [28280]`) exibindo apenas `CW` na barra. Agora formata também `>= 1e3` como `$318k` (`CW $318k`).
- **`[OPEN$]` 100% fiel ao `Volume > OI`:** Removida a trava arbitrária `ratio > 0.35` que escondia `[OPEN$]` em barras entre `25%` e `35%` da largura máxima. Agora toda etiqueta visível mostra `[OPEN$]` (+ ponta âmbar/dourada) estritamente quando há abertura de dinheiro novo hoje (`Volume > Open Interest` e `> 100` contratos); barras sem `[OPEN$]` representam exposição herdada (`OI >= Volume`).

### 25.2. `NiveisGammaPro` — Linhas Laser Estilizadas em SharpDX & Pílulas Fora da Linha
- **Fim das linhas WPF atravessando o texto:** Substituídas as 17 chamadas `Draw.HorizontalLine` WPF por renderização direta em SharpDX GPU dentro de `OnRender()` (em Z-order correto: linhas desenhadas **antes** das etiquetas, com limpeza automática única `legacyCleared` das linhas antigas salvas no gráfico):
  - **Muralhas Macro (`CW`, `PW`, `DP`):** Feixe laser fino (`1.5px`) com sub-aura translúcida (`5px`, alpha `0.16f`).
  - **`ZG` & `MP`:** Linha limpa pontilhada (`Dot`) / tracejada (`Dash`) de `1.3px` (`StrokeStyle` pré-cacheado via `Globals.D2DFactory`) com halo leve `3.6px`.
  - **Níveis DTE (`0DTE`, `1DTE`, `2DTE`, `7DTE`):** Traços discretos `1.05px–1.35px`.
- **Etiquetas flutuando acima da linha + afastadas das barras de volume:**
  - `dyCandidates` agora prioriza `-15px` (flutuando limpa **acima** da linha) antes de `+15px`, conectada à linha por uma micro-haste vertical + ponto indicador (`2.3px`) sobre o nível exato — **zero linha cortando texto**.
  - `MargemDireitaTags` padrão ajustado de `190` para **`370` px** (atualizando automaticamente também templates antigos que ainda carregavam `190`), tirando `MAX PAIN` e tags de cima do histograma de `300px` do `NiveisEstruturaPro`.
- **Performance:** `Desenhar()` (`DashFundo`) movido para dentro do throttle de 3 segundos em `OnBarUpdate()`, evitando recriar o painel HUD a cada tick.

### 25.3. `VWAPInstitucionalPro` — Cálculo Welford Estável & Correção das Bandas Muito Abertas
- **Bug de `DesvioMaximo` ignorado & padrão `4σ` exagerado:** O parâmetro `DesvioMaximo` (antes `3.0`) não era utilizado no código, que plotava `±1σ, ±2σ, ±3σ, ±4σ` (abrindo até `~2.000` pts no NQ). Agora:
  - Novo padrão institucional: **`DesvioMaximo = 2.0`** com **`NumBandas = 4`** → `step = DesvioMaximo / NumBandas = 0.5`, plotando **`±0.5σ, ±1.0σ, ±1.5σ, ±2.0σ`** (reduz pela metade a abertura excessiva, respeitando qualquer `DesvioMaximo` configurado!). Atualizado também no wrapper NinjaScript `#region`.
- **Bug numérico/tick no cálculo `sumP2V / sumVol - vwap²`:** Substituído por **Algoritmo de Welford Ponderado por Volume (`AcumularWelford`)** mantendo acumuladores congelados de barras fechadas (`closedSumVol`, `closedVwap`, `closedM2`) somados à barra em formação `[0]` sem mutar o histórico a cada tick (`Calculate.OnEachTick`). Elimina cancelamento numérico em preços altos (`28.000²`) e qualquer dupla contagem intrabar.

### 25.4. Validações & Commits (`17/11/2026 15:19`)
- **`py_compile instalador_cloud2.0.py`:** **OK** (`PY_COMPILE_OK`).
- **Balanço `{`/`}` em todos os 9 blocos `CODE_*`:** **OK** (`CODE_ESTRUTURA` 451 linhas `{=107 }=107 diff=0`; `CODE_GAMMA` 430 linhas `{=92 }=92 diff=0`; `CODE_VWAP` 264 linhas `{=41 }=41 diff=0`; todos os 9 blocos com `diff=0`).
- **`python -m unittest -v test_gex_profile_v7_cloud.py`:** **51/51 OK** em `5.778s`.
- **`gex_profile_v7` (`main`) — Commits `050e1d7` e `5fa4a7b`.**

---

## 26. Correção de Tabelas/Negrito da `/biblioteca`, Explicação do `SOFR (SR3)`, Guia `[OPEN$]` em `niveisestruturapro` & Redesign Completo de `FluentliWatchdog.cs` (`17/11/2026 20:30`)

### 26.1. `gex-dashboard` (`master`) — E-book `niveisestruturapro`, `/biblioteca` CSS/Markdown & `SOFR (SR3)`
- **`public/ebooks/niveisestruturapro/teoria.md` & `pratica.md` (`9c7e3b2`):** Adicionadas Seções 6 e 5 (sem remover conteúdo prévio) explicando `[OPEN$]` (`Volume > OI`) vs. sem `[OPEN$]`, barras em `$k` (`CW $318k`), barras apagadinhas (`ratio <= 0.25`), modos `GAMMA / VOLUME / OPENING_FLOW` e `EfeitoVisual` (`NEON_GLOW / GLASS_3D / ECO`).
- **`app/biblioteca/page.tsx` (`formatInline`):** Corrigido regex de negrito para `/\*\*((?:(?!\*\*)[^\n])+?)\*\*/g`, resolvendo casos de negrito com itálico interno (`**CBOT · Aveia (*Oats*)**`) que antes quebravam mostrando asteriscos literais sem negrito.
- **`app/globals.css`:** Adicionado `word-break: normal` e `white-space: nowrap` em `.md-table th` e `.md-table code` + `min-width: 78px` em `.md-table td` (impedindo colunas como `Código` / `SR3` de quebrar letra por letra na vertical) e restaurada a regra `.reader-audio { justify-content: flex-start; }` em `@media (max-width: 800px)`.
- **`public/ebooks/microestrutura_mercados_cme/pratica.md`:** Limpos aninhamentos de asteriscos e adicionada explicação direta do **CME · 3-Month SOFR (`SR3`)** ("DI Futuro dos EUA", índice `100 - Taxa %`).

### 26.2. `gex_profile_v7` — Auditoria & Reescrita Completa de `FluentliWatchdog.cs` (Icebergs Dinâmico & Sintético em SharpDX)
- **Problemas encontrados no `FluentliWatchdog.cs` original:**
  1. Só disparava em print único (`agressao >= LotePequeno && volumeAnterior[preco] < agressao`), sem detectar recarregamento no livro DOM (`ReloadCount`) nem ordens fracionadas (**Iceberg Sintético**).
  2. `OnMarketDepth` gravava apenas `volumeAnterior[e.Price] = e.Volume` ignorando `Operation.Remove` e `e.Position` (gerando falsos disparos quando um nível era removido virando `0`).
  3. `bool icebergDeVenda = preco >= Close[0]` classificava quase todo trade recente no Ask como venda (porque `Last` atualizava `Close[0] = preco`).
  4. Bolinhas `PlotStyle.Dot` ficavam limitadas a `4/8/14 px` (não cresciam proporcionalmente acima de `LoteGigante`) e `Draw.Text(..., yPos ± 6 * TickSize)` desenhava o texto **em cima da bolinha** quando o zoom vertical comprimia os candles; além disso faltavam `lock (syncLock)`, `Cooldown` de voz e `Dispose()` no `SpeechSynthesizer`.
- **Correções implementadas em `FluentliWatchdog.cs` (601 linhas, `{=97 }=97 diff=0`):**
  - **Rastreamento completo Level 2 por `Position` (`Operation.Add / Update / Remove`) + Bid/Ask L1:** Atualiza profundidade real por preço e distingue compra vs. venda passiva comparando `e.Price` contra `Ask` e `Bid` reais.
  - **Iceberg Dinâmico (`D` — bolinha preenchida com aura Neon):** Detectado por recarregamento passivo no DOM (`ReloadCount >= 2` durante agressões no nível, compatível com Live e Market Replay via `e.Time`) ou agressão que supera a liquidez visível no book.
  - **Iceberg Sintético (`S` — anel duplo vazado):** Detectado por acúmulo fracionado no mesmo preço dentro de `JanelaSinteticoSeg` (padrão `15s`), atualizando e crescendo a mesma bolinha quando novos lotes picados entram naquele nível e barra.
  - **Tamanho proporcional real + texto SEMPRE fora da bolinha:** Renderização SharpDX GPU na coordenada `(BarIndex, Price)` exata com raio dinâmico (`5.5px` até `22px` via raiz quadrada do volume) e pílulas de texto (`D 540` / `S 320`) ancoradas **a `+7px` da borda externa da bolinha** em pixels de tela (com anti-colisão vertical `LabelColide`).
  - **Segurança & Leveza para 8GB RAM:** Acesso protegido por `lock (syncLock)`, lista limitada a `400` eventos, cooldown de `4s` no `SpeechSynthesizer` e `.Dispose()` limpo em `State.Terminated` e `OnRenderTargetChanged()`.

### 26.3. Validações & Commits (`17/11/2026 20:30`)
- **`gex-dashboard` (`master`):** `eslint app/biblioteca/page.tsx` -> **`0 erros`** (`1` aviso pré-existente linha 919); `tsc --noEmit` -> **`0 erros`**; regex Markdown validado (`broken_asterisks=0` em `teoria.md` e `pratica.md`); commits `9c7e3b2` e `74a7c19`.
- **`gex_profile_v7` (`main`):** `FluentliWatchdog.cs` & `RELATORIO_CORRECOES_V9.md` (`d1d080d`).

---

## 27. Correção NinjaTrader 8 de `FluentliWatchdog.cs` (`Operation` / `#region` / Áudio Zero-DLL) & Inclusão no `instalador_cloud2.0.py` (`17/11/2026 20:58`)

- **Erro `CS0234` em `OnMarketDepth` (`Operation`):** No NinjaTrader 8, o enum `Operation` (`Add / Update / Remove`) de `MarketDepthEventArgs.Operation` pertence a **`NinjaTrader.Cbi.Operation`** (e não a `NinjaTrader.Data.Operation`). Adicionado `using NinjaTrader.Cbi;` e qualificado explicitamente `NinjaTrader.Cbi.Operation.Remove` e `NinjaTrader.Cbi.Operation.Update`.
- **Erro `CS0102` / `CS0111` / `CS0121` / `CS0229` (`cacheFluentliWatchdog` duplicado):** Removido o bloco `#region NinjaScript generated code` manual (mesmo padrão dos outros 7 indicadores SharpDX do instalador), eliminando qualquer colisão ao colar/compilar no NinjaScript Editor.
- **Zero dependência de `System.Speech.dll` em tempo de compilação:** Substituído `using System.Speech.Synthesis;` por carregamento em runtime (`Assembly.Load("System.Speech, ...")` + fallback automático para COM nativo `SAPI.SpVoice`), garantindo compilação no **F5** mesmo sem referenciar manualmente `System.Speech.dll` no NinjaScript Editor.
- **Antialiasing SharpDX:** Ativado `RenderTarget.AntialiasMode = SharpDX.Direct2D1.AntialiasMode.PerPrimitive` (com restauração garantida em todos os caminhos de `OnRender`).
- **`instalador_cloud2.0.py` (`10` indicadores):** Adicionado `CODE_WATCHDOG` e `"FluentliWatchdog.cs": CODE_WATCHDOG` em `arquivos_para_instalar`, atualizando o instalador para gravar todos os `10` indicadores diretamente na pasta `Indicators` do NinjaTrader 8.

---

## 28. `FluentliWatchdog.cs` — Cores Configuráveis (4 Brushes) & Rastreio Opcional de Defesa no Preço (`17/11/2026 22:25`)

- **Cores Personalizadas no Painel do NinjaTrader 8 (`Grupo 3. Cores Personalizadas`):**
  - Expostas `CorCompraDinamico`, `CorVendaDinamico`, `CorCompraSintetico` e `CorVendaSintetico` (`[XmlIgnore]` + pares `[Browsable(false)] ...Serialize` com fallback seguro contra `null` via `Serialize.BrushToString` / `StringToBrush`).
  - `EnsureRenderResources()` converte as cores WPF escolhidas para SharpDX GPU (`ExtractColor4`) e invalida o cache automaticamente sempre que o usuário altera alguma cor (`lastColorSignature`).
- **Rastreio Opcional de Defesa no Preço (`Grupo 4. Rastreio de Defesa no Preço`):**
  - Parametrizável via `AtivarLinhaRastreio` (`true`), `RastreioLoteMinimo` (`100` contratos), `ToleranciaRastreioTicks` (`8` ticks) e `MaxLinhasRastreio` (`6` linhas simultâneas).
  - **Transparência técnica sobre CME/NT8:** Como o feed público da CME não transmite CNPJ nem ID de corretora/player após a execução, o rastreio acompanha a **zona de preço da defesa passiva** — estendendo linha tracejada enquanto o preço respeitar o nível (`DEF C` / `DEF V`, contabilizando reforços do mesmo lado `(+N)` dentro da zona), e encerrando com marcação discreta caso o preço rompa além da tolerância.
- **Sincronização com `instalador_cloud2.0.py`:** `CODE_WATCHDOG` atualizado com o novo código completo.

---

## 29. Calibração Dinâmica de Proxies (`NQ ← QQQ/$NDX`, `ES ← SPY/$SPX`, `YM ← DIA`, `RTY ← IWM/RTY*0`) (`17/11/2026 23:36`)

- **Problema diagnosticado nos CSVs do Dropbox (`17/11`):**
  - A razão fixa `QQQ × 40` no `NQ` ficou defasada (`NQ / QQQ ≈ 41,4` por dividendos, taxa ETF e juros embutidos no futuro `NQ DEC26`), deslocando strikes do `QQQ` cerca de **`~900` pontos abaixo** do futuro real (`PW = 26320`, `CW/MP = 26760` vs. spot `27241`).
- **Correção aplicada em `gex_profile_v7_cloud.py` (`calibrate_proxy_strike_mult`, `fetch_reference_spot`, `process_group`, `ATIVOS_AGREGADOS`):**
  - Proxies de índices com `"align_to_ref": True` (`$SPX`/`SPY` para `ES`, `$NDX`/`QQQ` para `NQ`, `DIA` para `YM`, `IWM` para `RTY` usando `spot_ref_url = RTY*0`) passaram a calcular a razão real do pregão (`spot_futuro / spot_proxy`, com trava de sanidade `0.85x–1.15x` sobre o multiplicador estático).
  - Para `RTY`, `dte_strike_mult` no Time Travel também herda o multiplicador calibrado contra `RTY*0`, alinhando Macro e fatias `_0DTE`/`_1DTE`/`_2DTE`/`_7DTE` na grade do contrato futuro.
  - Refletido automaticamente no NinjaTrader 8 e no Dashboard Web via CSVs do Dropbox (zero alteração necessária no `gex-dashboard`).

---

## 30. Suíte `VeltrixQuant` no NT8 (13 Indicadores + Pasta Automática), Novo Studio TradingView Web (Drag SL/TP, Templates, `DeltaCumulativePro`, `MoneyRiskPro`, Feeds `$0` e Relatório de Performance) (`18/11/2026 15:08`)

### 30.1. `gex_profile_v7` (`main`) — Brand `VeltrixQuant` & 3 Novos Indicadores SharpDX/PCM no `instalador_cloud2.0.py`
- **Pasta da Marca & Realocação Automática (`VeltrixQuant`):**
  - Definida a marca `MARCA_PASTA = "VeltrixQuant"`. Ao rodar `instalador_cloud2.0.py`, cria automaticamente `Custom/Indicators/VeltrixQuant/`, remove cópias antigas da raiz dos 13 indicadores (evitando `CS0101` duplicado no F5 sem tocar em arquivos `@*.cs`), move eventuais arquivos soltos antigos da suíte para `VeltrixQuant/` e cria `VeltrixQuant_URL.txt` se ausente.
  - Todos os **13 indicadores** agora recebem `Name = "VeltrixQuant - ..."` em `State.SetDefaults` (agrupando juntos no menu `Ctrl+I`) mantendo **100% intactos** os `ClassName`s originais e o `namespace NinjaTrader.NinjaScript.Indicators` (preservando Chart Templates e `FluentliQuantBot_V1`), além de atualização síncrona em [FluentliWatchdog.cs](file:///C:/Users/alanb/source/gex_profile_v7/gex_profile_v7/FluentliWatchdog.cs).
- **Novos Indicadores Embutidos (Zero DLLs Externas, `{`/`}` Balanceados, Parser JSON Puro C# + TLS 1.2):**
  1. **`DarkPoolBeamsPro.cs` (`VeltrixQuant - DarkPoolBeamsPro`):** Consome `/api/macro-darkpool` em thread separada, correlaciona tokens raiz exatos (`ES/MES->SPY`, `NQ/MNQ->QQQ`, `RTY/M2K->IWM`, `YM/MYM->DIA`, `GC/MGC->GLD`, `ZB->TLT`, `ZN->IEF`, `CL/MCL->USO`), desenha **Feixes de Luz Lilás pulsantes** em `SharpDX.Direct2D1.LinearGradientBrush`, tags anti-colisão com mini-barra de força por absorção e Card resumo **FINRA Reg SHO (`% Compra/Non-Short vs % Short`)**.
  2. **`NyseTickBreadthPro.cs` (`VeltrixQuant - NyseTickBreadthPro`):** Implementado em **Modo A Automático**: verifica conexões via Reflection priorizando `TICK.Z` (IQFeed) ou `^TICK`/`$TICK`/`TICK-NYSE` via `Instrument.GetInstrument` em `State.Configure`; quando ausente/inativo (ex.: Tradovate Demo), chaveia automaticamente para **Modo B Proxy Web (~15s)** via `/api/market-context` com bandas de clímax `±1000` e strip de correlação adaptado ao ativo aberto.
  3. **`OrderFlowImbalanceFlash.cs` (`VeltrixQuant - OrderFlowImbalanceFlash`):** Motor de microestrutura em tempo real estilo *Bookmap Market Pulse* (`0ms` via `OnMarketData` L1 Bid/Ask + janela deslizante consistente com `e.Time`), faixas luminosas de desequilíbrio sobre os candles, card piscante com botão `[SOM: ON/MUTE]` DPI-aware (`ChartingExtensions.ConvertToHorizontalPixels`) e **6 sons não-vocais pré-sintetizados em PCM WAV 16-bit (`MemoryStream` + `SoundPlayer`)** com cadência progressiva controlada por `Stopwatch` (`700ms -> 360ms -> 210ms`).
- **Documentação Didática Criada:** [GUIA_DIDATICO_VELTRIXQUANT_E_DASHBOARD.md](file:///C:/Users/alanb/source/gex_profile_v7/gex_profile_v7/GUIA_DIDATICO_VELTRIXQUANT_E_DASHBOARD.md).

### 30.2. `gex-dashboard` (`master`) — Estabilidade, Customização, Mouse-Drag OCO, Performance & Feeds
- **Eliminação da Piscada/Reload a Cada 1 Minuto (`app/page.tsx`):** Substituído `setLoading(true)` global no polling de 60s por `hasInitialLoadRef` + `isRefreshing`, preservando zoom/arraste/boleta/templates do usuário durante atualizações em segundo plano.
- **Backend Dark Pool (`app/api/macro-darkpool/route.ts`):** Adicionados **`IEF`** (`ZN Notes 7-10Y`) e **`USO`** (`CL=F`, fallbackRatio `0.9`) à cesta e ao mapa de projeção ao vivo.
- **Studio TradingView & Indicadores (`TradingViewGexChart.tsx` & `TradingViewProfileOverlay.tsx`):**
  - Gerenciador completo de **Templates Nomeados** (`gex_tv_templates_v1` + auto-load padrão `gex_tv_default_template_v1` via lazy initializer livre de cascading renders), presets built-in (`Quant Neon Dark`, `Institutional Clean + Dark Pool`, `Modo Claro / Alto Contraste`) e painel **Fundo & Cores** para candles, fundo, grade, linhas GEX e todos os indicadores.
  - Sub-painel real (`BaselineSeries` na Pane 1) do **`DeltaCumulativePro`**, plotagem e card do **`MoneyRiskPro`** (`RISK STOP`, `ALVO 1:1`, `ALVO 2:1`), barra **`Pulso Macro & NYSE $TICK*`** sempre visível com retry explícito e ajuste anti-colisão no `TradingViewProfileOverlay` (`width <= 72%`, pílulas opacas `right-[74px]`).
  - **Mouse Drag & Drop no Gráfico (`pointerdown` capture phase + `coordinateToPrice` + `snapToInstrumentTick`):** Agora é possível arrastar com o mouse no gráfico as linhas de **`OCO Take Profit`**, **`OCO Stop Loss`**, **`Trailing SL`** e **Ordens Limit/Stop Pendentes**, com projeção em `$` ao vivo e botões rápidos **`+ Criar TP` / `+ Criar SL`** em [PaperTradingBoleta.tsx](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/components/PaperTradingBoleta.tsx).
  - **Feeds Baixa Latência + Aba `TradingView Oficial` ([TradingViewOfficialWidget.tsx](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/components/TradingViewOfficialWidget.tsx)):** Stream SSE reduzido para `2s` em `app/api/candles/stream/route.ts`, **WebSocket Binance 0ms** automático em `BTC-USD`/`ETH-USD`, suporte opcional a chave gratuita permanente **Finnhub WS (`$0/mês`)** para ETFs/Ações dos EUA, botão 1-clique **`Operar s/ Delay`** em futuros CME para o ETF correspondente e aba comparativa com o widget oficial do `TradingView.com`.
- **Relatório Profissional de Performance (`usePaperAccount.ts` + `PaperPerformanceModal.tsx`):**
  - Simulador Paper Account `$50.000` local no `localStorage` (transparente: não loga em corretora externa), expandido para 500 trades com cálculo de Risco Planejado e `R:R` Realizado, **Profit Factor**, **Win Rate**, **Expectancy**, **Max Drawdown ($ e %)**, **Take Profits vs Stop Losses vs Trailing**, **Curva de Equity em SVG** e **Exportação CSV**.

---

## 31. URL de Produção da Vercel Embutida por Padrão no Instalador NT8 & Expansão da Pasta `Cursos` (`18/11/2026 16:39`)

- **`instalador_cloud2.0.py` (`DarkPoolBeamsPro`, `NyseTickBreadthPro` e `DASHBOARD_URL_PADRAO`):**
  - Identificada via prints do navegador a URL permanente da branch `master` na Vercel (`https://gex-dashboard-git-master-gex-cloud.vercel.app`, onde `/correlacao` e `/macro` com `USO`/`IEF` já respondem direto da nuvem).
  - Atualizado `DASHBOARD_URL_PADRAO`, o fallback padrão de `ResolveDashboardBaseUrl()` em `DarkPoolBeamsPro` e `NyseTickBreadthPro`, e a lógica de criação/atualização do arquivo `VeltrixQuant_URL.txt` (agora promove automaticamente de `http://localhost:3000` antigo para a URL da Vercel ao rodar Play, preservando eventuais URLs customizadas).
- **`C:\Users\alanb\Desktop\Cursos\` (Educação Quant & Engenharia Full-Stack):**
  - Auditada a pasta `01_Programacao_Engenharia_e_Tecnologia/`, criados os novos arquivos [04_Cursos_Adicionais_APIs_Sockets_Estatistica_e_Canvas.md](file:///C:/Users/alanb/Desktop/Cursos/01_Programacao_Engenharia_e_Tecnologia/04_Cursos_Adicionais_APIs_Sockets_Estatistica_e_Canvas.md) e [05_Como_Construir_DOM_Footprint_VolumeProfile_TPO_e_TradingViewStudio.md](file:///C:/Users/alanb/Desktop/Cursos/01_Programacao_Engenharia_e_Tecnologia/05_Como_Construir_DOM_Footprint_VolumeProfile_TPO_e_TradingViewStudio.md) (trilhas gratuitas americanas sem Coursera + legendas PT-BR + engenharia completa de APIs, Sockets, Canvas, Drag & Drop, Volume Profile, TPO, Footprint e DOM) e atualizado [00_GUIA_MESTRE_E_MAPA_DA_JORNADA.md](file:///C:/Users/alanb/Desktop/Cursos/00_GUIA_MESTRE_E_MAPA_DA_JORNADA.md).

---

## 32. Correção da Escala Y (`ES 7300 → SPY 730`), Race Condition no WebSocket Finnhub e Persistência Resiliente da Chave (`18/11/2026 16:58`)

- **Bug diagnosticado (`SPY` com velas esmagadas no rodapé enquanto eixo Y ia até `7160`):**
  1. Ao trocar de `ES` (~`7330`) para `SPY` (~`730`), o WebSocket da Finnhub (`~50ms`) disparava o primeiro trade antes do `snapshot` do SSE retornar e desenhava em cima das barras antigas do `ES`, além de o `priceScale("right")` manter a escala anterior e `DarkPool` usar `projectedFutureLevel` em ETFs.
- **Correções em [TradingViewGexChart.tsx](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/components/TradingViewGexChart.tsx):**
  - Limpeza imediata das séries (`candle`, `volume`, `VWAP`, `Delta`) e `autoScale: true` ao trocar de ativo/timeframe, travando ticks de `liveWs` via `snapshotReadyKeyRef` até o snapshot do novo símbolo chegar (com abertura correta de novos candles por intervalo `getIntervalSeconds`).
  - Correção do preço do `DarkPool` para usar `etfPrice` quando o gráfico está no próprio ETF, filtro anti-outlier para linhas muito distantes e adição do botão **`Ajustar Escala`** no cabeçalho.
  - Persistência dupla da chave Finnhub (`localStorage` + `document.cookie` de 1 ano com `auto-save` imediato ao colar) + botão **`Mostrar/Ocultar (👁️)`** para conferir a chave salva.

---

## 33. Correção `CS0104` de Ambiguidade `Brush` / `SolidColorBrush` no NinjaTrader 8 (`18/11/2026 18:05`)

- **Erro reportado no F5 do NinjaScript Editor (`CS0104`):** `DarkPoolBeamsPro.cs` e `NyseTickBreadthPro.cs` importavam simultaneamente `using System.Windows.Media;` e `using SharpDX.Direct2D1;`, causando ambiguidade de referência para `Brush` e `SolidColorBrush`.
- **Correção aplicada em [instalador_cloud2.0.py](file:///C:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py):** Qualificadas explicitamente todas as ocorrências WPF como `System.Windows.Media.Brush` e `System.Windows.Media.SolidColorBrush`, mantendo `SharpDX.Direct2D1.Brush` e `SharpDX.Direct2D1.SolidColorBrush` separados; verificador AST atualizado para detectar qualquer referência ambígua em todo o pacote (`amb=[]`, `ALL_CHECKS_OK=True`).

---

## 34. Diagnóstico Vercel Auth (`RESPOSTA SEM DARKPOOL`), Failover Automático Local, Ajuste HUD `NyseTickBreadthPro` e 3 Novos Módulos na Biblioteca (`18/11/2026 18:52`)

- **Causa raiz diagnosticada em `DarkPoolBeamsPro` (`RESPOSTA SEM DARKPOOL`) e `NyseTickBreadthPro` (`TICKQ/ADD/VIX/CORR = 0`):** A proteção **Vercel Authentication (SSO)** do projeto `gex-cloud` retornava HTTP `200 text/html` (`vercel.com/login`) para clientes externos sem cookie de sessão (como o NinjaTrader 8), impedindo o parse do JSON mesmo fora de horário ou com o site aberto no navegador.
- **Correções em [instalador_cloud2.0.py](file:///C:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py):**
  - Adicionados detecção explícita de resposta HTML de login (`payload.TrimStart().StartsWith("<")`) e **failover automático para `http://localhost:3000`** tanto em `DarkPoolBeamsPro.FetchDarkPoolAsync()` quanto em `NyseTickBreadthPro.PollMarketContext()`, com mensagem clara (`VERCEL EXIGE LOGIN (Desligue Vercel Auth ou ligue localhost:3000)` / `VERCEL EXIGE LOGIN`) e expansão do card de status offline (`380x62`) para evitar corte de texto.
  - Reposicionado o HUD superior do `NyseTickBreadthPro` (`panelTop + 24f`) para eliminar a colisão com o título nativo `VeltrixQuant - NyseTickBreadthPro(...)` no NinjaTrader 8.
- **Novos E-Books & Documentação de Configuração (`Tick Replay`) em `gex-dashboard`:**
  - Criados os 3 novos módulos completos (`teoria.md` + `pratica.md`) e registrados em [books.ts](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/lib/i18n/books.ts): `darkpoolbeamspro`, `nysetickbreadthpro` (explicando inclusive `#FF00BFFF` em `NyseTickValue`, barras verdes/vermelhas e leitura entre Índices/Bonds/Ouro/Petróleo) e `orderflowimbalanceflash` (explicando fita `OnMarketData` dos futuros vs opções, `C/V/Δ`, `tr/s`, `Top1/Top2`, faixas e sons PCM L1/L2/L3).
  - Atualizados `deltacumulativepro/pratica.md` e `fluentliwatchdog/pratica.md` com orientações de **Tick Replay** (desnecessário ao vivo) e `Days to load` (`3–5` dias para evitar `(Calculating...)` longo no `DeltaCumulativePro`).

---

## 35. Matriz Completa de Compatibilidade Tradovate Demo (`My NinjaTrader`) × 13 Indicadores × Ativos (`18/11/2026 19:50`)

- **Auditoria linha a linha no código dos 13 indicadores ([instalador_cloud2.0.py](file:///C:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py) + `macro-darkpool/route.ts` + `gex_profile_v7_cloud.py`):** Confirmado que todos os 13 funcionam na conta **Tradovate Demo (`My NinjaTrader`)**, separando exatamente os **7 universais** (`DailyOHLCPro`, `GlobexRangePro`, `VWAPInstitucionalPro`, `DeltaCumulativePro`, `OrderFlowImbalanceFlash`, `FluentliWatchdog` com L1 Sintético/blocos e L2 opcional, `MoneyRiskPro` com IV nos 9 e ATR/Fixo nos demais), os **4 de GEX/IV via Dropbox** (`9 Futuros + Micros`, com modo manual extra em `VolatilidadeImplicitaPro` e `FluentliExpectedMove`), **`DarkPoolBeamsPro`** (`8 Futuros + Micros`, excluindo `NG`, além de `25` ETFs/Ações fora da Tradovate) e **`NyseTickBreadthPro`** (`$TICK` universal com `^TICK` nativo Modo A funcionando na Tradovate Demo + `CORR` macro).
- **Arquivos criados e registrados na Biblioteca (`/biblioteca` — 27 módulos / 54 ebooks):**
  - [TABELA_ATIVOS_TRADOVATE_13_INDICADORES.md](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/public/ebooks/TABELA_ATIVOS_TRADOVATE_13_INDICADORES.md)
  - `public/ebooks/compatibilidade_tradovate_ativos/` ([teoria.md](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/public/ebooks/compatibilidade_tradovate_ativos/teoria.md) + [pratica.md](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/public/ebooks/compatibilidade_tradovate_ativos/pratica.md))
  - Registrado em [books.ts](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/lib/i18n/books.ts), [ptBR.ts](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/lib/i18n/dict/ptBR.ts) e [enUS.ts](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/lib/i18n/dict/enUS.ts).

---

## 36. Otimização `?only=darkpool`, Timeout 20s + `127.0.0.1` Failover e Diagnóstico DLL/Vercel (`18/11/2026 20:26`)

- **Diagnóstico ao vivo na máquina do usuário (`Documents\NinjaTrader 8\bin\Custom`):**
  - Verificado que `DarkPoolBeamsPro.cs` e `NyseTickBreadthPro.cs` tinham sido gravados no disco às `19:13:14`, porém `NinjaTrader.Custom.dll` ainda era de `18:10:29` (não recompilado com `F5` no NinjaScript Editor após a atualização), mantendo na tela o código antigo (`RESPOSTA SEM DARKPOOL`) sem tentativas para `localhost:3000`.
  - Confirmado ainda que `/api/macro-darkpool` completo em `npm run dev` levava ~`4s–7s` (no limite do timeout antigo de `7000ms`), enquanto `VeltrixJsonParser` em C# (compilado contra o JSON real via `csc.exe`) decodificou todos os `24` blocos e `25` linhas FINRA sem erro (`ROOT_NULL=False`).
- **Melhorias aplicadas em [route.ts](file:///c:/Users/alanb/source/gex-dashboard/gex-dashboard/app/api/macro-darkpool/route.ts) e [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py):**
  - Adicionado suporte a `?only=darkpool` no backend (retorna apenas `finra` + `proxyBlocks` sem esperar FRED, Calendário USD e Finviz).
  - Elevado `VeltrixTimeoutWebClient` para `20000ms` (`20s`), adicionado fallback `http://127.0.0.1:3000` junto a `http://localhost:3000`, `ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12` e `ChartControl.InvalidateVisual()` no retorno de falha em `DarkPoolBeamsPro`.

---

## 37. Suporte a `Protection Bypass for Automation` (`x-vercel-protection-bypass`) no NinjaTrader 8 (`18/11/2026 20:50`)

- **Objetivo de segurança:** Permitir que o usuário mantenha **`Vercel Authentication` LIGADA** (protegendo 100% o site contra acessos sem login da conta Vercel), ao mesmo tempo em que `DarkPoolBeamsPro` e `NyseTickBreadthPro` autenticam automaticamente nas URLs `.vercel.app` sem depender de `localhost:3000` nem VS Code.
- **Alteração em [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py):** Adicionado `ResolveVercelBypassToken()` em `DarkPoolBeamsPro` e `NyseTickBreadthPro`, lendo `VELTRIX_BYPASS_TOKEN` ou `VeltrixQuant_BYPASS.txt` (`Documents\NinjaTrader 8\bin\Custom\Indicators\VeltrixQuant\VeltrixQuant_BYPASS.txt`) e enviando o cabeçalho HTTP `x-vercel-protection-bypass` sem alterar assinaturas de parâmetros dos templates salvos.

---

## 38. Exibição de `@ Preço` nas Pílulas Dark Pool + Expansão Visual/Matemática dos Manuais (`18/11/2026 21:11`)

- **[instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py) (`DarkPoolBeamsPro.OnRender()`):** Adicionado o preço formatado pelo `TickSize` do contrato (`@ 27430.75`) dentro de todas as etiquetas `DP <ETF> @ <preço> · $... · ASK ABS / BID SUP / CLUSTER · HH:MM BRT`.
- **Manuais ampliados sem remoção de conteúdo (`gex-dashboard/public/ebooks/`):**
  - `darkpoolbeamspro/` (`teoria.md`, `pratica.md`, `imagens/exemplo_real_dp_ask_cluster_finra.png`, `imagens/anatomia_feixes_e_matematica_darkpool.svg`): adicionada explicação completa com exemplos visuais de `ASK ABS` (parte vendedora passiva), `BID SUP` (parte compradora passiva), `CLUSTER` (nó neutro), FINRA `COMPRA/NON-SHORT % vs SHORT %`, explicação do horário `11:30 BRT`/`15:51 BRT` vs `21:07 BRT`, todas as 6 equações matemáticas (`Mediana 1m`, `RVOL`, `Nocional $M`, `absorptionScore`, `closePos`, `Nivel_Futuro` e `FINRA`) e guia do `VeltrixQuant_BYPASS.txt`.
  - `orderflowimbalanceflash/` (`teoria.md`, `pratica.md`, `imagens/exemplo_real_linha_verde_15.png`, `imagens/exemplo_faixa_verde_no_candle.svg`): documentada a linha fina verde `+15` / vermelha `-15` sobre os candles (`MostrarFaixasNoPreco = true`, `Math.Max(6, VolumeMinimoJanela / 3)`).

---

## 39. Restauração da Assinatura `private void StartPolling()` em `DarkPoolBeamsPro` (`18/11/2026 21:25`)

- **Erro reportado no F5 do NinjaScript Editor (`CS1519` / `CS0103` na linha `494`):** A inserção de `ResolveVercelBypassToken()` logo acima de `StartPolling()` havia removido acidentalmente a assinatura `private void StartPolling()` deixando `{ int intervalMs = ... }` solto no corpo da classe.
- **Correção aplicada em [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py):** Restaurada a linha `private void StartPolling()` antes do bloco de código e ampliado o verificador `verify_installer.py` com checagem estrutural automática para impedir blocos `{` sem assinatura em todos os 13 indicadores.

---

## 40. Redesign Visual/Móvel do QuantEngine, Painel Separado (`QuantEnginePainelPro`) e Cores Personalizadas no Imbalance e DarkPool (`19/11/2026 14:35`)

- **Problema reportado:** A caixa antiga do `QUANT ENGINE V8` (`Draw.TextFixed` opaca `420x235` fixa em `TopLeft`) cobria candles e o card do `OrderFlowImbalanceFlash` (`MARKET PULSE`), sem opção de mover/separar em painel próprio, além de `OrderFlowImbalanceFlash` e o retângulo FINRA de `DarkPoolBeamsPro` possuírem cores fixas no código.
- **Alterações aplicadas em [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py):**
  - **`NiveisGammaPro` (`CODE_GAMMA`):** Substituído o `Draw.TextFixed` por HUD moderno em SharpDX com fundo translúcido configurável (`OpacidadePainelPct`, padrão `72%`), `TamanhoFontePainel`, cores personalizáveis (`CorFundoPainel`, `CorTextoPainel`, `CorRegimeShort`, `CorRegimeLong`), **4 estilos visuais** (`Compacto`, `BarraHorizontal`, `Completo`, `Minimizado`), **7 posições** (`SuperiorEsquerdo`, `SuperiorDireito`, `InferiorEsquerdo`, `InferiorDireito`, `BarraTopo`, `BarraRodape`, `Oculto`), `OffsetPainelX`/`OffsetPainelY`, botões clicáveis `[⇄]` (trocar posição) e `[−]`/`[+]` (minimizar) e arraste direto com o mouse no cabeçalho, além de `hudReserve` dinâmico para as tags de níveis GEX.
  - **Novo indicador nº 14 `QuantEnginePainelPro` (`CODE_QUANT_PANEL`):** Painel separado (`IsOverlay = false; DrawOnPricePanel = false`) dedicado para exibir todo o `QUANT ENGINE V8` fora da área de candles/fluxo em 3 modos responsivos (`3 cartões`, `2 cartões` ou `faixa compacta`) com seletor `VencimentoDTE` e personalização completa de cores e opacidade.
  - **`OrderFlowImbalanceFlash` (`CODE_ORDERFLOW_IMBALANCE_FLASH`):** Adicionadas cores personalizáveis (`CorCompra`, `CorVenda`, `CorNeutra`, `CorFundoPainel`, `CorBordaPainel`, `CorTextoPrincipal`, `CorTextoSecundario`), `OpacidadeFundoPct`, `OpacidadeFaixasPct` (retângulos das faixas de preço), seletor `CantoPainel` em enum (`VeltrixImbalancePosicaoV8`), `OffsetPainelX`/`OffsetPainelY`, botão `[⇄]` e arraste direto com o mouse preservando o botão `[SOM]`.
  - **`DarkPoolBeamsPro` (`CODE_DARKPOOL_BEAMS`):** Adicionadas cores personalizáveis para os feixes e para o retângulo FINRA + pílulas (`CorFeixeBid`, `CorFeixeAsk`, `CorFundoRetangulo`, `CorBordaRetangulo`, `CorFundoEtiqueta`, `CorTextoPrincipal`, `CorTextoSecundario`), `OpacidadeRetanguloPct`, `PosicaoCardFinra` (`VeltrixDarkPoolPosicaoV8`), `OffsetCardX`/`OffsetCardY`, botão `[⇄]` e arraste direto no retângulo FINRA para não sobrepor a tabela de footprint.

---

## 41. Botões de Acesso Rápido na Barra Superior do Gráfico (`MainMenu`), Precisão `0.00%` FINRA e Manual QuantEngine V8 (`19/11/2026 16:00`)

- **Atalhos na barra superior da janela Chart (`OwnerChart.MainMenu`, ao lado de ativo/minutagem/`mzVolumeProfile`):**
  - Adicionados botões WPF deduplicados e multi-abas com janelas flutuantes escuras de configuração instantânea (`... settings`) em [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py) para:
    1. **`⚙ GammaPro` (`NiveisGammaPro`)**: presets rápidos (`Compacto`, `Barra Topo`, `Só Linhas (Ocultar HUD)`), `PosicaoPainel`, `EstiloPainel`, `OpacidadePainelPct`, `TamanhoFontePainel`, `MargemDireitaTags`, `OffsetPainelX/Y` + `Zero`, e cores Hex com prévia visual (`Aplicar` / `Aplicar & Fechar`).
    2. **`⚡ Imbalance` (`OrderFlowImbalanceFlash`)**: edição ao vivo de `JanelaSegundos`, `VolumeMinimoJanela`, `RatioDesequilibrio`, `BrilhoDecaimentoSeg`, faixas/caixinha, opacidade, offsets, áudio PCM (`VolumeAudioPct` + `InitAudioPlayers()`) e todas as cores.
    3. **`◉ DarkPool` (`DarkPoolBeamsPro`)**: edição ao vivo de `DashboardUrl`, `AtualizarSegundos`, `MaxFeixesVisiveis`, `LarguraFeixeBarras`, `NotionalMinMilhoes`, pulso, card FINRA, offsets, cores e botão **`Aplicar & Sincronizar`** imediato.
  - Compilação verificada via `csc.exe` C# 5 direto contra `NinjaTrader.Core.dll` e `NinjaTrader.Gui.dll` (`CSC_TOOLBAR_HUD_EXIT= 0`).
- **Precisão FINRA `0.00%` + indicação `(EOD)` em `DarkPoolBeamsPro`:**
  - Investigado o motivo de `QQQ` (`NQ`) e `SPY` (`ES`) exibirem ambos `54.9% | SHORT: 45.1%` no dia `2026-11-18`: ao vivo no `cdn.finra.org/equity/regsho/daily/CNMSshvol20261118.txt`, `QQQ` estava em `54.87% / 45.13%` (`$8.97B BULLISH`) e `SPY` em `54.92% / 45.08%` (`$11.00B NEUTRAL`) — ambos arredondavam para `54.9% / 45.1%` com 1 casa (`0.0`). Atualizado o card FINRA para `372px` com formato `0.00%` (`54.87%` vs `54.92%`) e rótulo `(EOD)`.
- **Novo Manual na Biblioteca (`gex-dashboard/public/ebooks/painel_quantengine_atalhos`):**
  - Criados `teoria.md`, `pratica.md` e diagrama SVG `comparacao_estilos_quantengine_e_barra_superior.svg` (registrado em `books.ts`, `ptBR.ts` e `enUS.ts` como 28º livro) explicando o que já está plotado no gráfico vs exclusivo do QuantEngine, comparação exata de `Compacto` vs `BarraHorizontal` vs `Completo` vs `Minimizado` vs `QuantEnginePainelPro` (#14), atalhos de barra superior/mouse e diagnóstico prático sobre Put Walls de `-Net GEX` em regime `SHORT GAMMA`.

---

## 42. `FluentliWatchdog` V2 (Linha Lateral Limpa + Filtro ES 800/NQ 200 + Painel Ao Vivo) & Indicador Nº 15 `HeatmapLiquidezPro` (`19/11/2026 16:28`)

- **`FluentliWatchdog` V2 ([FluentliWatchdog.cs](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/FluentliWatchdog.cs) sincronizado em `CODE_WATCHDOG` de [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py)):**
  - Novo padrão **`ModoVisual = LateralNoPreco`**: mantém os candles 100% livres traçando uma linha horizontal até a lateral direita com a bolinha (`D` / `S`) e pílula `@ Preço` (mantendo opção `SobreCandle`).
  - Filtros independentes para plotagem no gráfico: **`LoteMinGraficoES = 800`**, **`LoteMinGraficoNQ = 200`**, **`LoteMinGraficoOutros = 100`** e **`FiltroGraficoManual`** (`0=Auto`), enquanto **`LotePequeno` (`50`)** continua alimentando o novo **Painel Ao Vivo Móvel (`DINÂMICOS (DOM)` vs `SINTÉTICOS (FAT)`)** com arraste, `[⇄]` e `[−]`/`[+]`.
  - Mantido intacto todo o **motor de alerta de voz (`AtivarVoz` / `InitSpeech` / `SpeakAlertAsync`)** e adicionado botão na barra superior do Chart **`❄ Icebergs`** (`VeltrixToolbar_Watchdog`).
- **Novo Indicador Separado Nº 15 — `HeatmapLiquidezPro` (`CODE_HEATMAP_LIQUIDEZ` em `instalador_cloud2.0.py`):**
  - Mapa térmico Bookmap ultraleve em GPU (pincéis pré-alocados + buffer circular de `MaxSlicesHistorico = 120` a `500ms`) com escala **Vermelho Firme → Laranja → Amarelo → Cinza → Branco**, escada DOM L2 na lateral e **Painel Radar Móvel** exibindo **`SPOOF` (`FAKE / TIRADA`)**, **`HFT ROBÔ` (piscando)**, **`MANTIDA FIRME`**, **`⚡ STOP RUN` (varredura executada de ticks — com nota transparente sobre Book L2 vs Stops pendentes)** e botão na barra superior **`🔥 Liquidez`**.
- **Documentação Completa Preservação+Expansão (`gex-dashboard/public/ebooks/`):**
  - Criado 29º módulo **`heatmapliquidezpro/`** (`teoria.md`, `pratica.md`, diagrama SVG) registrado em `books.ts`, `ptBR.ts` e `enUS.ts`.
  - Adicionados os estudos de caso completos de **FINRA `54.87%` vs `54.92%` (`(EOD)`)** em `darkpoolbeamspro/pratica.md`, **Put Walls `-Net GEX` em `SHORT GAMMA` (`ES 7249` / `2DTE PW 7250 -$4.9M` / `NQ`)** em `niveisgammapro/pratica.md`, e as novidades V2 em `fluentliwatchdog/teoria.md` & `pratica.md`.

---

## 43. Suíte Estilo Rancho Dinero: `PerfilTpoVolumePro` (#16), `VWAP Value Channel` (#8), `VeltrixRangeVWAP`, Flodometer L2 (#15), 7 Templates XML & Manuais Multi-Ativos (`20/11/2026`)

- **`VWAPInstitucionalPro` (#8 em [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py)):**
  - Preservada a assinatura compatível de 4 `[NinjaScriptProperty]` (`NumBandas, MostrarBandas, ResetDiario, DesvioMaximo`) e adicionados: canal de valor sombreado em Direct2D (`SombrearCanalValor`, `BandaCanalSombreado`, `OpacidadeCanalPct`), tags à direita (`c VWAP`, `c +1.0`...), resets `SessaoGraficoETH` / `RthNovaYork0930` / `Semanal` / `Continuo` e botão na barra superior **`△ VWAP`**.
- **Nova Ferramenta de Desenho `VeltrixRangeVWAP` (`TOOL_RANGE_VWAP` -> `Custom\DrawingTools\VeltrixRangeVWAP.cs`):**
  - Ferramenta de desenho de 2 âncoras no estilo **Range VWAP (Rancho Dinero)** com moldura vertical, canal sombreado, curvas Welford `±0.5 / ±1.0 / ±1.5 / ±2.0 SD`, tags de preço e 3 modos (`SomenteNaFaixa`, `AncoradoAoVivo`, `ProjetarNiveisDireita`).
- **Upgrade `HeatmapLiquidezPro` (#15 -> Flodometer Pro):**
  - Adicionados: paleta viva **`BidAskAzulVermelho`** (Ask Carmim / Bid Azul Royal estendida no painel inteiro com `OpacidadeTrilhaPct = 52%`, mantendo **`Termica5Cores`**), **Bolhas Proporcionais de Execução com Números** ajustáveis (`BolhaVolMinimo`, `TamanhoBolhaMinPx/MaxPx`), e **3 colunas acopladas à direita (`Depth` | `LΔ PΔ` | `SVP`) + Termômetro Bid/Ask (%)**.
- **Novo Indicador Nº 16 `PerfilTpoVolumePro` (`CODE_TPO_VOLUME`):**
  - **Session TPO (`A, B, C...`) + Volume Profile Real CME** sem `Tick Replay` (com série `1m` automática em gráficos `>= 10m`), cálculo automático de `POC / VAH / VAL (70%) / IB / Mid / Naked POC`, cores personalizáveis dentro/fora da VA, botão **`📊 TPO+VP`** e menu de **clique direito direto por dia** (`Ocultar SÓ Retângulo VA deste Dia`, `Ocultar Dia inteiro`, `Juntar com Próximo Dia (Merge)`, `Dividir Perfil neste Candle (Split)`, `Desfazer Junção` e alternância em 1 clique das linhas padrão).
- **7 Templates XML de Gráfico NT8 Prontos (`templates\Chart\VeltrixQuant - 01..07.xml`):**
  - Instalados automaticamente por `instalador_cloud2.0.py` com **`IsTickReplay=false`**, incluindo templates completos (`30s`, `20R`, `30m`, `60m`, `1m`) e templates solitários (`Flodometer L2 Puro` e `TPO + VolumeProfile + VWAP`).
- **Novos E-Books & SVG Diagrams (`gex-dashboard/public/ebooks/`):**
  - Atualizado **`heatmapliquidezpro/`** (+ `flodometer_colunas_e_bolhas.svg` e matriz completa de `Tick Replay` / Bookmap).
  - Criados módulos 30 e 31: **`tpo_vwap_rancho_style/`** (+ `tpo_vwap_rancho_arquitetura.svg`) e **`config_ativos_e_templates/`** cobrindo presets completos para **`ES`, `NQ`, `CL`, `GC`, `SI`, `NG`, `YM`, `RTY`, `ZB`, `ZN`, Agro (`ZC`, `ZS`, `ZW`, `LE`) e Forex (`6E`, `6J`, `6B` vs Spot)**, registrados em `books.ts`, `ptBR.ts` e `enUS.ts`.

---

## 44. 20/11/2026 20:52 — Auditoria Completa (Pente Fino nos 17 Scripts), Correções de Cálculo / DirectX (`D2DERR_WRONG_RESOURCE_DOMAIN`) / Concorrência e Upgrades `PerfilTpoVolumePro`

- **Base Git / Arquivos Modificados:** Base `fd691dc`; alterados [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py) (`16` blocos `CODE_*` atualizados + `TOOL_RANGE_VWAP` auditado), [FluentliWatchdog.cs](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/FluentliWatchdog.cs) (sincronizado com `CODE_WATCHDOG`) e [RELATORIO_CORRECOES_V9.md](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/RELATORIO_CORRECOES_V9.md).

### 44.1 Diagnóstico dos Erros Laranja/Amarelos no Control Center Log (`0x88990015`) e Blindagem Geral Direct2D
- **Causa raiz nos logs (`trace.20261120.00000.txt` / `log.20261120.*.txt`):** Registrados `37.022` erros de `D2DERR_WRONG_RESOURCE_DOMAIN/WrongResourceDomain` (`0x88990015`) entre `16:23:09` e `17:54:25`. Após `18:52` (com `OnRenderTargetChanged` já corrigido previamente em `PerfilTpoVolumePro` e `VWAPInstitucionalPro`), os logs posteriores até `20:02:36` não geraram mais ocorrências (`log.20261120.00002.txt` limpo). As linhas laranjas visíveis no print de `19:29` eram registros antigos de `17:21–17:54` ainda abertos na aba **Log**.
- **Prevenção definitiva nos 8 indicadores SharpDX restantes:** Mesmo sem dispararem novos erros naquele gráfico, **8 de 10** indicadores com `SharpDX.Direct2D1` ainda não validavam a identidade de `RenderTarget.NativePointer` nem chamavam `base.OnRenderTargetChanged()` antes de reutilizar pincéis/gradientes. Endurecidos com rastreio `dxRenderTargetRef` / `dxRenderTargetPtr` e chamada explícita a `base.OnRenderTargetChanged()`:
  - `FluentliWatchdog` (`CODE_WATCHDOG`), `HeatmapLiquidezPro` (`CODE_HEATMAP_LIQUIDEZ`), `DarkPoolBeamsPro` (`CODE_DARKPOOL_BEAMS`), `NyseTickBreadthPro` (`CODE_NYSE_TICK_BREADTH`), `NiveisGammaPro` (`CODE_GAMMA`), `NiveisEstruturaPro` (`CODE_ESTRUTURA`), `QuantEnginePainelPro` (`CODE_QUANT_PANEL`) e `OrderFlowImbalanceFlash` (`CODE_ORDERFLOW_IMBALANCE_FLASH`).
  - `VeltrixRangeVWAP` (`TOOL_RANGE_VWAP`) já cria e descarta recursos Direct2D localmente dentro do `OnRender`, estando livre desse domínio cruzado.

### 44.2 `PerfilTpoVolumePro` (`CODE_TPO_VOLUME` — Nº 16): Bugs de Cálculo + Novos Recursos
- **Erros de cálculo e tempo real encontrados e corrigidos:**
  1. **TPO ao vivo perdido no rebuild (`OnMarketData` vs `RebuildAllProfilesSafe`):** `OnMarketData` atualizava letras `tpoLetters` apenas em `compiledProfiles`, sendo sobrescrito a cada fechamento de candle ou clique direito. Criado **`liveTickTpoByGroup`** aplicado dentro de `RebuildAllProfilesSafe` (com limpeza em `DataLoaded` e no fechamento de barra em `!usesSub1mSeries`).
  2. **Duplicação de volume na abertura do candle real-time (`!usesSub1mSeries`):** Em modo tick-by-tick sem série `1m`, `liveVolDeltasByGroup.Clear()` só rodava ao fechar o candle e somava o `Volume[0]` de abertura sobre os ticks já acumulados. Ajustada a posse do ciclo para evitar dupla contagem em `!usesSub1mSeries`.
  3. **Colisão de `BlockKey` e saltos ("pente") em candles rápidos:** `BlockKey` concatenado agora inclui `"_" + b.BarIdx0` contra duplicação no mesmo segundo; elevado o teto de `loopStep` em `DistributeBarToBlock` de `400L` para **`1500L`** para não pular ticks intermediários em barras muito voláteis de `NQ`.
  4. **Expansão cega da Value Area (70%) em níveis vazios (`CompileProfileRange`):** Quando tanto `upVol == 0` quanto `dnVol == 0`, o empate `0 >= 0` avançava sempre apenas para cima ignorando concentração logo abaixo. Implementada busca pelo próximo aglomerado populado mais próximo em volume/TPO.
- **Respostas à dúvida sobre `Mid (50% Range)` e novos recursos implementados:**
  - **Visibilidade real do `Mid (50% Range)`:** Ele existia apenas como linha `Dot` fina (`1.0f`) sem etiqueta nem seletor de cor, sumindo atrás das barras de Volume. Criada propriedade **`CorMid`** (padrão `#E879F9` orquídea brilhante, também no popup **`📊 TPO+VP`**), traço `DashDot` (`1.65f` via `dxDashDotStyle`) e pílula lateral **`MID 50% <preço>`**.
  - **Extensão seletiva de Zona (Retângulo VA + POC) até a borda direita:** Adicionados conjuntos **`extendedVaKeys`** e **`extendedPocKeys`** para estender até `panelRight` apenas os perfis/dias ou grupos unidos escolhidos pelo trader (mesmo após rolar para a esquerda e ainda exibindo linhas/extensões mesmo quando o corpo do dia já saiu à esquerda da tela), com tags identificadoras **`VA EXT [<data>]`** e **`POC EXT [<data>] <preço>`**. Transferência automática das extensões ao executar `Juntar com Dia Anterior`.
  - **Clique direito 2D direto sobre Retângulo VA ou POC estendida:** `OnChartContextMenuOpening` agora testa coordenadas `(px, py)` diretamente contra `ExtendedVaRect` e faixa `±8px` de `ExtendedPocY`, exibindo no topo do menu opções rápidas para **`Desfazer Extensão VA + POC desta Zona`**, **`Desfazer SÓ Retângulo VA Estendido`** e **`Desfazer SÓ POC Estendida`**.
  - **Desfazer Individual mantido + Desfazer Global em 1 Clique:** Preservado **`Desfazer Junção / Divisão SÓ deste Perfil`** e adicionados **`Desfazer TODOS os Merges / Splits (Restaurar Todos os Dias)`** e **`Parar TODAS as Extensões (VA + POC Estendidas)`** tanto no menu de clique direito quanto em botões dedicados no popup **`📊 TPO+VP`**.

### 44.3 Demais Indicadores Auditados e Corrigidos em `instalador_cloud2.0.py`
- **`VWAPInstitucionalPro` (`CODE_VWAP` — Nº 8) & `VeltrixRangeVWAP` (`TOOL_RANGE_VWAP`):**
  - Corrigido `ShouldResetAtBarIndex` para **`RthNovaYork0930`** cruzar exatamente `09:30 ET` em dias úteis `(prevNy, curNy]` (impedindo falso reset na abertura de domingo `18:00` e em lacunas entre dias) e ajustada chave semanal **`Semanal`** para domingo `18:00 ET` via deslocamento `+6h`. Preservados os 4 `[NinjaScriptProperty]` exigidos por `FluentliQuantBot_V1.cs`.
- **`DeltaCumulativePro` (`CODE_DELTA` — Nº 9 — BUG CRÍTICO corrigido):**
  - Corrigida falha grave em `OnMarketData` onde `e.Ask == 0` (comum fora de book L1 completo/replay) fazia `e.Price >= 0` classificar **100% dos negócios como compra (`isBuy = true`)**. Agora faz cache de **`lastBidPrice` / `lastAskPrice`**, exige `curAsk > 0 && curBid > 0` antes de comparar (com fallback na regra do tick), exige `e.Volume > 0`, zera estado em `DataLoaded` e passa a respeitar **`TipoVisualizacao == "Histogram"`** (`PlotStyle.Bar`).
- **`FluentliWatchdog` (`CODE_WATCHDOG` — Nº 10):**
  - Removida a falsa classificação **`(!hasDepthData && agressao >= LotePequeno)`** que fabricava rótulos **`"DINÂMICO (DOM)"`** sem existência de book L2. Impedida criação duplicada de evento ativo no mesmo cluster via `!cl.ActiveEvent.TrackCompleted`, adicionado fallback temporal com pruning acima de 300 clusters, limpeza em `DataLoaded` sob `syncLock` e liberação segura de arraste quando `e.LeftButton != Pressed`.
- **`HeatmapLiquidezPro` (`CODE_HEATMAP_LIQUIDEZ` — Nº 15):**
  - Substituído `.Clear()` destrutivo de `limitAddDeltaByTicks` / `limitPullDeltaByTicks` (acima de 350 ticks) por **`PruneDeltaMapLocked`** (preservando os 240 ticks mais próximos do último preço negociado). Movidas leituras `Ld`/`Pd` para dentro do snapshot inicial sob lock no `OnRender` (evitando dezenas de locks por linha), gravado `BarIndex` em `VolumeBubble`, ajustada transição `Historical -> Realtime` no SVP e adicionado guarda `LeftButton != Pressed` no arraste.
- **`DarkPoolBeamsPro` (`CODE_DARKPOOL_BEAMS` — Nº 11):**
  - Restaurado `Opacity = 1.0f` em `dxCoreAsk` / `dxCoreBid` / `dxCoreLilac` antes do medidor FINRA (evitando que o pulso dos feixes apagasse a barra FINRA), trocado `Close[0]` em `OnRender` por `Bars.GetClose(CurrentBar)`, garantido início automático de `pulseTimer` se ativo no load e protegido `levelPrice` contra `NaN/Infinity`.
- **`NyseTickBreadthPro` (`CODE_NYSE_TICK_BREADTH` — Nº 12), `NiveisGammaPro` (`CODE_GAMMA`), `NiveisEstruturaPro` (`CODE_ESTRUTURA`), `QuantEnginePainelPro` (`CODE_QUANT_PANEL`) e `OrderFlowImbalanceFlash` (`CODE_ORDERFLOW_IMBALANCE_FLASH`):**
  - Sincronizados `Lines[1]/[2]` com `NivelAlertaAlto` em `DataLoaded` e cor de polaridade no cabeçalho do `$TICK` mesmo no Modo A, além de reuso de coleções temporárias (`corrSnapScratch`, `itemsScratch`, `placedRectsScratch`, `staleKeysScratch`, `zoneSnapScratch`, `topLvlsScratch`), `CultureInfo.InvariantCulture` na formatação, detecção de troca de cores de `CorCallWall`/`CorPutWall` no cache DX, cache Bid/Ask em `OrderFlowImbalanceFlash` e proteção `audioLock` no `SoundPlayer`.
- **Scripts Clássicos & Overlay (`MoneyRiskPro`, `VolatilidadeImplicitaPro`, `FluentliExpectedMove`, `GlobexRangePro`, `DailyOHLCPro`):**
  - Pré-congelamento de `SolidColorBrush` do `BackBrush` e proteção `TickSize > 0` em `MoneyRiskPro`; resets em `DataLoaded` e formatação `InvariantCulture` em `VolatilidadeImplicitaPro`; `SecurityProtocolType.Tls12`, timeout de `8000ms` (`TimeoutWebClient`), trava `vixLock` e atualização de tela via `TriggerCustomEvent` em `FluentliExpectedMove`; corrigida condição diurna vs noturna `(HoraInicio > HoraFim)` e abertura `HoraInicio == 0` em `GlobexRangePro`; protegido intervalo invertido `fimRTH <= inicioRTH` e adicionado reset `DataLoaded` em `DailyOHLCPro`.

### 44.4 Verificações Executadas Após a Edição Final
- **`verify_python_and_templates.py`**: `PY_COMPILE_OK=True`, `WATCHDOG_SYNC=True`, `ALL_CHECKS_OK=True`, `16/16` blocos `CODE_*` sem chaves desbalanceadas ou colisão `Brush`/`SolidColorBrush`, `TOOL_RANGE_VWAP_OK=True`, e `7/7` templates XML `VeltrixQuant - 01..07.xml` válidos.
- **`verify_cs_from_installer.ps1` (`csc.exe .NET 4.0`)**: **`CS_FAILED_COUNT=0` (`17/17 PASS`: 16 indicadores + `TOOL_RANGE_VWAP.cs`)** compilados contra as DLLs locais do NinjaTrader 8.
- **`python -m unittest discover` (`test_gex_profile_v7_cloud.py`)**: **`Ran 54 tests in 9.267s — OK`**.
- **`verify_bot_combo.ps1` / Roslyn**: Confirmadas assinaturas de 4 parâmetros em `VWAPInstitucionalPro(4, true, true, 3.0)` e `DeltaCumulativePro("Line", 100, ...)`; compilação isolada de `FluentliQuantBot_V1.cs` via `csc.exe` externo acusa apenas interpolação C# 6 (`$""`) no `.NET 4.0` ou classes parciais já presentes em `NinjaTrader.Custom.dll`, sendo o pacote completo compilado normalmente via `F5` no **NinjaScript Editor**.

---

## 45. 20/11/2026 23:23 — Correção de Textos/Botões Cortados nos Popups, Persistência em `F5`/Reinício do NT8 e Espelhamento Cross-Chart (`PerfilTpoVolumePro`)

- **Arquivos Modificados:** [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py) (`CODE_HEATMAP_LIQUIDEZ`, `CODE_TPO_VOLUME`, `CODE_VWAP`) e [RELATORIO_CORRECOES_V9.md](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/RELATORIO_CORRECOES_V9.md).

### 45.1 Popups sem Cortes (`HeatmapLiquidezPro`, `PerfilTpoVolumePro`, `VWAPInstitucionalPro`)
- **Causa raiz:** As janelas `OpenQuickSettingsWindow` (`HeatmapLiquidezPro`, `Width = 445`) e `OpenQuickSettingsPopup` (`PerfilTpoVolumePro`, `Width = 460`, e `VWAPInstitucionalPro`, `Width = 445`) usavam largura fixa com `SizeToContent.Height` e barras horizontais de botões/checkboxes sem quebra (`StackPanel` rígido com alinhamento à direita), decepando botões na esquerda (`Zerar LΔ/PΔ`) e checkboxes/ações à direita (`Limpar Extensões VA/POC`, `Naked POC`, etc.).
- **Correção aplicada:** Trocado para `SizeToContent.WidthAndHeight` com `MinWidth` adequado (`540` no Heatmap, `580` no TPO+VP, `500` na VWAP), `TextWrapping.Wrap` nos títulos, grupos de checkboxes e botões em **`Wpf.WrapPanel`** e separação das ações/presets (`actionRow` à esquerda) dos botões de confirmação (`btnRow` `Aplicar`, `Aplicar & Fechar`/`OK`, `Fechar` à direita).

### 45.2 Persistência Automática em Atualização de Gráfico (`F5`) e Reinício do NinjaTrader 8 (`CODE_TPO_VOLUME`)
- **Causa raiz:** `mergeWithNextKeys`, `extendedVaKeys`, `extendedPocKeys`, `hiddenVaKeys`, `hiddenProfileKeys` e o antigo `userSplitBars` (indexado por número mutável de barra `#BarIdx0`) ficavam apenas em `HashSet` privados em memória, sendo apagados quando o NinjaTrader recriava a instância ao atualizar o gráfico (`F5` / *Reload All Historical Data*) ou ao fechar e reabrir a plataforma.
- **Correção aplicada:**
  - Trocado `userSplitBars` (`int`) por **`userSplitTimeKeys`** (baseado em `Time.Ticks` exato da barra) e sufixo determinístico `_sN` na chave de bloco `BlockKey`, tornando junções e splits imunes a mudanças na quantidade de barras históricas carregadas.
  - Adicionada persistência dupla via propriedades serializáveis **`[Browsable(false)] InstanceStateKey` / `EstadoPersistenteSerialize`** (salvas no Workspace/Template XML do NT8) + espelho em arquivo por instrumento/timeframe em `Documentos\NinjaTrader 8\VeltrixTpoState\TpoState_<Ativo>_<Timeframe>_*.dat`, com carregamento automático no `State.DataLoaded` pelo timestamp (`TS`) mais recente e gravação imediata (`SaveAndRepublishSafe()`) a cada Merge, Split, Extensão VA/POC, Ocultação ou Clear.

### 45.3 Espelhamento Cross-Chart de Área de Valor e POC + Correção de Initial Balance (`CODE_TPO_VOLUME`)
- **Espelhamento entre gráficos (`VeltrixTpoCrossChartHub`):** Adicionado hub estático thread-safe por ativo raiz (`ES/MES`, `NQ/MNQ`, `YM/MYM`, `RTY/M2K`, `GC/MGC`, `CL/MCL`, `NG`) e canal (`CanalSync 1..4`) com novas opções em `04. Espelhamento Entre Gráficos`, no popup **`📊 TPO+VP`** e no menu de clique direito:
  - **`PublicarZonasCrossChart`** (`DiaAtualEEstendidas`, `SomenteEstendidasEPinadas`, `TodosPerfisVisiveis`) + opção por dia **`📡 Espelhar VA/POC em Outros Gráficos`** (`pinnedSyncKeys`).
  - **`ReceberZonasCrossChart`** + **`SomenteZonasRecebidas` (`Modo Receptor Limpo`)**: permite exibir no gráfico operacional (`30s`, `20 Range`, `Tick`, `Renko`, `Flodometer`, `1m`/`5m`) apenas os retângulos de Área de Valor e POC vindos do gráfico macro de TPO, com mapeamento temporal por busca binária (`FindBarXByTime`) e clique direito na zona externa para ocultar individualmente (`🙈 Ocultar Zona Externa`).
  - **Initial Balance (`IB H/L`) em gráficos `1D` (`RebuildAllProfilesSafe`):** corrigido o cálculo de `IbHigh / IbLow` para usar a sub-série `1 Minute` quando `usesSub1mSeries` estiver ativo (evitando confundir o IB de 60 minutos com a máxima/mínima inteira do candle diário).

### 45.4 Validação Pós-Edição Final
- **`verify_python_and_templates.py`**: `PY_COMPILE_OK=True`, `WATCHDOG_SYNC=True`, `ALL_CHECKS_OK=True`, `TOOL_RANGE_VWAP_OK=True`, `16/16` blocos e `7/7` templates XML válidos.
- **`verify_cs_from_installer.ps1`**: **`CS_FAILED_COUNT=0` (`17/17 PASS`)** incluindo `CODE_TPO_VOLUME.cs`, `CODE_HEATMAP_LIQUIDEZ.cs` e `CODE_VWAP.cs`.

---

## 46. 21/11/2026 01:55 — Limpeza de Marcas nos E-books de Trading, Painel Privado de Estudos & Blueprint `VeltrixQuant Footprint Pro (#17)`

- **Arquivos Criados / Modificados em `gex_profile_v7`:**
  - [PROJETO_VELTRIX_FOOTPRINT_PRO.md](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/PROJETO_VELTRIX_FOOTPRINT_PRO.md) e [PROJETO_VELTRIX_FOOTPRINT_PRO.pdf](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/PROJETO_VELTRIX_FOOTPRINT_PRO.pdf) (**6 páginas vetoriais** — especificação pura sem código C#, conforme solicitado).
  - Diagramas SVG em `docs_footprint_imagens/`: [footprint_anatomia_visual.svg](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/docs_footprint_imagens/footprint_anatomia_visual.svg), [footprint_arquitetura_fluxograma.svg](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/docs_footprint_imagens/footprint_arquitetura_fluxograma.svg) e [footprint_matriz_ecossistema.svg](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/docs_footprint_imagens/footprint_matriz_ecossistema.svg).
- **Arquivos Modificados / Reorganizados em `gex-dashboard` e Painel Privado:**
  - Removidas todas as menções a softwares e empresas concorrentes (preservando `NinjaTrader 8`, `Tradovate`, `CME`, `FINRA`, `FRED`) e comparações de "parecido com/estilo" em todos os e-books `.md` e `.svg` de trading em `public/ebooks/` e em `lib/i18n/{books.ts,dict/ptBR.ts,dict/enUS.ts}`, renomeando `tpo_vwap_rancho_style` para `tpo_vwap_institucional`.
  - Movido `plano_carreira_stem_eua` para fora do repositório público comercial (`C:\Users\alanb\source\planejamento_pessoal_privado\`) com leitor próprio separado ([index.html](file:///c:/Users/alanb/source/planejamento_pessoal_privado/index.html), `app.js`, `styles.css`, `build_bundle.py`, `docs_bundle.js` e `COMO_USAR_E_PUBLICAR.md`).
- **Validações Executadas:**
  - Varredura automatizada em `public/ebooks`, `lib/i18n`, `PROJETO_VELTRIX_FOOTPRINT_PRO.md` e `docs_footprint_imagens/`: **`FINAL_COMPETITOR_HITS=0`**.
  - **`npx tsc --noEmit`** em `gex-dashboard`: exit code **`0`**.
  - **`node --check`** em `planejamento_pessoal_privado/{app.js,docs_bundle.js}`: **`JS_CHECK_OK`**.
  - **`build_bundle.py`**: `4` arquivos `.md` empacotados em `docs_bundle.js`.

---

## 47. 21/11/2026 03:06 — Implementação `FootprintPro (#17)`, Bolhas Laterais no `HeatmapLiquidezPro`, Template #08, Limpeza de Grupo A/Tooltips e Manuais Multi-Ativos

- **Implementação NinjaTrader 8 ([instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py)):**
  - **`FootprintPro.cs` (`CODE_FOOTPRINT_PRO` — Indicador #17):** Motor Orderflow GPU SharpDX Direct2D completo e compatível com C# 5 / `.NET 4.0` sem vazamento de `RenderTarget` (`OnRenderTargetChanged` + guarda `dxRtRef`/`dxRtPtr`). Inclui estilos independentes Left/Right (`BidAsk`, `Volume`, `Delta`, `SplitDeltaImbalance`, `Ladder`, `TradesNumber`, `Bid`, `Ask`, `DeltaPercentage`, `None`), formatos (`Brick`, `Histogram`, `HeatGradient` + gloss 3D), `AutoZoomLOD` dinâmico, reconstrução de tape (`ReconstructTapeMs`), modos históricos sem Tick Replay (`Hybrid1Minute`, `Real1TickNoReplay`, `BarVolumeOnly`) + stream 100% L1+L2 em tempo real, Imbalance (`Diagonal`/`Horizontal`) + **Stacked S/R Zones**, **Absorção L2 Real (`OnMarketDepth` + Tape)** e Zonas de Absorção, **Bar VPOC + Naked VPOC + Bar VA 68%**, **Unfinished Auction (`UA`)**, **Exhaustion (`EXH`)**, **Buying/Selling Traps**, **Ratio Numbers**, **Bottom Statistic Grid** (incl. `Vol/sec`, `Delta Rate/s`, `COT H/L`, `Predicted`), 4 alertas focados, clique direito para fixar/remover níveis-chave (`.dat` persistente) e janela Studio WPF **`🐾 Footprint`** com presets (`ES/MES`, `NQ/MNQ`, `GC/CL`, `ZB/ZN`, `FX 6E/6J`) e editor completo de cores.
  - **`HeatmapLiquidezPro.cs` (`CODE_HEATMAP_LIQUIDEZ`):** Adicionado `VeltrixHeatmapBolhaPosV9` (`CentroDoCandle`, `DireitaDoCandle`, `EsquerdaDoCandle`) e `DeslocamentoBolhaPx` (`38 px`) com linha guia conectora do centro do candle até a borda da bolha — eliminando sobreposição sobre os números do Footprint (exposto no popup `🔥 Liquidez` + botão `📐 Lateral Footprint (38px)`).
  - **Template #08 & Limpeza de Concorrentes C#:** Adicionado **`VeltrixQuant - 08 Footprint Pro + Flodometer + Watchdog (20 Range).xml`** (`DireitaDoCandle` pré-ativado nas bolhas), registrado `FootprintPro` em `arquivos_para_instalar` e `PREFIXOS_ECOSISTEMA`, e removidas todas as strings concorrentes (`Rancho`, `Acme`, `Bookmap`) das propriedades, tooltips e popups C#.
- **Reorganização Comercial Grupo A, Estudo Privado & Novo Manual Footprint (`gex-dashboard` + `planejamento_pessoal_privado`):**
  - Removidos da loja pública (`gex-dashboard/public/ebooks/` e catálogos `lib/i18n/`) todos os manuais não-comerciais/internos (`guia_programacao_dashboard`, `arquitetura_devops`, e versão original crua com código de `estatistica`) para `c:\Users\alanb\source\planejamento_pessoal_privado\estudos\`, reempacotando **10 documentos `.md`** no leitor offline via `build_bundle.py`.
  - Criados em `gex-dashboard/public/ebooks/`: **`estatistica`** limpo (*Metodologia Quantitativa & Black-Scholes GEX*, sem XSRF/scraping/código) e **`footprintpro`** (*Teoria, Fluxo Visual SVG e Tabela Prática Completa* cobrindo **Índices, Metais, Commodities Agro/Energia, Bonds/Treasuries e Forex Futuros CME**), além de atualização do guia [config_ativos_e_templates/teoria.md](file:///c:/Users/alanb/source/gex-dashboard/gex-dashboard/public/ebooks/config_ativos_e_templates/teoria.md) e [pratica.md](file:///c:/Users/alanb/source/gex-dashboard/gex-dashboard/public/ebooks/config_ativos_e_templates/pratica.md) para os **17 indicadores e 8 templates**.
  - Atualizada a lista `### Grupo A` em [04_Auditoria_Ebooks_Idioma_e_Padronizacao_Global.md](file:///c:/Users/alanb/source/modelo%20de%20neg%C3%B3cio%20e%20expans%C3%A3o/04_Auditoria_Ebooks_Idioma_e_Padronizacao_Global.md).
- **Validações Executadas:**
  - `py_compile` no [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py): **OK**; todos os **8 XML** de templates válidos; **`COMPETITOR_HITS=0`**.
  - Compilação `.NET 4.0 csc.exe` contra as DLLs locais do NinjaTrader 8 (`NinjaTrader.Core.dll`, `NinjaTrader.Gui.dll`, `NinjaTrader.Custom.dll`, `SharpDX*.dll`): **`16/18 PASS_RAW`** (incluindo **`FootprintPro.cs`**, `HeatmapLiquidezPro.cs`, `PerfilTpoVolumePro.cs`, `VeltrixRangeVWAP.cs`; os 2 restantes apenas referenciam o rodapé `@Indicator` gerado no `F5` do NT8) e **`COMBINED_18_PASS`** (**`0` erros / `0` colisões** compilando todos os 18 arquivos juntos num assembly único!).
  - **`npx tsc --noEmit`** (`0` erros) e **`npm run lint`** (`0` erros, `1` warning pré-existente `no-img-element` em `app/biblioteca/page.tsx`) em `gex-dashboard`.

---

## 48. 21/11/2026 04:49 — Correção Definitiva dos 8 Templates XML NT8 + Redesign Neon & Histórico Sem Tick Replay no `FootprintPro`

- **Causa Raiz do Erro ao Carregar Templates (`Unable to load chart template` / `Direct2DForm.CreateChartControlResources()`):**
  - Diagnóstico direto nos logs do NinjaTrader (`trace.20261121.00001.txt`) e validação via `XmlSerializer` em `.NET 4.0` revelaram que os templates XML gerados omitiam propriedades obrigatórias do `<CandleStyle>` (`StrokeSerialize`, `Stroke2Serialize`, `DojiBrushSerialize`), `<BarsProperties>` (`BarsSeriesId`, `Id`, `PriceMarker`, `From`, `To`, `Long/ShortExecutionBrushSerialize`, `PositionPen*`), `<ChartControlProperties>` (`AxisPenSerialize`, `CrosshairPen`, `ChartTextSerialize`, `LabelFont`, `BarDistance`, `TimeHighlighter0..9`) e `<ChartTrader>`.
  - **`_xml_ind` + `_build_nt8_chart_template` + `build_chart_templates` ([instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py)):** Esquema 100% alinhado ao `Default.xml` nativo do NT8 (`miss_cc=[]`, `miss_bp=[]`, `miss_cs=[]`, `miss_root=[]`, e `CANDLE_OK` em todos os **8 templates**), com `BarDistance=94` e candlesticks nativos ultrafinos/translúcidos (`BarWidth=1.2`) no **Template #08** para não poluir o Footprint.
- **Correções Visuais & Motor Sem `Tick Replay` no `FootprintPro.cs`:**
  - **Carregamento Histórico 100% Funcional Sem `Tick Replay` (mesmo com mercado fechado):** Novo modo padrão **`HybridFastInstant`** re-semeia cada barra histórica (`SeededVol`, `SeededH`, `SeededL`) com distribuição completa `[Low..High]` assim que `Volumes[0][0]` atualiza, eliminando barras vazias no carregamento sem `Tick Replay` e corrigindo `Real1TickNoReplay` para mapear via `CurrentBars[0]` em gráficos `Range`/`Tick`.
  - **Estética Limpa, Contínua e Sem Linhas Feias:**
    - Preenchimento opcional de lacunas de preço (`FillEmptyPriceLevels=true` padrão) com alinhamento pixel-a-pixel pelas bordas reais do tick e acabamento translúcido 3D glass.
    - Removida a linha curta laranja de `UA` em cima dos números, removida a linha vertical ciana externa de Value Area (substituída por barra neon interna e contraste de brilho na VA), e substituída a vela central grossa pelo **`VeltrixFpCandleSpineMode.LeftSlimRail`** (mini trilho OHLC limpo à esquerda, mantendo `Bid x Ask | Delta` livres).
    - **Marcadores Imbalance & Absorção Grandes e Luminosos:** Substituída a bolinha minúscula (`3px`) pelos modos personalizáveis **`NeonAuraBadge`** / `GlowingOrb` / `GlowingDiamond` / `LightningPill` (`ImbMarkerSizePx=10px` padrão) e **`ShieldPulseRing`** / `GlowingDoubleOrb` / `HexagonBadge` (`AbsMarkerSizePx=12px` padrão) com halo em múltiplas camadas + borda luminosa no cluster e painel **`🐾 Footprint`** atualizado.
- **Implantação & Verificação Pós-Edição:**
  - Arquivos atualizados em `C:\Users\alanb\Documents\NinjaTrader 8\bin\Custom\Indicators\VeltrixQuant\`, `DrawingTools\` e `templates\Chart\` (`8` templates verificados contra `Default.xml` + `TestXmlV4`).
  - Revalidação final pós-edição: `py_compile` OK, `COMPETITOR_HITS=0`, `ALL 8 XML templates valid`, `16/18 PASS_RAW` e **`COMBINED_18_PASS`** (`combined_rc=0`) no `csc.exe` `.NET 4.0`.

---

## 49. 21/11/2026 07:59 — Otimização O(N) de Carregamento Histórico & Zero-Alloc SharpDX + Resiliência Horizontal (`FootprintPro`)

- **Arquivo Modificado:** [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py) (`CODE_FOOTPRINT_PRO` — Indicador `#17`).
- **Causas Raiz Diagnosticadas:**
  1. **Lentidão extrema no carregamento histórico (mesmo sem Tick Replay):** `OnBarUpdate()` executava `RecomputeAnalyticsLocked(false)` (varredura de até `320` barras anteriores com ordenação de chaves e alocação de `SortedDictionary` + `List` por barra) em **todas** as barras históricas (`State.Historical`), criando complexidade quadrática `O(N * 320)`, enquanto `DistributeHistoricalBarOHLC` alocava `double[]` e iterava até `160` níveis em cada barra (e truncava candles muito altos acima de 160 ticks).
  2. **Peso na renderização (`60 FPS` lag) e perda dos clusters ao esticar/comprimir horizontalmente:** `DrawTextCentered` criava e descartava um objeto COM `DW.TextLayout` para cada célula/badge em todo frame, e `OnRender` alocava `new SortedDictionary<long, BucketRenderCell>` por barra visível, usava `Closes[0][0]` na thread de render, cortava barras largas fora de `±95px`, deixava deltas `0px` (`nxtX == cx`) derrubarem `pitchPx` para `8px` e ocultava os clusters quando `leftW < 4f` ou `availW < 18px`.
- **Correções Aplicadas:**
  - **Carregamento Histórico Instantâneo (`O(N)`):** Removida a chamada de `RecomputeAnalyticsLocked` de dentro do loop `State.Historical` em `OnBarUpdate()`; adicionado acumulador incremental `O(1)` (`histRunningCumDelta`, `histPrevBarDelta`, `lastHistCumBarIdx`), `DistributeHistoricalBarOHLC` cobrindo `[Low..High]` completos com passo adaptativo (`<= 56` bins) e `reusableWeights`, e extração de `ComputeBarCoreMetricsLocked` sob demanda (`MetricsComputed`) na janela recente (`<= 300` barras no `State.Transition`) ou ao rolar no gráfico. Ajustado `IsSuspendedWhileInactive = false` somente no `FootprintPro`.
  - **Cache por Barra & Pipeline Zero-Alloc GPU (`OnRender` / `RenderSideCell`):**
    - `FpBarData` agora mantém cache por barra (`CachedBuckets`, `CachedMaxVol`, `CachedMaxDelta`, `CachedTxtL`, `CachedTxtR`) invalidado apenas quando `DataVer`, `effGroup`, `FillEmptyPriceLevels` ou `sigHash` mudam, reutilizando `reusableBMap` e `reusableSortedTicks`.
    - `EnsureDxResources()` pré-configura alinhamento (`Center`) e `DW.WordWrapping.NoWrap` nos `DW.TextFormat` (`dxFontLeft`, `dxFontRight`, `dxFontSmall`, `dxFontStat`, `dxFontHdr`, `dxFontCompact`) além de `dxFillerFill`/`dxFillerEdge`, substituindo `DW.TextLayout` por `RenderTarget.DrawText(...)` direto em `DrawTextCentered`.
  - **Clusters 100% Visíveis em Qualquer Zoom/Estiramento Horizontal:**
    - Cálculo de altura por tick em thread segura via ponto médio da escala (`(chartScale.MaxValue + chartScale.MinValue) * 0.5`), limites `ChartBars` validados, margem horizontal dinâmica (`cullMargin = Math.Max(320f, defaultPitch * 1.5f)`) para barras esticadas e filtragem de deltas `< 2px` em barras com timestamps iguais.
    - Largura adaptativa mantendo colunas Esquerda/Direita visíveis até `1.2px` (`availW >= 2.2px`), fonte compacta `dxFontCompact` em larguras médias, aumento automático de opacidade + `FillRectangle` rápido no modo compacto (`w < 12f || h < 7f`) e descarte rápido de fillers vazios quando comprimido.
- **Validação Técnica Pós-Edição:**
  - `verify_installer_cs.py`: `py_compile: OK`, `COMPETITOR_HITS=0`, `ALL 8 XML templates valid`, `16/18 PASS_RAW` (incluindo **`FootprintPro.cs`**) e **`COMBINED_18_PASS`** (`combined_rc=0`) contra DLLs `.NET 4.0` locais do NinjaTrader 8.

---

## 50. 21/11/2026 08:53 — Redesign Visual Institucional (`3D Glass Bevel` Real, Clusters Sem Vazamento de Texto e `Statistic Grid` Moderno)

- **Arquivo Modificado:** [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py) (`CODE_FOOTPRINT_PRO`, `OpenStudioPopup`, `_build_nt8_chart_template`, `build_chart_templates`).
- **Melhorias Visuais & Estéticas Implementadas:**
  1. **`3D Glass Bevel` Real (`EnsureDxResources`, `DisposeDx`, `RenderSideCell`):** Substituída a antiga linha quase invisível (`1.8px`, `0.16` alpha) por acabamento em vidro 3D em múltiplas camadas (`dxCellBackdrop` vidro escuro translúcido -> preenchimento cromático -> gradiente especular superior `dxGlassTopGrad` via `LinearGradientBrush`/`GradientStopCollection` -> filete luminoso superior `dxGlassRimHighlight` -> sombra inferior profunda `dxGlassBotShadow` -> borda em relevo).
  2. **Tipografia Auto-Fit Sem Sobreposição (`DrawTextOptions.Clip`, `DrawTextShadowed`, `FormatCompactNum`):** Adicionado recorte estrito por célula (`D2D.DrawTextOptions.Clip`), sombra de leitura (`dxTextShadow`) e cascata automática de fontes (`dxFontLeft` -> `dxFontMid` -> `dxFontCompact`) com compactação inteligente em `K` (`1.6K x 875`) para que números grandes nunca invadam o candle central ou barras vizinhas, além de `DW.WordWrapping.NoWrap` garantido no `instalador_cloud2.0.py`.
  3. **Clusters, VPOC & Corredores S/R Mais Limpos:** Espaçamento central ajustado (`colGap = 3.5f`), VPOC com aura dourada e abas laterais luminosas (`beacon tabs`), zonas Stacked/Absorption suavizadas (`ZoneOpacityPct = 14`, âncora lateral `3.5px` e borda tracejada com pill `⚡ STK` / `🛡 ABS`), e padrões mais limpos (`CandleSpineMode = None` e `FillEmptyPriceLevels = false`) no `SetDefaults` e **Template #08** (com candles nativos translúcidos `#36...`).
  4. **Redesign Completo do `Statistic Grid` (`RenderStatisticGrid`) & Studio (`Width = 590`):**
     - Dock inferior com fundo obsidian (`#060A12`), linha divisória superior com brilho ciano, margem inferior estendida (`+ 12f`, `StatCellHeightPx = 22`) evitando corte da linha `Predicted`, e sidebar de legenda com indicadores coloridos por métrica (`dxFontLegend`).
     - Cada célula transformada em mini-card (`RadiusX = 3.5f`) com codificação visual viva e barras de progresso inferiores (`Volume`, `Buy Vol`, `Sell Vol`, `Trades`, `Cum Delta`, `Vol / sec`), medidor bidirecional no `Delta %`, card 3D no `Delta`, destaque âmbar/violeta em `Min/Max Δ` / `COT H / L` e card dourado em `Predicted` na barra ativa.
     - Janela `FootprintPro Studio` alargada para `Width = 590` (aba **`Color Studio`** exibida sem truncar o título) e label atualizado para `3D Glass Bevel`.
- **Validação Pós-Edição:**
  - `verify_installer_cs.py`: `py_compile: OK`, `COMPETITOR_HITS=0`, `ALL 8 XML templates valid`, `16/18 PASS_RAW` (incluindo **`FootprintPro.cs`**) e **`COMBINED_18_PASS`** (`combined_rc=0`).

---

## 51. 21/11/2026 09:18 — Pílulas 3D Glass em Todo o `Statistic Grid`, Fim das Linhas/Divisória, Borda Simétrica & Tipografia Maior (`FootprintPro`)

- **Arquivo Modificado:** [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py) (`CODE_FOOTPRINT_PRO`, `RenderStatisticGrid`, `EnsureDxResources`, `OpenStudioPopup`, `build_chart_templates`).
- **Melhorias Visuais Aplicadas:**
  - **Remoção total das linhas fininhas internas e divisória da legenda:** Removidas as barras de progresso inferiores e divisórias horizontais/verticais dentro do `Statistic Grid` (inclusive a linha divisória que separava `Volume` / `Sell Vol` / `Delta` dos quadros).
  - **Cards em Pílula 3D Glass em todas as linhas & Legenda em Cards:** Todas as linhas de métricas (`Volume`, `Buy Vol`, `Sell Vol`, `Trades`, `Delta`, `Delta %`, `Cum Delta`, `Min/Max Δ`, `Δ Change`, `Δ Rate/s`, `Vol / sec`, `COT H / L`, `Predicted`) e os rótulos da legenda lateral agora usam o mesmo formato de **cápsula 3D Glass arredondada (`RadiusX = 5.0f`)** com gradiente especular (`dxGlassTopGrad`), filete superior iluminado, sombra inferior em relevo e borda luminosa proporcional à intensidade.
  - **Dock Simétrico, Livre da Marca D'água NT8 & Tipografia Maior:**
    - Dock inferior flutuante com moldura simétrica (`dockX = panelLeft + 6f`, `dockW = panelRight - panelLeft - 12f`, `RadiusX = 8f`), folga inferior abaixo do dock (`statGridH + 26f`) deixando `© 2026 NinjaTrader, LLC` fora de `Predicted`, e recorte estrito por `RenderTarget.PushAxisAlignedClip(...)` / `PopAxisAlignedClip()` para alinhar colunas nas bordas direita/esquerda sem buracos.
    - Fontes maiores e nítidas por padrão: **`StatCellHeightPx = 25`**, **`StatFontSize = 12`** (`Segoe UI Bold` em `dxFontStat` sem sombra borrada), **`dxFontLegend = 11.0f Bold`** (`legW = 104f`), **`LeftFontSize = 12`**, **`RightFontSize = 12`**, todos editáveis ao vivo nas abas `Clusters & Tape` e `Signals & Grid` do **`FootprintPro Studio`** e gravados explicitamente no **Template #08**.
- **Validação Pós-Edição:**
  - `verify_installer_cs.py`: `py_compile: OK`, `COMPETITOR_HITS=0`, `ALL 8 XML templates valid`, `16/18 PASS_RAW` (incluindo **`FootprintPro.cs`**) e **`COMBINED_18_PASS`** (`combined_rc=0`).

---

## 52. 21/11/2026 09:42 — Correção Definitiva de `D2DERR_PUSH_POP_UNBALANCED` / Memória Protegida no `OnRender` & Distinção Visual `Brick` vs `HeatGradient`

- **Arquivo Modificado:** [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py) (`CODE_FOOTPRINT_PRO` — Indicador `#17`).
- **Causas Raiz Identificadas (via Log NT8):**
  1. **Desaparecimento ao arrastar lateralmente (`D2DERR_PUSH_POP_UNBALANCED 0x88990016` + `Attempted to read or write protected memory`):**
     - `RenderTarget.PushAxisAlignedClip` / `PopAxisAlignedClip` no `RenderStatisticGrid` causava desbalanceamento de pilha D2D no Wrapper SharpDX do NinjaTrader 8 ao rolar lateralmente.
     - `GetDynBrush` chamava `.Dispose()` nos pincéis em cache no meio do frame ao atingir `Count > 240`, liberando ponteiros COM antes de o Direct2D executar o lote no `EndDraw()`.
  2. **`Brick` idêntico ao `HeatGradient` (`RenderSideCell`):** Ambos usavam rampa linear quase igual por volume (`0.24 + 0.56 * norm` vs `0.26 + 0.48 * norm`).
- **Correções Aplicadas (preservando integralmente o design 3D Glass):**
  - Removidas todas as chamadas a `PushAxisAlignedClip` / `PopAxisAlignedClip` no `RenderStatisticGrid`, substituídas por clamping numérico em C# (`Math.Max(rawCardX, cardsClipLeft)` e `Math.Min(..., cardsClipRight)`), mais guardas `float.IsNaN` / `float.IsInfinity` em `OnRender` e `RenderStatisticGrid`.
  - Quantizado o alpha de `GetDynBrush` em 20 níveis (`aStep * 12 + 15`) com fila `retiredDynBrushes` limpa via `FlushRetiredDynBrushes()` apenas antes de desenhar (`EnsureDxResources` / `DisposeDx`), eliminando qualquer `.Dispose()` no meio do frame.
  - **`RenderSideCell` distinto por formato:** `Brick` agora usa blocos uniformes sólidos (`0.56f * vaMult`); `HeatGradient` aplica contraste térmico perceptivo (`Math.Pow(norm, 1.35)` de `0.10` até `0.96` com destaque térmico nos níveis mais intensos); e `Histogram` desenha barras horizontais proporcionais com acento de `2px` na ponta.
- **Validação Pós-Edição:**
  - `verify_installer_cs.py`: `py_compile: OK`, `COMPETITOR_HITS=0`, `ALL 8 XML templates valid`, `16/18 PASS_RAW` (incluindo **`FootprintPro.cs`**) e **`COMBINED_18_PASS`** (`combined_rc=0`).

---

## 53. 21/11/2026 10:25 — Canal Central Simétrico para Candles + Candles Visíveis + Efeito de Iluminação Neon 3D + Personalização Completa de Cores e Fontes (`Clusters`, `Imbalance`, `Absorção` e `Statistic Grid`)

- **Arquivo Modificado:** [instalador_cloud2.0.py](file:///c:/Users/alanb/source/gex_profile_v7/gex_profile_v7/instalador_cloud2.0.py) (`CODE_FOOTPRINT_PRO`, `OnRender`, `RenderSideCell`, `RenderStatisticGrid`, `EnsureDxResources`, `DisposeDx`, `OpenStudioPopup`, `_build_nt8_chart_template`, `build_chart_templates`).
- **Melhorias Implementadas:**
  1. **Corredor Central Simétrico para o Candle (`CenterCandleGapPx = 11`, padrão `Range(2, 24)`):**
     - Corrigida a proporção assimétrica `55%/45%` entre colunas Left/Right: quando ambos os lados estão ativos (`CandleSpineMode != LeftSlimRail`), os blocos Left e Right são posicionados de forma simétrica em torno de **`cx`** (centro real do candlestick no NinjaTrader 8), abrindo um canal central limpo (`[cx - colGap*0.5 .. cx + colGap*0.5]`) com encolhimento proporcional em zoom afastado e ajuste automático de `CenterMicroWick`, `ShowBarVpoc`, `Absorption` e alinhamento de badges (`badgeCx = cx`).
     - No **Template #08** (`_build_nt8_chart_template`), candles nativos atualizados de opacidade apagada `#36...` para esmeralda/coral nítidos (**`#E810B981`**, **`#E8F43F5E`**, borda `#D0CBD5E1`, `candle_width=2.1`) para se destacarem perfeitamente dentro do canal entre clusters.
  2. **Efeito Real de Iluminação Neon 3D (`ShowSpecularGloss` + `GlowIntensityPct = 125%`, `Range(0, 200)`):**
     - **Halos Externos Multi-Camada:** Células quentes, Value Area, **Imbalances**, **Absorção**, **Bar VPOC** e cards ativos do grid agora projetam brilho externo em duas camadas (`5.0px` halo suave + `2.5px` aura intensa), núcleo interno iluminado em células ativas, domo especular (`dxGlassTopGrad` intensificado), filete superior cristalino (`dxGlassRimHighlight`) e fita LED cromática retroiluminada na base inferior de cada bloco e de cada cápsula/legenda do `Statistic Grid`.
  3. **Customização Completa de Fontes & Cores (Clusters, Imbalance, Absorção, Badges e Grid):**
     - **Tamanhos de números e textos:** `LeftFontSize` (`8..26`), `RightFontSize` (`8..26`), **`BadgeFontSize`** (`8..18`, padrão `10`, controla `▲IMB`/`▼IMB`, `ABS`, `UA`, `EXH`, `TRAP`, `Ratio`), `StatFontSize` (`8..24`, padrão `12`) e **`StatLegendFontSize`** (`8..20`, padrão `11`, tamanho dos nomes na legenda do grid), com fallback `dxFontLeftMid`/`dxFontLeftCompact`, `dxFontRightMid`/`dxFontRightCompact` e `dxFontStatCompact` independentes por coluna.
     - **Cores independentes:** Além de `ColValuesText` (texto normal dos clusters), `ColAskText` (Imbalance compra / `▲IMB`) e `ColBidText` (Imbalance venda / `▼IMB`), adicionadas propriedades XML + DX: **`ColAbsText`** (`#67E8F9`, números em nível de absorção & badge `ABS`), **`ColStatText`** (`#F8FAFC`, números base do grid), **`ColStatPosText`** (`#6EE7B7`, positivos no grid), **`ColStatNegText`** (`#FCA5A5`, negativos no grid), **`ColStatLegendText`** (`#F1F5F9`, texto dos rótulos da legenda) e **`ColStatCardBg`** (`#0E1625`, preenchimento das cápsulas do grid).
     - **`FootprintPro Studio` (`Width = 665`):** Tab 1 expõe `Gap(px)` e `Glow%`; Tab 2 e Tab 3 expõem `TxtPx`/`BadgePx`, `NumPx`, `LegPx` e toggles `Buy`/`Sell`/`Trades`; Tab 4 (**`Color Studio`**) remodelada em **2 colunas com 20 seletores `#HEX`** + **paleta rápida clicável de 30 cores** em cada quadrado de cor.
- **Validação Pós-Edição:**
  - `verify_installer_cs.py`: `py_compile: OK`, `COMPETITOR_HITS=0`, `ALL 8 XML templates valid`, `16/18 PASS_RAW` (incluindo **`FootprintPro.cs`**) e **`COMBINED_18_PASS`** (`combined_rc=0`).







