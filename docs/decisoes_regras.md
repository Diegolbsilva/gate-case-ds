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

- **1.2, link não achado = Não atende, com duas travas.** O critério mede se o cidadão acha o portal pela capa; se nenhum texto clicável tem relação com transparência, o cidadão também não acharia. Travas: (1) a capa precisa ter carregado com conteúdo e sem captcha, senão Inconclusivo (ou Indisponível, se nem abriu); (2) o robô lê o texto alternativo (`alt`) das imagens, para não punir banner "Portal da Transparência" feito de imagem. Para isso a descoberta passou a salvar a capa do site (`descoberta_capa_site`), que também vira a evidência visual do 1.2.
- **4.6, seguir a referência legal que o avaliador usaria.** "Tempo real" = disponibilização até o 1º dia útil seguinte à data do registro contábil (Decreto 10.540/2020, art. 7º, §1º, com o requisito do Anexo incluído pelo Decreto 11.644/2023; o Decreto 7.185/2010, que tinha a mesma regra, foi revogado pelo art. 19 do Decreto 10.540/2020). Avaliando no dia D, o registro do último dia útil antes de D ainda está no prazo (vence no próprio D); o de qualquer dia útil anterior já tem que estar publicado. Por isso: até 1 dia útil entre a data mais recente e D = Atende. Feriado não é dia útil.
- **4.6, Parcial mantido** (de 2 dias úteis a 30 dias corridos). O decreto não define parcial; é critério nosso, para separar "atrasou alguns dias" de "parou de publicar" e dar mais informação ao score.
- **Melhor resultado entre as fontes** (seção 1, passo 3): decorre da proposta 2 aprovada em 12/10/2026.

## 4.1 Limitações e melhorias futuras

| Limitação | Efeito | Melhoria futura |
|---|---|---|
| Só feriados nacionais na conta de dias úteis | Feriado estadual ou municipal (ex.: São Jorge, 23/04, no RJ) conta como dia útil e pode gerar Parcial falso no 4.6 | Tabela de feriados por município e ano |
| O robô vê a data do registro mais recente publicado, não a data do registro contábil | Dia sem nenhum empenho "envelhece" a data sem descumprimento; risco maior em entidade pequena ou quando só parte das entidades responde à API | Preferir o rótulo "dados atualizados até" (já é a prioridade quando existe); usar datas de liquidação e pagamento também |
| 1.2 sem faixa de "texto fraco" | Link com nome distante de transparência (ex.: só "Acesso à Informação") dá Não atende mesmo se levar ao portal | Termos fracos no dicionário; se o clique leva ao portal, Parcial (acesso indireto) |

## 5. Resultado na execução oficial de 13/10/2026 (execução 16)

24 de 25 células iguais ao gabarito (15.4 fica para o LLM). A diferença:

- Rio 4.1: Inconclusivo, gabarito Atende. A tabela do Contas Rio ainda carregava depois de 90 s. É limite da coleta, não da regra: a mesma regra aplicada ao HTML da execução 12 (tabela carregada) dá Atende. Correção: espera pelo indicador de carregamento subiu para 180 s.

Com as decisões finais de 13/10 (1.2 e 4.6 acima) o resultado na execução 16 é o mesmo: 24 de 25.

Testes: 28 casos pequenos montados a partir dos portais reais, todos ok (`python -m regras.teste_regras`).
