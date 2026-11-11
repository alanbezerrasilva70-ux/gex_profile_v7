# Resumo das correcoes RTY, IV e integracoes

Data da verificacao: 11/11/2026

Este documento separa o que foi enviado ao GitHub do bot, o que ja existia no
clone do dashboard e o que ficou apenas na copia de trabalho em Downloads.

## 1. Bot GEX e GitHub Actions

### `gex_profile_v7_cloud.py`

- A rota Futures de RTY do Barchart foi substituida por opcoes do ETF IWM como
  proxy, pois a rota Futures testada retornava pagina inexistente.
- Os strikes de IWM sao escalados para a faixa de preco do RTY antes da
  exportacao. O resultado e um proxy, nao uma cadeia de opcoes Futures de RTY.
- A coleta dos vencimentos do ETF foi adicionada para gerar os arquivos
  macro, 1DTE, 2DTE e 7DTE do RTY.
- Os CSVs passam a identificar a fonte `IWM proxy for RTY`.
- O CSV de alvos exporta o valor da base de IV usada e informa `IV base
  assumida`. Nao foi usada IV de SPY/IWM como se fosse IV das opcoes Futures.
- Correcao posterior para NG: na rota semanal `IN2X26`, a API do Barchart
  retorna strikes em escala 10x (por exemplo, 33.0 enquanto o spot e cerca de
  3.36). Quando nenhum strike NG semanal passa pelo filtro normal, o parser
  tenta a escala 0.1 e registra essa normalizacao no log. As demais rotas
  continuam usando a escala original.
- O run GitHub Actions #254 confirmou que o commit `f1ffe96` estava sendo
  executado. Ele chegou a NG, processou 0DTE e 1DTE, mas falhou em 2DTE porque
  os strikes retornados para `IN2X26` estavam 10x acima da escala do spot.

### `test_gex_profile_v7_cloud.py`

- Foram adicionados testes para descobrir vencimentos ETF, processar os
  vencimentos DTE do proxy RTY e verificar a escala dos strikes e os metadados
  dos CSVs, alem de uma regressao para a escala de strikes NG 10x.
- O teste de compatibilidade dos campos antigos foi atualizado para conferir
  os indices originais do CSV depois da inclusao da coluna de fonte.
- Validacao deste follow-up: 23 testes passaram e `py_compile` passou,
  incluindo o caso NG com strikes retornados em escala 10x.

### `.github/workflows/main.yml`

- Nao foi alterado neste envio.
- O workflow ja executa os testes antes do scraper, roda por agendamento e
  tambem permite `workflow_dispatch`.
- O commit `f1ffe96` foi enviado para `main` no repositorio do bot:
  `alanbezerrasilva70-ux/gex_profile_v7`, e o run #254 usou esse SHA.
- A normalizacao NG descrita acima e um follow-up ao #254. E necessario
  confirmar um novo run desse follow-up e o upload correspondente ao Dropbox.

## 2. Dashboard, clone correto e Vercel

O clone do dashboard existe em:

`C:\Users\alanb\source\gex-dashboard\gex-dashboard`

Esse clone estava limpo na verificacao, na branch `master`, com remote
`alanbezerrasilva70-ux/gex-dashboard`. Ele ja contem o trabalho anterior de
2DTE (historico inclui `18d6323`), portanto a publicacao anterior do suporte
2DTE nao foi perdida.

Porem, as alteracoes mais recentes em `page.tsx` e `route.ts` foram feitas na
copia:

`C:\Users\alanb\Downloads\gex_profile_v7-main\gex-dashboard-master`

Elas **nao foram enviadas via Git** ao clone do dashboard nem ha confirmacao de
que chegaram a Vercel. Os arquivos nas duas pastas diferem. Na versao do clone,
a rota API ainda escolhe sempre o arquivo `_2DTE.csv`; a copia em Downloads
aceita `1DTE`, `2DTE` e `7DTE`, e a pagina envia o DTE escolhido para a API
quando precisa baixar esses arquivos do RTY. A copia tambem inclui a exibicao
da fonte de IV e da fonte proxy.

### `app/page.tsx`

- Na copia de Downloads, os botoes/consultas DTE foram ajustados para buscar os
  arquivos correspondentes e para solicitar os DTE do RTY via API Dropbox.
- A tela exibe a classificacao da IV e a fonte proxy quando os CSVs trazem
  esses metadados.
- Essa versao ainda precisa ser integrada ao clone acima para afetar o site.

### `app/api/gamma-data/route.ts`

- Na copia de Downloads, a rota aceita arquivos `1DTE`, `2DTE` e `7DTE` do
  Dropbox, em vez de somente `2DTE`.
- A rota continua usando as variaveis de ambiente `DBX_APP_KEY`, `DBX_SECRET`
  e `DBX_REFRESH`.
- Essa versao ainda precisa ser integrada ao clone acima para afetar o site.

### `README.md`

- A copia em Downloads documenta os tres DTE e a origem IWM do proxy RTY.
- Essa alteracao de documentacao tambem nao foi enviada ao clone.

### O que fazer na Vercel

- Nao e necessario alterar variaveis da Vercel se as tres variaveis `DBX_*`
  acima ja estao configuradas no projeto. Se nao estiverem, a API nao conseguira
  autenticar no Dropbox.
- Para publicar as mudancas de pagina/API, elas precisam estar no clone correto
  e ser commitadas/enviadas para a branch de producao conectada a Vercel
  (o clone local observado usa `master`). Depois, confirmar que o deploy ficou
  pronto e testar os filtros 1DTE, 2DTE e 7DTE, inclusive RTY.
- Nao foi feito deploy da copia em Downloads. O comportamento de deploy
  automatico depende de o projeto Vercel estar conectado a esse repositorio e
  com deploy automatico habilitado; isso nao foi confirmado pelas fontes locais.

## 3. NinjaTrader

A pasta encontrada para os indicadores instalados foi:

`C:\Users\alanb\Documents\NinjaTrader 8\bin\Custom\Indicators`

### `instalador_cloud2.0.py`

- O instalador foi modificado localmente para o `NiveisGammaPro` mostrar a
  fonte proxy e a natureza de base assumida da IV, alem de ler os metadados dos
  CSVs e os niveis DTE.
- Esse arquivo Python **nao deve ser copiado para a pasta de indicadores**.
  Quando executado, ele grava cinco indicadores na pasta `Custom\Indicators`
  e remove/substitui os arquivos de mesmo nome. Portanto, faca backup antes de
  executa-lo e confirme que deseja atualizar o conjunto todo.
- O `NiveisGammaPro.cs` instalado ja tinha mapeamento RTY e linhas 1DTE/2DTE/
  7DTE, mas nao apresentou os novos campos de fonte verificados no instalador.

### `VolatilidadeImplicitaPro.cs`

- A versao local foi alterada para reconhecer RTY/YM/NG, ler a IV exportada no
  CSV e mostrar a fonte/indicacao de IV assumida.
- O arquivo instalado no NinjaTrader e diferente da versao local. Para usar
  essa melhoria, substitua o `.cs` instalado pela versao revisada e compile
  no NinjaTrader (F5). Isso so muda o indicador exibido no NinjaTrader; nao e
  requisito para o bot enviar dados ao Dropbox.

### `FluentliExpectedMove.cs`

- A versao local agora avisa que o VIX mede volatilidade do S&P 500 e e apenas
  uma proxy quando aplicado a outros ativos.
- O `.cs` instalado tambem e diferente da versao local. Para ver o aviso,
  substitua o arquivo instalado e compile no NinjaTrader. Isso nao muda o
  calculo GEX nem a IV que o bot grava.

### `MoneyRiskProAvançado.py`

- Nao foi alterado. E um instalador independente, fora do caminho ativo
  Cloud/Dropbox descrito aqui; nao precisa ser enviado para o NinjaTrader por
  causa dessas mudancas.

## 4. IV e estado de validacao

- A IV individual por contrato nao foi validada para a cadeia Futures usada
  pelo bot. Para os ativos afetados, o GEX continua usando uma base assumida,
  explicitamente identificada nos dados.
- A IV de SPY/IWM nao foi copiada para ES/RTY Futures como se fosse equivalente.
- Os testes Python passaram. O lint e o build que passaram foram executados na
  copia do dashboard em Downloads, nao no clone que a Vercel usa.
- A publicacao do dashboard e a compilacao dos indicadores NinjaTrader sao
  etapas separadas: o push do bot nao publica o dashboard nem instala
  indicadores no computador.
