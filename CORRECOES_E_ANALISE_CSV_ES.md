# Correcoes do bot GEX e conferencia dos CSVs ES

## Alteracoes no bot

- `DP` agora seleciona o strike com maior volume combinado de calls e puts,
  tanto por vencimento quanto no agregado macro.
- `DPM` exporta a quantidade de volume reportada em vez de um valor monetario
  estimado por contratos x preco x multiplicador.
- `FlowSig` descreve apenas qual volume foi maior (`CALLS > PUTS`,
  `PUTS > CALLS` ou igualdade); `FlowVal` exporta o saldo numerico em unidades
  de volume/modelo. Esses campos nao indicam agressao compradora/vendedora.
- `GexSig` agora informa `POSITIVE`, `NEGATIVE` ou `NEUTRAL`, sem converter o
  sinal matematico em uma afirmacao direcional de mercado.
- Um GEX Flip inexistente e escrito como campo vazio em
  `NiveisGamma_<ativo>.csv`, em vez de `0.00`.
- As posicoes e a quantidade de colunas dos CSVs foram mantidas para preservar
  a leitura por NinjaTrader e dashboard.

## Conferencia dos perfis ES fornecidos

| Perfil | Linhas | Spot aproximado | DP | Volume Call+Put no DP | Max Pain recalculado | Soma de `ng` |
|---|---:|---:|---:|---:|---:|---:|
| Macro | 274 | 7614.50 | 7600 | 17,216 | 7550 | -$160.973M |
| 1DTE | 308 | 7614.50 | 6590 | 1,065 | 7525 | +$11.759M |
| 2DTE | 326 | 7614.75 | 6600 | 4,969 | 7600 | +$1.556M |
| 7DTE | 260 | 7615.00 | 6700 | 2,254 | 7600 | +$1.559M |

Os quatro perfis tinham strikes unicos, ordenados e valores numericos finitos.
A soma de `ng` e o Max Pain recalculado coincidem com os respectivos arquivos
de resumo. O DP antigo tambem coincide com o strike de maior volume combinado;
nos vencimentos 1/2/7DTE, porem, os strikes selecionados ficam cerca de 12% a
13.5% abaixo do spot. Isso nao indica erro de parser por si so, mas evidencia
que volume maximo isolado nao e necessariamente um nivel util perto do preco,
uma ordem institucional ou um block trade.

Essa verificacao comprova coerencia interna entre os CSVs fornecidos, nao a
correcao/completude da resposta do Barchart nem a validade das hipoteses do
modelo. O bot continua usando uma IV-base anualizada presumida, nao IV
observada por contrato.

## Validacao

Os testes unitarios cobrem selecao de volume combinado, unidades exportadas,
neutralidade semantica e flip ausente. A validacao local nao substitui uma
execucao do workflow nem a conferencia dos arquivos novos no Dropbox.
