# GATE: descobertas da exploração manual (09 e 10/10/2026)

Registro do que foi observado navegando nos portais, para guiar a codificação e a documentação.

## 1. Portais e fornecedores

| Prefeitura | Site oficial | Portal da transparência | Fornecedor | Observações |
|---|---|---|---|---|
| Japeri | https://japeri.rj.gov.br/ | https://japeri.geosiap.net.br/portal-transparencia/home | GeoSiap / Grupo Embras | Domínio do fornecedor, diferente do site. Tem API pública com Swagger. Ficou fora do ar por volta das 14:59 de 09/10 |
| Duque de Caxias | https://duquedecaxias.rj.gov.br/ (redireciona para portal.duquedecaxias.rj.gov.br) | https://transparencia.duquedecaxias.rj.gov.br/ | Site: desenvolvimento próprio (rodapé "Secretaria de Governo / Subsecretaria de Tecnologia"). Portal: Modernização Informática | Domínio próprio. Grade de ícones com nomes muito próximos aos do checklist. Selo "Transparência Ouro 2025" (Radar da Transparência Pública / PNTP). Consultas de despesas e RGF com reCAPTCHA |
| Itaboraí | https://site.ib.itaborai.rj.gov.br/ | https://transparencianovo.ib.itaborai.rj.gov.br/ | Portal: desenvolvimento próprio (rodapé "Desenvolvido por Secretaria de Fazenda e Tecnologia / SEMFAT"). Despesas: sistema "Contas Públicas" da Supernova (itaborai.supernova.com.br:8443) | Subdomínio "transparencianovo" sugere migração recente de portal. Grade numerada de 23 categorias. Selo prata do Radar da Transparência. Selos "N novo(s) documento(s) inserido(s) em 1 semana" nas categorias |
| Cachoeiras de Macacu | https://www.prefeituracachoeiras.com/ (domínio .com, não .gov.br) | https://transparencia.betha.cloud/#/VZIcwd3tEQSz63QIK2HkQw== | Betha Sistemas (rodapé "BETHA"); plataforma em nuvem compartilhada, a entidade é identificada por um código na URL | Menu "TRANSPARÊNCIA" no topo da capa leva ao portal com 1 clique; botões "TRASFEREGOV" (sic) e "E-MAIL"; ícone de acessibilidade fixo no canto. Cada consulta tem endereço próprio (ex.: .../consulta/31180) |
| Rio de Janeiro | https://prefeitura.rio/ | https://transparencia.prefeitura.rio/ | Sem crédito de fornecedor no rodapé; provável desenvolvimento próprio. Selo "Diamante 2024" do Radar da Transparência no rodapé | Capa com vários acessos ligados à transparência: ícone "Transparência Rio" na grade "O que eu preciso?", "Portais de Transparência da Saúde", "Central Anticorrupção", "Escritório de Dados", Data.Rio; barra superior com "Acesso à Informação" e "LGPD"; rodapé com "Transparência", "Acesso à Informação", "Lei de Acesso à Informação" e "Data.Rio" |

Atenção: existia um portal da Câmara de Japeri (http://rj.portaldatransparencia.com.br/camara/japeri/, sem HTTPS). Em 10/10/2026 ele mostra "SERVIÇO INDISPONÍVEL PARA ESTE MUNICÍPIO" (Portal da Transparência Imprensa Oficial / RED); os dados da Câmara aparecem agora no próprio portal GeoSiap da Prefeitura, como entidade id 1. É outra entidade e não pode ser confundida com a Prefeitura. Em Caxias, o ícone "CÂMARA MUNICIPAL" fica ao lado do "PORTAL DA TRANSPARÊNCIA" na capa do site, e o portal também tem um ícone "Câmara Municipal de Duque de Caxias".

## 2. Gabarito dos critérios do protótipo (avaliação manual)

Critérios em uso: 1.2 (navegação), 4.1 (dados estruturados), 4.6 (atualização), 12.1 (documento), 15.4 (interpretação semântica), 16.2 (existência simples).

| | 1.2 | 4.1 | 4.6 | 12.1 | 15.4 | 16.2 |
|---|---|---|---|---|---|---|
| Japeri | Parcial | Atende | Atende | Parcial | Não atende | Atende |
| Duque de Caxias | Atende | Atende | Atende | Atende | Atende | Atende |
| Itaboraí | Parcial | Atende | Atende | Atende | Atende | Atende |
| Cachoeiras de Macacu | Atende | Atende | Atende | Parcial | Parcial | Atende |
| Rio de Janeiro | Atende | Atende | Atende | Atende | Atende | Atende |

Gabarito completo: 24 Atende, 5 Parcial, 1 Não atende.

Data de referência das avaliações de 10/10/2026: sábado, último dia útil 09/10/2026; RGF mais recente esperado: 2º quadrimestre de 2026.

## 3. Resultado por critério (detalhe e evidências)

### Japeri

| Item | Resultado | Evidência | Caminho |
|---|---|---|---|
| 1.1 Possui portal | Atende | Portal GeoSiap acessível a partir do site oficial | Site > Transparência > Transparência |
| 1.2 Acesso na capa | Parcial | Menu "Transparência" existe na capa, mas exige 2 cliques até o portal | Site > Transparência > Transparência |
| 1.3 Ferramenta de pesquisa | Atende | Caixa "Pesquise..." no topo do portal | Home do portal |
| 4.1 Empenho, liquidação, pagamento | Atende | Tabela com colunas "Doc. Despesa" (nº do empenho), "Valor Empenhado", "Valor Liquidado", "Valor Pago" | Execução Orçamentária > Despesas Detalhadas > Pesquisar |
| 4.3 Credor | Atende | Colunas "Credor" e "CNPJ/CPF" | Mesma tabela |
| 4.4 Pesquisa específica | Atende | Campo "Busca por Documento, Credor ou Empenho" e filtros (ano, período, entidade) | Mesma página |
| 4.5 Relatórios em formatos | Atende (formatos a confirmar) | Botão "Exportar" e botão "Dados Abertos" | Mesma página |
| 4.6 Informação atualizada | Atende | Empenho mais recente de 09/10/2026. O rodapé "dados atualizados em" mostrou 09/10/2026 14:44 na visita de 09/10 e 10/10/2026 15:05 e 15:08 nas visitas de 10/10, sempre a hora da visita: parece o horário de geração da página, não da carga dos dados | Tabela de despesas (rodapé não serve sozinho) |
| 12.1 RGF | Parcial | RGF mais recente: 1º Quadrimestre de 2026, só Anexo I (Despesa com Pessoal, publicado em 26/08/2026) e Anexo II (DCL, publicado em 10/09/2026). Esperado em 10/10/2026: 2º Quadrimestre de 2026, não encontrado. Exercício 2025 só tem o 1º Quadrimestre (2º e 3º não encontrados). 76 registros, de 2017 a 2026 | Portal > ícone "RGF - Relatório de Gestão Fiscal" (nova aba) > japeri.geosiap.net.br/portal-transparencia/publicacoes?id_publicacao_tipo=5 > Entidade "Prefeitura Municipal de Japeri" > Pesquisar, sem captcha |
| 15.1 e-SIC | Atende | Pedido eletrônico pelo Fala.BR, plataforma da CGU ("Pedido de Acesso à Informação") | Portal > ícone "SIC - Atendimento / Ouvidoria" ou menu Acesso à Informação > Atendimento / Ouvidoria > falabr.cgu.gov.br/v2/?uf=rj&municipio=japeri (nova aba) |
| 15.4 Prazos, autoridade e recurso | Não atende | Menu "Acesso à Informação" só tem "Atendimento / Ouvidoria", que leva à capa genérica do Fala.BR (igual para qualquer município). Nem o portal nem a página de destino divulgam prazos, autoridade ou procedimento próprios de Japeri. Registrado como "não encontrado no portal" | Portal > Acesso à Informação > Atendimento / Ouvidoria |
| 16.2 Alto contraste | Atende | Link "Alto Contraste" no topo | Topo do portal |
| 16.3 Redimensionar texto | Atende | Links "A-" e "A+" no topo | Topo do portal |
| 16.4 Símbolo de acessibilidade | Atende | Ícone de acessibilidade (VLibras) fixo à direita | Todas as páginas |
| 18.3 Dados abertos / API | Atende | "Documentação da API (Swagger)" no rodapé; endpoints de contatos, RH (cargos, servidores) etc. | Rodapé > Swagger |

Outros itens vistos no menu Publicações: Parecer do Tribunal de Contas (12.5), Informação sobre Obras (11.x), Processos Seletivos e Concursos (5.12), Planejamento Orçamentário (19.x), RREO.

### Duque de Caxias

| Item | Resultado | Evidência | Caminho |
|---|---|---|---|
| 1.2 Acesso na capa | Atende | Ícone "PORTAL DA TRANSPARÊNCIA" na grade de acesso rápido, logo abaixo do carrossel, visível sem passar o mouse; portal a 1 clique (abre em nova aba). Não há "Transparência" no menu do topo nem no rodapé | Capa do site (portal.duquedecaxias.rj.gov.br) > ícone Portal da Transparência |
| 1.3 Ferramenta de pesquisa | Atende | Ícone "Ferramenta de Pesquisa (Busca)" | Home |
| 2.7 Perguntas frequentes | Atende | Ícone "Perguntas e Respostas (Perguntas frequentes)" | Home |
| 4.1 Empenho, liquidação, pagamento | Atende | Coluna "Despesa" com a fase (Empenho, Liquidação, Pagamento), "Nr. Empenho" (ex.: 4595), "Valor Empenho/Liquidação/Pago"; também "Valor Liquidado" e "Valor Pago Liquidado". 1.181 registros em out/2026. Primeira tentativa (10/10 11:35) falhou com erro do servidor; abriu na segunda | Portal > Despesas, Subvenções, Ordem Cronológica... > Despesas (Empenho, Liquidação e Pagamento) > reCAPTCHA > Pesquisar |
| 4.2 Classificação orçamentária | Atende | Colunas Unidade Orçamentária, Função, Subfunção, Programa, Ação, Natureza da Despesa, Fonte | Mesma tabela |
| 4.3 Credor | Atende | Colunas "Nome do Favorecido" e "CPF/CNPJ Favorecido" | Mesma tabela |
| 4.6 Informação atualizada | Atende | "Última Atualização (Empenhado): 10/10/2026 - Última Atualização (Liquidado): 10/10/2026 - Última Atualização (Pago): 10/10/2026"; último registro real de 08/10/2026 | Mesma página, cabeçalho |
| 12.1 RGF | Atende | 2026, quadrimestre 2: 5 demonstrativos (Despesa com Pessoal, Dívida Consolidada Líquida, Garantias, Operações de Crédito, Demonstrativo Simplificado), upload em 01/10/2026. 127 registros de histórico. "Data da Última Atualização: 01/10/2026" | Portal > Prestação de Contas > Relatório de Gestão Fiscal (RGF) > reCAPTCHA > Pesquisar |
| 14.1 a 14.4 SIC presencial | Atende | Bloco "Serviço de Atendimento ao Cidadão - SIC (Presencial)": Ouvidoria Geral do Município, Alameda Esmeralda 206, seg a sex 08h às 17h; telefone e e-mail no bloco e-SIC | Rodapé da home do portal |
| 15.1 e-SIC eletrônico | Atende | e-SIC pela plataforma COLAB, com link | Rodapé da home |
| 15.3 Regulamentação local da LAI | Atende | "Lei de Acesso à Informação - Regulamentação no Município" | Pedido de Informação |
| 15.4 Prazos, autoridade e recurso | Atende | Resposta: "em até no máximo 20 dias corridos" (texto HTML). Procedimento do pedido: Colab.Gov, formulário eletrônico, protocolo e acompanhamento online. Recurso: dirigido ao Prefeito ou autoridade delegada via Ouvidoria, decisão em até 20 dias úteis, Decreto nº 8.820/2024 (infográfico em imagem). Administração: Ouvidoria Geral do Município | Pedido de Informação > 02 - e-SIC (pedido) e > 03 - Interposição de Recurso > Orientações sobre Recurso |
| 15.5 Relatório estatístico | Atende | "Relatórios Estatísticos Mensais e-SIC" (versão antiga até maio/2026 e nova versão digital) | Pedido de Informação |
| 15.6 e 15.7 Sigilo | Provável | "Grau de Sigilo - Informações" | Pedido de Informação |
| 16.1 Caminho de páginas | Observado | Breadcrumb "Início / Despesas, Subvenções... / Despesas (Empenho, Liquidação e Pagamento)" | Páginas internas do portal |
| 16.2 Alto contraste | Atende | Portal: opção "Alto contraste" no menu "Acessibilidade" (abre ao clicar no ícone fixo no canto inferior direito). Site oficial: botão "Alto contraste" na barra do topo | Portal > ícone de acessibilidade |
| 16.3 Redimensionar texto | Atende | Portal: "Aumentar fonte" no menu Acessibilidade. Site: "A-", "A", "A+" no topo | Portal e site |
| 16.4 Símbolo de acessibilidade | Atende | Ícones VLibras e de acessibilidade fixos à direita | Todas as páginas |
| 18.1 Encarregado de dados (LGPD) | Atende | "Responsável pelo Tratamento de Dados Pessoais" com e-mail | Rodapé da home |
| 18.3 Dados abertos / API | Provável | Ícone "API de Dados Abertos" | Home |
| 18.4 Pesquisa de satisfação | Provável | Ícone "Pesquisa de Satisfação" | Home |

### Itaboraí

| Item | Resultado | Evidência | Caminho |
|---|---|---|---|
| 1.1 Site e portal | Atende | Site oficial e portal próprio | site.ib.itaborai.rj.gov.br |
| 1.2 Acesso na capa | Parcial (mesma regra de Japeri) | Menu "Transparência" no topo do site; o link "Portal da Transparência" só aparece no submenu, ao passar o mouse (1 interação) | Site oficial > Transparência > Portal da Transparência |
| 1.3 Ferramenta de pesquisa | Atende | "Busque documentos no portal transparência" | Home |
| 2.4 a 2.6 Endereço, telefone, horário | Atende | Rodapé: endereço, e-mail, telefones, funcionamento seg a sex 08h às 17h | Rodapé da home |
| 2.7 Perguntas frequentes | Atende | Seção "FAQ - Perguntas Frequentes" | Home |
| 4.1 Empenho, liquidação, pagamento | Atende | Colunas "Empenho" (ex.: 897 - 2026), "Vr. Empenhado R$", "Vr. Liquidado R$", "Vr. Pago R$" (mais as colunas de anulado); credor com CPF mascarado; 20 páginas em out/2026 | Portal > 01-Receitas, Despesas e Ordem Cronológica > Despesas (abre na mesma aba, em itaborai.supernova.com.br:8443/contaspublicas/despesa.xhtml?exercicio=2026) > mês Outubro > Pesquisar, sem captcha |
| 4.6 Informação atualizada | Atende | Cabeçalho do Supernova: "Dados atualizados até: 09/10/2026" (visto no segundo acesso, 10/10/2026 16:43; no primeiro print o cabeçalho ficou fora do recorte). Empenho mais recente em 09/10/2026 (ex.: 2542 - 2026, FNDE). Selo "1 novo documento inserido em 1 semana" no card 01 | Cabeçalho da consulta de despesas e última página da paginação |
| 12.1 RGF | Atende | Página "RGF / Atualizado em: 01 de outubro de 2026"; lista de relatórios por quadrimestre de 2023 a 2026; o mais recente é o 2º Quadrimestre/2026; há republicações ("3º Quadrimestre/2025 - 1ª Republicação"); unidade: Controladoria. Arquivo em si não aberto (fica em "Ver mais detalhes") | Home > 15 - Relatórios Fiscais LRF > submenu RGF |
| 14.1 a 14.4 SIC presencial | Atende | Bloco "SIC / e-SIC": autoridade de monitoramento, unidade responsável (Ouvidoria), telefone e e-mail, endereço, horário seg a sex 08h às 17h | Home |
| 15.1 e-SIC | Atende | Botão "Solicitar Informação" | Home |
| 15.3 Regulamentação local da LAI | Atende | Link "Decreto de Regulamentação da LAI" | Home, bloco SIC |
| 15.4 Prazos | Atende | PDF "Prazos, Procedimentos e Autoridades" (Decreto 15/2020): resposta 20 dias + 10 de prorrogação; recurso 1ª instância 10 dias (autoridade hierarquicamente superior); 2ª instância 10 dias (Controladoria Geral do Município); autoridades por etapa e fluxo do pedido. PDF com texto selecionável (gerado no LibreOffice), em tabelas | Home > Prazos de respostas do SIC > Ver mais detalhes > ANEXO 1 |
| 15.5 Relatório estatístico | Provável | Link "Relatório Estatístico" | Home, bloco Ouvidoria |
| 15.6 e 15.7 Sigilo | Provável | Links "Solicitações com grau de sigilo" e "Solicitações não classificadas como sigilo" | Home, bloco SIC |
| 16.2 e 16.3 Contraste e tamanho de texto | Atende | Barra "Acessibilidade" com contraste, +A, -A | Topo |
| 16.4 Símbolo de acessibilidade | Atende | Ícone VLibras fixo à direita | Todas as páginas |
| 18 LGPD | Provável | Categoria "22 - Lei Geral de Proteção de Dados / LGPD" | Home > 22 |

### Cachoeiras de Macacu

| Item | Resultado | Evidência | Caminho |
|---|---|---|---|
| 1.1 Site e portal | Atende | Site oficial com menu Transparência | Capa |
| 1.2 Acesso na capa | Atende | Menu "TRANSPARÊNCIA" visível no topo, portal a 1 clique | Capa > Transparência |
| 1.3 Ferramenta de pesquisa | Atende | Campo "O que você está buscando?" | Home do portal |
| 2.4 a 2.6 Endereço, telefone, horário | Atende | Rodapé "Canal de atendimento": Rua Oswaldo Aranha 6, Centro; (21) 2649-4814; seg a sex 10h às 16h | Rodapé |
| 2.7 Perguntas frequentes | Atende | Card "Perguntas frequentes" e link no rodapé | Home do portal |
| 4.1 Empenho, liquidação, pagamento | Atende | Colunas "Número do empenho", "Valor do empenho", "Valor liquidado R$", "Valor pago R$", "Saldo a pagar R$". 29.614 registros | Portal > Despesas públicas > Execução Detalhada de Despesas (#/VZIcwd3tEQSz63QIK2HkQw==/consulta/31180), sem captcha |
| 4.6 Informação atualizada | Atende | "Última atualização dos dados em 09/10/2026 20:03"; empenho mais recente em 08/10/2026 | Mesma página, topo |
| 12.1 RGF | Parcial | RGF mais recente: 3º quadrimestre de 2025 (publicado em 26/03/2026). Esperado em 10/10/2026: 2º quadrimestre de 2026. 1º e 2º quadrimestre de 2026 não encontrados no portal. 53 registros. Publicações anteriores também atrasadas (1º quadrimestre de 2024 publicado em 03/07/2025) | Portal > Relatórios > LRF - RGF (#/VZIcwd3tEQSz63QIK2HkQw==/consulta/195139), ordenado por Data/Hora Publicação |
| 15.1 e-SIC | Atende | Formulário "Solicitação de Acesso à Informação" no próprio portal, com reCAPTCHA antes de "Enviar" | Portal > Acesso à informação > Solicitar pedido (#/VZIcwd3tEQSz63QIK2HkQw==/acesso-informacao/solicitacao-acesso-informacao) |
| 15.2 Solicitação simples | Atende | Obrigatórios só CPF, nome completo e e-mail (mais entidade e descrição do pedido); gênero, escolaridade e profissão opcionais; sem exigência de documentos ou assinatura | Mesma página |
| 15.4 Prazos, autoridade e recurso | Parcial | Prazo de resposta: "O prazo para o fornecimento da informação é de 20 dias, prorrogável por mais 10 dias." Prazo recursal: "poderá interpor recurso em até 10 dias, a partir da ciência, ao órgão, que terá 5 dias para se manifestar". Autoridade competente não identificada (só "ao órgão"). Procedimento: apenas o formulário, sem descrição dos passos nem do recurso. Nenhum decreto municipal citado | Portal > Acesso à informação (#/VZIcwd3tEQSz63QIK2HkQw==/acesso-informacao), seção "Sobre a LAI" |
| 15.5 Estatísticas | Provável | Botão "Estatísticas dos dados" | Portal > Acesso à informação |
| 16.2 a 16.4 Acessibilidade | Atende | Barra com A-, A+, contraste e ícone de acessibilidade; VLibras fixo à direita; atalhos "Ir para o conteúdo 1 / menu 2 / busca 3 / rodapé 4" | Topo |
| 18 LGPD | Provável | Card "LGPD e Governo Digital" | Home do portal |
| Outros | Observado | Cards "Dados abertos", "Estrutura organizacional", "Glossário"; link "Radar da Transparência" no topo | Home do portal |

### Rio de Janeiro

| Item | Resultado | Evidência | Caminho |
|---|---|---|---|
| 1.1 Site e portal | Atende | Site oficial com acesso à transparência | Capa |
| 1.2 Acesso na capa | Atende | Ícone "Transparência Rio" visível na grade "O que eu preciso?", 1 clique; também no rodapé | Capa |
| 1.3 Ferramenta de pesquisa | Atende | Campo "O que você procura?" no topo do portal | Topo |
| 2.4 Endereço | Atende | "Rua Afonso Cavalcanti, 455, Cidade Nova, 20211-110" | Rodapé do portal |
| 2.5 e 2.6 Telefone e horário | A verificar | Não aparecem no rodapé do portal (na capa do site: "Ligue 1746, domingo a domingo, 24h") | Site oficial |
| 2.7 Perguntas frequentes | Atende | Menu e ícone "Perguntas frequentes" | Topo e home do portal |
| 4.1 Empenho, liquidação, pagamento | Atende | Colunas "Nota de Empenho" (ex.: 2026NE000276), "Data NE", "Nota de Liquidação" (ex.: 2026NL002315), "Valor Empenhado", "Valor Liquidado", "Valor Pago", "Pagamento de RP"; favorecido com CNPJ. 17.753 registros com filtro de mês Outubro/2026. A página "Gráficos" do mesmo menu mostra só totais agregados e não serve para o 4.1 | Portal > Contas Rio (rio.rj.gov.br/web/contasrio, nova aba) > Novo Portal Contas Rio, a partir de 2024 (contasrio.rio.rj.gov.br, nova aba) > Despesas > Empenhos (#!Despesas/Empenhos) |
| 4.6 Informação atualizada | Atende | "Data de atualização dos dados: 09/10/2026" | Contas Rio > Despesas > Gráficos (#!Despesas/Gráficos), rodapé |
| 12.1 RGF | Atende | Página "LRF Quadrimestrais Ano 2026": 2º Quadrimestre publicado (com link) nos Anexos 1, 2, 3, 4 e 6, "Arquivo Editável - Resolução 2165/2026"; 1º Quadrimestre pela Resolução 2146/2026; 3º Quadrimestre listado sem link (ainda não publicado, esperado). Anexo 5 só tem a linha do 3º Quadrimestre. Histórico de 2000 a 2026 | Contas Rio > Prestação Contas > Demonstrativos da Lei de Responsabilidade Fiscal > botão "Demonstrativos da LRF" (controladoria.prefeitura.rio/quadros-da-lrf/, nova aba) > bloco "Relatório de Gestão Fiscal (RGF) - Quadrimestral" > 2026 (controladoria.prefeitura.rio/lrf-quadrimestrais-ano-2026/) |
| 14.1 a 14.4 SIC presencial | Atende | Unidade responsável: Coordenadoria de Transparência, da Subsecretaria de Integridade e Transparência, da Secretaria Municipal de Integridade e Transparência; e-mail transparencia@prefeitura.rio. Protocolo SIC Central: Rua Afonso Cavalcanti, 455, Cidade Nova, de 9h às 17h, telefone 2976-2969; SICs setoriais com listagem de endereços | Portal > Acesso à Informação > Pedido de Informação |
| 15.1 e-SIC | Atende | Pedido pela Central 1746 (Portal 1746, telefone 1746 ou (21) 3460-1746, aplicativo); botão "Fazer pedido" | Portal > Acesso à Informação > Pedido de Informação |
| 15.3 Regulamentação local da LAI | Atende | "Na Prefeitura do Rio, a LAI é regulamentada pelo Decreto RIO nº 44.745/2018 [...] alterado pelo Decreto RIO nº 54.226/2024" | Portal > Acesso à Informação (transparencia.prefeitura.rio/acesso-a-informacao/) |
| 15.4 Prazos, autoridade e recurso | Atende | Resposta: "até 20 dias para responder ao pedido. Este prazo, contudo, pode ser prorrogado por mais 10 dias, mediante justificativa expressa do órgão", com regras de contagem (Art. 61) e tabela de cientificação do pedido. Procedimento do pedido: cadastro (nome, documento, contato), descrição do pedido, protocolo para acompanhamento na Central 1746. Recurso 1ª instância: "10 dias para entrar com recurso, a partir da data de resposta do órgão" (ou após 30 dias da abertura sem resposta), "direcionado ao dirigente máximo do órgão [...] que se manifestará em até 05 dias". 2ª instância: "10 dias para entrar com recurso à Comissão de Reavaliação de Informações do Município do Rio de Janeiro (CORE-Rio)"; pareceres CORE 01 a 09 publicados. Procedimento do recurso: número do protocolo e descrição do descumprimento, pelo Portal 1746 | Portal > Acesso à Informação > Pedido de Informação (/acesso-a-informacao/pedido-de-informacao/) e > Recursos (/acesso-a-informacao/recursos/) |
| 16.2 Alto contraste | Atende | Opção "Alto Contraste" no painel "Ferramentas de Acessibilidade" (abre ao clicar no ícone azul de cadeira de rodas, à direita); o painel também tem Aumentar/Diminuir o Texto, Escala de Cinza, Contraste Negativo, Links Sublinhados, Fonte Legível. Na primeira exploração (09/10) o botão não foi visto, porque fica escondido no painel | Portal > ícone de acessibilidade (lateral direita) |
| 16.3 Redimensionar texto | Atende | "-A +A" no topo e "Aumentar o Texto / Diminuir o Texto" no painel | Topo e painel de acessibilidade |
| 16.4 Símbolo de acessibilidade | Atende | Ícone de acessibilidade e VLibras fixos na lateral; selo "Site compatível com leitores de tela" no topo | Todas as páginas |
| 18 LGPD | Provável | Ícone "LGPD" | Home do portal |
| Outros | Observado | Dados abertos, Contratos, Licitação, Painel de obras, Radar da Transparência, Ouvidoria | Home do portal |

## 3.1 APIs dos fornecedores

### Duque de Caxias (Modernização Informática)

| Item | Detalhe |
|---|---|
| Onde | Portal > API de Dados Abertos (Dados Abertos) > Documentação uso APIs (abre dentro do portal; a URL do navegador não muda, fica só transparencia.duquedecaxias.rj.gov.br). Na primeira tentativa (10/10 15:20) deu o mesmo erro "Network error IOException: Address already in use: connect"; abriu ao recarregar |
| Endpoint único | https://transparencia.duquedecaxias.rj.gov.br/sincronia/apidados.rule?sys=LAI |
| Parâmetros | JSON { "api": "<serviço>", "ano": <inteiro> } ("Consumo"); método HTTP não informado na tela, a testar |
| Catálogo | 60 serviços; cada um com documentação em JSON e PDF (https://transparencia.duquedecaxias.rj.gov.br/ver20230623/tmp/json_api/<serviço>.json/.pdf), exemplo de resposta, resultado de erro, metadados, dicionário (CREATE TABLE) e data de última alteração. Página "Data da Última Atualização: 24/09/2026" |
| Autodescoberta | Serviço "consulta_api" devolve a lista de APIs com nome e parâmetros de entrada |
| Chave de acesso | Nenhuma mencionada |
| Limitação | Alguns serviços avisam "Esta API só retorna dados do ANO corrente" |
| Serviços para o protótipo | 4.1 e 4.6: despesas_todas ("Consulta de Todas as Despesas Empenhadas, Liquidadas e Pagas"); alternativas despesas_empenhadas, despesas_liquidadas, despesas_pagas. 12.1: consulta_rgf_m2 ("Relatório de Gestão Fiscal - RGF - Modelo 2") |
| Reuso | O exemplo de resposta do "busca_avancada" traz "transparencia.mesquita.rj.gov.br": a mesma API e documentação são usadas em outros clientes da Modernização; o adaptador de Caxias deve servir para eles |
| Erros documentados | { "status": "erro", "retorno": "Não foi encontrado comando para busca. Entre em contato com suporte técnico da API." } e "Não existem registro para esse filtro" |

### Japeri (GeoSiap / Grupo Embras)

| Item | Detalhe |
|---|---|
| Onde | Rodapé do portal > "Documentação da API (Swagger)" > japeri.geosiap.net.br/portal-transparencia/api-docs (especificação em .../api-docs/v1/sw..., endereço cortado no print) |
| Base | /portal-transparencia/api, versão v1; quase todos os endpoints são GET (único POST visto: /licitacoes/licitacoes/new, registro de retirada de anexo, não usar) |
| Grupos | Configurações, Contatos, RH (cargos, servidores, estruturas remuneratórias, competências), Patrimônios, Execução (despesas, receitas, ordem cronológica, despesas detalhadas, fonte de aplicação, empenhos, diárias, adiantamentos, suprimento de fundos, repasse), Emenda Parlamentar, Folha de Pagamento, Licitações (atas, empresas penalizadas, licitações, contratos, manifestação de interesse, convênios), Portal (menu_itens, configurações), AAC, PEC, SIS (entidade, pessoa), Tabelas, SUP, PCA |
| Serviços para o protótipo | 4.1 e 4.6: GET /execucao/despesas_detalhadas/despesas_detalhadas (também /empenhos, /liquidacoes, /pagamentos no mesmo grupo e em "Execução - Empenhos"). Entidade: GET /sis_entidade (lista entidades, para obter o id da Prefeitura). 12.1: sem endpoint de publicações; continua pela página publicacoes?id_publicacao_tipo=5 |
| Parâmetros de despesas_detalhadas | id_entidade (obrigatório, inteiro); ano (texto; a descrição diz "Data no formato AAAA-MM-DD", inconsistente com o nome); data_inicial e data_final (alternativa ao ano: é obrigatório informar ano OU data_inicial e data_final); filtro (texto) |
| Campos da resposta (exemplo) | id_doc_despesa, ano_doc_despesa, nr_doc_despesa, doc_despesa, processo_despesa, dt_doc_despesa, tp_empenho, ... |
| Acesso direto | GET em https://japeri.geosiap.net.br/portal-transparencia/api/sis_entidade aberto direto no navegador devolve o JSON, sem chave nem sessão: o coletor pode usar requisição HTTP simples, sem navegador automatizado. A base sozinha (.../api) dá 404 |
| Resultado de /sis_entidade (testado em 10/10/2026 pelo "Try it out!") | 15 entidades no mesmo portal. Prefeitura: id_entidade "10", "PREFEITURA MUNICIPAL DE JAPERI", principal "1" (única com principal = 1). Câmara: id_entidade "1", "CAMARA MUNICIPAL DE JAPERI". Demais: 12 fundos municipais (Saúde id 3, Assistência Social id 4, Educação id 18, Cultura id 9 etc.) e PREVIJAPERI (id 2). Ids vêm como texto ("10"), embora a documentação diga inteiro |
| Resultado de despesas_detalhadas (testado em 10/10/2026 pelo "Try it out!") | Com id_entidade = 10 e "ano" = 2026 não funcionou; funcionou com data_inicial = 2026-10-01 e data_final = 2026-10-09. 7 empenhos da Prefeitura no período (só os emitidos no período e só da entidade 10; fundos ficam em outras entidades), ordenados do mais recente para o mais antigo. Campos usados: nr_doc_despesa (ex.: "925"), doc_despesa ("Empenho 925/2026"), dt_doc_despesa (ISO, "2026-10-09"), vl_empenhado, vl_liquidado, vl_pago (texto em reais, "R$ 261,15"), credor, doc_pessoa, classificação orçamentária completa (unidade, função, subfunção, programa, ação, conta, fonte). Totais no fim: total_empenhado, total_liquidado, total_pago. Data máxima: 2026-10-09 (confirma 4.6) |
| Cuidados no código | Valores vêm como texto com "R$", ponto de milhar e vírgula decimal: converter antes de somar. doc_pessoa traz CPF completo de pessoas físicas: mascarar na evidência. Usar sempre data_inicial e data_final (o parâmetro "ano" não respondeu) |
| Observações | Selo "INVALID" do validador Swagger no rodapé (especificação não passa na validação). Endereço segue o padrão <município>.geosiap.net.br: adaptador GeoSiap deve servir para outros clientes. Swagger tem botão "Try it out!" |

## 4. Regras de decisão

### 1.2 Acesso na capa

| Situação | Status |
|---|---|
| Link visível na capa, portal a 1 clique | Atende |
| Link na capa, mas dentro de submenu (aparece ao passar o mouse) ou portal a 2 cliques | Parcial |
| Sem link na capa | Não atende |

Rolar a página não conta como clique: link abaixo do banner (Caxias) é "visível na capa" (decidido em 10/10/2026). Rolagem entra só como desempate na nota gradual: status continua Atende, nota um pouco menor se o link só aparecer depois de rolar (ex.: 1,0 sem rolar, 0,9 com rolagem). Para ser reproduzível, o coletor abre sempre com o mesmo tamanho de janela (1366x768).

### 4.1 Empenho, liquidação e pagamento

A regra precisa aceitar os dois formatos de tabela encontrados:

| Formato | Onde | Como reconhecer |
|---|---|---|
| Largo: uma coluna de valor por fase | Japeri, Itaboraí, Cachoeiras | Cabeçalhos com empenhado, liquidado e pago + coluna de número do empenho |
| Longo: uma linha por fase | Caxias | Coluna de fase com valores Empenho / Liquidação / Pagamento + uma coluna de valor + coluna de número do empenho |

Usar só os cabeçalhos de Japeri daria falso negativo em Caxias.

### 4.6 Informação atualizada

- Prioridade 1: texto de atualização na página ("dados atualizados em", "Última Atualização", "Última atualização dos dados em").
- Prioridade 2 (sem texto de atualização, ou texto não confiável como o rodapé de Japeri): data máxima entre os registros. Exige percorrer a paginação ou aumentar linhas por página; não confiar na ordem (Betha ordena decrescente, Supernova crescente).
- Ignorar linhas de total/consolidado e datas posteriores à data da avaliação (Caxias tem "TOTAL DO MÊS (CONSOLIDADO)" com data 31/10/2026).
- Comparar com o último dia útil, não com a data da avaliação (avaliação num sábado não pode virar "desatualizado").

### 12.1 RGF

| Situação | Status |
|---|---|
| Publica o RGF e o mais recente é o último período que já deveria estar publicado (em outubro: 2º quadrimestre do ano) | Atende |
| Publica o RGF, mas o mais recente é de um período anterior | Parcial |
| Não publica RGF | Não atende |

- O período vem do título do relatório, não da coluna "Ano" (em Cachoeiras, "Ano 2025" aparece com "RGF - 1º QUADRIMESTRE 2024").
- Agrupar por (ano, quadrimestre): Caxias publica 5 demonstrativos por quadrimestre; republicação conta como a mesma competência (Itaboraí).
- O dia de atraso no upload não muda o status (Caxias: 2º quadrimestre enviado em 01/10/2026, prazo de 30 dias após o quadrimestre pela LRF art. 55, §2º, a conferir).
- Registrar como "não encontrado no portal", pois pode estar publicado em outro meio (Diário Oficial).
- Se o 12.2 entrar no protótipo, o atraso não pode ser punido nos dois critérios.

### 15.4 Prazos, autoridade e recurso

- Subitens: prazo de resposta, prazo recursal, autoridade, procedimento do pedido e do recurso. Subitem sem trecho citado = não atende.
- Juntar as páginas da seção do e-SIC antes de avaliar (Caxias: pedido em HTML numa página, recurso em imagem em outra). Avaliar página por página daria falso Parcial.
- Guardar número e unidade separados ("20 dias corridos" no pedido, "20 dias úteis" no recurso, em Caxias).

### Lista de status (decidida em 10/10/2026)

| Status | Quando usar | Entra no score? |
|---|---|---|
| Atende | Evidência completa | Sim |
| Parcial | Evidência incompleta (ex.: RGF atrasado) | Sim |
| Não atende | O coletor chegou à página certa e a informação não está lá | Sim |
| Inconclusivo | O coletor não conseguiu chegar ou ler (captcha, layout novo, formato desconhecido, OCR falhou) | Não; vai para revisão humana |
| Indisponível | Site fora do ar ou erro do servidor, mesmo depois das novas tentativas | Não; nova tentativa na próxima execução |
| Não aplicável | Critério não vale para o tipo de entidade (ex.: 19 a 21 para a Câmara) | Não |

- Os três últimos aparecem ao lado do score como cobertura (ex.: "6 de 6 critérios avaliados").
- No protótipo (6 critérios, 5 prefeituras) Não aplicável não ocorre; o status existe para o §11 e para quando o checklist crescer, com tabela critério x tipo de entidade na documentação.
- Inconclusivo pode não ocorrer no protótipo; existe porque, em escala, o sistema vai encontrar páginas que não sabe ler, e essa limitação não pode virar "Não atende".

### Indisponível

Erro do servidor ou site fora do ar = "Indisponível", nunca "Não atende". Dentro de uma execução: novas tentativas com intervalo crescente (ex.: 3 tentativas em cerca de 10 minutos). Persistindo, registra Indisponível com data, hora e erro, e a próxima execução agendada tenta de novo. Caso real: em Caxias, a consulta de despesas falhou às 11:35 e às 15:20 de 10/10 e abriu na segunda tentativa nas duas vezes; Japeri ficou fora do ar da tarde de 09/10 até 10/10.

### Identidade do coletor (decidida em 10/10/2026)

Teste com Playwright 1.63 na consulta de despesas da Betha (Cachoeiras de Macacu, .../consulta/31180), janela 1366x768:

| Modo | Resultado |
|---|---|
| Navegador invisível (headless) com User-Agent padrão ("HeadlessChrome") | 403 Forbidden |
| Navegador visível (headless=False) | Página carregou ("Portal da Transparência") |
| Navegador invisível com User-Agent próprio "GATE-MPRJ-Prototipo/0.1 (+https://github.com/Diegolbsilva/gate-case-ds)" | Página carregou ("Portal da Transparência") |

- Decidido: o coletor se identifica de forma honesta, com User-Agent próprio e link do repositório (o site sabe quem acessa e pode liberar ou bloquear).
- Reserva, se um portal bloquear a identidade própria: navegador visível (Chrome real, sem disfarce), documentando a limitação.
- Descartado: disfarçar o navegador como Chrome comum (não é postura adequada para um órgão de controle).
- Na documentação: em produção, o caminho para bloqueios é institucional (MPRJ solicita ao fornecedor liberação ou acesso aos dados abertos), não contornar a proteção.

### Caminho de coleta em cascata (decidido em 12/10/2026)

Objetivo: escalar sem código por prefeitura. O código especial é por FORNECEDOR (poucos, cada um cobre muitos municípios).

1. Detectar o fornecedor automaticamente pela URL e pelo HTML da capa do portal (domínio, rodapé, assinaturas), registrando a evidência.
2. Fornecedor com adaptador (GeoSiap: API; Modernização: API; Betha: consultas por endereço direto): usar o adaptador.
3. Sem adaptador ou adaptador falhou: descoberta genérica (textos clicáveis + dicionário de termos do checklist, até 2 cliques).
4. Descoberta falhou: cadastro manual como reserva.
5. Nada funcionou: Inconclusivo.

- Cadastro por prefeitura: só site oficial e tipo de entidade; flag de fornecedor no cadastro apenas como exceção manual (forçar caminho quando a detecção errar).
- Cada avaliação registra por qual caminho foi resolvida (adaptador, descoberta, cadastro): métrica de escala para a documentação.
- Descoberta genérica, primeiro teste nas 10 capas reais (12/10/2026, HTML estático): primeiro clique certo em 19 de 20 alvos. Falha: Rio, despesas ("CONTAS RIO" não contém termo de despesa); resolvida pela reserva do cadastro, sem acrescentar termo específico do município ao dicionário.
- Achado da descoberta: a capa do site de Japeri tem um quadro "PORTAL DE TRANSPARÊNCIA" com link direto para o portal (gabarito manual registrou 1.2 Parcial por 2 cliques no menu): conferir visibilidade e, se visível, corrigir o gabarito para Atende.

### Unidade avaliada (decidida em 10/10/2026)

Unidade avaliada: o Poder Executivo municipal (Prefeitura, fundos e autarquias), sem a Câmara, para usar a mesma régua em todas as prefeituras.

| Prefeitura | O que o portal mostra | Como o coletor aplica |
|---|---|---|
| Caxias | Prefeitura + fundos na mesma tabela | Como vem |
| Itaboraí | Prefeitura + fundos na mesma tabela | Como vem |
| Cachoeiras de Macacu | Prefeitura + fundos + autarquias + instituto de previdência na mesma tabela | Como vem |
| Rio de Janeiro | Toda a administração, com filtro por unidade gestora | Sem filtro de unidade |
| Japeri | Uma entidade por vez (Prefeitura id 10, Câmara id 1, 12 fundos, PREVIJAPERI id 2) | Laço na API sobre todas as entidades de /sis_entidade, exceto a Câmara, juntando os resultados |

- A Câmara nunca entra na avaliação da Prefeitura (outro Poder).
- Nos 6 critérios atuais o resultado não muda; a regra fica uniforme e documentada para critérios futuros mais sensíveis.

### Score: decisões tomadas (10/10/2026)

- Problema: com 6 critérios, 24 de 30 células deram Atende; Rio e Caxias empatam com 6/6.
- Decidido: (A) notas graduais dentro dos critérios, usando o detalhe já coletado (15.4: subitens atendidos de 4; 12.1: quadrimestres de atraso; 1.2: cliques ou submenu); (D) pesos por importância (obrigação legal da LRF/LAI pesa mais que boa prática), com discussão dos problemas da média simples (pedida no §5).
- Opcional, se sobrar tempo (17 e 18/10): (B) 16.5 acessibilidade automática (AccessMonitor ou axe-core via Playwright), única opção que tende a separar Rio de Caxias por dar nota contínua.
- Descartado: (C) adicionar mais critérios simples (quase todos dariam Atende).
- Na documentação: assumir o empate Rio/Caxias como resultado honesto (ambos atendem a tudo o que foi medido) e explicar que o poder de separação cresce com o número de critérios.

| Nota gradual (dados do gabarito) | 15.4 (subitens) | 12.1 (atraso) | 1.2 (cliques) |
|---|---|---|---|
| Rio | 4/4 | 0 | 1 |
| Caxias | 4/4 | 0 | 1 |
| Itaboraí | 4/4 | 0 | submenu |
| Cachoeiras | 2/4 | 2 quadrimestres | 1 |
| Japeri | 0/4 | 1 quadrimestre | 2 |

## 5. Desafios técnicos encontrados e decisão de arquitetura

| Desafio observado | Onde | Decisão para a solução |
|---|---|---|
| Portais de fornecedores diferentes (GeoSiap/Embras, Modernização Informática) | Japeri, Caxias | Identificar o fornecedor (domínio, rodapé, presença de Swagger) e usar adaptadores por fornecedor; caminho genérico para os demais |
| Fornecedor com API pública documentada | Japeri | Quando houver API, consultar a API (dados estruturados, mais barato e confiável); raspar a página só quando não houver |
| Conteúdo carregado por JavaScript; consulta exige preencher filtros e clicar em "Pesquisar" | Japeri (Despesas Detalhadas); WebFetch não conseguiu carregar o portal | Navegador automatizado (Playwright) para o caminho genérico |
| Nomenclatura diferente do checklist ("Execução Orçamentária" em vez de "Despesa"; e-SIC dentro de "Atendimento / Ouvidoria") | Japeri | Dicionário de sinônimos por critério; LLM como apoio para mapear menus quando as regras falham |
| Informação espalhada em várias páginas, a 3 ou 4 cliques da home | Caxias (15.4) | Crawler com limite de profundidade e priorização de links por palavras-chave |
| Informação dentro de imagem (infográfico), não em texto | Caxias (15.4) | OCR ou modelo de visão para extrair o texto; guardar a imagem como evidência |
| Critério ambíguo ("visível na capa" com 2 cliques conta?) | Japeri (1.2) | Definir regra explícita na documentação e usar o status "Parcial" |
| Site fora do ar | Japeri, 14:59 | Status "indisponível" (não é "não atende"), novas tentativas com intervalo crescente, registro do erro com data e hora |
| Portal de outra entidade com nome parecido (Câmara) | Japeri; Caxias (ícone da Câmara ao lado do portal na capa e dentro do portal) | Validar o tipo de entidade antes de avaliar; cadastro de entidades com URL confirmada |
| Mesmo portal do fornecedor serve várias entidades do município (Prefeitura, Câmara, 12 fundos, instituto de previdência) | Japeri (GeoSiap, /sis_entidade) | Usar o campo "principal" = 1 para achar a Prefeitura automaticamente; a Câmara no mesmo portal é o caso real para o §11 (tipo de entidade): Poder Legislativo, matriz específica do Executivo (19 a 21) não aplicável. Decidido: unidade avaliada = Poder Executivo inteiro sem a Câmara; em Japeri, juntar todas as entidades exceto a Câmara (seção 4, "Unidade avaliada") |
| Três modelos diferentes em três prefeituras: fornecedor com API (Japeri), fornecedor sem API conhecida (Caxias), desenvolvimento próprio (Itaboraí) | Japeri, Caxias, Itaboraí | Reforça a arquitetura híbrida: adaptador por fornecedor quando houver, caminho genérico (navegador, regras e LLM) para os demais |
| Portal mudou de endereço ("transparencianovo") | Itaboraí | Cadastro de entidade com histórico de URLs; descoberta automática do portal a partir do site oficial a cada execução; alerta quando a URL muda |
| Site oficial redireciona para outro endereço (duquedecaxias.rj.gov.br → portal.duquedecaxias.rj.gov.br) | Caxias | Registrar a URL final após redirecionamento junto com a cadastrada; mudança de redirecionamento entra no alerta de URL |
| Sinais de atualização na própria interface ("N novos documentos inseridos em 1 semana") | Itaboraí | Usar como evidência adicional do critério de atualização |
| Link do portal escondido em menu suspenso (aparece ao passar o mouse) no site oficial | Itaboraí | Buscar o link no HTML completo (o item existe no código mesmo escondido) e registrar se é visível sem interação; regra explícita do 1.2 para link em submenu |
| Pop-up (modal) cobrindo a capa do site | Caxias (Anistia Fiscal), Itaboraí (Adiamento de Audiência) | Fechar o modal é etapa padrão do coletor antes de ler a capa; ler o HTML não depende do modal |
| Link do site abre o portal em nova aba | Caxias (nova aba); Itaboraí, sistema Supernova (mesma aba) | Ler o endereço do link (href) em vez de depender do clique; quando precisar clicar, tratar a nova aba |
| Opção de acessibilidade dentro de widget que só abre ao clicar | Caxias e Rio (16.2 no portal) | Procurar o texto ("Alto contraste") no HTML completo, não só no que está visível. No Rio, a própria avaliação manual de 09/10 deixou passar o botão por estar escondido no painel |
| Site oficial em domínio .com, não .gov.br | Cachoeiras de Macacu | Não usar o domínio .gov.br como prova de que o site é oficial; cadastro de entidades com URL confirmada manualmente |
| Betha bloqueia o navegador invisível padrão com 403 Forbidden (User-Agent "HeadlessChrome"); libera navegador visível e navegador invisível com User-Agent próprio | Cachoeiras de Macacu (teste de 10/10/2026) | Identidade honesta do coletor (seção 4, "Identidade do coletor"); bloqueio vira evidência de que, em escala, cada fornecedor pode exigir tratamento próprio |
| Plataforma de fornecedor grande e compartilhada (Betha): mesmo portal para vários municípios, entidade identificada por código na URL; página montada por JavaScript (rota com "#/") | Cachoeiras de Macacu | Adaptador Betha tem alto retorno (serve para todos os municípios clientes); guardar o código da entidade no cadastro; navegador automatizado obrigatório, pois o HTML inicial vem vazio |
| Cada consulta Betha tem endereço próprio (listagem ".../consultas/52185", consulta ".../consulta/31180") | Cachoeiras de Macacu | Adaptador Betha abre a consulta direto pelo número; a confirmar se o número é o mesmo em outros municípios ou muda por entidade |
| Cards com nome quase igual ("Execução Detalhada de Despesas" e "Execução Detalhada de Despesas Multas de Trânsito") | Cachoeiras de Macacu | Preferir nome exato; excluir termos de recorte ("Multas de Trânsito", "Pessoal") na busca por palavra-chave |
| Capital com vários portais e acessos (Transparência Rio, Portais de Transparência da Saúde, Data.Rio, Acesso à Informação), em vez de um portal único | Rio de Janeiro | Cadastro permite mais de uma URL por entidade, cada uma com papel definido (portal principal, dados abertos, e-SIC); critério pode ser atendido em qualquer uma delas, com a URL registrada na evidência |
| Portal funciona como central de links: os dados ficam em sistemas separados (ex.: "Contas Rio" para receitas e despesas) | Rio de Janeiro | Crawler segue links para outros sistemas, mas só dentro de uma lista de domínios da entidade (ex.: *.prefeitura.rio, *.rio), para não sair do escopo; registrar em qual sistema a evidência foi achada |
| Despesas do Rio em domínio fora do padrão previsto: portal em transparencia.prefeitura.rio, Contas Rio em rio.rj.gov.br e contasrio.rio.rj.gov.br; dois saltos de domínio, cada um em nova aba | Rio de Janeiro | A lista de domínios permitidos vem dos links que o portal oficial aponta, não de padrão de nome (*.prefeitura.rio e *.rio bloqueariam o Contas Rio) |
| Sistema dividido por período: Novo Contas Rio (a partir de 2024, SIAFIC Carioca, Decreto Rio nº 53.891/2024) e Antigo (até 2023) | Rio de Janeiro | Coletor escolhe o sistema pelo período avaliado; critérios de histórico (ex.: 4.7) precisam juntar os dois |
| Página com totais agregados e gráficos, com os textos "Despesa Empenhada / Liquidada / Paga", mas sem empenho individual | Rio de Janeiro (Despesas > Gráficos) | Regra do 4.1 exige número do empenho por registro; só as palavras dariam falso positivo |
| Consulta pesada: portal recomenda 2 filtros além de mês e ano; mostra no máximo 1.000 registros na tela, acima disso só por download | Rio de Janeiro (Despesas > Empenhos) | Coletor aplica filtros (mês atual) para não sobrecarregar o servidor; para data máxima ou volume, usar o botão de download em vez da tela |
| Tabela com rolagem virtual (só renderiza as linhas visíveis) e linha "Total" no topo | Rio de Janeiro (Empenhos) | Preferir o download do arquivo à leitura da tela; ignorar a linha de total |
| RGF num terceiro domínio (controladoria.prefeitura.rio), também em nova aba: o caminho até o RGF passa por 4 sistemas (portal, rio.rj.gov.br, contasrio.rio.rj.gov.br, controladoria.prefeitura.rio) | Rio de Janeiro | Limite de profundidade do crawler contado por clique, não por domínio; registrar a cadeia completa de URLs na evidência |
| Mesma página com dois blocos de anos idênticos (RREO em cima, RGF embaixo) | Rio de Janeiro (Quadros da LRF) | Associar o link ao título da seção mais próxima acima dele; não pegar o primeiro "2026" da página |
| Só o número do ano é clicável; a caixa cinza ao redor não reage | Rio de Janeiro (Quadros da LRF) | Ler o href do elemento de texto em vez de clicar na área do card |
| Período listado sem link ("3º Quadrimestre - Arquivo Editável" em texto comum) ao lado de períodos publicados (com link) | Rio de Janeiro (RGF 2026) | Período só conta como publicado se tiver link para arquivo; só o texto daria falso positivo para o 3º quadrimestre |
| Sistema de despesas de terceiro fornecedor em domínio e porta próprios (itaborai.supernova.com.br:8443), linkado a partir do portal oficial | Itaboraí | A lista de domínios permitidos inclui os sistemas de fornecedor linkados pelo portal oficial; sem isso, o próprio crawler bloqueia a evidência do 4.1 |
| Formulário JSF (".xhtml"), dependente de estado de sessão; parâmetro "?exercicio=2026" na URL, aceito sem validação (com "{ano}" literal a tela mostra "EXERCÍCIO : {ANO}" e usa 2026). Endereço direto deu "Internal Server Error" uma vez (10/10/2026, por volta de 16:35) e abriu normalmente às 16:43, sem visita prévia ao Supernova | Itaboraí (Supernova) | Navegador automatizado (JSF); endereço direto como ponto de partida, com novas tentativas em caso de erro do servidor e entrada pelo link do portal como alternativa. Validar o parâmetro do exercício no próprio coletor |
| Consulta carregada dentro de quadro embutido (iframe) | Caxias (despesas) | Coletor entra no iframe para ler a tabela |
| Erro do servidor exibido como modal dentro da página, com resposta HTTP normal ("Network error IOException: Address already in use: connect") | Caxias (despesas, 10/10 11:35) | Reconhecer textos de erro na página, não só o código HTTP; nova tentativa antes de registrar "indisponível" |
| reCAPTCHA antes do botão Pesquisar | Caxias (despesas e RGF) | Não burlar captcha (limitação documentada). Ler o que está fora dele: datas de "Última Atualização" e cabeçalhos da tabela vazia (4.1 com confiança menor). Caminho alternativo confirmado na documentação: API de Dados Abertos (serviços despesas_todas e consulta_rgf_m2, seção 3.1), sem captcha; chamada real a testar no código |
| Dois formatos de tabela de despesas (colunas por fase x linha por fase) | Caxias x Japeri, Itaboraí, Cachoeiras | Regra do 4.1 aceita os dois formatos (seção 4) |
| Linhas de total consolidado com data futura e nº de empenho 0 | Caxias (despesas) | Ignorar linhas de total e datas posteriores à avaliação no cálculo da data máxima |
| Ordenação diferente entre sistemas; ausência de texto de atualização | Betha (decrescente), Supernova (crescente, sem rótulo) | Calcular a data máxima percorrendo a paginação; nunca assumir que a primeira página tem o mais recente |
| Codificação de texto quebrada ("Preg?o Eletr?nico") | Itaboraí (Supernova, coluna Modalidade) | Normalizar o texto antes de comparar por palavra-chave |
| CPF completo de pessoas físicas na tabela de despesas (Caxias); CPF mascarado (Itaboraí) | Caxias, Itaboraí | Mascarar CPF em trechos e prints guardados como evidência (LGPD na própria solução) |
| Submenu escondido: a categoria só mostra RGF e RREO depois do clique | Itaboraí (15 - Relatórios Fiscais LRF) | Crawler precisa clicar e esperar o menu abrir, não só ler os links do HTML inicial |
| Documento atrás de mais um clique ("Ver mais detalhes") e lista paginada (4 páginas) | Itaboraí (RGF) | Ler o título dos cards resolve o critério sem abrir o PDF; abrir o arquivo só para confirmar; percorrer a paginação quando precisar do histórico |
| Periodicidade define o que é "em dia": RGF é quadrimestral | Itaboraí, Caxias, Cachoeiras (RGF) | Regra de atualização por tipo de documento: calcular o último período que já deveria estar publicado na data da avaliação (ex.: em outubro, o 2º quadrimestre) e comparar com o mais recente encontrado |
| RGF atrasado: mais recente é o 3º quadrimestre de 2025 | Cachoeiras de Macacu | Primeiro caso em que o sistema precisa distinguir "existe" de "está em dia" (12.1 Parcial) |
| Coluna "Ano" não corresponde ao período do relatório | Cachoeiras de Macacu (RGF) | Extrair a competência do título do relatório |
| Republicações com o mesmo período ("1ª Republicação") | Itaboraí (RGF) | Extrair período do título com expressão regular e tratar republicação como mesma competência, sem contar duas vezes |
| Vários demonstrativos por quadrimestre, com Ano e Quadrimestre em colunas próprias | Caxias (RGF, 5 linhas por quadrimestre) | Agrupar por (ano, quadrimestre); contagem de registros não é contagem de relatórios |
| Rótulo "dados atualizados em" que acompanha a hora da visita | Japeri (rodapé GeoSiap) | Validar o rótulo: se for igual à hora da coleta em execuções seguidas, descartar e usar a data máxima dos registros |
| RGF agrupado em árvore (Exercício > Subtipo/Anexo > Quadrimestre), depois de escolher a Entidade e clicar em Pesquisar | Japeri (GeoSiap) | Adaptador GeoSiap: selecionar a entidade certa no filtro (há outras entidades no mesmo portal) e ler os níveis da árvore; endereço com "id_publicacao_tipo=5" permite ir direto |
| Mesmo nome de arquivo ligado a quadrimestres diferentes ("RGF 1.2025-04-24_11_11_03.pdf" no 1º e no 3º Quadrimestre de 2024; "75620212RGF1.pdf" no 2º e no 3º de 2022) | Japeri (RGF) | Guardar hash de cada arquivo; mesmo hash em períodos diferentes vira alerta de possível publicação trocada, para revisão humana |
| Quadrimestres faltando no meio do histórico (2025 só com o 1º) e anexos incompletos no período mais recente (2026 só com Anexos I e II) | Japeri (RGF) | Para o 12.1 conta o período mais recente; lacunas do histórico vão para a evidência e para um futuro 12.3 |
| Link de download em pasta temporária (".../webrun/tmp/lai_lei_RGF/<código>") | Caxias (RGF) | Guardar o arquivo baixado com hash como evidência, não só a URL, que pode expirar |
| Botões de exportação (CSV, Excel, PDF) | Itaboraí (RGF), Caxias e Cachoeiras (despesas) | Evidência para critérios de formato aberto / exportação |
| Mesmo modelo de página para todo conteúdo: card com título, unidade, ano e "Ver mais detalhes" (vale para RGF e para "Prazos de respostas do SIC"); o título do card não traz o conteúdo | Itaboraí | Um único adaptador para o portal inteiro (o template se repete); para critérios semânticos (15.4) é obrigatório abrir o detalhe, o título não basta |
| Detalhe abre em janela (modal) sem texto; o conteúdo está num arquivo para baixar com nome genérico ("ANEXO 1") | Itaboraí (15.4) | Coletor precisa abrir o modal, baixar o anexo e extrair o texto (PDF com texto: extração direta; PDF escaneado ou imagem: OCR). Nome do arquivo não serve de evidência; guardar o arquivo baixado e o link ("Copiar link") como evidência |
| Mesmo critério (15.4) em três formatos: imagem (Caxias), PDF com texto em tabelas (Itaboraí), página HTML (Caxias, prazo do pedido) | Caxias, Itaboraí | Etapa de extração com roteamento por tipo: HTML → texto da página; PDF com texto → extração direta preservando tabelas (ex.: pdfplumber); PDF sem texto ou imagem → OCR. Decidir pelo próprio arquivo (tem camada de texto?), não pela extensão |
| 15.4 dividido em duas páginas e dois formatos; unidades diferentes (dias corridos x úteis) | Caxias | Juntar as páginas da seção do e-SIC antes do LLM; extrair número e unidade separados |
| Página do e-SIC em passo a passo ("Próximo") que termina em login com CPF (Colab) | Caxias | Texto útil está no primeiro passo; coletor não segue até a autenticação |
| Formulário de pedido com reCAPTCHA antes de "Enviar" | Cachoeiras de Macacu (Betha) | Coletor só lê o formulário (campos obrigatórios servem de evidência para o 15.2); nunca preenche nem envia pedido |
| e-SIC terceirizado para plataforma federal (Fala.BR, falabr.cgu.gov.br), com banner de cookies cobrindo a página | Japeri | Conteúdo genérico da plataforma federal não conta como divulgação da prefeitura no 15.4; o 15.1 conta (canal existe). Fechar o banner de cookies, como os pop-ups das capas |
| Texto da LAI com cara de padrão da plataforma, sem decreto municipal nem autoridade nomeada | Cachoeiras de Macacu (Betha) | Comparar com outro município cliente da Betha: se o texto for idêntico, a evidência é do fornecedor, não da prefeitura. Para o 15.4, "ao órgão" não conta como autoridade identificada |
| 15.4 dividido em duas páginas HTML (Pedido de Informação e Recursos), com texto repetido na mesma página ("até 20 dias" aparece duas vezes) | Rio de Janeiro | Confirma a regra de juntar as páginas da seção antes do LLM; remover parágrafos duplicados para não gastar contexto |
| Páginas com metadado "Publicado em ... / Atualizado em ..." | Rio de Janeiro (Acesso à Informação) | Evidência adicional de atualização da própria página |
| Documento completo atende o critério de uma vez (prazos, recursos, autoridades e base legal), mas mistura conteúdo extra (lista de secretários) | Itaboraí (15.4) | LLM recebe o texto extraído e responde por subitem (prazo de resposta, prazo recursal, autoridade, procedimento), citando o trecho; subitem sem trecho citado = não atende |

## 6. Tipos de verificação (critérios do protótipo)

| Tipo | Exemplo | Técnica |
|---|---|---|
| Existência simples | 16.2 alto contraste, 16.3 A-/A+ | Regra: procurar elemento ou texto na página |
| Navegação | 1.2 acesso na capa | Regra: link na home e número de cliques |
| Dados estruturados | 4.1 empenho, liquidação, pagamento | Regra: cabeçalhos da tabela; ou API do fornecedor |
| Documento | 12.1 RGF | Encontrar arquivos (PDF) e checar título e período |
| Atualização | 4.6 | Regra: data de "atualizado em" ou data do registro mais recente, comparada à data da avaliação |
| Interpretação semântica | 15.4 prazos e recurso | LLM sobre trechos já coletados, com citação obrigatória do trecho como evidência; OCR quando o texto estiver em imagem |

## 7. Validação dos resultados

Usar as notas do Radar da Transparência Pública (PNTP) como referência externa: comparar a classificação do sistema com a oficial e medir a concordância. Selos observados nos portais: Rio "Diamante 2024", Caxias "Ouro 2025", Itaboraí "Prata". Os três níveis diferentes formam um teste natural: o score do sistema deve ordenar as três prefeituras na mesma ordem dos selos. Japeri e Cachoeiras de Macacu têm link para o Radar, selo a consultar no próprio Radar.

## 8. Pendências

- Betha: comparar o texto "Sobre a LAI" de Cachoeiras com o de outro município cliente.
- Rio: confirmar telefone e horário (2.5, 2.6), se entrarem no protótipo.
- Rio 1.2: verificar no coletor (janela 1366x768) se o ícone "Transparência Rio" aparece sem rolar (possível desempate com Caxias).
- Caxias: testar no código a chamada à API (método HTTP, resposta de despesas_todas e consulta_rgf_m2 para 2026, se precisa de cabeçalho ou sessão).
- Betha: confirmar se o número da consulta (ex.: 31180) é o mesmo em outros municípios.
