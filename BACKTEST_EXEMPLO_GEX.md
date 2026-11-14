# Exemplo de backtest dos níveis GEX

## Resposta curta

Os CSVs disponíveis neste workspace são fotografias de um único momento, não
um histórico de sinais acompanhado dos preços que vieram depois. O robô também
grava os mesmos nomes de arquivo a cada execução, substituindo os dados
anteriores. Portanto, ainda não há amostra suficiente para afirmar que o flip,
as paredes ou o Max Pain acertam uma porcentagem específica das vezes.

O exemplo numérico abaixo é **fictício**. Ele mostra como medir o resultado
quando houver snapshots arquivados e preços posteriores; não é resultado do
robô nem promessa de desempenho.

## Exemplo de medição

Suponha que, em 20 pregões, sejam registrados antes do início da janela de
avaliação 50 encontros independentes do preço com uma zona GEX. Defina antes
do teste que um encontro será considerado "respeitado" se, depois de tocar a
zona, o preço se afastar pelo menos 0,25% antes de atravessá-la por mais de
0,10%. Os limites são apenas um exemplo: escolha-os antes do teste e não os
ajuste olhando os resultados.

| Resultado hipotético | Quantidade |
|---|---:|
| Encontros que respeitaram a zona conforme a regra | 31 |
| Encontros que romperam a zona conforme a regra | 19 |
| Total de encontros avaliados | 50 |
| Taxa de respeito | 31 / 50 = **62%** |

Mesmo nesse exemplo inventado, 62% não prova uma vantagem. Com 50 observações,
a incerteza estatística ainda é grande (intervalo de Wilson de 95% de
aproximadamente 48% a 74%). Além disso, vários encontros no mesmo pregão
podem estar correlacionados e não equivaler a 50 oportunidades independentes.

### O que significa "acertar"

"Respeitar" uma linha não é o mesmo que prever a direção do fechamento, nem
significa que uma operação teria sido lucrativa. Para cada nível, registre
uma regra objetiva, por exemplo:

1. **Sinal:** congelar os níveis em um horário fixo, antes da janela testada.
2. **Toque:** o preço entra numa faixa predefinida ao redor do nível.
3. **Respeito/rejeição:** após o toque, anda a distância mínima definida para
   longe do nível antes de invalidá-lo.
4. **Rompimento:** cruza o limite de invalidação antes de atingir o alvo.
5. **Ambos na mesma barra:** usar dados de menor intervalo para saber a ordem;
   se não houver esses dados, marcar como ambíguo, não escolher o resultado
   mais favorável.

Uma tabela de eventos poderia ter estas colunas:

```text
data_hora_sinal,símbolo,vencimento,nível,tipo_nível,spot_no_sinal,
máxima_janela,mínima_janela,fechamento_janela,alvo_pct,invalidação_pct,
resultado,MFE,MAE,custos
```

MFE é a maior excursão favorável após o sinal; MAE é a maior excursão
desfavorável. Para avaliar operação, calcule também o resultado líquido após
spread, comissão e slippage. Uma taxa de acerto isolada pode esconder perdas
grandes e ganhos pequenos.

## Como ler os conceitos

### OI (Open Interest)

OI é a quantidade de contratos que continuam abertos. Não informa se os
dealers estão comprados ou vendidos, quem abriu a posição, nem se ela pertence
a dealers. O OI é insumo do modelo, não uma leitura direta de posicionamento
institucional.

### GEX positivo, GEX negativo e GEX líquido

Gamma mede como o delta de uma opção muda quando o preço do ativo muda. GEX
estima a exposição a esse efeito usando gamma, OI, multiplicador e preço.
Neste robô, a convenção do modelo atribui contribuição positiva às calls e
negativa às puts:

```text
GEX líquido por strike = GEX de calls - GEX de puts
GEX total = soma do GEX líquido de todos os strikes considerados
```

Assim, "GEX positivo" ou "GEX negativo" descreve o sinal calculado sob essa
hipótese. Não prova que o mercado ou os dealers estejam realmente long ou
short gamma. O sinal e a interpretação também dependem da convenção do modelo.

### Call Wall e Put Wall

- **Call Wall:** strike com maior contribuição calculada de GEX das calls.
- **Put Wall:** strike com maior contribuição calculada de GEX das puts.

São concentrações estimadas pelo modelo a partir do OI, não suportes ou
resistências garantidos. Uma parede pode ser atravessada, mudar quando o OI é
atualizado ou refletir posições de participantes com lados opostos.

### Flip e Zero Gamma

Em muitos usos, **GEX Flip** e **Zero Gamma** são nomes para o preço em que o
GEX agregado estimado muda de sinal. Neste código atualizado, o robô recalcula
o GEX total do modelo para preços hipotéticos e procura um cruzamento de sinal
na faixa analisada; por isso o CSV e os gráficos o chamam de flip estimado.

Isso é diferente de escolher o strike individual cujo GEX por strike está mais
perto de zero. Essa era a definição antiga usada pelo robô e não encontrava o
cruzamento do GEX agregado. O flip atual também continua dependente do OI, da
IV assumida e da convenção calls-positivas/puts-negativas; não é um nível
observado diretamente.

### Max Pain

Max Pain é, neste cálculo, o strike de liquidação candidato que minimiza o
payout agregado estimado das calls e puts em aberto no vencimento. É uma
medida derivada do OI e dos strikes. Não significa que o preço será atraído
para esse strike nem é, por si só, um alvo de trade.

## IV fixa por ativo versus IV por contrato

- **IV fixa por ativo:** o robô usa uma hipótese de volatilidade para todas as
  opções daquele ativo e vencimento. É simples, mas não representa o smile/skew
  entre strikes nem a diferença individual entre calls e puts.
- **IV por contrato:** cada opção teria sua própria volatilidade implícita,
  associada corretamente ao strike, vencimento e tipo (call/put). Pode
  representar melhor o smile/skew, mas só é uma melhoria se os valores forem
  dados reais, atuais e associados à opção correta.

No momento da verificação, a página Barchart aberta não forneceu IV por
contrato na tabela de opções; o valor geral exibido estava marcado no HTML
como mockup. Por isso, não deve ser tratado como dado medido. O backtest atual
deve rotular a IV usada como hipótese. Um teste comparando IV fixa com IV por
contrato só será válido quando houver uma fonte confiável para a segunda opção
e quando ambos os métodos forem avaliados nos mesmos períodos, sem olhar o
futuro.

## O que falta para medir uma taxa real

1. Arquivar cada snapshot com data/hora, símbolo e vencimento, sem sobrescrever
   o anterior.
2. Guardar os dados de preço do mesmo período com resolução adequada para
   identificar toque, rejeição, rompimento e a ordem dos eventos.
3. Definir regras de sucesso, alvo, invalidação e janela antes de calcular os
   resultados.
4. Separar sessões de desenvolvimento das sessões de validação; não ajustar
   regras usando o período que será apresentado como teste final.
5. Apresentar quantidade de observações, taxa de respeito, intervalo de
   confiança, resultado líquido, MFE/MAE e resultados separados por tipo de
   nível e regime.

Um perfil CSV isolado com strikes e OI, sem snapshots datados e sem a sequência
posterior de preços, não permite calcular essa porcentagem. Também não se deve
usar sem validação um perfil histórico que contenha linhas desalinhadas ou
valores de strike misturados com contagens.
