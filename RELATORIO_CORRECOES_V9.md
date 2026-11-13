# Relatório de Refatoração e Auditoria Quantitativa (V9)

Este documento separa claramente o que foi **corrigido hoje (13/11/2026)** do que já havia sido **corrigido e enviado ontem (12/11/2026)**, além de detalhar o status de cada arquivo dos dois repositórios e do pacote NinjaTrader 8.

---

## 1. Resumo Executivo: O Que Foi Feito Hoje (13/11/2026) vs. Ontem (12/11/2026)

### A. Corrigido HOJE — `13/11/2026` (Pendente de `git commit` / `git push`)

| Arquivo | Status Hoje (`13/11/2026`) | O Que Foi Feito Hoje |
|---|---|---|
| **`gex_profile_v7/gex_profile_v7_cloud.py`** | **Modificado hoje** | **1.** Inclusão de `Monthly Options` (3ª sexta-feira ou data real da página para commodities) e `EOM Options` (último dia útil) na extração de vencimentos de futuros (`extract_futures_expiration_options` / `parse_futures_expiration_options`), além de teto de **21 dias corridos** (`MAX_SHORT_DTE_CALENDAR_DAYS = 21`) com fallback automático para `7DTE`.<br>**2.** Extração de **IV real e gregas por strike** (`volatility,delta,gamma,theta,vega`) da API interna do Barchart (`/proxies/core-api/v1/quotes/get`), inversão de Black-Scholes (`implied_vol_from_gamma`) quando o feed de futuros fornece `raw.gamma`, cálculo de `cgex`, `pgex` e `find_gex_flip` com *Volatility Skew* real por strike e exportação de `IVSource = "IV real por strike (Barchart)"`.<br>**3.** Injeção explícita de `api.expirationDate = expirationToken` nas rotas de ETF (`RTY` via `IWM`) quando a URL contém `?expiration=...` ou `?expirationDate=...`, garantindo que `0DTE`, `1DTE`, `2DTE` e `7DTE` carreguem cadeias distintas. |
| **`gex_profile_v7/test_gex_profile_v7_cloud.py`** | **Modificado hoje** | Expandido de 31 para **49 testes unitários** (todos aprovados: `Ran 49 tests in 10.319s — OK`), cobrindo OPEX mensal/EOM, limite de 21 dias, IV/Gamma reais por strike, filtro de ruído numérico de gamma e injeção de `expirationDate` no `IWM`/`RTY`. |
| **`gex_profile_v7/VolatilidadeImplicitaPro.cs`** | **Auditado e corrigido hoje** | **1.** Corrigida piscada/sumiço das 6 bandas (`±1 SD`, `±2 SD`, `±3 SD`) durante a escrita do Dropbox (preserva o último `ivVal` válido).<br>**2.** Adicionado suporte a todos os micro futuros (`M2K` → `RTY`, `MYM` → `YM`, `MCL` → `CL`, `MGC` → `GC`, `MNG`/`QG` → `NG`).<br>**3.** `ForceRefresh()` restrito a `State == State.Realtime`.<br>**4.** Preço exato exibido nos rótulos das bandas (`1 SD (+68%) [7645.25]`). |
| **`gex_profile_v7/FluentliExpectedMove.cs`** | **Auditado e corrigido hoje** | **1.** Corrigida condição de corrida assíncrona (`Task.Run`) que deixava `VixInterno = 0` nas barras históricas.<br>**2.** Integração automática com `AlvosVolatilidade_{ATIVO}.csv` do Dropbox para todos os 9 ativos (`ES`/`MES`, `NQ`/`MNQ`, `GC`/`MGC`, `CL`/`MCL`, `ZB`, `ZN`, `YM`/`MYM`, `RTY`/`M2K`, `NG`/`QG`).<br>**3.** Corrigida opacidade duplicada em `Draw.Rectangle` (`20% × 20% = 4%` deixava as nuvens quase invisíveis).<br>**4.** HUD reposicionado para `TextPosition.BottomLeft` para não sobrepor o `VolatilidadeImplicitaPro`. |
| **`gex_profile_v7/instalador_cloud2.0.py`** | **Modificado hoje** | **1.** Adicionado mapeamento dos micro futuros `M2K` → `RTY` e `QG` → `NG` nos indicadores `NiveisEstruturaPro`, `NiveisGammaPro` e `MoneyRiskPro`.<br>**2.** `NiveisGammaPro` agora lê a coluna `p[12]` (`dashIvSource`) de `AlvosVolatilidade_{ATIVO}.csv` para exibir no painel `🛡️ QUANT ENGINE V8` se a IV é `"IV REAL POR STRIKE (BARCHART)"` ou `"IV BASE ASSUMIDA"`.<br>**3.** O instalador agora detecta e instala automaticamente também `VolatilidadeImplicitaPro.cs` e `FluentliExpectedMove.cs` na pasta `NinjaTrader 8\bin\Custom\Indicators` (instalando os **7 indicadores** de uma só vez). |
| **`gex-dashboard/app/page.tsx`** | **Modificado hoje** | Em `fetchDataset`, priorizada a rota interna `buildApiUrl(dteFilter, dataset)` (`/api/gamma-data`) **antes** de `getStaticLink(dteFilter, dataset)` em todos os modos (`ALL`, `1DTE`, `7DTE`), eliminando atrasos de cache dos links estáticos do Dropbox. |

---

### B. Corrigido e Enviado ONTEM — `12/11/2026` (Já está no GitHub)

Estes arquivos já foram corrigidos e enviados ontem nos commits `2fa12e8` (`gex_profile_v7`) e `4eed2ae` (`gex-dashboard`) e **não precisam de novas alterações hoje**:

1. **`gex-dashboard/app/api/gamma-data/route.ts`** *(Commit `4eed2ae` de 12/11/2026 às 21:23)*:
   - Já recebeu ontem o suporte completo a `"ALL"`, `"0DTE"` (com fallback automático para `"1DTE"` quando o ativo não tem vencimento no dia), `"1DTE"`, `"2DTE"` e `"7DTE"`, além de cache em memória do token OAuth (`cachedAccessToken`) e cabeçalhos `Cache-Control: no-store` + `X-Resolved-DTE`. **Não precisa de nenhuma modificação adicional hoje.**
2. **`gex_profile_v7/.github/workflows/main.yml`** *(Commit `2fa12e8` de 12/11/2026 às 21:20)*:
   - Já recebeu ontem o ajuste `timeout-minutes: 35`. **Não precisa de nenhuma modificação adicional hoje.**
3. **As 9 Anomalias Base de Ontem** *(Commits `2fa12e8` e `4eed2ae`)*:
   - **Anomalia 1**: Call Wall (`ng > 0` máx.) e Put Wall (`ng < 0` mín.) por exposição líquida (`select_walls`), evitando `CW == PW` no mesmo strike ATM.
   - **Anomalia 2**: Seleção de `1DTE` e `2DTE` por dias úteis (`_dte_target_date`) sem duplicar sexta-feira quando executado na quinta-feira.
   - **Anomalia 3**: Geração e leitura dedicada dos arquivos `_0DTE.csv` (`GammaProfile_*_0DTE.csv`, `NiveisGamma_*_0DTE.csv`, `AlvosVolatilidade_*_0DTE.csv`).
   - **Anomalia 4**: `<ReferenceLine>` para Call Wall (`cw`), Put Wall (`pw`) e GEX Flip (`zg`) na Curva GEX e no Heatmap, com `<XAxis dataKey="strike" type="number" domain={['dataMin', 'dataMax']} />`.
   - **Anomalia 5**: Arredondamento `STRIKE_ROUNDING` restrito a `ES`, `NQ`, `YM`, `RTY`, preservando strikes naturais de `NG`, `CL`, `GC`, `ZB` e `ZN`.
   - **Anomalia 6**: Escala do proxy `RTY` (`IWM` com `strike_mult=10` e `gex_correcao=5`) aplicada em todas as fatias DTE (`apply_proxy_scaling`).
   - **Anomalia 7**: Piso de expiração (`MIN_TIME_TO_EXPIRY_SECONDS = 300.0`), avanço de pregão após 16h NY (`effective_session_date`) e isolamento de falhas por ativo/DTE (`RUN_ERRORS`).
   - **Anomalia 8**: Unificação das rotas DTE e links estáticos de fallback no dashboard.
   - **Anomalia 9**: Correção de `FormatVal(n.NetGamma)` sem `* 100 * Close[0]` no `NiveisEstruturaPro` dentro de `instalador_cloud2.0.py`.
   - **Extra (Ontem)**: Parser de cotações fracionárias de Treasuries (`parse_treasury_price` para `110-085` em `ZN`/`ZB`) e calibração de `IV_BASE_POR_ATIVO`.

---

## 2. Algum Outro Arquivo do Repositório Precisa de Correção?

Foi feita uma varredura completa em todos os demais arquivos das duas pastas:
- **`gex-dashboard/app/api/gamma-data/route.ts`**: **100% pronto** desde o commit de ontem (`4eed2ae`).
- **`gex_profile_v7/.github/workflows/main.yml`**: **100% pronto** desde o commit de ontem (`2fa12e8`).
- **`DAILYOLHC.PY`, `DeltaCumulativePro.py`, `vwap.py`**: São scripts avulsos antigos de indicadores técnicos de preço/volume (não leem CSVs do GEX nem usam Barchart/Dropbox). `DailyOHLCPro` e `GlobexRangePro` já estão embutidos dentro do `instalador_cloud2.0.py`. Não precisam de alteração.
- **`gex-dashboard/public/ebooks/gexcloudengine/pratica.md` e `teoria.md`**: Possuem edições locais suas nos e-books (podem ser commitadas junto ou separadamente no `gex-dashboard`, conforme sua preferência).

> [!IMPORTANT]
> **Lembrete para o NinjaTrader 8 na sua máquina local:**
> Como o `instalador_cloud2.0.py` grava os arquivos `.cs` dentro da pasta `NinjaTrader 8\bin\Custom\Indicators` do Windows, após o commit lembre-se de executar `python instalador_cloud2.0.py` e pressionar **F5** dentro de uma janela NinjaScript Editor no NinjaTrader 8 para recompilar os **7 indicadores** atualizados.

---

## 3. Comandos Exatos para Subir as Alterações de HOJE (`13/11/2026`)

### Passo 1 — Repositório `gex_profile_v7` (branch `main`)
```powershell
cd C:\Users\alanb\source\gex_profile_v7\gex_profile_v7
git add gex_profile_v7_cloud.py test_gex_profile_v7_cloud.py instalador_cloud2.0.py VolatilidadeImplicitaPro.cs FluentliExpectedMove.cs RELATORIO_CORRECOES_V9.md
git status
git commit -m "feat(quant-v9): real per-strike IV/Greeks skew, monthly/EOM OPEX, IWM DTE expiration injection and NT8 indicators"
git push origin main
```

### Passo 2 — Repositório `gex-dashboard` (branch `master`)
```powershell
cd C:\Users\alanb\source\gex-dashboard\gex-dashboard
git add app/page.tsx
git status
git commit -m "perf(dashboard): prioritize /api/gamma-data before static Dropbox links"
git push origin master
```
*(Opcional: se quiser subir também as suas edições nos e-books do dashboard, basta adicionar `public/ebooks/gexcloudengine/pratica.md public/ebooks/gexcloudengine/teoria.md` no `git add` do Passo 2).*
