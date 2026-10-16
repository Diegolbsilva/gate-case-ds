# Documentação técnica: avaliação automática de portais da transparência municipais

Protótipo para o desafio técnico do GATE/MPRJ (Cientista de Dados). Repositório: https://github.com/Diegolbsilva/gate-case-ds. Instalação e comandos: `README.md`.

O documento segue os 11 tópicos pedidos no §14 do enunciado (entregáveis) e responde também às perguntas do §15 (uso de IA), à justificativa de escopo do §13 e à discussão de escala dos §8 e §17. Dois anexos completam a documentação:

- `docs/exploracao_portais.md`: exploração manual dos 5 portais, gabarito e evidências encontradas;
- `docs/validacao.md`: comparação dos resultados com o gabarito e com os selos do PNTP.

| Tópico | Seção |
|---|---|
| Problema identificado | 1 |
| Arquitetura proposta | 2 |
| Abordagem utilizada (inclui a escolha dos critérios e a coleta) | 3 |
| Tecnologias escolhidas | 4 |
| Metodologia de avaliação | 5 |
| Metodologia de cálculo da pontuação | 6 |
| Tratamento de critérios não aplicáveis | 7 |
| Tratamento de erros | 8 |
| Estratégia de atualização | 9 |
| API e dashboard | 10 |
| Uso de inteligência artificial | 11 |
| Limitações conhecidas | 12 |
| Possibilidades de evolução e escala | 13 |

Escopo: 5 prefeituras do RJ (Japeri, Duque de Caxias, Itaboraí, Cachoeiras de Macacu e Rio de Janeiro), 6 critérios do checklist (1.2, 4.1, 4.6, 12.1, 15.4 e 16.2) e 4 execuções oficiais completas entre 13 e 16/10/2026.

## 1. Problema identificado

Hoje, verificar se um portal da transparência cumpre o checklist exige que uma pessoa navegue pelo portal, localize cada informação e registre o resultado. O enunciado pede um processo automático, repetível, auditável e escalável.

A exploração manual dos 5 portais (anexo `exploracao_portais.md`) mostrou que a dificuldade principal não está em verificar uma informação, e sim em **chegar até ela** de forma confiável, em portais sem nenhum padrão comum:

| Característica observada | Consequência para a solução |
|---|---|
| 5 prefeituras, 5 modelos de portal: fornecedor com API pública (GeoSiap, Japeri), fornecedor com API não divulgada na navegação (Modernização, Caxias), plataforma em nuvem compartilhada (Betha, Cachoeiras), sistema de fornecedor dentro de portal próprio (Supernova, Itaboraí) e desenvolvimento próprio com vários sistemas (Rio) | Código por município não escala. É preciso um caminho genérico e adaptadores por fornecedor |
| 3 dos 5 portais montam o conteúdo com JavaScript; menus sem link (blocos do Angular, itens abertos por script); consultas que só mostram dados depois de "Pesquisar" | Navegador real e descoberta por texto clicável, não só por link |
| A mesma informação aparece como tabela, API, PDF ou infográfico em imagem | Extração conforme o tipo de fonte |
| Informação disponível, mas não localizada pelo sistema, é diferente de informação ausente | Status próprio para "não foi possível verificar" (Inconclusivo), separado de Não atende |
| Portais mudam: endereço novo ("transparencianovo" em Itaboraí), dados diários, relatórios quadrimestrais | Execuções periódicas, histórico e versão do código em cada execução |
| Contexto de fiscalização: um falso Não atende pode instruir um procedimento contra a entidade | Não atende só com prova da ausência; evidência verificável por humano em cada célula |

Formulação adotada: para cada entidade e critério, produzir um status com evidência auditável e grau de confiança, separar a falha da entidade da limitação do sistema, agregar num score explicável e repetir o processo com histórico comparável.

## 2. Arquitetura proposta

```
cadastro (config/entidades.yaml: 5 campos por entidade; o site oficial basta)
   │
   ▼
COLETA (coletor/)  uma execução = 4 etapas em processos separados
   │   1. descoberta: do site oficial até o portal e as páginas de cada critério
   │   2. APIs: reconhece o fornecedor e coleta pela API quando há adaptador
   │   3. cadastro: URLs anotadas por critério (reserva) e caminhos de cliques
   │   4. anexos: PDFs e páginas de detalhe da seção do e-SIC
   ▼
artefatos (HTML após JavaScript, print, JSON, PDF, imagem), cada um com hash SHA-256
   │
   ▼
AVALIAÇÃO (regras/)  não acessa portal: lê só o que foi coletado
   │   regras determinísticas (1.2, 4.1, 4.6, 12.1, 16.2) + LLM com citação conferida (15.4)
   │   status, nota, grau de confiança, justificativa e evidências
   ▼
SCORE (regras/score.py)  pesos e faixas alinhados ao PNTP, cobertura explícita
   │
   ▼
banco SQLite (histórico por execução)  ──  API (FastAPI, somente leitura)  ──  dashboard (Streamlit)
```

Princípios do desenho:

- **Coletar separado de avaliar.** Uma regra nova é reaplicada sobre coletas antigas sem acessar os portais (`python -m regras.avaliar --execucao N`). O reprocessamento não gera tráfego e permite comparar execuções com o mesmo código.
- **Cada execução acrescenta, nada é sobrescrito.** É o que permite responder às perguntas do §7 (melhorou, piorou, o que foi corrigido e quando).
- **Versão do código (commit) gravada em cada execução**, para separar "o portal mudou" de "o sistema mudou".
- **API e dashboard somente leitura.** A consulta não altera o histórico.

Modelagem de dados (`db/schema.sql`):

| Tabela | Conteúdo |
|---|---|
| `entidades`, `entidade_urls` | Quem é avaliado (com tipo) e seus endereços, com período de validade |
| `criterios`, `criterio_aplicabilidade` | Itens do checklist com versão, categoria, fundamentação, tipo de verificação e tipos de entidade a que se aplicam |
| `execucoes` | Cada rodada: data, origem (manual ou agendada), versão do checklist e do código, status |
| `artefatos` | Tudo o que foi baixado: caminho, hash, URL final, data |
| `descobertas` | Cada clique da descoberta: texto, nota, destino, se estava visível, se precisou rolar |
| `avaliacoes` | Resultado de um critério para uma entidade numa execução: status, nota, grau de confiança, método, justificativa e detalhe da regra |
| `evidencias` | Provas de cada avaliação: trecho (CPF mascarado), arquivo, hash, URL, data |
| `scores` | Score, faixa, cobertura e médias de comparação por execução e entidade |
| `ocorrencias` | Erros e novas tentativas, com tipo (timeout, erro do servidor, bloqueio, captcha) |
| `respostas_llm` | Respostas do modelo guardadas por hash da entrada: cache e trilha de auditoria |

## 3. Abordagem utilizada

### 3.1 Combinação de técnicas

A abordagem é híbrida, na linha do que o §15 descreve ("dados + regras + automação + IA + validação + evidências"). Cada técnica entra onde é a mais barata, previsível e auditável:

| Técnica | Onde | Por quê |
|---|---|---|
| API do fornecedor | 4.1, 4.6 e 12.1 em Japeri e Caxias | Dado estruturado, independente da tela; evita o reCAPTCHA das consultas de Caxias sem burlá-lo, pela API de dados abertos |
| Navegador automatizado | Todas as páginas | JavaScript, iframes, cliques em portais que não mudam de endereço |
| Descoberta por texto clicável com nota | Do site oficial ao portal e às páginas de cada critério | Cadastro mínimo por entidade; funciona em portal desconhecido; cada clique fica gravado com texto e nota |
| Regras determinísticas | 1.2, 4.1, 4.6, 12.1, 16.2 | Critérios verificáveis pela estrutura (cabeçalhos de tabela, datas, períodos, elementos); resultado reproduzível |
| LLM com citação conferida | 15.4 | Único critério que exige interpretar texto livre (seção 11) |
| Validação contra referências | Todos | Gabarito manual e selos do PNTP (anexo `validacao.md`) |

Alternativas descartadas para a navegação: classificar links com aprendizado de máquina exigiria muitos exemplos rotulados, e o protótipo tem 5 portais; deixar um LLM escolher onde clicar teria custo por página, respostas variáveis entre execuções e auditoria difícil; rastrear o site inteiro seria lento e acessaria páginas desnecessárias de um órgão público.

### 3.2 Escolha dos critérios (§13)

O §13 recomenda um subconjunto com diferentes níveis de complexidade e lista 6 tipos. Foi escolhido um critério por tipo, todos da matriz comum do checklist (6 de 66):

| Tipo pedido no §13 | Critério | Por que este |
|---|---|---|
| Existência simples de informação | 16.2 Opção de alto contraste | Elemento verificável no HTML; exige ler menus fechados e painéis de acessibilidade, não só o visível |
| Exige navegação | 1.2 Acesso ao portal visível na capa do site | Mede o caminho do cidadão: visibilidade, submenu, rolagem, número de cliques |
| Dados estruturados | 4.1 Número e valor de empenho, liquidação e pagamento | Tabelas em formatos diferentes (fase em coluna ou em linha) e APIs de fornecedor |
| Envolve documentos | 12.1 Publica o Relatório de Gestão Fiscal | Documento periódico: além de existir, o período mais recente precisa estar em dia com o prazo da LRF |
| Atualização das informações | 4.6 Informações atualizadas da despesa | Referência temporal objetiva (Decreto 10.540/2020: até o 1º dia útil seguinte ao registro) |
| Interpretação semântica | 15.4 Prazos, autoridades e procedimentos do e-SIC | Cada portal redige de um jeito, em página, PDF ou infográfico |

Além da cobertura dos 6 tipos:

- os 6 têm fundamentação explícita na LAI ou na LRF, e 4.1, 4.6 e 12.1 tratam da execução orçamentária e financeira, cuja falta impede transferências voluntárias;
- cobrem 5 categorias do checklist (informações prioritárias, despesa, planejamento e prestação de contas, e-SIC, acessibilidade);
- cada critério foi levado até o fim (coleta, regra, evidência, nota gradual, testes e validação), o que mostra mais sobre a viabilidade da solução do que muitos critérios superficiais;
- cada tipo de verificação tem uma regra-modelo: um critério novo do mesmo tipo reaproveita a coleta e a estrutura da regra (o 16.3, A-/A+, segue o modelo do 16.2).

Limitação assumida: com 6 critérios, a separação entre entidades é baixa (Rio e Caxias empatam em 100). O empate é correto para o que foi medido; a separação cresce com o número de critérios.

### 3.3 Coleta

**Caminho em cascata.** Para cada prefeitura, a coleta tenta, nesta ordem: a descoberta a partir do site oficial; o adaptador do fornecedor, quando existe; as URLs anotadas no cadastro, como reserva. Se nada funciona, o critério fica Inconclusivo. O cadastro precisa só de 5 campos (id, nome, município, tipo e site oficial); o resto é descoberto. Cada resultado registra por qual caminho foi obtido, o que mede quanto depende de configuração manual.

**Navegador** (`coletor/navegador.py`):

| Decisão | Por quê |
|---|---|
| Playwright (Chromium) | 3 dos 5 portais montam o conteúdo com JavaScript; uma requisição simples recebe a página vazia |
| Janela fixa de 1366 x 768 | O 1.2 mede se o link do portal exige rolagem; sem tamanho fixo, o resultado não seria reproduzível |
| User-Agent próprio, com o link do repositório | A Betha bloqueia o navegador automatizado padrão (HTTP 403) e libera a identidade própria. O portal sabe quem acessa; disfarçar o navegador não é postura adequada para um órgão de controle |
| Espera até a tela estabilizar | Espera mínima de 3 s; depois, relê o texto a cada 1,5 s até ele parar de mudar (até 30 s) e até sumir qualquer indicador de carregamento visível (até 180 s). O Contas Rio leva mais de 90 s para montar a tabela de empenhos |
| HTML depois do JavaScript, print da página inteira, iframes salvos à parte | É o que o visitante vê; o print permite conferência humana sem rodar nada; em Caxias as consultas ficam dentro de um iframe |
| Hash SHA-256 de cada arquivo | Detecta mudança de página entre execuções e o mesmo arquivo publicado em períodos diferentes (caso real: RGF de Japeri) |

**Descoberta** (`coletor/descoberta.py`, `coletor/descobrir.py`). Os menus aparecem de formas diferentes: links comuns (Itaboraí, Rio), links sem endereço abertos por script (Caxias), itens sem endereço (Betha) e blocos clicáveis sem nenhum link (GeoSiap, com 5 links na página inteira). Por isso a descoberta lista todos os textos de elementos clicáveis, guarda o caminho CSS de cada um e clica no elemento quando não há link.

Cada alvo tem uma lista de termos com peso, tirados do texto do checklist e de sinônimos vistos nos portais. A nota de um texto é a soma dos pesos dos termos que ele contém, menos 6 pontos por termo de recorte ou de outro assunto:

| Alvo | Termos fortes | Termos fracos | Termos que tiram pontos |
|---|---|---|---|
| Portal | "portal da transparência" (10) | "transparência" (5) | radar, TCE, saúde, câmara, diário, ouvidoria |
| Despesa | "execução detalhada de despesas", "despesas detalhadas" (10) | "despesas" (6), "empenho" (6), "execução orçamentária" (5) | multa, trânsito, pessoal, diária, educação, emenda, receita |
| RGF | "relatório de gestão fiscal", "RGF" (10) | "LRF" (5), "prestação de contas" (4), "relatórios" (2) | RREO, balanço, opcionais |
| e-SIC | "prazos de respostas do SIC" (10), "e-SIC", "pedido de informação" (8) | "acesso à informação" (6), "ouvidoria" (2) | LGPD, estatística, sigilo |

Regras de escolha:

- clica no texto de maior nota; em empate, no mais curto (texto curto costuma ser item de menu); nota zero ou negativa não é clicada;
- só clica no que uma pessoa conseguiria clicar: elemento visível ou com endereço. Na Betha, um item escondido no menu lateral fechado era clicado sem efeito e registrado como sucesso; clique sem efeito (mesmo endereço e mesmo texto antes e depois) passou a ser registrado como falha;
- o texto alternativo (`alt`) das imagens entra no rótulo: um banner "Portal da Transparência" feito só de imagem é encontrado;
- botões genéricos ("ACESSAR", "Saiba mais") recebem como rótulo os títulos do card ao redor;
- até 2 cliques; o segundo só em texto com nota 6 ou mais que **não estava visível antes do primeiro clique** (submenu aberto, página nova), nunca repetido. Isso evita ir para um item irmão do menu, como "Execução Detalhada de Despesas - Educação" em Cachoeiras;
- nenhum termo específico de município. No Rio, as despesas ficam em "CONTAS RIO", sem a palavra despesa; acrescentar "contas rio" ao dicionário seria ajustar a regra a um município, o que não escala. Nesse caso vale a reserva do cadastro.

Resultado: 13 de 15 alvos (despesa, RGF e e-SIC nas 5 entidades) encontrados sem cadastro; as 2 falhas são do Rio e são cobertas pelo cadastro. Erro de descoberta nunca vira Não atende (seção 5.2).

**Fornecedores e APIs** (`coletor/fornecedores.py`, `coletor/apis.py`). O fornecedor é reconhecido pela URL e pelo HTML do portal, com a evidência gravada (ex.: "domínio do portal: japeri.geosiap.net.br"). Em Caxias, o nome do fornecedor não aparece em texto, e a assinatura usada é estrutural (`/webrun/form.jsp?sys=LAI`), válida para todos os clientes da plataforma.

| Adaptador | O que faz |
|---|---|
| GeoSiap (Japeri) | Lista as entidades do portal, exclui a Câmara pelo nome ("câmara", "legislativo") e baixa as despesas dos últimos 30 dias de cada entidade, por data inicial e final (o parâmetro de ano não respondeu). Registra as entidades que não responderam; tempo limite de 180 s por consulta |
| Webrun, da Modernização (Caxias) | Chama o endpoint único de dados abertos com o serviço (`despesas_todas`, `consulta_rgf_m2`) e o ano. Como o método HTTP não é documentado, testa POST com JSON, POST com formulário e GET, nessa ordem, e registra qual funcionou |
| Betha, Supernova | Sem adaptador: a descoberta genérica resolve |

Cada adaptador é escrito uma vez e serve para todos os municípios daquele fornecedor; o exemplo de resposta da API da Modernização cita outro município cliente.

**Cadastro como reserva** (`coletor/cadastro.py`). Abre as URLs anotadas por critério e salva HTML e print ligados ao critério. Em consultas de dados (4.1, 4.6, 12.1), se houver um botão visível "Pesquisar", "Consultar" ou "Buscar", clica uma vez e salva também o resultado, escolhendo antes o mês corrente quando há seletor de mês vazio (Japeri e Itaboraí só mostram a tabela depois disso). Nunca clica em página com reCAPTCHA nem em página do e-SIC, para não enviar formulário. Para páginas sem endereço próprio, o cadastro aceita um caminho de cliques a partir da capa do portal (Caxias, 15.4: "Pedido de Informação" > "Interposição de Recurso" > "Orientações sobre Recurso"). Nessa tela final, o coletor baixa o arquivo original das imagens grandes (no mínimo 600 x 400 px, até 5) que surgiram com os cliques: o infográfico do recurso de Caxias fica numa caixa com rolagem própria e sai cortado no print, e as imagens já presentes antes dos cliques são do layout.

**Anexos do e-SIC** (`coletor/anexos.py`). Lê as páginas do e-SIC já salvas, segue páginas de detalhe ("Ver mais detalhes", 1 nível), baixa os PDFs (inclusive quando o endereço está num `onclick`, caso do ANEXO 1 de Itaboraí) e extrai o texto com `pypdf`, marcando a página. Só aceita arquivo que começa com `%PDF`, no máximo 5 PDFs de até 15 MB por entidade e só dos domínios da entidade. PDF sem camada de texto é registrado como "precisaria de OCR".

Postura de coleta: identidade própria no User-Agent, uma visita por vez, nenhum contorno de captcha, nenhum formulário preenchido ou enviado, nenhum login seguido. Páginas de despesa trazem nome e CPF de credores pessoa física: os arquivos brutos ficam fora do Git, e todo trecho gravado como evidência tem o CPF mascarado.

### 3.4 Desafios do §12 e tratamento

| Desafio do §12 | Caso real | Tratamento |
|---|---|---|
| Páginas com JavaScript | Betha, GeoSiap, Contas Rio | Playwright com espera por estabilização e por indicador de carregamento |
| Dados em tabelas | Despesas dos 5 portais | A regra lê cabeçalhos de tabela (inclusive grades Vaadin), não texto solto |
| Documentos PDF | ANEXO 1 de Itaboraí, decretos do Rio | Download, conferência de que é PDF, extração de texto; digitalizado registrado como "precisaria de OCR" |
| Arquivos CSV ou XLS | Botões de exportação (Itaboraí, Caxias, Cachoeiras) | Não necessários nos 6 critérios: API ou tabela da tela bastaram |
| Portais de diferentes fornecedores | GeoSiap, Modernização, Betha, Supernova | Detecção com evidência; adaptador por fornecedor |
| Links quebrados | Japeri: 2º clique do e-SIC em "página não encontrada" | Página não encontrada fica fora da entrada do LLM e não vira evidência |
| Informações espalhadas | 15.4 de Caxias em duas páginas e um infográfico; RGF do Rio em outro domínio | Caminhos de cliques; domínios permitidos por entidade; todas as fontes juntas na avaliação |
| Nomenclaturas diferentes | "Execução Orçamentária", "Contas Rio", "Atendimento / Ouvidoria" | Dicionário com pesos e termos negativos |
| Navegação por várias páginas | e-SIC e RGF de Caxias, portal que não muda de endereço | Até 2 cliques na descoberta; caminho de cliques no cadastro |
| Portais sem estrutura padronizada | Os 5 | Descoberta genérica, reserva no cadastro e Inconclusivo quando nada funciona |
| Informação disponível, mas difícil de localizar | Link do portal em submenu (Itaboraí); alto contraste em painel fechado (Rio) | Leitura do HTML completo, com registro de visibilidade |
| Informação visual, não estruturada | Infográfico do recurso de Caxias | Arquivo original da imagem e transcrição por chamada separada do modelo |

## 4. Tecnologias escolhidas

| Tecnologia | Uso | Por quê | Alternativa considerada |
|---|---|---|---|
| Python 3.13 | Todo o projeto | Ecossistema de coleta, dados e APIs; um só idioma do coletor ao dashboard | |
| Playwright (Chromium) | Coleta de páginas | Navegador real: JavaScript, iframes, novas abas, prints de página inteira | `requests` + HTML bruto: não vê conteúdo montado por script (usado nas APIs e anexos) |
| requests | APIs de fornecedor e anexos | JSON e arquivos não precisam de navegador | |
| BeautifulSoup | Leitura do HTML salvo | Regras sobre a estrutura (cabeçalhos, atributos, elementos escondidos) | Expressões regulares sobre o HTML: frágeis |
| pypdf | Texto dos PDFs | Python puro, sem dependência do sistema; extração por página | pdfplumber: melhor para tabelas, desnecessário nos casos reais |
| SQLite | Banco | Um arquivo, sem servidor; modelagem portável para PostgreSQL | PostgreSQL desde o início: infraestrutura desnecessária para 5 entidades |
| PyYAML | Configuração | Cadastro, critérios, pesos e gabarito legíveis e versionados | |
| SDK da Anthropic (Claude Sonnet 5.5) | 15.4 | Leitura e extração com resposta em JSON de formato fixo | |
| FastAPI + uvicorn | API | Documentação interativa automática em `/docs`; validação de parâmetros | Flask: sem documentação automática |
| Streamlit + Altair | Dashboard | Um arquivo, um comando; tabelas e gráficos prontos | Página HTML com JavaScript: mais código para o mesmo resultado |
| Git | Versão do código | O commit vira `versao_codigo` em cada execução | |

## 5. Metodologia de avaliação

### 5.1 Status

| Status | Significado | Entra no score |
|---|---|---|
| Atende | A informação exigida foi encontrada e provada por evidência | Sim (nota 1) |
| Parcial | Parte do que o critério pede foi encontrada | Sim (nota gradual) |
| Não atende | A página certa foi lida e a informação não está lá (prova da ausência) | Sim (nota 0) |
| Indisponível | O site não respondeu, mesmo após novas tentativas. É falha da entidade: o cidadão também não acessa | Sim (nota 0,5) |
| Inconclusivo | O sistema não conseguiu verificar (página não localizada ou ilegível). É limitação do método | Não; aparece na cobertura e vai para revisão humana |
| Não aplicável | O critério não vale para o tipo da entidade | Não; fora também da cobertura |

### 5.2 Como uma avaliação é feita

A avaliação (`regras/avaliar.py`) não acessa nenhum portal: lê o banco e os arquivos da execução. Para cada entidade e critério:

1. junta as fontes salvas, na ordem API do fornecedor, páginas da descoberta, páginas do cadastro;
2. aplica a regra do critério (`regras/verificacoes.py`) a cada fonte, que responde atende, parcial, não atende ou "não é evidência" (página errada, tabela que não carregou, captcha);
3. fica com o melhor resultado entre as fontes; em empate, vale a primeira na ordem. Uma página errada da descoberta (no Rio, "Plano de execuções orçamentária e de gestão fiscal" no lugar do RGF) não derruba o que a página certa mostra;
4. se nenhuma fonte serviu: Indisponível, quando nada foi salvo e houve erro de acesso; senão, Inconclusivo, com o motivo de cada fonte na justificativa.

O detalhe gravado inclui o resultado de todas as fontes avaliadas, não só da escolhida.

### 5.3 Regra de cada critério

| Critério | Fonte | Atende | Parcial | Não atende |
|---|---|---|---|---|
| 1.2 | 1º clique da descoberta e capa do site salva | Link do portal visível na capa, 1 clique (rolar não conta como clique; fica registrado no detalhe) | Link só em submenu | Capa carregada (mais de 200 caracteres, sem captcha) e nenhum texto clicável sobre transparência, inclusive texto alternativo de imagem |
| 4.1 | API (campos de número e valores) ou cabeçalhos da tabela da página | Número do empenho e valores empenhado, liquidado e pago, em colunas ou em linhas por fase (Caxias) | Parte das quatro informações | Não usado: tabela ilegível é Inconclusivo |
| 4.6 | API (data mais recente dos registros) ou rótulo na página ("dados atualizados até", "última atualização dos dados", "data de atualização dos dados") | Até 1 dia útil de defasagem | De 2 dias úteis a 30 dias corridos | Mais de 30 dias |
| 12.1 | API (ano e quadrimestre) ou períodos nos títulos dos relatórios | Último RGF publicado = último devido (prazo da LRF: 30 dias após o fim do quadrimestre) | Publicado com atraso (quadrimestres de atraso no detalhe) | Página do RGF sem nenhum relatório |
| 15.4 | Páginas, PDFs e imagens da seção do e-SIC, pelo LLM (seção 11) | 5 de 5 subitens comprovados por citação | 1 a 4 subitens | 0 subitens com página do e-SIC legível |
| 16.2 | HTML completo da capa do portal | Controle de alto contraste (texto, título, `aria-label`, atributos `data-*`) | Não existe | Capa carregada e nenhum controle |

Cuidados contra erros vistos nos portais reais:

| Cuidado | Caso real |
|---|---|
| 4.1 lê cabeçalhos de tabela, não texto solto | Itens de menu como "Despesas Empenhadas" dariam falso Atende; a página de gráficos do Rio tem as palavras, mas não os empenhos |
| 4.6 ignora rótulo com a hora da própria visita (até 15 min da coleta) | Rodapé de Japeri: "dados atualizados em" mostra a hora do acesso |
| 4.6 ignora datas futuras e linhas de total | Caxias: "TOTAL DO MÊS (CONSOLIDADO)" com data do fim do mês |
| 4.6 conta dias úteis com os feriados nacionais | 12/10 não é dia útil |
| 12.1 lê o ano junto do quadrimestre e, sem ele, o último "Exercício" acima | Japeri agrupa por exercício; em Cachoeiras a coluna "Ano" não é o ano do relatório |
| 12.1 só conta período com link no próprio item | O Rio lista o 3º quadrimestre ainda sem arquivo |
| 12.1 ignora tabelas escondidas | Itaboraí tem uma cópia oculta da lista, só para exportar CSV |
| 12.1 só dá Não atende em página cujo título fala de RGF, sem captcha | A página errada do Rio e o captcha de Caxias dariam falso Não atende |
| 16.2 não conta classe CSS sozinha | Folhas de estilo têm "contrast" mesmo sem botão |

Testes: 56 casos montados a partir dos portais reais (`python -m regras.teste_regras`).

### 5.4 Decisões de interpretação

- **1.2, link não encontrado.** Vira Não atende, porque se nenhum texto clicável da capa tem relação com transparência, o cidadão também não acharia o portal. Duas travas: a capa precisa ter carregado com conteúdo e sem captcha (senão Inconclusivo, ou Indisponível se nem abriu), e o texto alternativo das imagens é lido, para não punir banner feito de imagem.
- **4.6, referência legal.** "Tempo real" é a disponibilização até o 1º dia útil seguinte ao registro contábil (Decreto 10.540/2020, art. 7º, §1º). Avaliando no dia D, o registro do último dia útil antes de D ainda está no prazo; por isso, até 1 dia útil de defasagem é Atende. O decreto não define Parcial: a faixa de 2 dias úteis a 30 dias corridos é critério do sistema, para separar "atrasou alguns dias" de "parou de publicar".
- **4.6 pela API com entidade sem resposta.** Se alguma entidade do portal não respondeu, a data mais recente vista é só um mínimo: a real é igual ou posterior. Atende continua provado; Parcial ou Não atende não, e a API passa a ser "não é evidência". Mesma lógica de "Não atende só com prova".
- **Unidade avaliada.** O Poder Executivo municipal (prefeitura, fundos e autarquias), sem a Câmara, que é outro Poder. Em Japeri, o mesmo portal serve à Câmara e a 13 outras entidades.

### 5.5 Evidências (§6)

Cada avaliação grava a justificativa, a URL avaliada, o método (API, navegador ou LLM) e uma ou mais evidências: trecho lido (com CPF mascarado), arquivo de origem, hash SHA-256 e data da coleta. Os arquivos brutos (HTML, print da página inteira, JSON, PDF, imagem) ficam em `dados/execucoes/N/`, fora do Git. Um avaliador humano confere qualquer célula abrindo o arquivo indicado e procurando o trecho; o hash garante que o arquivo é o mesmo que foi avaliado.

### 5.6 Grau de confiança (§4)

O §4 pede o "grau de confiança da avaliação, quando aplicável". Cada veredito recebe um nível pela natureza da evidência (`regras/verificacoes.py`, função `nivel_confianca`):

- **alta:** o que foi lido prova o veredito (Atende com trecho conferido; 4.6 com a data lida no rótulo da página; Indisponível com os erros de acesso registrados);
- **média:** o veredito depende de ausência (Não atende; Parcial por falta de item, subitem ou período) ou de valor inferido (4.6 Parcial pela data mais recente dos registros da API, que pode refletir só um dia sem despesa);
- **sem nível:** Inconclusivo e Não aplicável, que não têm veredito a qualificar.

O princípio é que a presença de uma informação se prova com um trecho, e a ausência depende de o sistema ter procurado no lugar certo. Não há nível "baixo" porque um veredito com evidência fraca não é emitido: vira Inconclusivo.

Junto do nível, a API e o dashboard mostram o acerto observado nesse nível contra o gabarito manual (`python -m regras.validar --gravar-confianca`, gravado em `config/confianca_observada.yaml`):

| Nível | Acerto nas 4 execuções |
|---|---|
| Alta | 80 de 80 (100%) |
| Média | 20 de 22 (91%) |

Os 2 erros caíram no nível médio. Como têm a mesma causa (coleta incompleta do 15.4 de Caxias) e a base é pequena, a separação entre os níveis é um indício, que precisa de mais amostra para ser confirmado. Um percentual por critério, como o "92%" do exemplo do §4, não foi adotado: com cerca de 13 células por critério, o número não seria confiável. A confiança declarada pelo próprio LLM também não, porque não há como conferi-la. A confiança não entra no score: mede o sistema, não o portal, e serve para orientar a revisão humana.

### 5.7 Validação

| Medida (4 execuções, 105 células com gabarito) | Resultado |
|---|---|
| Concordância nas células conclusivas | 100 de 102 (98%) |
| Taxa sem veredito (Inconclusivo ou Indisponível) | 3 de 105 (3%) |
| Falso Não atende | 0 |
| Células estáveis entre execuções (sem o 4.6, que muda com o dia) | 23 de 25 |
| Ordem das entidades com selo do PNTP preservada | 3 de 3 pares |

As 5 divergências vieram da coleta, não das regras, e cada uma foi corrigida; a execução de 16/10 teve 25 de 25. Números completos e ressalvas no anexo `validacao.md`.

## 6. Metodologia de cálculo da pontuação

Código: `regras/score.py`; parâmetros: `config/score.yaml`.

| Passo | Regra | Por quê |
|---|---|---|
| Nota do critério (0 a 1) | Atende 1; Não atende 0; Indisponível 0,5; Parcial com nota gradual (tabela abaixo) | A nota mede quanto do que o critério pede foi cumprido |
| Quem fica fora | Inconclusivo e Não aplicável | Inconclusivo é limitação do sistema, não falha da entidade |
| Pesos | Essencial 2; Obrigatória 1,5 | Um RGF atrasado pesa mais que a falta de botão de contraste |
| Score | soma(peso × nota) ÷ soma dos pesos dos critérios que entraram, em % | Média ponderada; o denominador muda com a cobertura, por isso a cobertura é sempre exibida junto |
| Faixa | Diamante (95), Ouro (85), Prata (75), Elevado, Intermediário, Básico, Inicial, Inexistente. Diamante, Ouro e Prata exigem todos os essenciais atendidos | Uma falha num essencial não pode ser compensada por critérios fáceis |
| Comparação | Média simples binária (% de Atende) e média simples das notas, gravadas junto | Base para a discussão sobre a média simples |

Nota gradual de cada critério:

| Critério | Classificação | Parcial vale | Origem |
|---|---|---|---|
| 1.2 | Obrigatória | 0,5 | Ponto médio, por convenção |
| 4.1 | Essencial | informações encontradas ÷ 4 | O critério pede 4 informações (número, empenhado, liquidado, pago) sem hierarquia |
| 4.6 | Essencial | 0,5 | Ponto médio, por convenção |
| 12.1 | Essencial | 1 − quadrimestres de atraso ÷ 3 (mínimo 0) | O RGF é quadrimestral; 3 de atraso equivalem a um ano sem RGF, a mesma nota de não publicar |
| 15.4 | Obrigatória | subitens comprovados ÷ 5 | O critério tem 5 subitens |
| 16.2 | Obrigatória | não existe Parcial | Ou o controle existe, ou não |

Decisões:

- **Classificação dos critérios.** O checklist do case não traz classificação. Foi adotada a lógica do PNTP: essencial é a execução orçamentária e financeira cuja falta impede transferências voluntárias (LRF, arts. 48, 48-A e 51): 4.1, 4.6 e 12.1; obrigatória é a exigência da LAI: 1.2, 15.4 e 16.2.
- **Indisponível com 0,5, Inconclusivo fora.** Site fora do ar, mesmo após as novas tentativas, é falha da entidade, mas pode ser momentânea: punição leve. Inconclusivo não prova culpa da entidade e não pode virar nota.
- **Faixas em vez de bônus por essencial.** Um bônus contaria duas vezes o que o peso já conta e poderia passar de 100.
- **Essencial Inconclusivo não bloqueia a faixa.** Essencial Parcial, Não atende ou Indisponível bloqueia Diamante, Ouro e Prata. Inconclusivo não, porque a causa não está provada; a faixa sai marcada como provisória (`*`), com o critério não verificado. Atribuir culpa sem prova é o erro mais grave num contexto de fiscalização.
- **Alinhar ao PNTP, não substituí-lo.** O PNTP é anual, preenchido pela própria entidade e validado por amostra; o sistema é automático, frequente e traz evidência de cada célula. O alinhamento de pesos e faixas dá linguagem comum com quem já usa o PNTP e permite validar contra os selos oficiais.

Problemas da média simples (§5), com o efeito medido na execução 27:

| Problema | Tratamento | Efeito |
|---|---|---|
| Todos os critérios pesam igual | Pesos por classificação | A falha de Itaboraí (1.2, obrigatória) custa menos que a de Cachoeiras (12.1, essencial) |
| É binária | Nota gradual | Cachoeiras: 66,7 pela média binária, 82,2 pela média das notas |
| Compensação | Faixa exige os essenciais | Cachoeiras, com 81,6, ficaria em Prata pelo número; fica em Elevado pelo RGF atrasado |
| Critério não avaliado distorce | Fora do cálculo, com cobertura explícita | Japeri na execução 25: 74,5 com 5 de 6; contar o Inconclusivo como 0 daria 60,3 por limitação do coletor |
| Poucos critérios separam pouco | Assumido | Rio e Caxias empatam em 100 |

Resultado da execução 27 (16/10/2026; soma dos pesos 10,5):

| Entidade | Score | Faixa | Média simples binária | Média simples das notas | O que pesou |
|---|---|---|---|---|---|
| Duque de Caxias | 100,0 | Diamante | 100,0 | 100,0 | |
| Rio de Janeiro | 100,0 | Diamante | 100,0 | 100,0 | |
| Itaboraí | 92,9 | Ouro | 83,3 | 91,7 | 1.2 Parcial (link só no submenu) |
| Cachoeiras de Macacu | 81,6 | Elevado | 66,7 | 82,2 | 12.1 Parcial (2 quadrimestres de atraso); 15.4 com 3 de 5 subitens |
| Japeri | 69,8 | Intermediário | 50,0 | 69,4 | 4.6 Parcial (último empenho de 09/10); 12.1 Parcial; 15.4 Não atende |

## 7. Tratamento de critérios não aplicáveis (§11)

| Pergunta do §11 | Tratamento |
|---|---|
| Identificar o tipo de entidade | Campo `tipo` no cadastro (prefeitura, câmara, autarquia, fundo, outro). O tipo é dado de entrada, como lista o §4, e não inferido: em fiscalização, um tipo classificado errado mudaria os critérios exigidos |
| Determinar os critérios aplicáveis | Cada critério declara `aplica_a` em `config/criterios.yaml`, gravado em `criterio_aplicabilidade`. O checklist tem matriz comum e critérios específicos; os 6 do protótipo são da matriz comum |
| Tratar não aplicáveis | Status Não aplicável, gravado sem coleta nem regra, com a justificativa |
| Não penalizar | Fora do score e fora do denominador da cobertura ("5 de 5", não "5 de 6"). `GET /entidades/{id}/criterios` mostra o que se aplica |

Teste: com a aplicabilidade do 16.2 retirada numa cópia do banco, as 5 entidades receberam Não aplicável, cobertura 5 de 5 e score sobre os 5 critérios restantes.

## 8. Tratamento de erros

| Situação | Tratamento | Status resultante |
|---|---|---|
| Falha temporária de acesso | 3 tentativas, com intervalos de 5 s e 15 s. Três falhas reais em dois dias, todas resolvidas na 2ª tentativa | Nenhum, se a nova tentativa funcionar |
| Erro exibido dentro da página com HTTP 200 | Reconhecido pelo texto ("Network error IOException", em Caxias), não só pelo código HTTP | Igual a erro de acesso |
| Site fora do ar após as tentativas, sem nenhuma fonte salva | Ocorrência gravada com tipo, data e tentativa | Indisponível |
| Página carregada, mas informação ilegível (tabela carregando, captcha, página errada) | Motivo de cada fonte no detalhe | Inconclusivo |
| API com parte das entidades sem resposta | A data vista é só um mínimo (seção 5.4) | Atende ou Inconclusivo |
| Clique sem efeito | Registrado como falha, não como sucesso | Segue a cascata |
| Captcha, login, formulário | Não contornados nem preenchidos; registrados como ocorrência | Inconclusivo quando impedem a leitura |
| PDF digitalizado | Registrado como "precisaria de OCR" | Segue com as demais fontes |
| Falha de uma etapa da execução | Etapas em processos separados: a falha de uma não derruba as outras | Execução registrada com o status de cada etapa |
| LLM sem chave ou sem resposta válida | Inconclusivo com o motivo; citação que não existe na fonte não comprova o subitem | Inconclusivo ou subitem não comprovado |

Princípio: nenhuma falha do sistema ou do acesso vira Não atende.

## 9. Estratégia de atualização

| Elemento | Como funciona |
|---|---|
| Execução completa | `python -m coletor.executar`: coleta das 4 etapas, avaliação e score num comando, cerca de 19 min para as 5 entidades |
| Repetição automática (§2) | Tarefa diária no Agendador de Tarefas do Windows, criada por `agendamento/registrar_tarefa.ps1` (horário configurável). A tarefa chama `agendamento/executar_agendado.ps1`, que roda a execução completa com `--origem agendada` e grava a saída em `dados/logs/`. Se o computador estiver desligado no horário, roda assim que ligar; limite de 2 h por execução; nunca duas execuções simultâneas no mesmo banco |
| Histórico | Cada execução acrescenta avaliações, evidências e scores; nada é sobrescrito |
| Comparação entre execuções | `GET /entidades/{id}/historico` lista cada mudança de status: de, para, melhorou ou piorou, em qual execução e data. Mudança envolvendo Inconclusivo sai como "sem comparação" |
| Mudança do sistema x mudança do portal | Cada mudança informa se as duas execuções usaram a mesma versão do código. Para comparar com justiça, as coletas antigas são reavaliadas com o código atual, sem acessar os portais |
| Mudança de endereço | Descoberta a partir do site oficial em toda execução; `entidade_urls` guarda endereços com período de validade |
| Mudança de conteúdo | Hash diferente entre execuções = arquivo mudou |
| Reprocessamento | `python -m regras.avaliar --execucao N` reaplica as regras sobre uma coleta antiga; o LLM reaproveita as respostas guardadas para entradas iguais |

Exemplo do histórico: Japeri 4.6 foi Atende na execução 16, Parcial na 19, Inconclusivo na 25 (API da Prefeitura sem resposta no tempo limite da época) e Parcial na 27 (último empenho de 09/10).

## 10. API e dashboard

### 10.1 API (§9)

`api/app.py`, com documentação interativa em `/docs`. Somente leitura; expõe só as execuções oficiais (completas, concluídas, para todas as entidades e avaliadas), para que testes parciais não apareçam no histórico.

| Endpoint | Retorna |
|---|---|
| `GET /entidades` | Entidades com score, faixa, cobertura, essenciais pendentes e nota de cada critério da avaliação mais recente |
| `GET /entidades/{id}` | Cadastro, critérios aplicáveis ao tipo da entidade e score mais recente |
| `GET /entidades/{id}/criterios` | Todos os critérios, com `aplicavel` e o status mais recente |
| `GET /entidades/{id}/avaliacao` | Avaliação mais recente: status, nota, grau de confiança, método, justificativa, URL e evidências de cada critério; score |
| `GET /entidades/{id}/historico` | Score e status por execução e lista de mudanças (de, para, melhorou ou piorou, quando, mesma versão do código) |
| `GET /criterios` | Critérios com categoria, fundamentação, tipo de verificação, classificação e peso |
| `GET /execucoes` | Execuções oficiais e o banco em uso |

Os nomes seguem os exemplos do §9, em português (`/entidades/{id}/avaliacao` corresponde a `/entities/{id}/evaluations/latest`). "Melhorou" e "piorou" seguem a ordem Não atende < Parcial < Atende, por critério, porque o §7 pergunta quais itens foram corrigidos e quando. Os arquivos de evidência não são servidos (contêm CPF de credores): a API devolve caminho, hash e trecho mascarado. O banco usado é o indicado em `GATE_BANCO`; sem ele, `dados/gate.db`; sem ele, a amostra pública `amostra/gate.db`, com CPF mascarado e sem arquivos brutos (`db/exportar_amostra.py`), para quem clona o repositório ver os resultados sem coletar.

### 10.2 Dashboard (§10)

`dashboard/app.py` (Streamlit) usa as mesmas funções da API: o que o dashboard mostra é exatamente o que a API devolve.

| Visão | Conteúdo |
|---|---|
| Visão geral | Quantidade de entidades, pontuação média, melhor e pior classificação; quantidade de avaliações por status; score por entidade; distribuição das entidades pelas faixas; matriz entidade × critério e contagem por critério |
| Por entidade | Score, faixa, cobertura; critérios não atendidos (Não atende e Parcial, com nota e motivo); desempenho por categoria, com a melhor e a pior; evolução histórica do score e do status de cada critério; evidências de cada critério com grau de confiança |
| Evolução | Score de todas as entidades por data e tabela "o que mudou e quando" |

Status aparecem com símbolo, texto e cor (a cor nunca carrega o significado sozinha). A distribuição usa as faixas, com as vazias no eixo, porque com 5 entidades um histograma de score seria pouco informativo. O desempenho de uma categoria é a média das notas dos seus critérios, já calculadas pelo score.

## 11. Uso de inteligência artificial (§15)

O LLM é usado só no 15.4. Código: `regras/llm_15_4.py`; conferência humana: `python -m regras.auditar_15_4 --execucao N`.

| Pergunta do §15 | Resposta |
|---|---|
| Qual problema a IA resolve | Verificar se a seção do e-SIC divulga 5 elementos (prazo de resposta, prazo recursal, autoridades que examinam o pedido, procedimento do pedido, procedimento do recurso) em texto livre, redigido de forma diferente em cada portal e espalhado por páginas, PDFs e infográficos |
| Por que ela é necessária | Uma regra por palavra-chave não separa "o prazo é de 20 dias" de uma citação da lei sem o prazo do município, nem reconhece uma autoridade descrita de formas diferentes ("Ouvidor Geral", "Coordenadoria de Transparência", "Dirigente Máximo"). Nos outros 5 critérios uma regra explícita é mais barata, previsível e auditável |
| Modelo ou estratégia | Claude Sonnet 5.5, raciocínio baixo, resposta em JSON com esquema fixo. Uma chamada por entidade, com as fontes já coletadas e numeradas (F1, F2...). O modelo responde por subitem, nunca "o portal está em conformidade?". Imagens são transcritas numa chamada separada, que não conhece o critério |
| Como os resultados são validados | Cada subitem que atende exige citação literal de até 300 caracteres com a fonte; o código confere se o trecho existe no texto da fonte (ignorando acento, caixa e espaço). Contra o gabarito: 18 de 20 células do 15.4 corretas nas 4 execuções; os 2 erros vieram de coleta incompleta, não do modelo |
| Como reduzir falsos positivos e falsos negativos | Falso positivo: citação inexistente não comprova; a transcrição de imagem não sabe o que procurar, então não tem motivo para "achar" um prazo. Falso negativo: 0 de 5 só é Não atende se havia página do e-SIC legível; senão Inconclusivo. Não atende sai com confiança média, para revisão |
| Como lidar com respostas inconsistentes | Esquema JSON fixo; subitens com o texto literal do checklist; prompt versionado: mudar o prompt muda a chave do cache, e o resultado fica atribuído à versão. Caso real: a auditoria da execução 25 mostrou que a 1ª versão aceitava a autoridade do recurso no subitem das autoridades; a 2ª versão corrigiu e as execuções foram reavaliadas |
| Como controlar custos | LLM só no critério semântico; textos repetidos entram uma vez; até 60 mil caracteres por fonte; respostas guardadas por hash do modelo, da versão do prompt e da entrada. Na execução 27 houve 1 chamada nova (14,7 mil tokens de entrada); as demais vieram do cache. O custo acompanha a taxa de mudança dos portais, não o número de execuções |
| Como garantir rastreabilidade | Tabela `respostas_llm`: o que foi enviado e o que voltou, com modelo, versão do prompt, execução, entidade e tokens. Cada citação vira evidência com arquivo e hash. A auditoria mostra, por subitem, a fonte e se a citação foi conferida |

Decisões de interpretação do 15.4:

| Decisão | Escolha | Por quê |
|---|---|---|
| Subitens | Os 5 elementos, nas palavras do critério; nota = comprovados ÷ 5 | Texto literal, sem adaptação |
| Autoridades | Só conta a autoridade que examina o **pedido**; a que examina apenas o recurso não basta | O critério fala em "autoridades competentes para o exame dos pedidos", e o recurso só existe depois do primeiro exame |
| Prazo recursal | Conta o prazo de resposta ao recurso ou o prazo para apresentá-lo; o detalhe grava qual foi encontrado | Leitura literal de "prazos de resposta ao cidadão, incluindo o recursal" |
| Status | 5 de 5 Atende; 1 a 4 Parcial; 0 Não atende só com página do e-SIC legível | Mesma lógica das demais regras: Não atende só com prova |
| Fontes | Páginas do e-SIC (descoberta, cadastro, detalhes), texto dos PDFs e transcrição das imagens; página "não encontrada" fica fora; CPF mascarado antes do envio | Caxias divide o 15.4 entre duas páginas e um infográfico; Itaboraí, num PDF |
| PDF linkado na seção do e-SIC | Conta como divulgação | Um decreto municipal publicado na seção é fonte formal de prazos e autoridades. Excluir PDFs de legislação exigiria separá-los dos documentos de procedimento, como o ANEXO 1 de Itaboraí, de onde vêm os 5 subitens comprovados lá |
| Plataforma federal (Fala.BR) | Entra na entrada, mas o conteúdo genérico não comprova divulgação da prefeitura | O canal existe, mas prazos, autoridades e procedimentos próprios do município não estão publicados; Japeri: 0 de 5, igual ao gabarito |
| Sem chave da API | 15.4 Inconclusivo, com o motivo; a chave fica só no `.env`, fora do Git | Quem testa o projeto não depende da chave de quem desenvolveu; as respostas da amostra pública já estão guardadas |

## 12. Limitações conhecidas

| Limitação | Efeito | Mitigação |
|---|---|---|
| Amostra pequena: 5 entidades, 6 critérios, 4 dias | Percentuais de validação com pouca precisão; baixa separação entre entidades | Ressalvas explícitas; referência externa (PNTP) |
| Gabarito feito por quem escreveu as regras | Concordância pode estar inflada | Selos do PNTP como referência independente |
| Gabarito do 4.6 conferido em um único dia | 5 células de 4.6 na concordância | Gabarito datado: só compara no dia conferido |
| Pesos do dicionário da descoberta heurísticos | Podem falhar em portais com outro vocabulário | Medidos (13 de 15 alvos sem cadastro); falha vira Inconclusivo |
| Feriados só nacionais | Feriado estadual ou municipal pode gerar Parcial falso no 4.6 | Lista fixa e documentada |
| 4.6 pela data do registro mais recente publicado | Um dia sem despesa "envelhece" a data | Prioridade ao rótulo "dados atualizados até"; Parcial pela API sai com confiança média |
| Notas 0,5 do Parcial no 1.2 e no 4.6 são convenção | Mudam o número, não a regra | Parâmetros em `config/score.yaml` |
| Classificação dos critérios inferida | Outra classificação mudaria os pesos | Lógica do PNTP, documentada |
| Sem OCR | Documento só em imagem não é lido | Ocorrência "precisaria de OCR" |
| Captcha não contornado | Consultas com captcha dependem de API | API de dados abertos do fornecedor (Caxias) |
| Sem adaptador Betha | Cachoeiras depende da descoberta genérica | Descoberta funcionou nas 4 execuções |
| Erro do servidor (HTTP 500) numa página, com o resto do site no ar, sai Inconclusivo | Falha da plataforma sem punição | Nenhum caso real até 16/10 |
| Espera fixa mínima e limites de espera | Portal muito lento pode ser lido incompleto | Vira Inconclusivo, não Não atende |
| Variação do LLM entre versões de prompt | Subitens no limite podem mudar | Cache por versão do prompt; auditoria por subitem |
| Agendamento local | Depende do computador ligado; sem alerta de falha | Roda assim que o computador ligar; log de cada execução |
| API sem autenticação e sem paginação | Inadequada para uso institucional | Somente leitura; evolução na seção 13 |

## 13. Possibilidades de evolução e escala (§8 e §17)

### 13.1 Números medidos no protótipo

| Medida | Valor |
|---|---|
| Duração de uma execução completa (5 entidades, sequencial) | cerca de 19 min |
| Duração média por entidade | cerca de 4 min |
| Artefatos por execução | cerca de 190 |
| Chamadas ao LLM sem cache | 1 avaliação por entidade + 1 transcrição por imagem |
| Tokens de entrada do LLM sem cache | cerca de 118 mil por execução, a maior parte dos PDFs do Rio |
| Cadastro mínimo de uma entidade nova | 5 campos |
| Descoberta sem cadastro de URLs | 13 de 15 alvos |

### 13.2 Projeção para 5.000 portais

| Recurso | Protótipo | 5.000 portais (estimativa) | Como resolver |
|---|---|---|---|
| Tempo de coleta | cerca de 4 min por entidade, uma por vez | cerca de 330 h por ciclo, se sequencial | 10 navegadores simultâneos fazem o ciclo em cerca de 33 h, o que cabe num ciclo mensal |
| Frequência | Tudo a cada execução | Desnecessário | Frequência por critério: 4.6 diário; 12.1 após cada prazo quadrimestral da LRF; 1.2, 15.4 e 16.2 semanal ou mensal |
| Artefatos | Pasta local | cerca de 1 milhão de arquivos por ciclo | Armazenamento de objetos com deduplicação por hash e política de retenção |
| Banco | SQLite | Escrita concorrente de vários workers | PostgreSQL com a mesma modelagem |
| LLM | 1 chamada por entidade | Proporcional às páginas que mudaram | Cache existente; processamento em lote nas execuções agendadas |
| Carga nos portais | Uma visita por vez | Risco de sobrecarregar portais pequenos | Limite de requisições por domínio e horários de menor uso |

Arquitetura de produção:

```
agendador (frequência por critério)
   │
   ▼
fila de tarefas (uma tarefa = entidade × etapa)
   │
   ▼
workers em contêiner (Playwright + adaptadores), com limite por domínio
   │                     │
   ▼                     ▼
armazenamento de      PostgreSQL (execuções, artefatos, avaliações, evidências, scores, ocorrências)
objetos (hash)            │
                          ▼
                    avaliação (regras + LLM com cache) ── API ── dashboard
                          │
                          ▼
                    fila de revisão humana (Inconclusivos, confiança média e amostra aleatória)
```

### 13.3 Os 11 pontos do §8

| Ponto | No protótipo | Em escala |
|---|---|---|
| Execução de múltiplas análises | Uma execução cobre todas as entidades, com id, data e versão do código | Uma tarefa por entidade × etapa, em paralelo |
| Processamento assíncrono | Etapas em processos separados (`coletor/executar.py`) | Workers independentes consumindo uma fila |
| Filas | Não implementadas (5 entidades, sequencial) | Fila com reentrega em caso de falha do worker |
| Controle de erros | 3 tentativas com intervalo crescente; cada falha em `ocorrencias`, com tipo | Mesma tabela, com alarme por fornecedor e por tipo de erro |
| Sites indisponíveis | Status Indisponível, distinto de Inconclusivo e de Não atende; nova tentativa na execução seguinte | Reagendamento automático da entidade |
| Páginas muito grandes | Espera com limite (até 180 s); PDFs até 15 MB, 5 por entidade; até 60 mil caracteres por fonte para o LLM | Limites por tipo de fonte, com o corte registrado |
| Limites de requisições | Uma visita por vez, identidade própria, nenhum contorno de captcha | Limite por domínio e horários de menor uso |
| Conteúdo dinâmico | Navegador real, espera por estabilização, cliques, iframes | Igual; adaptador por fornecedor quando houver API |
| Diferentes tecnologias de portal | Descoberta genérica + adaptadores GeoSiap e Webrun | Novos adaptadores, priorizados pelo número de municípios de cada fornecedor |
| Reprocessamento | `regras.avaliar --execucao N` sobre coletas antigas; respostas do LLM guardadas | Reprocessamento em lote após cada mudança de regra |
| Custos computacionais | cerca de 19 min por execução; LLM só no critério semântico, com cache | Cache, deduplicação por hash e frequência por critério |

### 13.4 Pergunta central (§17)

| Requisito | Resposta do desenho |
|---|---|
| Confiável | Não atende só com prova; Inconclusivo em vez de chute; nenhuma falha de acesso vira não conformidade; validação contínua por amostragem com as métricas de `regras/validar.py` |
| Explicável | Cada célula tem justificativa, evidência com hash, fonte e grau de confiança; cada clique da descoberta e cada resposta do LLM ficam gravados |
| Economicamente viável | Cadastro mínimo; adaptador por fornecedor; LLM só onde é necessário e com cache; reprocessamento sem nova coleta |

Sem gabarito para 5.000 portais, a qualidade passa a ser acompanhada por revisão humana contínua de uma amostra mensal de células, estratificada por nível de confiança, critério e fornecedor, com uma parte aleatória de todas as células (revisar só a confiança média nunca revelaria erro na alta). As células revisadas formam o novo gabarito, o mesmo cálculo de `regras/validar.py` atualiza o acerto de cada nível, e uma queda no acerto de um grupo (por exemplo, um fornecedor) dispara alarme. Pelo tamanho de amostra para uma proporção, n = 1,96² × p × (1 − p) ÷ margem², com acerto em torno de 90% e margem de 5 pontos são cerca de 140 células por grupo: um custo humano fixo, que não cresce na proporção do número de portais.

Riscos em escala:

| Risco | Mitigação |
|---|---|
| Mudança de layout de um fornecedor derruba muitos municípios de uma vez | Alarme por taxa de Inconclusivo por fornecedor |
| Resultado mudar por mudança do sistema, não do portal | Versão do código em cada execução e reavaliação das coletas antigas antes de comparar |
| Captcha e bloqueio de robôs | Não contornar; registrar como ocorrência; preferir a API do fornecedor; em produção, pedido institucional de acesso aos dados abertos |
| Dados pessoais em páginas de despesa | CPF mascarado nas evidências; acesso aos arquivos brutos restrito |

### 13.5 Próximos passos

| Evolução | Motivo |
|---|---|
| Orquestrador em servidor (cron ou Airflow), com alerta de falha | Execução independente de um computador pessoal |
| Fila de tarefas com workers em contêiner | Paralelismo com limite por domínio |
| PostgreSQL e armazenamento de objetos com deduplicação | Escrita concorrente e volume de artefatos |
| Levantamento dos fornecedores dos 92 municípios do RJ e adaptadores para os maiores (Betha primeiro) | Um adaptador cobre todos os clientes do fornecedor |
| Mais critérios, um tipo de verificação por vez, reaproveitando as regras-modelo | Mais separação entre entidades |
| Avaliação automática de acessibilidade (16.5, com axe-core via Playwright) | Nota contínua, que separaria entidades hoje empatadas |
| Fila de revisão humana; a revisão de um caso difícil vira cadastro e não se repete | Trabalho humano concentrado onde o sistema tem menos certeza |
| Com mais erros observados, probabilidade de acerto por célula (regressão logística sobre método, status, fornecedor e fontes concordantes), gravada na coluna numérica `confianca` | Confiança mais fina que os 2 níveis atuais |
| LLM como reserva da descoberta quando a melhor nota for baixa | Portais com vocabulário fora do dicionário |
| OCR para PDFs digitalizados; tabela de feriados por município | Fecham limitações da seção 12 |
| Extensão para Niterói e Maricá (opcional no §2) | Teste da descoberta em portais novos, só com o site oficial |
| Autenticação, paginação e filtros na API | Uso institucional |
