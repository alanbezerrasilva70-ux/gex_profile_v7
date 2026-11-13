# Relatório de Refatoração, Auditoria Quantitativa e Histórico Cronológico (V9)

Este documento segue o padrão oficial definido em [regras.md](file:///C:/Users/alanb/source/gex_profile_v7/gex_profile_v7/regras.md), registrando **Data (`dd/MM/aaaa`)**, **Horário (`HH:mm`)**, **Arquivo**, **Commit** e **Descrição Técnica** de todas as alterações realizadas nos repositórios `gex_profile_v7` e `gex-dashboard`.

---

## 1. Registro Cronológico de Modificações por Data e Horário

### A. Modificações de HOJE — `13/11/2026`

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
| **`13/11/2026 15:24`** | `gex-dashboard/app/page.tsx` | Atualizado às `15:24` | **1.** Criado `focusedChartData` para remover automaticamente as caudas distantes onde `|ng| ≈ 0` (strikes de `±15%` sem gamma no `0DTE` que esmagavam a curva no centro do gráfico), preservando `Call Wall`, `Put Wall`, `GEX Flip` e paredes `0DTE` com folga lateral.<br>**2.** Atualizado o rótulo de `GEX FLIP (estimado)` para `GEX FLIP (Zero Gamma)` / `GEX Flip` e destacado `IV real por strike (Barchart)` em verde esmeralda no cabeçalho. |

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
