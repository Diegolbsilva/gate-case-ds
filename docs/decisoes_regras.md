# Decisões das regras de avaliação (13/10/2026)

Código: `regras/verificacoes.py` (uma regra por critério) e `regras/avaliar.py` (junta as fontes e grava o resultado). Testes: `regras/teste_regras.py`.

## 1. Como uma avaliação é feita

| Passo | O que acontece | Por quê |
|---|---|---|
| 1. Fontes | Para cada entidade e critério, junta o que a execução salvou: API do fornecedor, páginas da descoberta e páginas do cadastro | A coleta guarda todas as fontes; a avaliação escolhe |
| 2. Regra em cada fonte | Cada fonte responde: atende, parcial, não atende ou "não é evidência" (página errada, tabela que não carregou, captcha) | Separar "não achei" de "achei e falta" |
| 3. Melhor resultado | Fica com o melhor entre as fontes (atende > parcial > não atende); em empate, a primeira na ordem API, descoberta, cadastro | Uma página errada da descoberta não pode derrubar o que a página certa mostra (Rio: "Plano de execuções... gestão fiscal" no lugar do RGF) |
| 4. Nenhuma serviu | Inconclusivo (havia página, mas ilegível) ou Indisponível (nenhuma fonte salva e erro de acesso) | Fora do score, vai para revisão humana |

- Não acessa nenhum portal: lê só o banco e os arquivos. Pode ser rodada de novo sobre a mesma coleta quando uma regra mudar.
- Grava em `avaliacoes` o status, a justificativa e o detalhe (inclusive o resultado de cada fonte avaliada, para auditoria) e em `evidencias` o trecho lido, o arquivo e o hash. CPF é mascarado em qualquer trecho gravado.
- A nota gradual não é calculada aqui: o detalhe guarda os números (dias de atraso, quadrimestres de atraso, colunas achadas, se precisou rolar) e o score usa esses números (bloco de 15/10).
- O 15.4 fica com o LLM (bloco de 15/10).

## 2. Regra de cada critério

| Critério | Fonte | Atende | Parcial | Não atende | Não é evidência |
|---|---|---|---|---|---|
| 1.2 | 1º clique da descoberta (link do portal no site oficial) e a capa do site salva pela descoberta | Link visível na capa, 1 clique (rolar não conta, mas fica no detalhe) | Link só no submenu | Capa carregada (mais de 200 caracteres, sem captcha) e nenhum texto clicável relacionado a transparência, inclusive `alt` de imagem | Capa vazia ou com captcha (Inconclusivo); capa nem abriu (Indisponível) |
| 4.1 | API: campos de número e valores. Página: cabeçalhos da tabela (`th`, `role=columnheader`, grade Vaadin) | Número do empenho + empenhado + liquidado + pago, em colunas ou em linhas por fase (Caxias) | Número ou parte das fases | Não usado | Sem tabela de despesa legível (formulário, carregando) |
| 4.6 | API: data máxima dos registros. Página: rótulo "dados atualizados até/em", "última atualização (dos dados)", "data de atualização dos dados" | Até 1 dia útil de defasagem (decreto, ver seção 4) | De 2 dias úteis até 30 dias corridos | Mais de 30 dias | Sem data legível |
| 12.1 | API Webrun: ano e quadrimestre. Página: períodos nos títulos dos relatórios | Último publicado = último devido (prazo da LRF: 30 dias após o fim do quadrimestre) | Publicado, mas atrasado (detalhe: quadrimestres de atraso) | Página do RGF (título fala de RGF) sem nenhum relatório | Página que só cita "gestão fiscal", captcha, conteúdo em moldura |
| 16.2 | HTML completo da capa do portal | Controle de alto contraste (texto, título, aria-label, data-*) | Não existe Parcial neste critério: ou há o controle, ou não há | Capa carregada e nenhum controle | Página que não carregou |

## 3. Detalhes que evitam erro (todos vistos nos portais reais)

| Cuidado | Caso real |
|---|---|
| 4.1 lê cabeçalhos de tabela, não o texto solto | Menus como "Despesas Empenhadas" dariam falso Atende |
| 4.6 ignora rótulo cuja hora é a da visita (até 15 min da coleta) | Rodapé de Japeri: "dados atualizados em" mostra a hora do acesso |
| 4.6 ignora datas futuras e linhas de total | Caxias: "TOTAL DO MÊS (CONSOLIDADO)" com data de 31/10 |
| 4.6 conta dias úteis com feriados nacionais de 2026 (lista fixa no código) | Avaliação de 13/10: 12/10 foi feriado |
| 4.6 registra no detalhe as entidades que não responderam à API | Japeri, execução 16: a própria Prefeitura (entidade 10) não respondeu; os 13 fundos sim |
| 12.1 lê o ano junto do quadrimestre ("2º Quadrimestre / 2026"); se a página não traz, usa o último "Exercício: 2026" antes dele | Japeri agrupa por exercício; Cachoeiras tem coluna "Ano" que não é o ano do relatório |
| 12.1 só conta período com link no próprio item | Rio lista o 3º quadrimestre ainda sem link |
| 12.1 ignora tabelas escondidas | Itaboraí tem uma cópia oculta da lista, só para exportar CSV |
| 12.1 só dá Não atende em página cujo título fala de RGF, sem captcha e sem conteúdo em moldura | Rio (página errada) e Caxias (captcha) dariam falso Não atende |
| 16.2 não conta classe CSS sozinha | Folhas de estilo têm "contrast" mesmo sem botão |

## 4. Decisões (tomadas por Diego em 13/10/2026)

- **1.2, link não achado = Não atende, com duas travas.** O critério mede se o cidadão acha o portal pela capa; se nenhum texto clicável tem relação com transparência, o cidadão também não acharia. Travas: (1) a capa precisa ter carregado com conteúdo e sem captcha, senão Inconclusivo (ou Indisponível, se nem abriu); (2) o coletor lê o texto alternativo (`alt`) das imagens, para não punir banner "Portal da Transparência" feito de imagem. Para isso a descoberta passou a salvar a capa do site (`descoberta_capa_site`), que também vira a evidência visual do 1.2.
- **4.6, seguir a referência legal que o avaliador usaria.** "Tempo real" = disponibilização até o 1º dia útil seguinte à data do registro contábil (Decreto 10.540/2020, art. 7º, §1º, com o requisito do Anexo incluído pelo Decreto 11.644/2023; o Decreto 7.185/2010, que tinha a mesma regra, foi revogado pelo art. 19 do Decreto 10.540/2020). Avaliando no dia D, o registro do último dia útil antes de D ainda está no prazo (vence no próprio D); o de qualquer dia útil anterior já tem que estar publicado. Por isso: até 1 dia útil entre a data mais recente e D = Atende. Feriado não é dia útil.
- **4.6, Parcial mantido** (de 2 dias úteis a 30 dias corridos). O decreto não define parcial; o critério é próprio do sistema, para separar "atrasou alguns dias" de "parou de publicar" e dar mais informação ao score.
- **Melhor resultado entre as fontes** (seção 1, passo 3): decorre da proposta 2 aprovada em 12/10/2026.
- **4.6 pela API com entidade sem resposta (15/10/2026, opção B).** Se alguma entidade do portal não respondeu, a data máxima vista é só um mínimo: a data real é igual ou mais recente. Se o mínimo já dá Atende, Atende está provado e fica (com aviso na justificativa). Se dá Parcial ou Não atende, não está provado: a API vira "não é evidência" e a avaliação usa as outras fontes; sem nenhuma, Inconclusivo, com o motivo na justificativa. Mesma lógica de "Não atende só com prova". Caso real: execução 19, Japeri, uma entidade com 3 timeouts e data vista 08/10 (2 dias úteis em 14/10). Alternativas descartadas: manter Parcial com aviso (pune o município por falha de rede do coletor) e tentar de novo só as entidades que falharam (mais tempo, sem garantia; pode entrar depois).

## 4.0 Critério 15.4 com LLM (decisões de 15/10/2026)

Código: `regras/llm_15_4.py`, chamado por `regras/avaliar.py`. Por que LLM só aqui: o 15.4 é semântico (cada portal escreve prazos, autoridades e procedimentos de um jeito, em página, PDF ou infográfico); nos outros critérios uma regra explícita é mais barata, previsível e auditável.

| Decisão | Escolha | Por quê |
|---|---|---|
| Subitens | 5, nas palavras do critério: prazos de resposta; prazo recursal; autoridades competentes para o exame dos pedidos; procedimento do pedido; procedimento do recurso | Texto literal, sem adaptação. A nota gradual (comprovados / 5) alimenta o score |
| Autoridades (subitem 3) | Só conta a autoridade que examina o **pedido**. A que examina apenas o recurso não basta | O objetivo do critério é o cidadão conhecer o processo inteiro; o 1º exame é o passo mais básico, e o recurso só existe depois dele. Na 1ª versão do prompt (v1) a autoridade do recurso também contava, por uma explicação acrescentada sem decisão; a auditoria da execução 25 mostrou que Caxias, Itaboraí e Rio só citavam a autoridade do recurso. Corrigido na v2 |
| Prazo recursal | Conta o prazo de **resposta ao recurso** ou o prazo para **entrar** com ele; o detalhe grava qual foi achado | Leitura literal: "prazos de resposta ao cidadão, incluindo o recursal". Caso real: o infográfico de Caxias traz "em até 20 (vinte) dias úteis" para a decisão do recurso, mas não o prazo para recorrer |
| Citação | Obrigatória em cada subitem que atende: trecho literal e contínuo de até 300 caracteres, com a fonte (F1, F2...) | O código confere se o trecho existe na fonte (sem acento, caixa ou diferença de espaço). Trecho que não existe = subitem não comprovado. Protege contra resposta inventada |
| Imagem | Uma chamada separada **transcreve** a imagem, sem saber do critério; a transcrição vira fonte de texto e a citação é conferida nela | A prova fica verificável como nas páginas. A transcrição não conhece o critério, então não tem motivo para "achar" prazo; a imagem e o hash ficam guardados para conferência humana |
| Status | 5 de 5 = Atende; 1 a 4 = Parcial; 0 = Não atende só se havia página do e-SIC legível; senão Inconclusivo | Mesma lógica das outras regras: Não atende só com prova |
| Modelo | Claude Sonnet 5.5, `effort: low`, resposta em JSON com formato fixo (`output_config.format`) | Tarefa de leitura e extração. JSON fixo evita resposta fora do formato |
| Fontes | Páginas do e-SIC (descoberta, cadastro, anexos), texto dos PDFs e imagens do caminho de cliques; página "não encontrada" fica de fora; textos repetidos entram uma vez; CPF mascarado antes de enviar | Japeri: o 2º clique da descoberta cai em `informabr.cgu.gov.br/pagina-nao-encontrada` |
| Respostas guardadas | Tabela `respostas_llm`, por hash do modelo, da versão do prompt e da entrada | Reavaliar a mesma coleta não chama a API de novo (reprodutível e sem custo). É também a trilha de auditoria |
| Sem chave | 15.4 Inconclusivo, com o motivo; chave só no `.env` (fora do Git), modelo em `.env.exemplo` | Quem testa o projeto não precisa da chave de quem desenvolveu |

Decisões sobre as fontes (16/10/2026), conferidas com `python -m regras.auditar_15_4 --execucao 27`:

| Decisão | Escolha | Alternativa considerada | Por quê |
|---|---|---|---|
| PDF linkado na seção do e-SIC (ex.: Lei 12.527 e Decretos Rio 44.745/2018 e 54.226/2024) | Conta como divulgação | Excluir PDFs de legislação | O decreto municipal é a fonte formal de prazos e autoridades; publicá-lo na seção é divulgação. Excluir exigiria uma heurística para separar legislação de documento de procedimento, que poderia descartar um PDF como o ANEXO 1 de Itaboraí, origem dos 5 subitens comprovados lá. Impacto medido: nenhum, porque os 5 subitens do Rio foram comprovados em páginas (Pedido de informação e Recursos). Custo: os PDFs do Rio são a maior parte dos tokens de entrada, mas as respostas ficam guardadas pelo hash da entrada e lei raramente muda; a execução 27 fez 1 chamada nova ao modelo |
| Página genérica do Fala.BR (plataforma federal da CGU), destino do e-SIC de Japeri | Entra na entrada do LLM, mas o conteúdo genérico da plataforma não comprova divulgação da prefeitura | Tratar o Fala.BR como a seção do e-SIC de Japeri | Decisão de 12/10 (`docs/gate_descobertas.md`): o canal existe (conta para o 15.1, fora do protótipo), mas prazos, autoridades e procedimentos próprios do município não estão publicados. Na execução 27, o LLM registra que "a fonte F1 é a página geral do Fala.BR e não informa o prazo de resposta"; resultado 0 de 5, igual ao gabarito |

O detalhe grava o tipo de fonte de cada citação (página, PDF, imagem), então uma mudança nessas decisões pode ser aplicada sem chamar o LLM de novo.

## 4.0.1 Critérios não aplicáveis (§11)

| Pergunta do §11 | Tratamento |
|---|---|
| Identificar o tipo de entidade | Campo `tipo` no cadastro (`config/entidades.yaml`): prefeitura, câmara, autarquia, fundo ou outro. O tipo é dado de entrada (o §4 o lista entre as entradas), não inferido: em fiscalização, classificar errado o tipo mudaria os critérios exigidos |
| Determinar os critérios aplicáveis | Cada critério declara `aplica_a` em `config/criterios.yaml`, gravado na tabela `criterio_aplicabilidade`. O checklist do case tem matriz comum (vale para todos) e critérios específicos; os 6 do protótipo são da matriz comum |
| Tratar critérios não aplicáveis | `regras/avaliar.py` grava o status Não aplicável, sem coleta nem regra, com a justificativa (tipo da entidade e origem da regra de aplicabilidade) |
| Não penalizar a entidade | Não aplicável fica fora do score e fora do denominador da cobertura ("5 de 5", não "5 de 6"). `GET /entidades/{id}/criterios` mostra o que se aplica e o que não se aplica |

Teste: retirada a aplicabilidade do 16.2 para prefeituras numa cópia do banco, as 5 entidades receberam Não aplicável no 16.2, com cobertura 5 de 5 e score calculado sobre os 5 critérios restantes.

## 4.0.2 Grau de confiança (§4, decisões de 16/10/2026)

O §4 pede, na saída de cada critério, o "grau de confiança da avaliação, quando aplicável", com o exemplo "Confiança: 92%". O enunciado não exige probabilidade; o exemplo é ilustrativo.

| Decisão | Escolha | Alternativas consideradas | Por quê |
|---|---|---|---|
| O que é o grau | Nível ordinal (alta ou média) pela natureza da evidência, acompanhado do % de acerto observado nesse nível na validação | % de acerto por critério; confiança declarada pelo LLM; concordância entre duas fontes | Por critério há cerca de 13 células com gabarito, amostra pequena para um % por critério. A confiança declarada por LLM não é calibrada e só cobriria o 15.4. Duas fontes por critério dobrariam a coleta, e nem todo critério tem duas. Agregado por nível, o % tem amostra maior e é medido, não estimado |
| Regra do nível | **Alta**: o que foi lido prova o veredito (Atende com trecho conferido; 4.6 com a data lida no rótulo da página; Indisponível com os erros de acesso registrados). **Média**: o veredito depende de ausência (Não atende; Parcial por falta de item, subitem ou período) ou de valor inferido (4.6 Parcial pela data máxima dos registros da API, que pode refletir apenas um dia sem despesa) | Um nível por critério, fixo | A presença de uma informação se prova com um trecho; a ausência depende de o sistema ter procurado no lugar certo. A regra é a mesma para os 6 critérios (`regras/verificacoes.py`, `nivel_confianca`) |
| Inconclusivo e Não aplicável | Sem nível (vazio) | "Baixa" | Não há veredito a qualificar. "Baixa" sugeriria um veredito fraco. Corresponde ao "quando aplicável" do §4 |
| Entra no score? | Não | Ponderar a nota pela confiança (o §5 cita essa possibilidade) | A confiança mede o sistema, não o portal. Ponderar a nota puniria ou favoreceria a entidade por um limite do método, o mesmo princípio aplicado ao Inconclusivo. A confiança orienta a revisão humana: em escala (§17), os vereditos de confiança média formam a fila de conferência |
| Armazenamento | Coluna `nivel_confianca` (texto) em `avaliacoes`; a coluna numérica `confianca` fica reservada para uma probabilidade calibrada | Converter em número (alta = 1,0; média = 0,5); guardar no `detalhe_json` | Um número arbitrário pareceria probabilidade sem ser. No JSON, a API e o dashboard teriam que abrir o detalhe. Bancos anteriores recebem a coluna por migração (`coletor/banco.py`) |
| % observado | `python -m regras.validar --execucoes ... --gravar-confianca` grava o acerto por nível em `config/confianca_observada.yaml`; a API e o dashboard o mostram ao lado do nível | Recalcular a cada consulta | O arquivo versionado registra de quais execuções o número saiu (reprodutível). O nível é recalculado pela mesma regra nas execuções avaliadas antes da coluna existir |

Saída de um critério na API (`GET /entidades/{id}/avaliacao`): `"confianca": {"nivel": "alta", "acerto_observado": 1.0, "base": "N de N celulas corretas nesse nivel na validacao (execucoes ...)"}`.

Resultado (execuções 16, 19, 25 e 27): confiança alta, 80 de 80 células conclusivas corretas (100%); média, 20 de 22 (91%). Os 2 erros (Caxias 15.4 nas execuções 16 e 19, coleta ainda incompleta) caíram no nível médio. Detalhe em `docs/validacao.md`, seção 5.

Evolução: com mais execuções e gabarito, o % por nível pode virar uma probabilidade calibrada por critério e método, gravada na coluna numérica.

## 4.1 Limitações e melhorias futuras

| Limitação | Efeito | Melhoria futura |
|---|---|---|
| Só feriados nacionais na conta de dias úteis | Feriado estadual ou municipal (ex.: São Jorge, 23/04, no RJ) conta como dia útil e pode gerar Parcial falso no 4.6 | Tabela de feriados por município e ano |
| O sistema vê a data do registro mais recente publicado, não a data do registro contábil | Dia sem nenhum empenho "envelhece" a data sem descumprimento; risco maior em entidade pequena ou quando só parte das entidades responde à API | Preferir o rótulo "dados atualizados até" (já é a prioridade quando existe); usar datas de liquidação e pagamento também |
| 1.2 sem faixa de "texto fraco" | Link com nome distante de transparência (ex.: só "Acesso à Informação") dá Não atende mesmo se levar ao portal | Termos fracos no dicionário; se o clique leva ao portal, Parcial (acesso indireto) |

## 5. Resultado na execução oficial de 13/10/2026 (execução 16)

24 de 25 células iguais ao gabarito (15.4 fica para o LLM). A diferença:

- Rio 4.1: Inconclusivo, gabarito Atende. A tabela do Contas Rio ainda carregava depois de 90 s. É limite da coleta, não da regra: a mesma regra aplicada ao HTML da execução 12 (tabela carregada) dá Atende. Correção: espera pelo indicador de carregamento subiu para 180 s.

Com as decisões finais de 13/10 (1.2 e 4.6 acima) o resultado na execução 16 é o mesmo: 24 de 25.

## 6. Resultado na execução oficial de 14/10/2026 (execução 19)

23 de 25. As diferenças:

- Japeri 4.6: Parcial, gabarito Atende. Uma entidade não respondeu à API (3 timeouts). Levou à decisão de 15/10 (seção 4): com a regra nova, vira Inconclusivo. O gabarito do 4.6 depende do dia e passa a ser gravado com data.
- Rio 4.1: Inconclusivo. A execução rodou com a espera antiga (90 s); a tabela de empenhos ainda mostrava o spinner. O próprio portal recomenda usar pelo menos 2 filtros além de mês e ano, porque a consulta do ano inteiro é pesada.

## 7. Resultado na execução oficial de 15/10/2026 (execução 25, código `28e059e`)

24 de 25, com o gabarito do 4.6 conferido à mão no próprio dia (as 5 entidades, registrado em `config/gabarito.yaml`). Nas células conclusivas: 24 de 24. Inconclusivas: 1 de 25.

- Rio 4.1: Atende. Primeira execução oficial com a espera de 180 s; a tabela de empenhos carregou.
- Japeri 4.6: Inconclusivo, gabarito Parcial (último empenho da Prefeitura em 09/10). A Prefeitura não respondeu à API (é a 3ª execução seguida: 16, 19 e 25), e a data vista sem ela (08/10) não prova atraso (decisão B). O sistema não errou o veredito; deixou de dar um. A falha da API da Prefeitura é sistemática, não ocasional: provável tempo limite curto para a consulta dela (o portal avisa que, sem descrição, "a pesquisa será mais lenta"). Correção (15/10): tempo limite das APIs de 90 s para 180 s (`TEMPO_LIMITE_API_S` em `coletor/fornecedores.py`). Teste só da etapa de APIs (execução 26): 14 de 14 entidades responderam, 143 registros, data máxima 09/10/2026, igual à conferência manual (empenho nº 925 da Prefeitura).
- O que a conferência de 15/10 mostra sobre 14/10: o sistema deu Parcial (data vista 08/10, sem a Prefeitura), mas a Prefeitura tem empenho de 09/10. Se ele já estava publicado em 14/10, o certo era Atende. É o tipo de erro que a decisão B evita.

Testes: 31 casos pequenos montados a partir dos portais reais, todos ok (`python -m regras.teste_regras`).
