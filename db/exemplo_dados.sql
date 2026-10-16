-- Dados de teste do esquema: SO dados reais da exploracao manual (docs/exploracao_portais.md).
-- Execucao 1 = exploracao de 09/10/2026 (parcial); execucao 2 = gabarito completo de 10/10/2026.
-- Notas graduais e pesos ainda nao definidos (metodologia do score em 15/10): ficam NULL / 1.0.

INSERT INTO entidades (id, nome, municipio, tipo, fornecedor) VALUES
 ('japeri', 'Prefeitura Municipal de Japeri', 'Japeri', 'prefeitura', 'GeoSiap / Grupo Embras'),
 ('duque_de_caxias', 'Prefeitura Municipal de Duque de Caxias', 'Duque de Caxias', 'prefeitura', 'Modernização Informática'),
 ('itaborai', 'Prefeitura Municipal de Itaboraí', 'Itaboraí', 'prefeitura', 'Próprio (SEMFAT) + Supernova'),
 ('cachoeiras_de_macacu', 'Prefeitura Municipal de Cachoeiras de Macacu', 'Cachoeiras de Macacu', 'prefeitura', 'Betha Sistemas'),
 ('rio_de_janeiro', 'Prefeitura da Cidade do Rio de Janeiro', 'Rio de Janeiro', 'prefeitura', 'Próprio');

INSERT INTO entidade_urls (entidade_id, papel, url, valido_desde, valido_ate, observacao) VALUES
 ('japeri', 'portal', 'https://japeri.geosiap.net.br/portal-transparencia/home', '2026-10-09', NULL, NULL),
 ('itaborai', 'portal', 'https://transparencianovo.ib.itaborai.rj.gov.br/', '2026-10-09', NULL, 'subdominio sugere portal anterior, endereco antigo desconhecido'),
 ('itaborai', 'sistema', 'https://itaborai.supernova.com.br:8443/contaspublicas/despesa.xhtml?exercicio={ano}', '2026-10-10', NULL, 'despesas');

INSERT INTO criterios (id, codigo, versao_checklist, categoria, descricao, fundamentacao, matriz, tipo_verificacao) VALUES
 (1, '1.2',  'v1-2026-10', 'INFORMAÇÕES PRIORITÁRIAS', 'O acesso ao portal transparência está visível na capa do site?', 'Art. 8º, caput da LAI', 'comum', 'navegacao'),
 (2, '4.1',  'v1-2026-10', 'DESPESA', 'Número e o valor de empenho, liquidação e pagamento', 'Arts. 7º, VI e 8º, §1º, inciso III, da LAI', 'comum', 'dados_estruturados'),
 (3, '4.6',  'v1-2026-10', 'DESPESA', 'Existência de informações atualizadas em relação aos critérios da despesa', 'Art. 8º, §3º, inciso VI, da LAI', 'comum', 'atualizacao'),
 (4, '12.1', 'v1-2026-10', 'PLANEJAMENTO E PRESTAÇÃO DE CONTAS', 'Publica o Relatório de Gestão Fiscal (RGF)', 'Art. 48º, "caput", da LC nº 101/00', 'comum', 'documento'),
 (5, '15.4', 'v1-2026-10', 'SERVIÇO DE INFORMAÇÕES AO CIDADÃO e-SIC (ELETRÔNICO)', 'Divulga, na seção relativa ao e-SIC, os prazos de resposta ao cidadão, incluindo o recursal, e as autoridades competentes para o exame dos pedidos, além do procedimento referente à realização do pedido e de eventual recurso?', 'Arts. 7º, 15º e 16º, da LAI', 'comum', 'semantica'),
 (6, '16.2', 'v1-2026-10', 'ACESSIBILIDADE', 'Opção de alto contraste', 'Art. 8º, §3º, inciso VIII, da LAI', 'comum', 'existencia');

-- Os 6 criterios da matriz comum valem para prefeitura e camara.
INSERT INTO criterio_aplicabilidade (criterio_id, tipo_entidade)
SELECT id, 'prefeitura' FROM criterios UNION ALL SELECT id, 'camara' FROM criterios;

INSERT INTO execucoes (id, iniciada_em, finalizada_em, origem, versao_checklist, status, observacao) VALUES
 (1, '2026-10-09 10:00', '2026-10-09 18:00', 'manual',   'v1-2026-10', 'concluida', 'Exploracao manual inicial, cobertura parcial'),
 (2, '2026-10-10 11:00', '2026-10-10 15:15', 'gabarito', 'v1-2026-10', 'concluida', 'Gabarito completo, 30 de 30 celulas');

-- Execucao 1 (09/10): so as celulas que estavam fechadas naquele dia.
INSERT INTO avaliacoes (execucao_id, entidade_id, criterio_id, status, metodo, justificativa, avaliado_em) VALUES
 (1, 'japeri', 1, 'parcial', 'manual', 'Menu Transparência exige 2 cliques', '2026-10-09'),
 (1, 'japeri', 2, 'atende',  'manual', 'Colunas Doc. Despesa, Valor Empenhado, Liquidado, Pago', '2026-10-09'),
 (1, 'japeri', 3, 'atende',  'manual', 'Empenho mais recente de 09/10/2026', '2026-10-09'),
 (1, 'japeri', 6, 'atende',  'manual', 'Link Alto Contraste no topo', '2026-10-09'),
 (1, 'duque_de_caxias', 5, 'parcial', 'manual', 'Recurso no infográfico; prazo do pedido inicial não encontrado', '2026-10-09'),
 (1, 'itaborai', 1, 'parcial', 'manual', 'Link só no submenu ao passar o mouse', '2026-10-09'),
 (1, 'itaborai', 4, 'atende',  'manual', '2º Quadrimestre/2026 publicado', '2026-10-09'),
 (1, 'itaborai', 5, 'atende',  'manual', 'PDF Prazos, Procedimentos e Autoridades', '2026-10-09'),
 (1, 'itaborai', 6, 'atende',  'manual', 'Barra Acessibilidade com contraste', '2026-10-09'),
 (1, 'cachoeiras_de_macacu', 1, 'atende', 'manual', 'Menu TRANSPARÊNCIA no topo, 1 clique', '2026-10-09'),
 (1, 'cachoeiras_de_macacu', 6, 'atende', 'manual', 'Barra com ícone de contraste', '2026-10-09'),
 (1, 'rio_de_janeiro', 1, 'atende',  'manual', 'Ícone Transparência Rio, 1 clique', '2026-10-09'),
 (1, 'rio_de_janeiro', 6, 'parcial', 'manual', 'Botão de alto contraste não visto', '2026-10-09');

-- Execucao 2 (10/10): gabarito completo.
INSERT INTO avaliacoes (execucao_id, entidade_id, criterio_id, status, metodo, justificativa, avaliado_em) VALUES
 (2, 'japeri', 1, 'parcial',    'manual', 'Menu Transparência exige 2 cliques', '2026-10-10'),
 (2, 'japeri', 2, 'atende',     'manual', 'API: nr_doc_despesa, vl_empenhado, vl_liquidado, vl_pago', '2026-10-10'),
 (2, 'japeri', 3, 'atende',     'manual', 'Data máxima 2026-10-09 na API', '2026-10-10'),
 (2, 'japeri', 4, 'parcial',    'manual', 'Mais recente: 1º Quadrimestre/2026; esperado 2º', '2026-10-10'),
 (2, 'japeri', 5, 'nao_atende', 'manual', 'Só capa genérica do Fala.BR, sem prazos nem autoridade', '2026-10-10'),
 (2, 'japeri', 6, 'atende',     'manual', 'Link Alto Contraste no topo', '2026-10-10'),
 (2, 'duque_de_caxias', 1, 'atende', 'manual', 'Ícone na grade de acesso rápido (precisa rolar)', '2026-10-10'),
 (2, 'duque_de_caxias', 2, 'atende', 'manual', 'Nr. Empenho e valores por fase', '2026-10-10'),
 (2, 'duque_de_caxias', 3, 'atende', 'manual', 'Última Atualização 10/10/2026', '2026-10-10'),
 (2, 'duque_de_caxias', 4, 'atende', 'manual', '2º Quadrimestre/2026 publicado', '2026-10-10'),
 (2, 'duque_de_caxias', 5, 'atende', 'manual', 'Pedido 20 dias corridos; recurso ao Prefeito em 20 dias úteis', '2026-10-10'),
 (2, 'duque_de_caxias', 6, 'atende', 'manual', 'Alto contraste no menu de acessibilidade', '2026-10-10'),
 (2, 'itaborai', 1, 'parcial', 'manual', 'Link só no submenu ao passar o mouse', '2026-10-10'),
 (2, 'itaborai', 2, 'atende',  'manual', 'Colunas Empenho, Vr. Empenhado, Liquidado, Pago', '2026-10-10'),
 (2, 'itaborai', 3, 'atende',  'manual', 'Dados atualizados até 09/10/2026', '2026-10-10'),
 (2, 'itaborai', 4, 'atende',  'manual', '2º Quadrimestre/2026 publicado', '2026-10-10'),
 (2, 'itaborai', 5, 'atende',  'manual', 'PDF Prazos, Procedimentos e Autoridades', '2026-10-10'),
 (2, 'itaborai', 6, 'atende',  'manual', 'Barra Acessibilidade com contraste', '2026-10-10'),
 (2, 'cachoeiras_de_macacu', 1, 'atende',  'manual', 'Menu TRANSPARÊNCIA no topo, 1 clique', '2026-10-10'),
 (2, 'cachoeiras_de_macacu', 2, 'atende',  'manual', 'Número do empenho e valores', '2026-10-10'),
 (2, 'cachoeiras_de_macacu', 3, 'atende',  'manual', 'Última atualização 09/10/2026 20:03', '2026-10-10'),
 (2, 'cachoeiras_de_macacu', 4, 'parcial', 'manual', 'Mais recente: 3º Quadrimestre/2025; esperado 2º/2026', '2026-10-10'),
 (2, 'cachoeiras_de_macacu', 5, 'parcial', 'manual', 'Prazos sim; autoridade não identificada', '2026-10-10'),
 (2, 'cachoeiras_de_macacu', 6, 'atende',  'manual', 'Barra com ícone de contraste', '2026-10-10'),
 (2, 'rio_de_janeiro', 1, 'atende', 'manual', 'Ícone Transparência Rio, 1 clique', '2026-10-10'),
 (2, 'rio_de_janeiro', 2, 'atende', 'manual', 'Nota de Empenho, Valor Empenhado, Liquidado, Pago', '2026-10-10'),
 (2, 'rio_de_janeiro', 3, 'atende', 'manual', 'Data de atualização dos dados 09/10/2026', '2026-10-10'),
 (2, 'rio_de_janeiro', 4, 'atende', 'manual', '2º Quadrimestre/2026 publicado (Resolução 2165/2026)', '2026-10-10'),
 (2, 'rio_de_janeiro', 5, 'atende', 'manual', 'Prazos, CORE-Rio e dirigente máximo', '2026-10-10'),
 (2, 'rio_de_janeiro', 6, 'atende', 'manual', 'Alto Contraste no painel de acessibilidade', '2026-10-10');

-- Algumas evidencias reais (a execucao automatica vai gravar uma ou mais por avaliacao).
INSERT INTO evidencias (avaliacao_id, tipo, url, titulo_pagina, conteudo, coletado_em)
SELECT a.id, 'trecho', 'https://transparencia.betha.cloud/#/VZIcwd3tEQSz63QIK2HkQw==/acesso-informacao', 'Acesso à informação',
       'O prazo para o fornecimento da informação é de 20 dias, prorrogável por mais 10 dias.', '2026-10-10 14:20'
FROM avaliacoes a JOIN criterios c ON c.id = a.criterio_id
WHERE a.execucao_id = 2 AND a.entidade_id = 'cachoeiras_de_macacu' AND c.codigo = '15.4';

INSERT INTO evidencias (avaliacao_id, tipo, url, titulo_pagina, conteudo, coletado_em)
SELECT a.id, 'tabela', 'https://japeri.geosiap.net.br/portal-transparencia/publicacoes?id_publicacao_tipo=5', 'Relatórios Publicados',
       'Exercício 2026: ANEXO I e ANEXO II, 01 QUADRIMESTRE (publicados em 26/08/2026 e 10/09/2026)', '2026-10-10 15:11'
FROM avaliacoes a JOIN criterios c ON c.id = a.criterio_id
WHERE a.execucao_id = 2 AND a.entidade_id = 'japeri' AND c.codigo = '12.1';

INSERT INTO ocorrencias (execucao_id, entidade_id, criterio_id, url, tipo, mensagem, tentativa, ocorrido_em) VALUES
 (2, 'duque_de_caxias', 2, 'https://transparencia.duquedecaxias.rj.gov.br/', 'erro_servidor', 'Network error IOException: Address already in use: connect', 1, '2026-10-10 11:35'),
 (2, 'itaborai', 2, 'https://itaborai.supernova.com.br:8443/contaspublicas/despesa.xhtml?exercicio=2026', 'erro_servidor', 'Internal Server Error', 1, '2026-10-10 16:35');
