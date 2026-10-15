# Escalabilidade: de 5 para 5.000 portais (§8 e §17)

O §8 pede a discussão de 11 pontos (seção 6 deste documento). O §17 pergunta se a solução continuaria confiável, explicável e economicamente viável avaliando 5.000 portais todos os meses.

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
| Tempo de coleta | ~4 min por entidade, uma por vez | ~330 h por ciclo completo se sequencial | Em ciclo mensal (§17), 330 h cabem no mês com poucos workers: 10 navegadores simultâneos fazem o ciclo em ~33 h. Com 50, ~7 h, o que permite ciclos mais frequentes para os critérios que mudam rápido |
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

## 6. Os 11 pontos do §8

| Ponto do §8 | Como o protótipo trata | Em escala |
|---|---|---|
| Execução de múltiplas análises | Uma execução cobre todas as entidades, com id, data e versão do código | Uma tarefa por entidade × etapa, executadas em paralelo |
| Processamento assíncrono | Etapas em processos separados (`coletor/executar.py`): a falha de uma etapa não derruba as outras | Workers independentes consumindo uma fila |
| Filas | Não implementadas (5 entidades, sequencial) | Fila de tarefas com reentrega em caso de falha do worker |
| Controle de erros | 3 tentativas com intervalo crescente; cada falha gravada em `ocorrencias` com tipo (timeout, erro do servidor, bloqueio, captcha, layout inesperado) | Mesma tabela, com alarme por fornecedor e por tipo de erro |
| Sites indisponíveis | Status Indisponível (fora do ar após as tentativas), distinto de Inconclusivo e de Não atende; nova tentativa na execução seguinte | Reagendamento automático da entidade, sem esperar o próximo ciclo |
| Páginas muito grandes | Espera por estabilização com limite (até 180 s com indicador de carregamento); PDFs até 15 MB e 5 por entidade; texto enviado ao LLM limitado a 60 mil caracteres por fonte | Limites por tipo de fonte, com registro do corte no detalhe (já gravado em `avisos`) |
| Limites de requisições | Uma visita por vez, identidade própria no User-Agent, nenhum contorno de captcha | Limite de requisições por domínio e horários de menor uso |
| Conteúdo dinâmico | Navegador real (Playwright), espera por estabilização, cliques para portais que não mudam de endereço, molduras (iframes) lidas | Igual; adaptador por fornecedor quando houver API |
| Diferentes tecnologias de portal | Descoberta genérica por texto clicável + adaptadores de fornecedor (GeoSiap, Modernização/Webrun) | Novos adaptadores conforme o levantamento de fornecedores |
| Necessidade de reprocessamento | Coleta separada da avaliação: `regras.avaliar --execucao N` reaplica regras novas sobre coletas antigas sem acessar o portal; respostas do LLM guardadas | Reprocessamento em lote após cada mudança de regra, com a versão da regra registrada |
| Custos computacionais | ~19 min por execução de 5 entidades; LLM só no critério semântico, com cache por hash da entrada; ~118 mil tokens de entrada por execução | Cache do LLM, deduplicação de arquivos por hash e frequência por critério reduzem o custo por ciclo |
