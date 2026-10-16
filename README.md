# Avaliação automática de portais da transparência municipais

Protótipo para o GATE/MPRJ: coleta, avalia e acompanha no tempo a conformidade de portais da transparência municipais com critérios do checklist do PNTP. Escopo do protótipo: 5 prefeituras do RJ (Japeri, Duque de Caxias, Itaboraí, Cachoeiras de Macacu e Rio de Janeiro) e 6 critérios (1.2, 4.1, 4.6, 12.1, 15.4 e 16.2).

## Como funciona

```
cadastro (config/entidades.yaml: site oficial de cada entidade)
   │
   ▼
coletor ── descoberta do portal e das páginas ── API do fornecedor (se houver adaptador)
   │       páginas do cadastro (reserva) ── anexos do e-SIC (PDF e imagem)
   ▼
banco SQLite + arquivos (HTML, print, JSON, PDF, com hash)
   │
   ▼
regras (1.2, 4.1, 4.6, 12.1, 16.2) + LLM com citação conferida (15.4)
   │
   ▼
avaliações com evidência ── score (pesos e faixas alinhados ao PNTP) ── histórico por execução
   │
   ▼
API (FastAPI, somente leitura) ── dashboard (Streamlit)
```

Cada critério recebe Atende, Parcial, Não atende, Inconclusivo (o sistema não conseguiu ler; fica fora do score) ou Indisponível (site fora do ar). Não atende exige prova: página certa carregada e informação ausente.

## Instalação

Python 3.13 no Windows (PowerShell) ou Linux.

```
python -m venv .venv
.venv\Scripts\Activate.ps1          (Linux: source .venv/bin/activate)
pip install -r requirements.txt
playwright install chromium
```

Chave da API da Anthropic, só para o critério 15.4: copiar `.env.exemplo` para `.env` e preencher `ANTHROPIC_API_KEY`. O `.env` não vai para o Git. Sem chave, o 15.4 sai Inconclusivo, a menos que a resposta do LLM para a mesma coleta já esteja guardada no banco.

## Ver os resultados sem coletar

O repositório traz uma amostra pública do banco (`amostra/gate.db`) com as execuções oficiais avaliadas: avaliações, evidências (trechos com CPF mascarado), scores e respostas do LLM, sem os arquivos brutos. Sem `dados/gate.db`, a API e o dashboard usam a amostra automaticamente:

```
streamlit run dashboard/app.py
uvicorn api.app:app --reload
python -m regras.validar --dados amostra --execucoes 16 19 25 27
```

A amostra é gerada por `python db/exportar_amostra.py`, que mascara o CPF de novo em todo texto, troca caminhos locais por caminhos relativos e se recusa a gravar se ainda encontrar algo com formato de CPF.

## Uso

| Objetivo | Comando | Tempo |
|---|---|---|
| Execução completa: coleta das 5 entidades, regras, LLM e score | `python -m coletor.executar` | ~20 a 30 min |
| Só coleta | `python -m coletor.executar --sem-avaliar` | ~20 min |
| Reavaliar uma coleta já feita (regra nova, sem acessar portal) | `python -m regras.avaliar --execucao N` | ~1 a 4 min |
| Validação contra o gabarito e os selos do PNTP | `python -m regras.validar --execucoes 16 19 25 27 --gravar-confianca` | segundos |
| Conferência humana das respostas do LLM | `python -m regras.auditar_15_4 --execucao N` | segundos |
| Testes das regras e do score | `python -m regras.teste_regras` | segundos |
| API (documentação interativa em http://127.0.0.1:8000/docs) | `uvicorn api.app:app --reload` | |
| Teste da API sem servidor | `python -m api.teste_api` | segundos |
| Dashboard (http://localhost:8501) | `streamlit run dashboard/app.py` | |

Os dados de uma coleta própria ficam em `dados/` (banco `gate.db` e arquivos de cada execução), fora do Git: páginas de despesa contêm nome e CPF de credores. Todo trecho gravado como evidência tem o CPF mascarado.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `coletor/` | Navegador (Playwright), descoberta, adaptadores de fornecedor, cadastro, anexos, banco e o comando único `executar` |
| `regras/` | Regra de cada critério, LLM do 15.4, avaliação, score, validação, auditoria e testes |
| `api/` | API de consulta |
| `dashboard/` | Dashboard |
| `config/` | Entidades, critérios, checklist original, gabarito manual, parâmetros do score e referências externas |
| `db/` | Esquema do banco e consultas de exemplo |
| `docs/` | Decisões técnicas, explorações e validação |

## Documentação

| Documento | Assunto |
|---|---|
| `docs/documentacao_tecnica.md` | **Documento principal**: os 11 tópicos do §14, uso de IA (§15), escolha dos critérios (§13) e escala (§17), com links para os detalhes |
| `docs/gate_descobertas.md` | Exploração manual dos portais, gabarito e desafios encontrados |
| `docs/decisoes_coletor.md` | Coleta: navegador, descoberta, fornecedores, cadastro, anexos, limitações |
| `docs/decisoes_regras.md` | Regras de cada critério, LLM do 15.4 e resultados por execução |
| `docs/decisoes_score.md` | Metodologia do score, decisões e problemas da média simples |
| `docs/validacao.md` | Validação contra a referência interna e externa |
| `docs/decisoes_api.md` | API |
| `docs/decisoes_dashboard.md` | Dashboard |
| `docs/escalabilidade.md` | Projeção para 5.000 portais, gargalos e arquitetura de produção |

## Resultado de referência (execução 27, de 16/10/2026)

| Entidade | Score | Faixa |
|---|---|---|
| Duque de Caxias | 100,0 | Diamante |
| Rio de Janeiro | 100,0 | Diamante |
| Itaboraí | 92,9 | Ouro |
| Cachoeiras de Macacu | 81,6 | Elevado (RGF atrasado) |
| Japeri | 69,8 | Intermediário (RGF e dados de despesa atrasados) |

Validação nas 4 execuções oficiais (13 a 16/10): 98% de concordância com o gabarito nas células conclusivas (100 de 102), 3% sem veredito, nenhum Não atende falso. Por grau de confiança: alta 100% (80 de 80), média 91% (20 de 22) (`docs/validacao.md`).
