# Documentação técnica: avaliação automática de portais da transparência municipais

Protótipo desenvolvido para o desafio técnico do GATE/MPRJ (Cientista de Dados). Repositório: https://github.com/Diegolbsilva/gate-case-ds. Instruções de instalação e execução: `README.md`.

Este documento responde aos 11 tópicos da documentação técnica pedidos no §14 do enunciado (entregáveis), às 8 perguntas do §15 (uso de IA) e à justificativa da escolha dos critérios do §13 (escopo mínimo). Cada seção resume as decisões e aponta para o documento de detalhe, onde estão as alternativas consideradas e os casos reais que motivaram cada escolha.

| Tópico do §14 | Seção |
|---|---|
| Problema identificado | 1 |
| Arquitetura proposta | 2 |
| Abordagem utilizada (inclui a escolha dos critérios, §13, e os desafios do §12) | 3 |
| Tecnologias escolhidas | 4 |
| Metodologia de avaliação (inclui evidências, §6, e grau de confiança, §4) | 5 |
| Metodologia de cálculo da pontuação | 6 |
| Tratamento de critérios não aplicáveis | 7 |
| Tratamento de erros | 8 |
| Estratégia de atualização | 9 |
| Uso de inteligência artificial (§15) | 10 |
| Limitações conhecidas | 11 |
| Possibilidades de evolução (inclui a pergunta central, §17) | 12 |

Escopo do protótipo: 5 prefeituras do RJ (Japeri, Duque de Caxias, Itaboraí, Cachoeiras de Macacu e Rio de Janeiro) e 6 critérios do checklist (1.2, 4.1, 4.6, 12.1, 15.4 e 16.2), com 4 execuções oficiais completas entre 13 e 16/10/2026.

## 1. Problema identificado

A avaliação de conformidade de um portal da transparência hoje depende de uma pessoa navegar pelo portal, localizar cada informação exigida pelo checklist e registrar o resultado. O enunciado pede que esse processo se torne automático, repetível, auditável e escalável.

A exploração manual dos 5 portais (09 e 10/10/2026, `docs/gate_descobertas.md`) mostrou que o problema técnico não é verificar uma informação, e sim **chegar até ela** de forma confiável em portais que não seguem nenhum padrão:

| Característica observada | Consequência para a solução |
|---|---|
| 5 prefeituras, 5 modelos de portal: fornecedor com API pública (GeoSiap, Japeri), fornecedor com API não divulgada (Modernização, Caxias), plataforma em nuvem compartilhada (Betha, Cachoeiras), sistema de fornecedor dentro de portal próprio (Supernova, Itaboraí) e desenvolvimento próprio com vários sistemas (Rio) | Código por município não escala. A solução precisa de um caminho genérico e de adaptadores por fornecedor |
| 3 dos 5 portais montam o conteúdo com JavaScript; menus sem link (blocos clicáveis do Angular, itens abertos por script); consultas que só mostram dados depois de "Pesquisar" | Navegador real, descoberta por texto clicável e não só por link |
| A mesma informação em formatos diferentes: tabela, API, PDF, infográfico em imagem | Extração roteada por tipo de fonte |
| Informação disponível, mas não localizada pelo sistema, é diferente de informação ausente | Status próprio para "não foi possível verificar" (Inconclusivo), separado de Não atende |
| Portais mudam: endereço novo ("transparencianovo" em Itaboraí), dados atualizados diariamente, relatórios quadrimestrais | Execuções periódicas, histórico e versão do código em cada execução |
| Contexto de fiscalização: um falso Não atende pode instruir um procedimento contra a entidade | Não atende só com prova da ausência; evidência verificável por humano em cada célula |

Formulação técnica adotada: para cada entidade e critério, produzir um status com evidência auditável e grau de confiança, separar a falha da entidade da limitação do sistema, agregar num score explicável e repetir o processo com histórico comparável.

## 2. Arquitetura proposta

```
cadastro (config/entidades.yaml: 5 campos por entidade, o site oficial basta)
   │
   ▼
COLETA (coletor/)  ── uma execução = 4 etapas em processos separados
   │   1. descoberta: do site oficial até o portal e as páginas de cada critério
   │   2. APIs: reconhece o fornecedor e coleta pela API quando há adaptador
   │   3. cadastro: URLs anotadas por critério (reserva) e caminhos de cliques
   │   4. anexos: PDFs e páginas de detalhe da seção do e-SIC
   ▼
artefatos (HTML após JavaScript, print, JSON, PDF, imagem), cada um com hash SHA-256
   │
   ▼
AVALIAÇÃO (regras/)  ── não acessa portal: lê só o que foi coletado
   │   regras determinísticas (1.2, 4.1, 4.6, 12.1, 16.2) + LLM com citação conferida (15.4)
   │   status + nota + grau de confiança + justificativa + evidências
   ▼
SCORE (regras/score.py)  ── pesos e faixas alinhados ao PNTP, cobertura explícita
   │
   ▼
banco SQLite (histórico por execução)  ──  API (FastAPI, somente leitura)  ──  dashboard (Streamlit)
```

| Princípio | Por quê |
|---|---|
| Coletar separado de avaliar | Uma regra nova é reaplicada sobre coletas antigas sem acessar os portais (`python -m regras.avaliar --execucao N`). Reprocessamento sem custo de rede e comparação justa entre execuções |
| Cada execução acrescenta, nada é sobrescrito | O histórico responde às perguntas do §7 (melhorou, piorou, o que foi corrigido e quando) |
| Versão do código (commit) gravada em cada execução | Separa "o portal mudou" de "o sistema mudou" |
| API e dashboard somente leitura | A consulta não altera nem corrompe o histórico |

**Modelagem de dados** (`db/schema.sql`):

| Tabela | Conteúdo |
|---|---|
| `entidades`, `entidade_urls` | Quem é avaliado (com tipo) e seus endereços, com período de validade |
| `criterios`, `criterio_aplicabilidade` | Itens do checklist com versão, categoria, fundamentação, tipo de verificação e tipos de entidade a que se aplicam |
| `execucoes` | Cada rodada: data, origem (manual ou agendada), versão do checklist e do código, status |
| `artefatos` | Tudo o que foi baixado, com caminho, hash, URL final e data |
| `descobertas` | Cada clique da descoberta: texto, nota, destino, se estava visível, se precisou rolar |
| `avaliacoes` | Resultado de um critério, para uma entidade, numa execução: status, nota, grau de confiança, método, justificativa, detalhe |
| `evidencias` | Provas de cada avaliação: trecho (CPF mascarado), arquivo, hash, URL, data |
| `scores` | Score, faixa, cobertura e médias de comparação por execução e entidade |
| `ocorrencias` | Erros e novas tentativas, com tipo (timeout, erro do servidor, bloqueio, captcha) |
| `respostas_llm` | Respostas do modelo guardadas por hash da entrada: cache e trilha de auditoria |

Detalhe: `docs/decisoes_coletor.md` (coleta) e `docs/decisoes_regras.md` (avaliação).

## 3. Abordagem utilizada

### 3.1 Combinação de técnicas

A abordagem é híbrida, como o §15 sugere ("dados + regras + automação + IA + validação + evidências"). Cada técnica entra onde é a mais barata, previsível e auditável para o problema:

| Técnica | Onde | Por quê |
|---|---|---|
| API do fornecedor | 4.1, 4.6 e 12.1 em Japeri e Caxias | Dado estruturado, sem depender da tela; contorna o reCAPTCHA das consultas de Caxias sem burlá-lo |
| Navegador automatizado | Todas as páginas | JavaScript, iframes, cliques em portais que não mudam de endereço |
| Descoberta por texto clicável com nota | Do site oficial ao portal e às páginas de cada critério | Cadastro mínimo por entidade; funciona em portal desconhecido. Cada clique é gravado com texto e nota (auditável) |
| Regras determinísticas | 1.2, 4.1, 4.6, 12.1, 16.2 | Critérios verificáveis por estrutura (cabeçalhos de tabela, datas, períodos, elementos); resultado reproduzível e explicável |
| LLM com citação conferida | 15.4 | Único critério que exige interpretação de texto livre (seção 10) |
| Validação contra referências | Todas | Gabarito manual e selos do PNTP (`docs/validacao.md`) |

**Caminho em cascata:** para cada critério, o sistema junta todas as fontes (API, páginas da descoberta, páginas do cadastro), aplica a regra a cada uma e fica com o melhor resultado. Uma página errada trazida pela descoberta não derruba o que a página certa mostra. Nenhuma fonte serviu: Inconclusivo, nunca Não atende.

### 3.2 Escolha dos critérios (§13)

O §13 recomenda um subconjunto que contemple diferentes níveis de complexidade e lista 6 tipos. Foi escolhido **um critério por tipo**, todos da matriz comum do checklist (6 de 66):

| Tipo pedido no §13 | Critério | Por que este |
|---|---|---|
| Existência simples de informação | 16.2 Opção de alto contraste | Elemento verificável no HTML; exige ler menus fechados e widgets de acessibilidade, não só o visível |
| Exige navegação | 1.2 Acesso ao portal visível na capa do site | Mede o caminho do cidadão: visibilidade, submenu, rolagem, número de cliques |
| Dados estruturados | 4.1 Número e valor de empenho, liquidação e pagamento | Tabelas em formatos diferentes (fase em coluna ou em linha) e APIs de fornecedor |
| Envolve documentos | 12.1 Publica o Relatório de Gestão Fiscal | Documentos periódicos: além de existir, o período mais recente precisa estar em dia com o prazo da LRF |
| Atualização das informações | 4.6 Informações atualizadas da despesa | Exige uma referência temporal objetiva (Decreto 10.540/2020: até o 1º dia útil seguinte ao registro) |
| Interpretação semântica | 15.4 Prazos, autoridades e procedimentos do e-SIC | Cada portal redige de um jeito, em página, PDF ou infográfico; só interpretação de texto resolve |

Outros motivos da escolha:

- **Relevância legal:** os 6 têm fundamentação explícita na LAI ou na LRF; 4.1, 4.6 e 12.1 são de execução orçamentária e financeira, cuja falta impede transferências voluntárias (essenciais no PNTP).
- **Cinco categorias do checklist:** informações prioritárias, despesa, planejamento e prestação de contas, e-SIC e acessibilidade.
- **Profundidade em vez de quantidade:** cada critério foi levado até o fim (coleta, regra, evidência, nota gradual, testes e validação). Seis critérios bem resolvidos mostram mais sobre a viabilidade da solução do que muitos critérios superficiais.
- **Extensibilidade:** cada tipo de verificação tem uma regra-modelo. Um critério novo do mesmo tipo reaproveita a coleta e a estrutura da regra (ex.: 16.3 A-/A+ segue o modelo do 16.2).
- **Limitação assumida:** com 6 critérios, a separação entre entidades é baixa (Rio e Caxias empatam em 100). O empate é resultado correto para o que foi medido; o poder de separação cresce com o número de critérios (seção 6).

### 3.3 Desafios do §12 encontrados e tratamento

| Desafio do §12 | Caso real | Tratamento |
|---|---|---|
| Páginas com JavaScript | Betha, GeoSiap, Contas Rio | Playwright; espera até a tela estabilizar e até sumir o indicador de carregamento (até 180 s) |
| Dados em tabelas | Despesas dos 5 portais | Regra lê cabeçalhos de tabela (inclusive grades Vaadin), não texto solto |
| Documentos PDF | ANEXO 1 de Itaboraí, decretos do Rio | Download, verificação de que é PDF, extração de texto com `pypdf`; PDF digitalizado registrado como "precisaria de OCR" |
| Arquivos CSV ou XLS | Botões de exportação (Itaboraí, Caxias, Cachoeiras) | Não usados: a API ou a tabela da tela bastaram nos 6 critérios. Evolução para critérios de formato aberto |
| Portais de diferentes fornecedores | GeoSiap, Modernização, Betha, Supernova | Detecção do fornecedor com evidência gravada; adaptador por fornecedor |
| Links quebrados | Japeri: 2º clique do e-SIC em "página não encontrada" | Página não encontrada excluída da entrada do LLM; não vira evidência |
| Informações espalhadas | 15.4 de Caxias em duas páginas e um infográfico; RGF do Rio em outro domínio | Caminhos de cliques no cadastro; domínios permitidos por entidade; todas as fontes juntas na avaliação |
| Nomenclaturas diferentes | "Execução Orçamentária", "Contas Rio", "Atendimento / Ouvidoria" | Dicionário de termos por critério, com pesos e termos negativos; nenhum termo específico de município |
| Navegação por várias páginas | e-SIC e RGF de Caxias (portal sem mudança de endereço) | Até 2 cliques na descoberta; caminho de cliques no cadastro para os casos mais fundos |
| Portais sem estrutura padronizada | Os 5 | Descoberta genérica + reserva no cadastro + Inconclusivo quando nada funciona |
| Informação disponível, mas difícil de localizar | Link do portal em submenu (Itaboraí), alto contraste em painel fechado (Rio) | Leitura do HTML completo, com registro de visibilidade |
| Informação visual, não estruturada | Infográfico do recurso de Caxias | Download do arquivo original da imagem e transcrição por chamada separada do modelo |

## 4. Tecnologias escolhidas

| Tecnologia | Uso | Por quê | Alternativa considerada |
|---|---|---|---|
| Python 3.13 | Todo o projeto | Ecossistema de coleta, dados e APIs; um só idioma do coletor ao dashboard | |
| Playwright (Chromium) | Coleta de páginas | Navegador real: JavaScript, iframes, novas abas, prints de página inteira | `requests` + HTML bruto: não vê conteúdo montado por script (usado só nas APIs e anexos) |
| requests | APIs de fornecedor, anexos | Arquivo e JSON não precisam de navegador | |
| BeautifulSoup | Leitura do HTML salvo | Regras sobre a estrutura (cabeçalhos, atributos, elementos escondidos) | Expressões regulares sobre o HTML: frágeis |
| pypdf | Texto dos PDFs | Python puro, sem dependência do sistema; extração por página | pdfplumber (melhor para tabelas, mais pesado; não necessário nos casos reais) |
| SQLite | Banco | Um arquivo, sem servidor, suficiente para o protótipo; modelagem portável para PostgreSQL | PostgreSQL desde o início: infraestrutura desnecessária para 5 entidades |
| PyYAML | Configuração | Cadastro, critérios, pesos e gabarito legíveis e versionados no Git | |
| SDK da Anthropic (Claude Sonnet 5.5) | 15.4 | Leitura e extração com resposta em JSON de formato fixo (seção 10) | |
| FastAPI + uvicorn | API | Documentação interativa automática em `/docs`; validação de parâmetros | Flask: sem documentação automática |
| Streamlit + Altair | Dashboard | Um arquivo, um comando; tabelas e gráficos prontos | HTML com JavaScript: mais código para o mesmo resultado |
| Git | Versão do código | O commit vira `versao_codigo` em cada execução | |

## 5. Metodologia de avaliação

### 5.1 Status

| Status | Significado | Entra no score |
|---|---|---|
| Atende | A informação exigida foi encontrada e provada por evidência | Sim (nota 1) |
| Parcial | Parte do que o critério pede foi encontrada | Sim (nota gradual) |
| Não atende | A página certa foi lida e a informação não está lá (prova da ausência) | Sim (nota 0) |
| Indisponível | O site não respondeu, mesmo após novas tentativas (falha da entidade: o cidadão também não acessa) | Sim (nota 0,5) |
| Inconclusivo | O sistema não conseguiu verificar (página não localizada ou ilegível): limitação do método | Não; aparece na cobertura e vai para revisão humana |
| Não aplicável | O critério não vale para o tipo da entidade | Não; fora também da cobertura |

### 5.2 Regra de cada critério

| Critério | Atende | Parcial | Não atende |
|---|---|---|---|
| 1.2 | Link do portal visível na capa, 1 clique | Link só em submenu | Capa carregada e nenhum texto clicável sobre transparência, inclusive texto alternativo de imagem |
| 4.1 | Número do empenho e valores empenhado, liquidado e pago | Parte das quatro informações | Não usado: tabela ilegível é Inconclusivo |
| 4.6 | Até 1 dia útil entre a data mais recente e o dia da avaliação | De 2 dias úteis a 30 dias corridos | Mais de 30 dias |
| 12.1 | Último RGF publicado = último devido pelo prazo da LRF | Publicado com atraso (quadrimestres de atraso no detalhe) | Página do RGF sem nenhum relatório |
| 15.4 | 5 de 5 subitens comprovados por citação | 1 a 4 subitens | 0 subitens com a página do e-SIC legível |
| 16.2 | Controle de alto contraste no HTML completo da capa do portal | Não existe | Capa carregada e nenhum controle |

Cada regra tem travas contra erros vistos nos portais reais (ex.: o 4.6 ignora o rótulo cuja hora é a da própria visita, no rodapé de Japeri; o 12.1 só conta período com link, porque o Rio lista o 3º quadrimestre sem arquivo). Detalhe: `docs/decisoes_regras.md`, seções 2 e 3. Testes: 56 casos montados a partir dos portais reais (`python -m regras.teste_regras`).

### 5.3 Evidências (§6)

Cada avaliação grava a justificativa em texto, a URL avaliada, o método (API, navegador, LLM) e uma ou mais evidências: trecho lido (com CPF mascarado), arquivo de origem, hash SHA-256 e data da coleta. O detalhe de cada avaliação guarda também o resultado de **todas** as fontes avaliadas, não só da escolhida. Os arquivos brutos (HTML após JavaScript, print da página inteira, JSON, PDF, imagem) ficam em `dados/execucoes/N/`, fora do Git, porque páginas de despesa trazem nome e CPF de credores. Um avaliador humano confere qualquer célula abrindo o arquivo indicado e procurando o trecho; o hash garante que o arquivo é o mesmo que foi avaliado.

### 5.4 Grau de confiança (§4)

O §4 pede o "grau de confiança da avaliação, quando aplicável". Adotado um nível ordinal pela natureza da evidência, acompanhado do acerto observado nesse nível na validação:

- **Alta:** o que foi lido prova o veredito (Atende com trecho conferido; 4.6 com data lida no rótulo da página; Indisponível com os erros registrados).
- **Média:** o veredito depende de ausência (Não atende; Parcial por falta de item, subitem ou período) ou de valor inferido (4.6 Parcial pela data máxima dos registros da API).
- **Sem nível:** Inconclusivo e Não aplicável (não há veredito a qualificar).

Princípio: a presença de uma informação se prova com um trecho; a ausência depende de o sistema ter procurado no lugar certo. Resultado nas 4 execuções: alta 80 de 80 corretas (100%); média 20 de 22 (91%). Os 2 erros caíram no nível médio. A confiança não entra no score (mede o sistema, não o portal) e orienta a revisão humana. Um percentual por critério, como o "92%" do exemplo do §4, não foi adotado: com cerca de 13 células por critério, o número não seria confiável. Detalhe: `docs/decisoes_regras.md`, seção 4.0.2.

### 5.5 Validação dos resultados

| Medida (4 execuções, 105 células com gabarito) | Resultado |
|---|---|
| Concordância nas células conclusivas | 100 de 102 (98%) |
| Taxa sem veredito (Inconclusivo ou Indisponível) | 3 de 105 (3%) |
| Falso Não atende | 0 |
| Células estáveis entre execuções (sem o 4.6, que muda com o dia) | 23 de 25 |
| Ordem das entidades com selo do PNTP preservada | 3 de 3 pares |

As 5 divergências vieram da coleta, não das regras, e cada uma foi corrigida; a execução de 16/10 teve 25 de 25. Ressalvas (gabarito feito pela mesma pessoa que escreveu as regras, amostra pequena) e números completos: `docs/validacao.md`.

## 6. Metodologia de cálculo da pontuação

| Passo | Regra |
|---|---|
| Nota do critério (0 a 1) | Atende 1; Não atende 0; Indisponível 0,5; Parcial gradual: 4.1 = informações achadas ÷ 4; 12.1 = 1 − quadrimestres de atraso ÷ 3; 15.4 = subitens comprovados ÷ 5; 1.2 e 4.6 = 0,5 |
| Pesos | Essencial 2 (4.1, 4.6, 12.1: execução orçamentária e financeira, LRF); Obrigatória 1,5 (1.2, 15.4, 16.2: exigência da LAI). Lógica do PNTP |
| Score | soma(peso × nota) ÷ soma dos pesos dos critérios que entraram, em % |
| Cobertura | Critérios no cálculo ÷ critérios aplicáveis, sempre exibida junto do score |
| Faixa | Faixas do PNTP (Diamante 95, Ouro 85, Prata 75, Elevado, Intermediário, Básico, Inicial, Inexistente). Diamante, Ouro e Prata exigem todos os essenciais atendidos. Essencial Inconclusivo não bloqueia, mas marca a faixa como provisória |
| Comparação | Média simples binária (% de Atende) e média simples das notas, gravadas para a discussão abaixo |

**Problemas da média simples (§5)** e como o score os trata:

| Problema | Tratamento | Efeito medido (execução 27) |
|---|---|---|
| Todos os critérios pesam igual | Pesos por classificação | A falha de Itaboraí (1.2, obrigatória) custa menos que a de Cachoeiras (12.1, essencial) |
| É binária | Nota gradual | Cachoeiras: 66,7 pela média binária, 82,2 pela média das notas |
| Compensação: critérios fáceis escondem falha num essencial | Faixa exige os essenciais | Cachoeiras, com 81,6, ficaria em Prata pelo número; fica em Elevado pelo RGF atrasado |
| Critério não avaliado distorce | Fora do cálculo, com cobertura explícita | Japeri na execução 25: 74,5 com 5 de 6; contar o Inconclusivo como 0 daria 60,3 por limitação do coletor |
| Poucos critérios separam pouco | Assumido | Rio e Caxias empatam em 100 |

Resultado de referência (execução 27, 16/10/2026): Duque de Caxias 100,0 Diamante; Rio de Janeiro 100,0 Diamante; Itaboraí 92,9 Ouro; Cachoeiras de Macacu 81,6 Elevado; Japeri 69,8 Intermediário.

Pesos e faixas foram alinhados ao PNTP, e não copiados como substituto dele: o PNTP é anual e autodeclarado com validação por amostra; o sistema é automático, frequente e traz evidência de cada célula. O alinhamento dá linguagem comum com quem já usa o PNTP e permite validar contra os selos oficiais. Parâmetros em `config/score.yaml`. Detalhe: `docs/decisoes_score.md`.

## 7. Tratamento de critérios não aplicáveis (§11)

| Pergunta do §11 | Tratamento |
|---|---|
| Identificar o tipo de entidade | Campo `tipo` no cadastro (prefeitura, câmara, autarquia, fundo, outro). O tipo é dado de entrada, como lista o §4, e não inferido: em fiscalização, um tipo classificado errado mudaria os critérios exigidos |
| Determinar os critérios aplicáveis | Cada critério declara `aplica_a` em `config/criterios.yaml`, gravado em `criterio_aplicabilidade`. O checklist tem matriz comum e critérios específicos; os 6 do protótipo são da matriz comum |
| Tratar não aplicáveis | Status Não aplicável, gravado sem coleta nem regra, com a justificativa |
| Não penalizar | Fora do score e fora do denominador da cobertura. `GET /entidades/{id}/criterios` mostra o que se aplica |

Caso real relacionado: o portal GeoSiap de Japeri serve também à Câmara (outro Poder). A unidade avaliada é o Poder Executivo (prefeitura, fundos e autarquias), e a Câmara é excluída pelo nome, regra que vale para qualquer município do fornecedor. Teste do tratamento: com a aplicabilidade do 16.2 retirada numa cópia do banco, as 5 entidades receberam Não aplicável, cobertura 5 de 5 e score sobre os 5 critérios restantes.

## 8. Tratamento de erros

| Situação | Tratamento | Status resultante |
|---|---|---|
| Falha temporária de acesso | 3 tentativas com intervalos de 5 s e 15 s (3 falhas reais em 2 dias, todas resolvidas na 2ª tentativa) | Nenhum, se a nova tentativa funcionar |
| Erro exibido dentro da página com HTTP 200 | Reconhecido pelo texto ("Network error IOException" em Caxias), não só pelo código HTTP | Igual a erro de acesso |
| Site fora do ar após as tentativas, sem nenhuma fonte salva | Ocorrência gravada com tipo, data e tentativa | Indisponível |
| Página carregada, mas a informação não pôde ser lida (tabela carregando, captcha, página errada) | Motivo de cada fonte gravado no detalhe | Inconclusivo |
| API com parte das entidades sem resposta | A data vista é só um mínimo: Atende continua provado; Parcial ou Não atende não, e a avaliação usa outras fontes | Atende ou Inconclusivo |
| Clique sem efeito | Endereço e texto iguais antes e depois do clique: registrado como "sem efeito", não como sucesso | Segue a cascata |
| Captcha, login, formulário | Não contornados nem preenchidos; registrados como ocorrência | Inconclusivo quando impedem a leitura |
| PDF digitalizado | Registrado como "precisaria de OCR" | Segue com as demais fontes |
| Falha de uma etapa da execução | Etapas em processos separados: a falha de uma não derruba as outras | Execução registrada com o status de cada etapa |
| LLM sem chave ou sem resposta válida | Inconclusivo com o motivo; citação inexistente na fonte = subitem não comprovado | Inconclusivo ou subitem não comprovado |

Princípio: nenhuma falha do sistema ou do acesso vira Não atende. Detalhe: `docs/decisoes_coletor.md`, seções 2 e 4.5.

## 9. Estratégia de atualização

| Elemento | Como funciona |
|---|---|
| Execução completa | `python -m coletor.executar`: coleta das 4 etapas, avaliação e score num comando (cerca de 19 min para as 5 entidades) |
| Repetição | Uma execução oficial por dia desde 13/10/2026 (execuções 16, 19, 25 e 27). O campo `origem` da execução distingue execução manual de agendada (`--origem agendada`) |
| Histórico | Cada execução acrescenta avaliações, evidências e scores; nada é sobrescrito |
| Comparação entre execuções | `GET /entidades/{id}/historico` lista cada mudança de status: de, para, melhorou ou piorou, em qual execução e data. Mudança envolvendo Inconclusivo sai como "sem comparação" |
| Mudança do sistema x mudança do portal | Cada mudança informa se as duas execuções usaram a mesma versão do código. Para comparar com justiça, as coletas antigas são reavaliadas com o código atual, sem acessar os portais |
| Mudança de endereço | Descoberta a partir do site oficial em toda execução; `entidade_urls` guarda endereços com período de validade |
| Mudança de conteúdo | Hash de cada arquivo: hash diferente entre execuções = página mudou |
| Reprocessamento | `python -m regras.avaliar --execucao N` reaplica as regras sobre uma coleta antiga; o LLM reaproveita as respostas guardadas para entradas iguais |

Exemplo real do histórico: Japeri 4.6 foi Atende (execução 16), Parcial (19), Inconclusivo (25, API da Prefeitura sem resposta) e Parcial (27, último empenho em 09/10). Em escala, a frequência passa a ser por critério (seção 12).

## 10. Uso de inteligência artificial (§15)

O LLM é usado em um único critério, o 15.4. Código: `regras/llm_15_4.py`; auditoria: `python -m regras.auditar_15_4 --execucao N`.

| Pergunta do §15 | Resposta |
|---|---|
| Qual problema a IA resolve | Verificar se a seção do e-SIC divulga 5 elementos (prazo de resposta, prazo recursal, autoridades que examinam o pedido, procedimento do pedido, procedimento do recurso) em texto livre, redigido de forma diferente em cada portal, espalhado por páginas, PDFs e infográficos |
| Por que ela é necessária | Uma regra por palavra-chave não separa "o prazo é de 20 dias" de uma citação da lei sem prazo do município, nem identifica uma autoridade descrita de formas diferentes ("Ouvidor Geral", "Coordenadoria de Transparência", "Dirigente Máximo"). Nos outros 5 critérios uma regra explícita é mais barata, previsível e auditável, por isso o LLM fica restrito ao 15.4 |
| Modelo ou estratégia | Claude Sonnet 5.5, raciocínio baixo (`effort: low`), resposta em JSON com esquema fixo. Uma chamada por entidade com as fontes já coletadas e numeradas (F1, F2...). O modelo responde por subitem, nunca "o portal está em conformidade?". Imagens são transcritas numa chamada separada, que não conhece o critério; a transcrição vira fonte de texto |
| Como os resultados são validados | Cada subitem que atende exige citação literal de até 300 caracteres com a fonte; o código confere se o trecho existe no texto da fonte (sem diferença de acento, caixa ou espaço). Validação externa: 18 de 20 células do 15.4 iguais ao gabarito nas 4 execuções; os 2 erros vieram de coleta incompleta (execuções 16 e 19), não do modelo |
| Como reduzir falsos positivos e falsos negativos | Falso positivo: citação inexistente na fonte = subitem não comprovado; a transcrição de imagem não sabe o que procurar, então não tem motivo para "achar" um prazo. Falso negativo: o 0 de 5 só vira Não atende se havia página do e-SIC legível; senão Inconclusivo. Não atende tem confiança média e entra na fila de revisão |
| Como lidar com respostas inconsistentes | Formato JSON fixo; texto dos subitens literal, sem paráfrase; prompt versionado (`VERSAO_PROMPT`): mudar o prompt muda a chave do cache e o resultado fica atribuído à versão. Caso real: a auditoria da execução 25 mostrou que o prompt v1 aceitava a autoridade do recurso no subitem 3; corrigido na v2, com reavaliação |
| Como controlar custos | LLM só no critério semântico; páginas repetidas entram uma vez; texto por fonte limitado a 60 mil caracteres; respostas guardadas por hash do modelo, da versão do prompt e da entrada: página que não mudou não gera nova chamada. Execução 27: 1 chamada nova ao modelo (14,7 mil tokens de entrada), as demais vieram do cache. O custo acompanha a taxa de mudança dos portais, não o número de execuções |
| Como garantir rastreabilidade | Tabela `respostas_llm`: o que foi perguntado e o que voltou, com modelo, versão do prompt, execução, entidade e tokens. Cada citação fica gravada como evidência com o arquivo de origem e o hash. A auditoria mostra, por subitem, a fonte e se a citação foi conferida |

Fontes e decisões de 16/10/2026: PDF linkado na seção do e-SIC conta como divulgação; a página genérica do Fala.BR (plataforma federal) não comprova divulgação da prefeitura. Detalhe: `docs/decisoes_regras.md`, seção 4.0.

## 11. Limitações conhecidas

| Limitação | Efeito | Mitigação no protótipo |
|---|---|---|
| Amostra pequena: 5 entidades, 6 critérios, 4 dias | Percentuais de validação com pouca precisão; baixa separação entre entidades | Ressalvas explícitas; validação com referência externa (PNTP) |
| Gabarito feito pela mesma pessoa que escreveu as regras | Concordância pode estar inflada | Selos do PNTP como referência independente |
| Gabarito do 4.6 em um único dia (15/10) | 5 células de 4.6 na concordância | Gabarito datado: só compara no dia conferido |
| Pesos do dicionário da descoberta heurísticos | Podem falhar em portais com outro vocabulário | Medidos contra o cadastro (13 de 15 alvos certos sem cadastro); falha vira Inconclusivo, não Não atende |
| Feriados só nacionais na conta de dias úteis | Feriado estadual ou municipal pode gerar Parcial falso no 4.6 | Lista fixa documentada |
| 4.6 pela data do registro mais recente, não do registro contábil | Dia sem despesa "envelhece" a data | Prioridade ao rótulo "dados atualizados até"; Parcial pela API sai com confiança média |
| Notas 0,5 do Parcial no 1.2 e no 4.6 são convenção | Mudam o número, não a regra | Parâmetros em `config/score.yaml` |
| Classificação dos critérios inferida (o checklist do case não a traz) | Outra classificação mudaria os pesos | Lógica do PNTP, documentada |
| Sem OCR para PDF digitalizado | Documento só em imagem não é lido | Ocorrência "precisaria de OCR" |
| Captcha não contornado | Consultas com captcha (Caxias) dependem de API | API de dados abertos do fornecedor |
| Sem adaptador Betha | Cachoeiras pela descoberta genérica | Descoberta funcionou nas 4 execuções |
| Página com erro do servidor (HTTP 500) com o resto do site no ar sai Inconclusivo | Falha da plataforma sem punição | Nenhum caso real até 16/10 |
| Variação do LLM entre versões de prompt | Subitens no limite podem mudar | Cache por versão do prompt; auditoria por subitem |

Limitações por componente: `docs/decisoes_coletor.md` (seção 7), `docs/decisoes_regras.md` (seção 4.1), `docs/decisoes_score.md` (seção 7), `docs/decisoes_api.md` (seção 4).

## 12. Possibilidades de evolução

### 12.1 Pergunta central (§17): 5.000 portais, todo mês

| Requisito do §17 | Resposta do desenho atual |
|---|---|
| Confiável | Não atende só com prova; Inconclusivo em vez de chute; nenhuma falha de acesso vira não conformidade; validação contínua por amostragem com as mesmas métricas de `regras/validar.py` |
| Explicável | Cada célula tem justificativa, evidência com hash, fonte e grau de confiança; cada clique da descoberta e cada resposta do LLM ficam gravados |
| Economicamente viável | Cadastro mínimo (site oficial); adaptador por fornecedor, não por município; LLM só no critério semântico e com cache; reprocessamento sem nova coleta |

Projeção: cerca de 4 min por entidade hoje, sequencial, dá cerca de 330 h por ciclo de 5.000 portais; com 10 navegadores simultâneos, cerca de 33 h, o que cabe num ciclo mensal. Arquitetura de produção, gargalos, riscos e os 11 pontos do §8: `docs/escalabilidade.md`.

### 12.2 Próximos passos

| Evolução | Motivo |
|---|---|
| Fila de tarefas (entidade × etapa) com workers em contêiner e limite de requisições por domínio | Paralelismo sem sobrecarregar portais pequenos |
| PostgreSQL e armazenamento de objetos com deduplicação por hash | Escrita concorrente e volume de artefatos |
| Frequência por critério: 4.6 diário; 12.1 após cada prazo quadrimestral da LRF; demais semanal ou mensal | Custo proporcional à velocidade de mudança de cada informação |
| Levantamento dos fornecedores dos 92 municípios do RJ e adaptadores para os maiores (Betha primeiro) | Um adaptador cobre todos os clientes do fornecedor |
| Mais critérios do checklist, um tipo de verificação por vez, reaproveitando as regras-modelo | Aumenta a separação entre entidades |
| 16.5 com avaliação automática de acessibilidade (axe-core via Playwright) | Nota contínua, separaria entidades que hoje empatam |
| Fila de revisão humana com Inconclusivos e vereditos de confiança média; a revisão vira cadastro e não se repete | Trabalho humano concentrado onde o sistema tem menos certeza |
| Probabilidade calibrada por critério e método, com o gabarito acumulado da revisão humana | Transforma o nível de confiança num percentual medido |
| Alarme por taxa de Inconclusivo por fornecedor | Mudança de layout de um fornecedor afeta muitos municípios de uma vez |
| LLM como reserva da descoberta quando a melhor nota for baixa | Portais com vocabulário fora do dicionário |
| OCR para PDFs digitalizados; tabela de feriados por município | Fecham limitações da seção 11 |
| Extensão para Niterói e Maricá (opcional no §2) | Teste da descoberta em portais novos, só com o site oficial |
| Autenticação e paginação na API | Uso institucional |
