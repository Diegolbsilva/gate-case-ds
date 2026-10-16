# Anexo: exploração manual dos portais

Registro da navegação manual nos 5 portais (09 e 10/10/2026, com conferência do 4.6 em 15/10/2026). É a base do gabarito usado na validação (`config/gabarito.yaml` e `docs/validacao.md`) e de boa parte das decisões de coleta e de regras (`docs/documentacao_tecnica.md`).

## 1. Portais e fornecedores

| Prefeitura | Site oficial | Portal da transparência | Fornecedor | Observações |
|---|---|---|---|---|
| Japeri | japeri.rj.gov.br | japeri.geosiap.net.br/portal-transparencia/home | GeoSiap (Grupo Embras) | Domínio do fornecedor. API pública com Swagger. O mesmo portal serve 15 entidades (Prefeitura, Câmara, 12 fundos e o instituto de previdência). Fora do ar na tarde de 09/10 |
| Duque de Caxias | duquedecaxias.rj.gov.br (redireciona para portal.duquedecaxias.rj.gov.br) | transparencia.duquedecaxias.rj.gov.br | Modernização Informática (plataforma Webrun) | Consultas de despesa e RGF com reCAPTCHA; API de dados abertos documentada dentro do portal. Selo "Transparência Ouro 2025" |
| Itaboraí | site.ib.itaborai.rj.gov.br | transparencianovo.ib.itaborai.rj.gov.br | Portal próprio; despesas no sistema Contas Públicas, da Supernova | O subdomínio "transparencianovo" indica migração recente. Selo Prata do Radar da Transparência |
| Cachoeiras de Macacu | prefeituracachoeiras.com (domínio .com) | transparencia.betha.cloud/#/VZIcwd3tEQSz63QIK2HkQw== | Betha Sistemas | Plataforma em nuvem compartilhada; a entidade é identificada por um código na URL; cada consulta tem endereço próprio. Bloqueia o navegador automatizado padrão (HTTP 403) |
| Rio de Janeiro | prefeitura.rio | transparencia.prefeitura.rio | Sem crédito de fornecedor | O portal funciona como central de links: despesas no Contas Rio (contasrio.rio.rj.gov.br) e RGF na Controladoria (controladoria.prefeitura.rio), cada um em outro domínio e em nova aba. Selo "Diamante 2024" |

A Câmara aparece junto da Prefeitura em dois casos: em Japeri, como entidade do mesmo portal GeoSiap; em Caxias, como ícone ao lado do portal na capa do site. É outro Poder e fica fora da avaliação da Prefeitura.

## 2. Gabarito

| | 1.2 | 4.1 | 4.6 (10/10) | 4.6 (15/10) | 12.1 | 15.4 | 16.2 |
|---|---|---|---|---|---|---|---|
| Japeri | Atende | Atende | Atende | Parcial | Parcial | Não atende | Atende |
| Duque de Caxias | Atende | Atende | Atende | Atende | Atende | Atende | Atende |
| Itaboraí | Parcial | Atende | Atende | Atende | Atende | Atende | Atende |
| Cachoeiras de Macacu | Atende | Atende | Atende | Atende | Parcial | Parcial | Atende |
| Rio de Janeiro | Atende | Atende | Atende | Atende | Atende | Atende | Atende |

- O 4.6 depende do dia da avaliação; por isso o gabarito guarda a data e a validação só compara no dia conferido.
- Japeri 1.2 foi corrigido de Parcial para Atende: a visita manual seguiu o menu "Transparência" do topo (2 cliques), e a descoberta automática encontrou um card "PORTAL DE TRANSPARÊNCIA" na capa, abaixo do carrossel, com 1 clique. A correção foi conferida visualmente.
- Referência de prazo em 10/10/2026: último dia útil 09/10; RGF mais recente esperado, 2º quadrimestre de 2026.

## 3. Evidências por entidade

### Japeri

| Critério | Resultado | Evidência | Caminho |
|---|---|---|---|
| 1.2 | Atende | Card "PORTAL DE TRANSPARÊNCIA" na capa, visível depois de rolar, 1 clique até o portal | Capa do site |
| 4.1 | Atende | Colunas "Doc. Despesa" (número do empenho), "Valor Empenhado", "Valor Liquidado", "Valor Pago" | Execução Orçamentária > Despesas Detalhadas > Pesquisar |
| 4.6 | Atende (10/10); Parcial (15/10) | Empenho mais recente de 09/10/2026, nas duas datas. O rodapé "dados atualizados em" mostra sempre a hora da visita e não serve como data dos dados | Despesas Detalhadas, Prefeitura |
| 12.1 | Parcial | RGF mais recente: 1º quadrimestre de 2026 (Anexos I e II); esperado o 2º. O exercício de 2025 só tem o 1º quadrimestre. Mesmo nome de arquivo ligado a quadrimestres diferentes em 2022 e 2024 | Ícone "RGF" > publicações tipo 5 > Entidade Prefeitura > Pesquisar |
| 15.4 | Não atende | O e-SIC leva à capa genérica do Fala.BR, a plataforma federal da CGU, igual para qualquer município. Nem o portal nem a página de destino divulgam prazos, autoridades ou procedimentos próprios de Japeri | Acesso à Informação > Atendimento / Ouvidoria |
| 16.2 | Atende | Link "Alto Contraste" no topo | Topo do portal |

### Duque de Caxias

| Critério | Resultado | Evidência | Caminho |
|---|---|---|---|
| 1.2 | Atende | Ícone "PORTAL DA TRANSPARÊNCIA" na grade de acesso rápido, abaixo do carrossel, 1 clique | Capa do site |
| 4.1 | Atende | Coluna de fase (Empenho, Liquidação, Pagamento) em linhas, "Nr. Empenho" e coluna de valor: formato diferente dos demais portais | Despesas (Empenho, Liquidação e Pagamento) > reCAPTCHA > Pesquisar |
| 4.6 | Atende | Cabeçalho "Última Atualização (Empenhado/Liquidado/Pago)". Em 15/10, CSV exportado com 90 registros de 14/10 (a tela ordenava por outro campo) | Mesma consulta |
| 12.1 | Atende | 2º quadrimestre de 2026, com 5 demonstrativos por quadrimestre | Prestação de Contas > RGF > reCAPTCHA > Pesquisar |
| 15.4 | Atende | Prazo de resposta em texto ("não ultrapassando o prazo de 20 dias, prorrogáveis por mais 10"); procedimento do pedido pela plataforma Colab; recurso dirigido ao Prefeito ou autoridade delegada, decisão em até 20 dias úteis, num infográfico em imagem; Ouvidoria Geral do Município | Pedido de Informação > e-SIC e > Interposição de Recurso > Orientações sobre Recurso |
| 16.2 | Atende | "Alto contraste" no menu Acessibilidade, que abre ao clicar no ícone do canto inferior direito | Portal > ícone de acessibilidade |

### Itaboraí

| Critério | Resultado | Evidência | Caminho |
|---|---|---|---|
| 1.2 | Parcial | O link "Portal da Transparência" só aparece no submenu "Transparência", ao passar o mouse | Capa do site > menu Transparência |
| 4.1 | Atende | Colunas "Empenho", "Vr. Empenhado R$", "Vr. Liquidado R$", "Vr. Pago R$"; CPF de credor já mascarado pelo portal | Despesas (Supernova) > mês > Pesquisar |
| 4.6 | Atende | "Dados atualizados até" no cabeçalho da consulta (09/10 na visita de 10/10; 14/10 na conferência de 15/10) | Cabeçalho da consulta de despesas |
| 12.1 | Atende | 2º quadrimestre de 2026; republicações contam como a mesma competência | 15 - Relatórios Fiscais LRF > RGF |
| 15.4 | Atende | PDF "Prazos, Procedimentos e Autoridades" (ANEXO 1): resposta em 20 dias + 10; recurso de 1ª instância em 10 dias à autoridade hierarquicamente superior; 2ª instância à Controladoria Geral; autoridades por etapa | Prazos de respostas do SIC > Ver mais detalhes > ANEXO 1 |
| 16.2 | Atende | Barra "Acessibilidade" com contraste | Topo do portal |

### Cachoeiras de Macacu

| Critério | Resultado | Evidência | Caminho |
|---|---|---|---|
| 1.2 | Atende | Menu "TRANSPARÊNCIA" visível no topo, 1 clique | Capa do site |
| 4.1 | Atende | Colunas "Número do empenho", "Valor do empenho", "Valor liquidado R$", "Valor pago R$" | Despesas públicas > Execução Detalhada de Despesas |
| 4.6 | Atende | "Última atualização dos dados em" no topo da consulta (14/10/2026 22:11 na conferência de 15/10) | Mesma consulta |
| 12.1 | Parcial | RGF mais recente: 3º quadrimestre de 2025, publicado em 26/03/2026; esperado o 2º de 2026. A coluna "Ano" não coincide com o ano do relatório | Relatórios > LRF - RGF |
| 15.4 | Parcial | Prazo de resposta ("20 dias, prorrogável por mais 10") e prazo recursal ("até 10 dias, a partir da ciência, ao órgão, que terá 5 dias") presentes. Autoridade não identificada (só "ao órgão") e recurso sem procedimento | Acesso à informação, seção "Sobre a LAI" |
| 16.2 | Atende | Barra com contraste no topo | Topo do portal |

### Rio de Janeiro

| Critério | Resultado | Evidência | Caminho |
|---|---|---|---|
| 1.2 | Atende | Ícone "Transparência Rio" na grade "O que eu preciso?", 1 clique (abaixo da primeira tela) | Capa do site |
| 4.1 | Atende | Colunas "Nota de Empenho", "Valor Empenhado", "Valor Liquidado", "Valor Pago". A tabela demora a carregar; a página "Gráficos" do mesmo menu tem só totais e não serve para o 4.1 | Contas Rio > Despesas > Empenhos |
| 4.6 | Atende | "Data de atualização dos dados" no rodapé | Contas Rio > Despesas > Gráficos |
| 12.1 | Atende | 2º quadrimestre de 2026 publicado; o 3º aparece listado sem link (ainda não devido) | Controladoria > Quadros da LRF > RGF quadrimestral 2026 |
| 15.4 | Atende | Prazo de resposta de 20 dias + 10; recurso em 10 dias ao dirigente máximo do órgão, 2ª instância à CORE-Rio; unidade responsável pelo SIC (Coordenadoria de Transparência); procedimentos do pedido e do recurso pela Central 1746 | Acesso à Informação > Pedido de Informação e > Recursos |
| 16.2 | Atende | "Alto Contraste" no painel "Ferramentas de Acessibilidade", que só abre ao clicar no ícone lateral. Na primeira visita manual o botão não foi visto, por estar escondido no painel | Portal > ícone de acessibilidade |

## 4. APIs dos fornecedores

### Modernização Informática (Duque de Caxias)

| Item | Detalhe |
|---|---|
| Onde | Portal > API de Dados Abertos > Documentação uso APIs |
| Endpoint | `https://transparencia.duquedecaxias.rj.gov.br/sincronia/apidados.rule?sys=LAI`, POST com corpo JSON `{"api": "<serviço>", "ano": <ano>}`, sem chave |
| Catálogo | 60 serviços, com documentação em JSON e PDF; o serviço `consulta_api` lista todos |
| Usados | `despesas_todas` (4.1 e 4.6) e `consulta_rgf_m2` (12.1) |
| Observações | Contorna o reCAPTCHA da tela pelos dados abertos oficiais. O exemplo de resposta cita outro município cliente (Mesquita), sinal de que o adaptador serve para outros clientes |

### GeoSiap (Japeri)

| Item | Detalhe |
|---|---|
| Onde | Rodapé do portal > Documentação da API (Swagger) |
| Base | `/portal-transparencia/api`, GET, sem chave nem sessão |
| Usados | `/sis_entidade` (lista as 15 entidades; a Prefeitura é a única com `principal = 1`) e `/execucao/despesas_detalhadas/despesas_detalhadas` (4.1 e 4.6) |
| Parâmetros | `id_entidade` e `data_inicial` + `data_final`; o parâmetro `ano` não respondeu |
| Cuidados | Valores em texto com "R$"; CPF completo de credores pessoa física no campo `doc_pessoa` (mascarado na evidência); sem paginação |
| Observações | O endereço segue o padrão `<município>.geosiap.net.br`, o que indica um adaptador reaproveitável. O RGF não tem endpoint e é lido pela página de publicações |

## 5. Selos do Radar da Transparência Pública (PNTP)

Observados nos próprios portais e usados como referência externa na validação (`config/referencias.yaml`): Rio de Janeiro Diamante (2024), Duque de Caxias Ouro (2025), Itaboraí Prata. Japeri e Cachoeiras de Macacu têm link para o Radar, sem selo exibido.
