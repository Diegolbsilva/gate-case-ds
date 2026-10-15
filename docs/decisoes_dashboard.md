# Dashboard: decisões (15/10/2026)

Atende ao §10 do enunciado (visão geral, visão por entidade e evolução). Código: `dashboard/app.py`.

## 1. Visões

| Visão | Conteúdo |
|---|---|
| Visão geral | Indicadores (entidades, maior e menor score, entidades com essencial pendente); tabela de score, faixa, cobertura, essenciais pendentes e média simples; barras de score; matriz entidade × critério com o status de cada célula; descrição, fundamentação, classificação e peso de cada critério |
| Por entidade | Score, faixa, cobertura e média simples; avisos de essencial pendente e de essencial não verificado (faixa provisória); cada critério com status, nota, justificativa, método, página avaliada e evidências (trecho mascarado, fonte, arquivo, hash, data) |
| Evolução | Score por data de coleta (uma linha por entidade); tabela "o que mudou e quando" (critério, de, para, melhorou ou piorou, e se as duas execuções usaram a mesma versão do código); tabela de scores por execução |

## 2. Decisões

| Decisão | Escolha | Alternativa considerada | Por quê |
|---|---|---|---|
| Ferramenta | Streamlit | Página HTML consumindo a API | Python, um arquivo, um comando para subir; tabelas, gráficos e filtros prontos. HTML exigiria JavaScript à parte para um protótipo de 5 entidades |
| Fonte dos dados | As mesmas funções da API (`api/app.py`) | Consultas próprias ao banco | Uma única fonte das consultas: o dashboard mostra exatamente o que a API devolve, sem duas versões da mesma regra de "execução oficial" ou de "melhorou/piorou" |
| Status | Símbolo + texto + cor de estado clara (✔ Atende, ◐ Parcial, ✖ Não atende, ? Inconclusivo, ⚠ Indisponível) | Só cor | Leitura por daltônicos e em impressão; a cor nunca carrega o significado sozinha |
| Cor das entidades | Fixa por entidade, em ordem, a mesma em todos os gráficos | Cor por posição no ranking | A cor identifica a entidade; mudar a ordem não repinta as linhas |
| Faixa provisória | Marcada com `*` e explicada na barra lateral e na visão por entidade | Esconder | A faixa não é rebaixada por limitação do método, mas o leitor precisa saber que um essencial não foi verificado |
| Aviso de versão do código | Na visão Evolução e em cada mudança | Omitir | Mudança entre execuções com códigos diferentes pode ser efeito do sistema (validação: Caxias 15.4 entre as execuções 19 e 25) |
| Arquivos de evidência | Só nome, hash e trecho mascarado | Mostrar o print ou o HTML | Prints e páginas de despesa contêm nome e CPF de credores |

## 3. Uso

```
pip install streamlit
streamlit run dashboard/app.py
```

Abre no navegador em `http://localhost:8501`. Banco padrão: `dados/gate.db` (outro caminho: variável `GATE_BANCO`).
