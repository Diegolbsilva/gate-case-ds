# Decisões técnicas do coletor

Explica cada escolha feita no código do coletor (pasta `coletor/`): o que faz, por que, quais eram as alternativas e como defender. Atualizado em 12/10/2026.

## 1. Visão geral: o caminho em cascata

Para cada prefeitura, o sistema tenta, nesta ordem:

| Passo | O que faz | Arquivo |
|---|---|---|
| 1. Capas | Abre o site oficial e o portal, salva HTML e print | `capas.py` |
| 2. Descoberta | Partindo só do site oficial, acha o portal e, dentro dele, as páginas de despesa, RGF e e-SIC | `descobrir.py`, `descoberta.py` |
| 3. Fornecedor | Reconhece o fornecedor do portal; se houver adaptador, coleta pela API | `apis.py`, `fornecedores.py` |
| 4. Reserva | Se a descoberta falha, usa o endereço do cadastro manual | `config/entidades.yaml` |
| 5. Inconclusivo | Se nada funciona, o critério fica Inconclusivo (fora do score, vai para revisão humana) | regras (13/10) |

**Por que assim:** o enunciado pergunta se a solução funcionaria para 5.000 portais (§17). Um código por prefeitura não escala. Código por **fornecedor** escala, porque cada fornecedor atende muitos municípios. Para quem não tem fornecedor conhecido, a descoberta genérica funciona em qualquer portal. O cadastro manual fica só como reserva e como gabarito para medir a descoberta.

**Como defender:** "O cadastro de cada prefeitura só precisa do site oficial. Todo o resto o sistema descobre ou resolve pelo adaptador do fornecedor. Cada resultado registra por qual caminho foi obtido, então dá para medir quanto depende de configuração manual."

## 2. Abrir uma página (`navegador.py`, função `abrir_pagina`)

| Decisão | Por quê | Alternativa descartada |
|---|---|---|
| **Playwright** (navegador de verdade, controlado por código) | 3 dos 5 portais montam o conteúdo com JavaScript (Betha, GeoSiap, Caxias). Uma requisição simples recebe a página vazia | `requests` + leitura do HTML: mais leve, mas não vê o conteúdo montado. Continua sendo usado nas APIs, onde basta |
| **Janela fixa de 1366x768** | O 1.2 mede se o link do portal precisa de rolagem. Isso depende do tamanho da tela: sem tamanho fixo, o resultado não é reproduzível | Tamanho padrão do navegador: varia entre máquinas |
| **Identidade honesta** (User-Agent "GATE-MPRJ-Prototipo/0.1" com o link do repositório) | A Betha bloqueia o navegador automatizado padrão (403). Com identidade própria, libera. O site sabe quem acessa | Fingir ser um Chrome comum: funciona, mas não é postura adequada para um órgão de controle |
| **Espera de 3 segundos** depois de carregar | Tempo para o JavaScript montar a página. Valor prático: suficiente nos 5 portais | Esperar "rede parada" (networkidle): em portais com chamadas contínuas, a espera nunca termina |
| **3 tentativas, com intervalos de 5 s e 15 s** | Vimos 3 falhas temporárias reais em 2 dias (Caxias 2x, Itaboraí 1x), todas resolvidas na segunda tentativa. O intervalo crescente evita martelar um servidor com problema | Uma tentativa só: transformaria falha temporária em Indisponível. Tentativas sem intervalo: sobrecarregam o servidor |
| **Erro reconhecido pelo código HTTP e pelo texto da página** | Caxias mostra o erro dentro de uma janela com HTTP 200 ("Network error IOException"). Só o código HTTP não pegaria | Só o código HTTP: falso "ok" em Caxias |
| **Tipos de falha:** erro_http, erro_servidor, bloqueio, timeout | Cada tipo tem tratamento diferente na doc e no dashboard (bloqueio pede contato com o fornecedor; erro_servidor, nova tentativa) | Um tipo genérico "erro": perde a informação |

**Como defender:** "Nenhuma falha do site vira Não atende. Ela é registrada com data, hora, tipo e número da tentativa, e o critério fica Indisponível até a próxima execução."

## 3. Guardar o que foi visto (`navegador.py`, função `salvar_pagina`)

| Decisão | Por quê |
|---|---|
| **HTML depois do JavaScript** (e não o HTML bruto do servidor) | É o que o visitante vê. O HTML bruto da Betha vem quase vazio |
| **Print da página inteira** | Evidência que um humano confere sem rodar nada (§6). Mostra até o pop-up que o visitante vê |
| **HTML de cada iframe salvo à parte** | Em Caxias, as consultas ficam dentro de um iframe. O HTML da página principal não inclui o conteúdo do iframe |
| **Hash SHA-256 de cada arquivo** | Uma "impressão digital": se o hash mudou entre duas execuções, a página mudou (§7). Também detecta o mesmo arquivo publicado em períodos diferentes (caso real: RGF de Japeri) |
| **Coletar separado de avaliar** (tabela `artefatos`) | As regras rodam sobre o que foi baixado. Se uma regra mudar, dá para reavaliar sem acessar os portais de novo (§8: reprocessamento e custo) |

## 4. Descoberta automática (`descoberta.py` e `descobrir.py`)

### 4.1 Por que procurar textos, e não só links

| Portal | Como o menu aparece |
|---|---|
| Itaboraí, Rio | Links comuns, com endereço |
| Caxias | Links sem endereço ("#"), abertos por JavaScript |
| Cachoeiras (Betha) | Itens sem endereço, abertos por JavaScript |
| Japeri (GeoSiap) | Nenhum link: blocos clicáveis do Angular (a página tem só 5 links) |

Procurar só links falharia em 3 dos 5. Por isso a descoberta lista **todos os textos de elementos clicáveis** (links, botões, itens de lista, blocos com evento de clique), guarda o **caminho CSS** de cada um (o "endereço" do elemento dentro da página) e, ao vivo, clica no elemento quando não há link.

### 4.2 Como o sistema escolhe onde clicar: a nota

Cada alvo tem uma lista de termos com peso. A nota de um texto é a soma dos pesos dos termos que ele contém, menos 6 pontos por termo que indica recorte ou outro assunto.

**De onde vêm os termos:** do próprio texto do checklist (ex.: 4.1 fala em "empenho, liquidação e pagamento"; 12.1 em "Relatório de Gestão Fiscal") e de sinônimos que aparecem nos portais ("despesas detalhadas", "execução orçamentária", "e-SIC").

**Como os pesos foram definidos:** frases específicas valem mais que palavras genéricas. "Execução detalhada de despesas" (10) é mais forte que "despesas" (6). "RGF" (10) é mais forte que "relatórios" (2). São pesos **heurísticos**, definidos por critério, e não ajustados estatisticamente.

| Alvo | Termos fortes (peso alto) | Termos fracos | Termos que tiram pontos |
|---|---|---|---|
| Portal | "portal da transparência" (10) | "transparência" (5) | radar, TCE, saúde, câmara, diário, ouvidoria |
| Despesa | "execução detalhada de despesas", "despesas detalhadas" (10) | "despesas" (6), "empenho" (6), "execução orçamentária" (5) | multa, trânsito, pessoal, diária, educação, emenda, receita |
| RGF | "relatório de gestão fiscal", "RGF" (10) | "LRF" (5), "prestação de contas" (4), "relatórios" (2) | RREO, balanço, opcionais |
| e-SIC | "prazos de respostas do SIC" (10), "e-SIC", "pedido de informação" (8) | "acesso à informação" (6), "ouvidoria" (2) | LGPD, estatística, sigilo |

**Regras de escolha:**
- Clica no texto de **maior nota**. Em empate, no **mais curto** (texto curto costuma ser o item do menu; texto longo costuma ser um bloco com várias coisas).
- Nota zero ou negativa: não clica e registra "não achado".
- **Só clica no que uma pessoa conseguiria clicar:** elemento visível na tela, ou elemento com endereço (aí o coletor abre o endereço, que é equivalente). Elemento escondido e sem endereço fica de fora. **Erro real que motivou a regra:** a Betha tem um menu lateral fechado com "Execução Detalhada de Despesas". O robô forçava o clique nesse item escondido, nada acontecia, e o registro dizia sucesso. Os prints de antes e depois eram idênticos.
- **Clique sem efeito é falha:** se o endereço e o texto da tela são os mesmos antes e depois do clique, o coletor registra "sem_efeito" e não sucesso.
- **Imagem conta como texto (13/10/2026):** o rótulo de cada elemento clicável inclui o texto alternativo (`alt`) das imagens dentro dele. Banner "Portal da Transparência" feito só de imagem é achado; sem `alt`, nem o robô nem um leitor de tela o identificam, e o 1.2 dá Não atende.
- **Capa do site salva (13/10/2026):** a descoberta salva a capa do site oficial (`descoberta_capa_site`, HTML e print) antes de procurar o link. É a evidência do 1.2 e a trava do Não atende: só vale se a capa carregou com conteúdo.
- **Botão genérico ganha contexto:** "ACESSAR", "Saiba mais" e "Clique aqui" não dizem para onde vão. O rótulo passa a incluir os títulos do card ao redor (ex.: "ACESSAR (Despesas públicas Despesas realizadas pelo município.)"). É genérico: vale para qualquer portal com cards, não só para a Betha. Resultado (execução 6): em Cachoeiras, despesa e RGF passaram a ser achados em 2 cliques (card > consulta), chegando na mesma consulta do gabarito manual.
- **Até 2 cliques.** O segundo clique só acontece se as duas condições valerem (decidido em 12/10/2026, depois da primeira execução real):
  - o texto tem **nota 6 ou mais**, para não clicar em algo pouco relacionado;
  - o texto foi **revelado pelo primeiro clique**: não estava visível antes dele (um submenu que abriu, uma página nova ou um modal). Um item que já estava na tela antes é **irmão no menu**, não um passo mais fundo. Texto já clicado nunca é clicado de novo, comparando pelo texto e pelo rótulo (texto + title + aria-label).
  - **Erros reais que motivaram a regra:** em Cachoeiras, o robô foi de "Execução Detalhada de Despesas" para o irmão "... - Educação". Em Caxias, clicou duas vezes em "Pedido de Informação (SIC e e-SIC)", porque o title repetia o texto e o filtro comparava campos diferentes. Os dois erros foram reproduzidos num site simulado: a versão antiga repete os dois, e a nova corrige os dois sem perder o submenu revelado (Caxias: "Prestação de Contas" > "Relatório de Gestão Fiscal").
- **Nenhum termo específico de município.** Exemplo real: no Rio, as despesas ficam em "CONTAS RIO", sem a palavra despesa. A descoberta erra, e o sistema usa o cadastro como reserva. Acrescentar "contas rio" ao dicionário seria ajustar a regra a um município, exatamente o que não escala.

**Resultado medido:**
- Nas 10 capas salvas (HTML estático), o primeiro clique foi certo em **19 de 20 alvos**.
- Na primeira execução real (navegador, execução 3), o primeiro clique foi certo em **18 de 20**: o Rio despesa não foi achado, e o Rio RGF foi para uma página errada, "Plano de execuções orçamentária e de gestão fiscal". O RGF do Rio fica em controladoria.prefeitura.rio.
- Os erros da descoberta não viram nota: ver 4.5.

**Como defender:** "A escolha é transparente e auditável: cada clique fica gravado com o texto e a nota (tabela `descobertas`), e qualquer pessoa reconstrói por que o sistema clicou ali. Os pesos são heurísticos, mas foram medidos contra o gabarito manual."

**Alternativas discutidas:**

| Alternativa | Por que não agora |
|---|---|
| Modelo de aprendizado de máquina para classificar links | Precisa de muitos exemplos rotulados. Temos 5 portais |
| LLM escolhendo onde clicar | Custo por página, respostas que variam entre execuções, difícil de auditar. Faz sentido como **reserva** quando a melhor nota for baixa (evolução na doc) |
| Crawler completo do site | Caro, lento, e acessa muitas páginas desnecessárias de um órgão público |

### 4.3 O que a descoberta mede para o 1.2

No clique do site para o portal, o sistema registra:
- **visível sem interação:** o link aparece sem passar o mouse? Um "não" indica submenu, ou seja, Parcial (caso de Itaboraí);
- **precisou rolar:** o link está abaixo da primeira tela (janela de 1366x768)? É o desempate que você definiu (caso de Caxias).

### 4.4 Detalhes de execução

| Decisão | Por quê |
|---|---|
| Fecha pop-ups antes de procurar (tecla Esc e botões "fechar" comuns) | Caxias e Itaboraí têm pop-up na capa, cobrindo os cliques |
| Item escondido em submenu: dispara o clique direto no elemento, sem abrir o menu | O item existe na página, só não está visível. Abrir o menu com o mouse varia de site para site |
| Nova aba: detectada e seguida | Vários links do site abrem o portal em nova aba (Caxias, Rio) |
| Procura também dentro de iframes | Menu de Caxias |

### 4.5 Erro da descoberta nunca vira Não atende (decidido em 12/10/2026)

A descoberta pode trazer a página errada (Rio RGF) ou nenhuma (Rio despesa). Por isso a avaliação não confia na página de olhos fechados. Para cada critério, ela procura a evidência nesta ordem:

1. Na página final do caminho da descoberta.
2. Nas outras páginas do mesmo caminho (às vezes o robô foi um clique além do necessário).
3. Na URL do cadastro, se existir.

| Resultado da busca | Status |
|---|---|
| Achou a evidência | Atende ou Parcial, registrando onde achou (descoberta ou cadastro) |
| Achou a página certa, e falta algo nela (ex.: Japeri 15.4: página do e-SIC sem prazos) | Não atende, porque há prova da ausência |
| Não achou a página certa em lugar nenhum | **Inconclusivo** (não localizado automaticamente): fora do score, entra como cobertura e vai para revisão humana |

**Prefeitura nova, sem cadastro:** o passo 3 não existe, então o caso do Rio daria Inconclusivo, e não um Não atende falso. Na revisão humana, a pessoa acha a página uma vez e anota no cadastro. Nas execuções seguintes, a prefeitura passa a ser avaliada sozinha. O trabalho manual acontece uma vez por caso difícil, e o sistema mede quanto foi automático.

**Como defender:** "O sistema só diz Não atende quando tem prova da ausência. Quando não localiza a página, diz Inconclusivo e manda para revisão humana. A revisão vira cadastro e não se repete."

## 5. Fornecedor e API (`fornecedores.py` e `apis.py`)

### 5.1 Como reconhecer o fornecedor

| Fornecedor | Assinatura | Por que essa |
|---|---|---|
| GeoSiap | Domínio `.geosiap.net.br` ou "geosiap"/"embras" no HTML | Padrão de domínio de todos os clientes |
| Betha | Domínio `betha.cloud` ou "Betha Sistemas" no HTML | Idem |
| Plataforma Webrun (Modernização, Caxias) | Links "/webrun/form.jsp?sys=LAI" no HTML | O nome do fornecedor não aparece em texto (o logo é imagem). A assinatura **estrutural** da plataforma é mais confiável e vale para todos os clientes dela |
| Supernova | Links para `supernova.com.br` | Subsistema de consultas (Itaboraí) |

A detecção é gravada com a **evidência** (ex.: "domínio do portal: japeri.geosiap.net.br"), para que um humano confira por que o sistema decidiu.

### 5.2 Adaptadores

| Adaptador | O que faz | Decisões |
|---|---|---|
| GeoSiap | Lista as entidades do portal, exclui a Câmara e baixa as despesas dos **últimos 30 dias** de cada entidade | **Câmara excluída pelo nome** ("câmara", "legislativo"), e não pelo id: funciona em qualquer município GeoSiap. **30 dias:** basta para o 4.1 (existe empenho com número e valores?) e o 4.6 (data mais recente), sem baixar o ano inteiro. Usa `data_inicial` e `data_final`, porque o parâmetro `ano` não respondeu no teste |
| Webrun | Chama o endpoint único com o serviço (`despesas_todas`, `consulta_rgf_m2`) e o ano | O método HTTP não está documentado. O adaptador **testa** POST com JSON, POST com formulário e GET, nessa ordem, e **registra qual funcionou** |
| Betha | Ainda sem adaptador: a descoberta genérica resolve | Pendente: confirmar se o número das consultas é igual em todos os municípios Betha |

**Como defender:** "Cada adaptador é escrito uma vez e serve para todos os municípios daquele fornecedor. A flag no cadastro existe só como exceção, para forçar um caminho quando a detecção errar."

## 5.2.1 Prefeitura nova: o que precisa no cadastro

Toda prefeitura precisa de uma entrada no `config/entidades.yaml`: é a lista de quem o sistema avalia. O mínimo são 5 campos:

```yaml
  - id: niteroi
    nome: "Prefeitura Municipal de Niterói"
    municipio: "Niterói"
    tipo: prefeitura
    site_oficial: "https://www.niteroi.rj.gov.br/"
```

Com isso, a descoberta acha o portal e as páginas sozinha, e as APIs reconhecem o fornecedor. Os demais campos são opcionais e só servem de reserva: `portal`, `dominios_permitidos` e `criterios` (URLs por critério). Sem portal achado e sem portal anotado, a descoberta registra a falha e segue para a próxima prefeitura; os critérios ficam Inconclusivos, sem erro. O campo `portal` passou a ser opcional em 13/10/2026 (antes o código exigia).

## 5.3 Páginas do cadastro (`cadastro.py` e `config/criterios.yaml`)

**O que faz:** para cada prefeitura, abre as URLs anotadas por critério no `entidades.yaml` e salva HTML e print, ligados ao critério no banco (`artefatos.criterio_id`).

**Por que existe:** é o passo 3 da avaliação em cascata (4.5). Quando a página da descoberta não tem a evidência, a regra procura aqui antes de concluir. Também cobre o que a descoberta não procura (16.2, segunda página do 15.4) e serve de gabarito para medir a descoberta.

**Regras:**

| Situação no cadastro | O que o programa faz | Por quê |
|---|---|---|
| Método `api` | Não coleta aqui | O `apis.py` já coleta pelo adaptador do fornecedor |
| URL | Abre, fecha pop-ups, salva HTML e print | Evidência guardada com hash, como as demais |
| Caminho descrito em texto (ex.: Caxias 15.4, "Portal > Pedido de Informação > ...") | Não coleta e avisa | Não há endereço: a página só existe navegando (Webrun não muda a URL). A evidência vem da descoberta |
| Mesma URL em vários critérios (ex.: capa do portal no 16.2) | Abre uma vez e liga o arquivo a cada critério | Menos acessos ao portal público, mesmo arquivo e mesmo hash |
| `{ano}` na URL | Vira o ano corrente | Exercício avaliado |
| Página fora do ar | 3 tentativas, depois Indisponível registrado | Mesma regra das demais coletas |

- **Espera de 6 s para o JavaScript** (o padrão é 3 s): Contas Rio e Betha são sistemas inteiros em JavaScript e demoram mais para montar a tela.
- **Pesquisa (decidido em 12/10/2026, depois da execução 8):** em consulta de dados (4.1, 4.6 e 12.1), se houver um botão visível "Pesquisar", "Consultar" ou "Buscar", o coletor clica uma vez e salva também o resultado (`_pesquisa`). Antes, se houver um seletor de mês vazio, escolhe o mês corrente. **Nunca clica** se a página tiver reCAPTCHA, nunca em página do e-SIC (15.4, para não enviar formulário) e não faz download. **Motivo:** em Japeri (RGF, GeoSiap) e Itaboraí (despesas, Supernova) a tabela só aparece depois do Pesquisar. Em Japeri a entidade já vem selecionada como Prefeitura (valor 10); em Itaboraí o mês é obrigatório. A regra é genérica (texto do botão e seletor com os 12 meses), não depende do fornecedor.
- **Espera até a tela estabilizar** (vale para todas as coletas, em `abrir_pagina`): depois da espera mínima, o coletor relê o texto da tela a cada 1,5 s e só segue quando ele tem pelo menos 200 caracteres e não mudou entre duas leituras, até 30 s. **Motivo:** na execução 8 o Contas Rio (Vaadin) ainda mostrava só o ícone de carregando depois de 6 s. Espera fixa maior atrasaria todas as páginas; esta só espera o necessário.
  - **Ajuste depois da execução 9:** texto parado não basta. No Contas Rio a tela montou, mas a tabela de empenhos ficou com um ícone de carregando enquanto o texto ao redor já estava parado, e a página foi salva sem a tabela. Na tela do Diego, a tabela aparece sozinha depois de algum tempo (223.030 registros, os 12 meses de 2026). Agora o coletor também espera **não haver indicador de carregamento visível** (elemento com classe "spinner", "loading" ou "loader", ou `aria-busy`). Limites: 30 s se nada indica carregamento; até 90 s enquanto houver um carregando visível. Testado em site simulado com tabela que aparece depois de 20 s de spinner: salva com a tabela.
  - **Risco conhecido:** um site com um elemento "loading" visível permanente faz cada página esperar 90 s. Fica registrado no tempo da execução, sem errar o resultado.
- **Limite:** se a mesma URL serve a dois critérios e o primeiro não é de consulta, a pesquisa não acontece no segundo. Não ocorre no cadastro atual.
- **`config/criterios.yaml`:** os 6 critérios com o texto do checklist (código, categoria, descrição, fundamentação, tipo de verificação, a quem se aplica). O programa grava no banco na primeira execução. O peso de cada critério fica para a metodologia do score.

## 6. Banco (`banco.py` e `db/schema.sql`)

| Decisão | Por quê |
|---|---|
| Tabela `artefatos` | Registra tudo o que foi baixado. Base do reprocessamento |
| Tabela `descobertas` | Registra cada clique da descoberta. Base da auditoria e da métrica "achou sozinho X de 30" |
| `CREATE TABLE IF NOT EXISTS` | O banco existente ganha as tabelas novas sem perder as execuções anteriores |
| Versão do código (commit do Git) gravada em cada execução | Separa "o portal mudou" de "o código mudou" |

## 7. Limitações conhecidas (para a seção da doc)

- Pesos do dicionário heurísticos, medidos em 5 portais. Em escala, precisam ser recalibrados com uma amostra maior de gabarito.
- A descoberta acha a página, mas não passa por captcha, não abre modal com anexo nem faz OCR. Isso fica com os adaptadores, ou o critério vira Inconclusivo.
- A espera de 3 s para o JavaScript é fixa. Um portal muito lento pode ser lido incompleto.
- O fechamento de pop-ups cobre os padrões comuns, e não qualquer pop-up.
- Adaptador Webrun confirmado na execução real de 12/10/2026 (POST JSON). Outros clientes da Modernização ainda não foram testados.
- No Japeri, o 2º clique do e-SIC entra na página de novo pedido do Fala.BR. O robô não preenche nada, mas a página é desnecessária para a avaliação.

## 8. Perguntas que o avaliador pode fazer

| Pergunta | Resposta curta |
|---|---|
| "Isso funciona para 5.000 portais?" | O cadastro precisa só do site oficial. A descoberta é genérica, e os adaptadores são por fornecedor. O que não for resolvido vira Inconclusivo, sem falso Não atende. Cada resultado registra o caminho usado, e isso mede a dependência de configuração manual |
| "Por que não usou IA para navegar?" | Custo, variação entre execuções e auditoria. As regras são transparentes e foram medidas (18 de 20 na execução real; os 2 erros não afetam o score por causa da 4.5). A IA entra onde agrega: interpretação do 15.4 e, como evolução, reserva quando a descoberta tem nota baixa |
| "Como sabe que acertou?" | Comparando com o gabarito manual das 30 células e o caminho da descoberta com o cadastro |
| "E se o site estiver fora do ar?" | 3 tentativas com intervalo crescente. Persistindo, Indisponível com o erro registrado; não entra no score e é tentado de novo na próxima execução |
| "Por que os pesos são esses?" | Frases específicas do checklist pesam mais que palavras genéricas, e termos de recorte tiram pontos. São heurísticos, documentados e medidos. Em escala, seriam recalibrados com mais gabarito |
