# Trilha gratuita para programacao quant

Trilha em ingles, com universidades, orgaos, bolsas de opcoes e projetos de codigo dos Estados Unidos. **Coursera nao esta incluido.** O material listado e gratuito para estudar; isso nao significa que todos oferecam certificado gratuito. Em geral, MIT OCW e documentacao nao emitem certificado.

## Sequencia sugerida

### 1. Programacao e ferramentas

1. [CS50's Introduction to Programming with Python (CS50P)](https://cs50.harvard.edu/python/) — Python, depuracao, bibliotecas, arquivos e testes. O conteudo e gratuito pelo CS50 OpenCourseWare; certificado verificado opcional pelo edX nao e gratuito.
2. [freeCodeCamp: Scientific Computing with Python](https://www.freecodecamp.org/learn/scientific-computing-with-python/) — exercicios e projetos para praticar Python. Curso e certificacao anunciados como gratuitos.
3. [Tutorial oficial de Python](https://docs.python.org/3/tutorial/) — referencia para consolidar a linguagem e a biblioteca padrao.
4. [pandas: guia de entrada e saida de dados](https://pandas.pydata.org/docs/user_guide/io.html) — importar e exportar CSV, JSON, Parquet e outros formatos comuns em pesquisa.
5. [DuckDB: documentacao](https://duckdb.org/docs/2.0/) — SQL analitico local para consultar conjuntos de dados.

### 2. Matematica e estatistica

6. [MIT OCW 18.01SC: Single Variable Calculus](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/) — derivadas, integrais e series; fundamentos para otimizacao e modelos continuos. Materiais gratuitos, sem certificado.
7. [MIT OCW 18.06SC: Linear Algebra](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/) — vetores, matrizes e sistemas lineares usados em risco e modelos quantitativos.
8. [MIT OCW 18.05: Introduction to Probability and Statistics](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/) — distribuicoes, inferencia, testes, intervalos de confianca e regressao.

### 3. Financas, derivativos, opcoes e futuros

9. [MIT OCW 15.401: Finance Theory I](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/) — precificacao de ativos, renda fixa, diversificacao, risco e introducao a derivativos/opcoes.
10. [MIT OCW 15.450: Analytics of Finance](https://ocw.mit.edu/courses/15-450-analytics-of-finance-fall-2010/) — curso quantitativo avancado: econometria financeira, inferencia, otimizacao dinamica, Monte Carlo e calculo estocastico; aplica a derivativos, risco e trading proprietario.
11. [Cboe Options Institute](https://www.cboe.com/optionsinstitute/) — portal educacional gratuito de conceitos de opcoes, estrategias e risco.
12. [OCC Options Industry Council: Getting Started with Options](https://www.optionseducation.org/optionsoverview/getting-started-with-options) — mecanica e riscos de opcoes listadas.
13. [CME: Introduction to Futures](https://www.cmegroup.com/education/courses/introduction-to-futures.html) — fundamentos de futuros pela bolsa. A pagina da CME nao foi confirmada durante a verificacao; confira disponibilidade e eventual exigencia de conta no site.
14. [CFTC Learning Resources](https://www.cftc.gov/learnandprotect/learningresources) — materiais do regulador dos EUA, incluindo fundamentos e riscos do mercado de futuros.
15. [CME Micro E-mini futures](https://www.cmegroup.com/markets/equities/micro-e-mini-futures.html) — consulte especificacoes vigentes de cada micro (multiplicador, tick, vencimentos e demais condicoes). A pagina de produto da CME nao foi confirmada durante a verificacao.

### 4. Dados, testes e pesquisa

16. [FRED API](https://fred.stlouisfed.org/docs/api/fred/) — series macroeconomicas e informacao sobre revisoes/vintages. Gratuita com chave registrada; **nao** e feed de cotacoes intraday.
17. [Alpha Vantage API](https://www.alphavantage.co/documentation/) — API para experimentar com dados financeiros. O fornecedor informa limite gratuito de requisicoes para varios servicos; confira cobertura, limite e termos atuais antes de depender dela.
18. [pytest](https://docs.pytest.org/en/stable/) — testes automatizados para transformacoes de dados, calculos, casos extremos e regressoes.
19. [QuantConnect LEAN](https://www.quantconnect.com/docs/v2/lean-engine) e [LEAN Getting Started](https://www.quantconnect.com/docs/v2/lean-engine/getting-started) — engine open source para estudar arquitetura e backtests. O codigo e gratuito, mas dados nao sao automaticamente gratuitos; o guia atual do LEAN CLI indica que o uso exige uma organizacao com plano pago.

## Como aplicar ao seu projeto

1. Aprenda Python e testes antes de alterar o scraper ou os calculos.
2. Reproduza os calculos em dados pequenos e verificaveis: GEX, Max Pain, VWAP, IV e movimento esperado.
3. Compare cada resultado com um calculo independente e registre unidades, multiplicadores, horario, fuso, vencimento e fonte.
4. Adicione testes para dados ausentes, IV assumida, ausencia de cruzamento, mudanca de vencimento, feriados e contratos micro.
5. So depois estude backtests. Inclua vies de antecipacao, sobrevivencia, revisao de dados, rollover de futuros, spread, slippage, taxas e risco por contrato.

## Realidade sobre dados gratuitos

E possivel aprender e validar a logica com dados publicos e amostras. Porem, uma cadeia historica completa de opcoes de futuros com cotacoes por strike, IV observada, open interest e timestamps confiaveis costuma ser limitada, atrasada ou paga. Os cursos e APIs acima nao substituem uma fonte licenciada, nem garantem dados suficientes para recalcular GEX em tempo real. Verifique termos de uso e qualidade antes de usar qualquer feed em operacao.
