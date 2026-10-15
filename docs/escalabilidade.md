# Escalabilidade: de 5 para 5.000 portais (§17)

Ponto de partida: o que foi medido no protótipo. Projeções para 5.000 portais são estimativas de ordem de grandeza, a confirmar com um piloto maior.

## 1. Números medidos no protótipo (5 prefeituras, 6 critérios)

| Medida | Valor | Fonte |
|---|---|---|
| Duração de uma execução completa (coleta das 4 etapas) | 18,9 a 19,1 min, sequencial | Execuções 19 e 25 |
| Duração média por entidade | ~4 min | Idem, dividido por 5 |
| Artefatos por execução (HTML, prints, JSON, PDF, imagens) | ~190 | Idem |
| Chamadas ao LLM por execução (só 15.4) | 1 avaliação por entidade + 1 transcrição por imagem; 8 na execução 25 | `respostas_llm` |
| Tokens de entrada do LLM por execução | ~118 mil (Rio, com 5 PDFs de lei, é a maior parte) | `regras.auditar_15_4` |
| Banco de 3 execuções avaliadas (sem arquivos brutos) | ~0,5 MB | `amostra/gate.db` |
| Cadastro mínimo de uma entidade nova | 5 campos (id, nome, município, tipo, site oficial) | `config/entidades.yaml` |
| Descoberta sem cadastro de URLs | 13 de 15 alvos corretos | `docs/decisoes_coletor.md` |

## 2. O que já escala no desenho atual

| Decisão do protótipo | Por que escala |
|---|---|
| Descoberta a partir do site oficial | Entidade nova não exige mapear URLs à mão; o cadastro de URLs é só reserva |
| Adaptador por fornecedor, não por município | Plataformas como GeoSiap, Betha e Modernização atendem vários municípios com a mesma estrutura: um adaptador cobre todos os clientes. Levantamento necessário antes de escalar: quais fornecedores atendem os municípios do RJ e quantos municípios cada um cobre |
| Coleta separada da avaliação | Regra nova é reaplicada sobre o que já foi coletado, sem acessar os 5.000 portais de novo |
| Respostas do LLM guardadas por hash da entrada | Página que não mudou não gera nova chamada; o custo do LLM acompanha a taxa de mudança dos portais, não o número de execuções |
| Inconclusivo em vez de chute | Em escala, layouts desconhecidos são inevitáveis; viram fila de revisão humana, não falsos Não atende |
| Ocorrências gravadas por tentativa | Base para monitorar falhas por fornecedor e por domínio |

## 3. Projeção e gargalos

| Recurso | Protótipo | 5.000 portais (estimativa) | Como resolver |
|---|---|---|---|
| Tempo de coleta | ~4 min por entidade, uma por vez | ~330 h por ciclo se sequencial | Paralelismo por entidade: com 50 navegadores simultâneos, ~7 h por ciclo completo, viável diariamente |
| Frequência | Tudo a cada execução | Desnecessário | Frequência por critério: 4.6 diário; 12.1 após cada prazo quadrimestral da LRF; 1.2, 15.4 e 16.2 semanal |
| Armazenamento de artefatos | Pasta local | ~1 milhão de arquivos por ciclo diário completo | Armazenamento de objetos com deduplicação por hash (página igual à anterior não é gravada de novo) e política de retenção |
| Banco | SQLite | Escrita concorrente de dezenas de workers | PostgreSQL com a mesma modelagem |
| LLM | 1 chamada por entidade | Proporcional às páginas que mudaram | Cache já existente; processamento em lote da API para execuções agendadas; LLM só nos critérios semânticos |
| Carga nos portais | Uma visita por vez, identidade própria | Risco de sobrecarregar portais pequenos | Limite de requisições por domínio, horários de menor uso, User-Agent identificado (já adotado) |

## 4. Arquitetura sugerida para produção

```
agendador (frequência por critério)
   │
   ▼
fila de tarefas (uma tarefa = entidade × etapa)
   │
   ▼
workers em contêiner (Playwright + adaptadores), com limite por domínio
   │                 │
   ▼                 ▼
armazenamento     PostgreSQL (execuções, artefatos, avaliações, evidências, scores, ocorrências)
de objetos              │
(arquivos com hash)     ▼
                  avaliação (regras + LLM com cache) ── API ── dashboard
                        │
                        ▼
                  fila de revisão humana (Inconclusivos e amostra aleatória para validação contínua)
```

## 5. Riscos em escala e mitigação

| Risco | Mitigação |
|---|---|
| Mudança de layout de um fornecedor derruba muitos municípios de uma vez | Alarme por taxa de Inconclusivo por fornecedor (a tabela `ocorrencias` já identifica fornecedor e tipo de erro) |
| Qualidade sem gabarito para 5.000 entidades | Validação contínua por amostragem: revisão humana mensal de uma amostra aleatória de células, com as métricas de `regras/validar.py` (concordância nas conclusivas, taxa sem veredito, falso Não atende) |
| Resultado mudar por mudança do sistema, não do portal | Versão do código em cada execução e reavaliação das coletas antigas com o código novo antes de comparar (`docs/validacao.md`, seção 4) |
| Captcha e bloqueio de robôs | Não contornar: registrar como ocorrência; quando houver API pública do fornecedor, preferir a API |
| Dados pessoais em páginas de despesa | Mascaramento de CPF nas evidências (já adotado), acesso aos arquivos brutos restrito |
