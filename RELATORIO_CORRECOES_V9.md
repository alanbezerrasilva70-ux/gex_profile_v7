# Relatório de Refatoração e Auditoria Quantitativa (V9)

Este documento resume as **9 correções críticas** solicitadas, as **anomalias adicionais** corrigidas durante a auditoria e o passo a passo para enviar (`git push`) as alterações dos dois repositórios para o GitHub.

---

## 1. Arquivos Alterados

### Repositório 1: `gex_profile_v7` (`C:\Users\alanb\source\gex_profile_v7\gex_profile_v7`)
1. **`gex_profile_v7_cloud.py`** — Motor quantitativo de coleta, cálculo Black-Scholes, agregação multi-ativo, Time Travel DTE e sincronização com o Dropbox.
2. **`test_gex_profile_v7_cloud.py`** — Suíte de testes unitários atualizada e expandida (31 testes cobrindo todas as correções).
3. **`.github/workflows/main.yml`** — Workflow do GitHub Actions com `timeout-minutes: 35`.
4. **`instalador_cloud2.0.py`** — Instalador dos 5 indicadores NinjaTrader 8 (`NiveisEstruturaPro`, `NiveisGammaPro`, `MoneyRiskPro`, `DailyOHLCPro`, `GlobexRangePro`).

### Repositório 2: `gex-dashboard` (`C:\Users\alanb\source\gex-dashboard\gex-dashboard`)
1. **`app/page.tsx`** — Dashboard Next.js/Recharts (Curva GEX + Heatmap, eixo X contínuo, ReferenceLines completas e tratamento de `0DTE`/`1DTE`/`2DTE`/`7DTE`).
2. **`app/api/gamma-data/route.ts`** — Rota de API do Dropbox com suporte a `ALL`, `0DTE` (com fallback automático para `1DTE`), `1DTE`, `2DTE` e `7DTE`, além de cache em memória do token OAuth.

---

## 2. Detalhamento das 9 Anomalias Corrigidas + Correções Extras

| # | Anomalia | Causa Raiz | Correção Aplicada |
|---|---|---|---|
| **1** | **Call Wall e Put Wall no mesmo strike** (`7600`/`7600` no ES, `27600` no NQ, `85` no CL) | Uso de `cgex.idxmax()` e `pgex.idxmax()` brutos em strikes ATM com alto Open Interest simultâneo (*straddles*). | Criada `select_walls(df)`: **Call Wall** = maior exposição líquida positiva (`df[df["ng"] > 0]["ng"].idxmax()`) e **Put Wall** = maior exposição líquida negativa (`df[df["ng"] < 0]["ng"].idxmin()`), garantindo `CW != PW` tanto em `process()` quanto em `process_group()`. |
| **2** | **Datas duplicadas entre `1DTE` e `2DTE`** (quinta-feira selecionando sexta nos dois) | `select_expiration_for_dte` somava dias corridos (`+2` caía no sábado) e escolhia o vencimento mais próximo (sexta, repetindo `1DTE`). | Criada `_dte_target_date(as_of, dte)` contando **pregões (dias úteis)** para DTEs curtos (`< 5`) e filtrando apenas vencimentos futuros ainda não selecionados (`exclude=used_expirations`). |
| **3** | **Botão `0DTE` fantasma** (repetia os dados de `ALL`) | `gex_profile_v7_cloud.py` não salvava `_0DTE.csv` e `page.tsx` não tinha branch para `dteFilter === "0DTE"`. | `process_dte(0, "0DTE", "_0DTE")` agora salva `GammaProfile_*_0DTE.csv`, `NiveisGamma_*_0DTE.csv` e `AlvosVolatilidade_*_0DTE.csv`. `route.ts` e `page.tsx` buscam `_0DTE` com fallback automático para `1DTE` quando o ativo não possui vencimento no próprio dia. |
| **4** | **Linhas tracejadas (`Call/Put Wall` e `GEX Flip`) sumindo na Curva GEX e em `1DTE`/`2DTE`/`7DTE`** | Falta de `<ReferenceLine>` para `niveis.cw` e `niveis.pw` no `<AreaChart>` e `<XAxis>` categórico que descartava valores decimais como `7612.84`. | Adicionadas `<ReferenceLine>` para `niveis.cw` (verde) e `niveis.pw` (vermelho) no `<AreaChart>`, `<ReferenceLine>` para `niveis.zg` no `<ComposedChart>`, e configurado `<XAxis dataKey="strike" type="number" domain={['dataMin', 'dataMax']} />` com `ifOverflow="extendDomain"`. |
| **5** | **Gráficos esmagados em `NG`, `CL`, `ZB`, `ZN` e `GC` no modo `ALL`** | Arredondamento fixo `(strike / 5).round() * 5` colapsava strikes de ativos de preço baixo (ex.: `NG` em `3.20–3.50` virava tudo `5.0`). | `STRIKE_ROUNDING = {"ES": 5, "NQ": 5, "YM": 5, "RTY": 5}` aplica arredondamento de 5 pontos apenas aos índices de pontuação alta, preservando a grade natural de `CL`, `GC`, `ZB`, `ZN` e `NG`. |
| **6** | **Escala errada do `RTY` nos DTEs** (`240` do `IWM` em vez de `2400`) | `process_dte` não aplicava `strike_mult` (`10`) nem `gex_correcao` (`5`) nas fatias `0DTE`, `1DTE`, `2DTE` e `7DTE`. | Criada `apply_proxy_scaling()` e `compute_levels()`, aplicadas tanto no agregado quanto em todas as fatias DTE de ativos com proxy (ajustando strikes, exposições e volumes). |
| **7** | **Falhas no GitHub Actions e erro após 16h NY** | `if T_years <= 0: raise ValueError` após as 16h NY, falta de `try/except` por ativo/DTE e `timeout-minutes: 18` curto demais. | Adicionado piso `MIN_TIME_TO_EXPIRY_SECONDS = 300.0`, avanço automático de pregão após 16h NY (`effective_session_date`), timeouts de página no Selenium (`45s`), blocos `try/except` isolados por ativo/DTE/arquivo e `timeout-minutes: 35` em `main.yml`. |
| **8** | **Unificação de rotas DTE no Dashboard** | `RTY` tinha links vazios para `1DTE`/`7DTE` e faltava fallback entre links estáticos e `/api/gamma-data`. | `route.ts` e `page.tsx` agora suportam `ALL`, `0DTE`, `1DTE`, `2DTE` e `7DTE` com `cache: "no-store"`, cache do token OAuth no servidor e fallback automático entre links diretos e API. |
| **9** | **Histograma do NinjaTrader inflado em ~760.000x** | `NiveisEstruturaPro` multiplicava `n.NetGamma * 100 * Close[0]` quando `ng` no CSV já estava em dólares (`mult * spot`). | Alterado para `string txt = FormatVal(n.NetGamma);` em `instalador_cloud2.0.py`. |
| **Extra** | **Cotação fracionária de `ZN`/`ZB` e IV base de `GC`/`ZB`/`ZN`** | `110-085` no `ZN` era lido como `110 + 85/32 = 112.66` em vez de `110 + 8.5/32 = 110.265625`; `ZB`/`ZN` usavam IV de 14%. | Criada `parse_treasury_price()` para meias-frações de 1/32 e calibradas `IV_BASE_POR_ATIVO` para `GC` (`18%`), `ZB` (`9%`) e `ZN` (`6%`). |

---

## 3. Auditoria Completa do `instalador_cloud2.0.py` (NinjaTrader 8)

Foram auditados os 5 indicadores C# gerados pelo instalador:

1. **`NiveisEstruturaPro` (Histograma Gamma por Strike)**:
   - Lê `NiveisGamma_{ATIVO}.csv` (para rotular `CW`, `PW` e `ZG`) e `GammaProfile_{ATIVO}.csv` (`strike`, `ng`).
   - **Corrigido**: `FormatVal(n.NetGamma)` agora exibe diretamente o valor em dólares (`$M` / `$B`) sem multiplicar novamente por `100 * Close[0]`.
2. **`NiveisGammaPro` (Linhas Horizontais + Painel `🛡️ QUANT ENGINE V8`)**:
   - **Leitura dos CSVs**:
     - De `NiveisGamma_{ATIVO}.csv`: `callWall` (`p[0]`), `putWall` (`p[1]`), `zeroGamma` (`p[2]`), `posGex` (`p[3]`), `negGex` (`p[4]`), `cwMoney` (`p[5]`), `pwMoney` (`p[6]`), `cw0DTE` (`p[7]`), `pw0DTE` (`p[8]`), `dashSource` (`p[9]`). Adicionado fallback automático para `NiveisGamma_{ATIVO}_0DTE.csv` caso `cw0DTE`/`pw0DTE` venham zerados.
     - De `NiveisGamma_{ATIVO}_{1DTE|2DTE|7DTE}.csv`: `cw1DTE`/`pw1DTE`/`zg1DTE`, `cw2DTE`/`pw2DTE`/`zg2DTE`, `cw7DTE`/`pw7DTE`/`zg7DTE`.
     - De `AlvosVolatilidade_{ATIVO}.csv`: `maxPain` (`p[0]`), `optionVolumeStrike` / Block Order (`p[1]`), `dashRatio` (`p[2]`), `dashIv` (`p[3]`), `dashNetFlow` (`p[4]`), `dashNetGex` (`p[5]`), `optionVolume` (`p[6]`), `dashFlowVal` (`p[7]`), `dashGexVal` (`p[8]`), `dashAlvoUp` (`p[9]`), `dashAlvoDown` (`p[10]`), `dashRegime` (`p[11]`).
   - **Painel `🛡️ QUANT ENGINE V8` atualizado**:
     - Exibe `REGIME`, `CALL/PUT VOLUME BALANCE`, `NET GEX (estimado)`, `POS GEX (CW)` e `NEG GEX (PW)` com valores financeiros, `MAX PAIN`, `BLOCK/MAX VOL` (strike de maior volume total de contratos + quantidade), `GEX FLIP estimado`, `RATIO` com classificação dinâmica (`[PUT DOMINANT]` quando `> 1.20`, `[CALL DOMINANT]` quando `< 0.80`, `[NEUTRAL]` entre `0.80` e `1.20`, substituindo o texto `[NEUTRAL]` que antes era fixo), `IV BASE`, `ALVOS VOL` (`AlvoDown <-> AlvoUp`) e `FONTE`.
3. **`MoneyRiskPro` (Gestão de Risco V76)**:
   - Lê `IV`, `Regime` e `IVSource` de `AlvosVolatilidade_{ATIVO}.csv`, calcula o *Daily Expected Move* (`Close[0] * (currentIV / 1600.0)`) e dimensiona o stop e o lote por `RiscoMax / (ticksCalculados * valorPorTick)`.

---

## 4. Como Enviar as Alterações para o GitHub (`git push`)

Execute os comandos abaixo no terminal do VS Code (**PowerShell**):

### Passo 1 — Subir o projeto `gex_profile_v7` (branch `main`)
```powershell
cd C:\Users\alanb\source\gex_profile_v7\gex_profile_v7
git status
git add gex_profile_v7_cloud.py test_gex_profile_v7_cloud.py .github/workflows/main.yml instalador_cloud2.0.py RELATORIO_CORRECOES_V9.md
git commit -m "fix(quant-v9): net GEX walls, business-day DTEs, 0DTE export, RTY DTE scaling and CI resilience"
git push origin main
```

### Passo 2 — Subir o projeto `gex-dashboard` (branch `master`)
```powershell
cd C:\Users\alanb\source\gex-dashboard\gex-dashboard
git status
git add app/page.tsx app/api/gamma-data/route.ts
git commit -m "fix(dashboard): add 0DTE support, continuous strike XAxis and Call/Put Wall lines on GEX curve"
git push origin master
```
