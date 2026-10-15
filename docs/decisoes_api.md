# API de consulta: decisões (15/10/2026)

Atende ao §9 do enunciado (endpoints de entidades, avaliação mais recente, histórico e critérios). Código: `api/app.py`. Teste: `api/teste_api.py`.

## 1. Endpoints

| Endpoint | Retorna |
|---|---|
| `GET /entidades` | Entidades ativas, com score, faixa (e se é provisória), cobertura e essenciais pendentes da avaliação mais recente |
| `GET /entidades/{id}` | Cadastro da entidade, critérios aplicáveis ao tipo dela e score mais recente |
| `GET /entidades/{id}/criterios` | Todos os critérios do checklist do protótipo, com `aplicavel` (para o tipo da entidade) e o status na avaliação mais recente |
| `GET /entidades/{id}/avaliacao` | Avaliação mais recente: cada critério com status, nota, método (regra, API ou LLM), justificativa, URL avaliada e evidências (trecho mascarado, caminho do arquivo, hash, data da coleta); e o score |
| `GET /entidades/{id}/historico` | Score, faixa, versão do código e status de cada critério por execução; lista de mudanças entre execuções seguidas (de, para, melhorou ou piorou, em qual execução e data) |
| `GET /criterios` | Critérios avaliados, com categoria, descrição, fundamentação, tipo de verificação, classificação e peso no score |
| `GET /execucoes` | Execuções oficiais avaliadas (id, data, versão do código) |

Documentação interativa gerada automaticamente em `/docs` (Swagger), com teste de cada endpoint pelo navegador.

## 2. Decisões

| Decisão | Escolha | Alternativa considerada | Por quê |
|---|---|---|---|
| Framework | FastAPI | Flask | Documentação interativa automática em `/docs`: quem avalia testa os endpoints sem ler o código. Validação de parâmetros e respostas em JSON sem código adicional |
| Acesso ao banco | SQLite aberto em modo somente leitura | API que também dispara coleta | Separação de responsabilidades: coleta e avaliação são processos em lote (minutos), a consulta é imediata. A API não altera nada e não pode corromper o histórico |
| Execuções expostas | Só as oficiais: completas, concluídas, para todas as entidades e já avaliadas | Todas as execuções | Testes parciais (ex.: só o cadastro do Rio) não representam a situação da entidade e confundiriam o histórico |
| "Melhorou" e "piorou" | Ordem Não atende < Parcial < Atende. Mudança envolvendo Inconclusivo ou Indisponível sai como "sem comparação" | Comparar o score | O §7 pergunta quais itens foram corrigidos e quando: a resposta é por critério. Sem veredito não permite dizer que houve melhora ou piora |
| Versão do código no histórico | Cada mudança informa se as duas execuções usaram a mesma versão do código | Omitir | A validação mostrou mudanças de resultado causadas pelo sistema, não pelo portal (Caxias 15.4 entre as execuções 19 e 25). O campo evita atribuir ao portal uma mudança do coletor |
| Banco usado | `GATE_BANCO`, se definido; senão `dados/gate.db`; senão a amostra pública `amostra/gate.db` | Exigir coleta antes de abrir | Quem clona o repositório vê os resultados reais sem 30 min de coleta e sem chave do LLM. A amostra tem CPF mascarado, caminhos relativos e nenhum arquivo bruto (`db/exportar_amostra.py`); `GET /execucoes` informa qual banco está em uso |
| Arquivos de evidência | Não servidos pela API: só caminho, hash e trecho mascarado | Endpoint de download | Páginas e prints de despesa contêm nome e CPF de credores pessoa física. O trecho gravado já é mascarado; o arquivo bruto, não |

## 3. Uso

```
pip install fastapi uvicorn httpx
uvicorn api.app:app --reload
```

Abrir `http://127.0.0.1:8000/docs`. Banco padrão: `dados/gate.db` (outro caminho: variável `GATE_BANCO`). Teste sem servidor: `python -m api.teste_api`.

## 4. Limitações e evolução para escala (§17)

| Protótipo | Em escala (5.000 portais) |
|---|---|
| SQLite, um arquivo local | PostgreSQL, com a mesma modelagem |
| Sem autenticação | Autenticação e perfis de acesso (o histórico pode instruir procedimentos) |
| Listas sem paginação | Paginação e filtros (município, faixa, critério, período) |
| Cálculo do histórico a cada chamada | Tabela de mudanças gravada no fim de cada avaliação |
