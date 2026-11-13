# Regras de Governança, Auditoria e Rastreabilidade de Alterações (`regras.md`)

Este arquivo define o protocolo obrigatório que qualquer assistente de IA (Antigravity, Claude, Copilot, Gemini) deve seguir ao criar, auditar ou modificar arquivos nos projetos **`gex_profile_v7`** e **`gex-dashboard`**.

---

## 1. Registro Obrigatório de Data e Horário (`dd/MM/aaaa HH:mm`)

1. **Rastreabilidade Cronológica Completa:**
   - Toda criação ou modificação de arquivo deve ser registrada no relatório mestre ([RELATORIO_CORRECOES_V9.md](file:///C:/Users/alanb/source/gex_profile_v7/gex_profile_v7/RELATORIO_CORRECOES_V9.md)) informando explicitamente a **Data (`dd/MM/aaaa`)**, o **Horário (`HH:mm`)**, o **Caminho do Arquivo**, o **Commit SHA** (quando aplicável) e o **Resumo Técnico da Alteração**.
2. **Separação Estrita por Dia e Rodada:**
   - Nunca misture alterações de dias diferentes na mesma tabela sem separar claramente o que já foi commitado/enviado em sessões anteriores do que foi alterado na sessão atual.
3. **Verificação Antes do `git commit` / `git push`:**
   - Antes de sugerir comandos de Git, verifique `git status` e `git log` para não incluir pastas de ambiente virtual (`.venv/`), configurações de editor (`.vscode/`), caches (`__pycache__/`) ou binários soltos (`msedgedriver.exe`, `Driver_Notes/`).

---

## 2. Regras de Formatação para a Biblioteca de E-books (`gex-dashboard/public/ebooks`)

O leitor da Biblioteca ([app/biblioteca/page.tsx](file:///C:/Users/alanb/source/gex-dashboard/gex-dashboard/app/biblioteca/page.tsx)) utiliza um conversor leve (`markdownToHtml`) e leitor de voz (`AudioReader`). Ao criar ou editar qualquer arquivo `teoria.md` ou `pratica.md` dentro de `public/ebooks/`:

1. **Estrutura de Títulos:** Utilize apenas `# `, `## ` e `### ` no início da linha.
2. **Parágrafos em Linha Única:** Cada parágrafo deve estar contido em **uma única linha** (sem quebras de linha manuais no meio da frase), separado por uma linha em branco.
3. **Listas com Hífen (`- `):** Utilize exclusivamente `- ` no início da linha para listas, mantendo cada item em uma única linha (não utilize `* ` nem sub-listas indentadas).
4. **Destaques e Fórmulas:** Utilize `**negrito**` para ênfase e `` `código inline` `` para fórmulas, variáveis e emblemas. **Não utilize** blocos LaTeX (`$$...$$`), tabelas Markdown (`|...|`), blocos de código com três crases (```` ``` ````), citações (`> `) ou linhas divisórias (`---`), pois esses elementos aparecem como texto cru no leitor da Biblioteca.
5. **Imagens e Diagramas SVG:** Salve os diagramas na pasta `public/ebooks/<indicador>/imagens/` e insira-os em linha própria usando o formato `![Legenda descritiva da imagem](/ebooks/<indicador>/imagens/arquivo.svg)`.

---

## 3. Regras de Integridade do Pacote NinjaTrader 8 e Coletor Cloud

1. **Instalador Único (`instalador_cloud2.0.py`):**
   - Todos os 7 indicadores (`NiveisEstruturaPro`, `NiveisGammaPro`, `MoneyRiskPro`, `DailyOHLCPro`, `GlobexRangePro`, `VolatilidadeImplicitaPro` e `FluentliExpectedMove`) ficam embutidos diretamente dentro de `instalador_cloud2.0.py`.
   - Ao embutir código C# que contenha três aspas duplas seguidas (`@"""...""`), utilize delimitador Python `r''' ... '''` e valide sempre com `python -m py_compile instalador_cloud2.0.py`.
2. **Compatibilidade com GitHub Actions (`gex_profile_v7_cloud.py`):**
   - Nunca altere `iniciar_driver()` para navegadores locais fixos (como Edge); mantenha sempre `webdriver.Chrome(options=options)` em modo `--headless=new` e valide a suíte de testes (`test_gex_profile_v7_cloud.py`) antes do commit.
