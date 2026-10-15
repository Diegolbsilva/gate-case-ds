# Score: metodologia e decisões (15/10/2026)

Código: `regras/score.py` (chamado no fim de `regras/avaliar.py`). Parâmetros: `config/score.yaml`. Testes: `regras/teste_regras.py`.

## 1. O que o score faz

Resume as avaliações de uma entidade numa execução num número de 0 a 100, com a cobertura (quantos critérios entraram) e uma faixa. Fica gravado na tabela `scores`, uma linha por execução e entidade, o que dá a evolução no tempo (§7).

## 2. Passo a passo

| Passo | Regra | Por quê |
|---|---|---|
| 1. Nota do critério (0 a 1) | Atende = 1; Não atende = 0; Parcial = nota gradual (tabela da seção 3); Indisponível = 0,5 | A nota mede quanto do que o critério pede foi cumprido |
| 2. Quem fica fora | Inconclusivo e Não aplicável não entram no cálculo; aparecem como cobertura ("5 de 6") | Inconclusivo é limitação do sistema (a fonte não pôde ser lida), não falha da entidade. Ex.: Japeri 4.6 em 15/10, API que não respondeu dentro do tempo limite definido pelo coletor |
| 3. Pesos | Essencial 2; Obrigatória 1,5; Recomendada 1 (pesos do PNTP) | Um RGF atrasado pesa mais que a falta de botão de contraste |
| 4. Score | soma(peso × nota) ÷ soma dos pesos dos critérios que entraram | Média ponderada; o denominador muda com a cobertura, por isso a cobertura é mostrada junto |
| 5. Faixa | Faixas do PNTP; Diamante, Ouro e Prata exigem 100% dos essenciais atendidos | Uma falha num essencial não pode ser compensada por critérios fáceis |
| 6. Comparação | Grava também a média simples binária (% de Atende) e a média simples das notas (sem peso) | Para a discussão da seção 5 |

## 3. Nota gradual de cada critério

| Critério | Classificação | Parcial vale | Origem da fórmula |
|---|---|---|---|
| 1.2 Acesso ao portal pelo site | Obrigatória | 0,5 (link só no submenu) | Ponto médio adotado por convenção |
| 4.1 Empenho, liquidação, pagamento | Essencial | informações achadas ÷ 4 | O critério pede 4 informações (número, empenhado, liquidado, pago), sem hierarquia entre elas |
| 4.6 Despesa em tempo real | Essencial | 0,5 (de 2 dias úteis a 30 dias corridos) | Ponto médio adotado por convenção |
| 12.1 RGF | Essencial | 1 − quadrimestres de atraso ÷ 3 (mínimo 0) | O RGF é quadrimestral: cada relatório em falta tira 1/3; 3 de atraso = um ano sem RGF = mesma nota de não publicar |
| 15.4 e-SIC | Obrigatória | subitens comprovados ÷ 5 | O critério tem 5 subitens (decisão de 15/10, texto literal) |
| 16.2 Alto contraste | Obrigatória | não existe Parcial | Ou o controle existe, ou não |

## 4. Decisões (tomadas por Diego em 15/10/2026)

- **Classificação dos critérios.** O checklist do case não traz classificação (só item, critério e fundamentação). Adotada a lógica do PNTP: Essencial = execução orçamentária e financeira, cuja falta impede transferências voluntárias (LRF, arts. 48, 48-A e 51): 4.1, 4.6 e 12.1. Obrigatória = exigida por lei: 1.2, 15.4 e 16.2. Trata-se de classificação própria do sistema, inspirada no PNTP, registrada em `config/score.yaml`.
- **Indisponível com 0,5; Inconclusivo fora.** Site fora do ar (mesmo depois das novas tentativas) é falha da entidade: o cidadão também não acessa. Punição leve, não zero, porque pode ser momentâneo. Inconclusivo é limitação do sistema e não pode virar nota da entidade.
- **Faixas do PNTP em vez de bônus por essencial.** O bônus contaria duas vezes o que o peso já conta e poderia passar de 100. As faixas dão efeito real à regra dos essenciais sem mexer no número.
- **Essencial Inconclusivo não bloqueia a faixa; fica marcada como provisória.** Princípio: falha provada da entidade pune, limitação do método não pune. Essencial Parcial, Não atende ou Indisponível (site fora do ar) bloqueia Diamante, Ouro e Prata. Essencial Inconclusivo não bloqueia, porque a causa não está provada; a faixa sai com a marca "provisória" e o critério não verificado (`faixa_provisoria`, `essenciais_nao_verificados`). Diferenciar a causa de um Inconclusivo (plataforma ou aplicação) foi considerado e descartado: nos dois casos reais a informação estava disponível ao cidadão (Rio 4.1, tabela que carrega após alguns minutos; Japeri 4.6, dados visíveis na tela e na API com tempo limite maior), e atribuir culpa sem prova é o erro mais grave num contexto de fiscalização. Quando há prova de falha da plataforma, o status já não é Inconclusivo: é Indisponível ou Não atende. Caso real: Rio, execuções 16 e 19, 4.1 Inconclusivo, score 100: Diamante provisório (antes da decisão, Elevado).
- **Por que alinhar ao PNTP e não só consultar o PNTP.** O PNTP é anual, preenchido pela própria entidade e validado por amostra; o sistema é automático, frequente, com evidência de cada critério (página, trecho, hash, data) e histórico entre os ciclos. Alinhar pesos e faixas dá linguagem comum com quem já usa o PNTP e permite validar contra os selos oficiais. Nota gradual, cobertura, evidência e frequência são do sistema.

## 5. Por que a média simples é problemática (§5)

| Problema da média simples | Como o score trata |
|---|---|
| Todos os critérios pesam igual: alto contraste vale o mesmo que o RGF | Pesos por classificação |
| É binária: Parcial com 1 quadrimestre de atraso vale o mesmo que com 2 | Nota gradual |
| Compensação: ir bem em critérios fáceis esconde a falha num essencial | Faixa exige 100% dos essenciais |
| Critério não avaliado distorce: contar como 0 pune a entidade por falha do coletor; ignorar sem avisar esconde a lacuna | Fora do cálculo, com cobertura explícita |
| Poucos critérios separam pouco | Assumido: com 6 critérios, empates (Rio e Caxias) são resultado honesto; o poder de separação cresce com o número de critérios |

Resultado com os dados reais: seção 6.

## 6. Resultado na execução 25 (15/10/2026)

Soma dos pesos com os 6 critérios: 10,5 (3 essenciais × 2 + 3 obrigatórios × 1,5).

| Entidade | Score | Faixa | Essenciais | Cobertura | Média simples binária | Média simples das notas | Observação |
|---|---|---|---|---|---|---|---|
| Duque de Caxias | 100,0 | Diamante | completos | 6 de 6 | 100,0 | 100,0 | |
| Rio de Janeiro | 100,0 | Diamante | completos | 6 de 6 | 100,0 | 100,0 | |
| Itaboraí | 92,9 | Ouro | completos | 6 de 6 | 83,3 | 91,7 | 1.2 Parcial (link só no submenu) |
| Cachoeiras de Macacu | 81,6 | Elevado | pendentes | 6 de 6 | 66,7 | 82,2 | 12.1 Parcial (2 quadrimestres de atraso); 15.4 com 3 de 5 subitens |
| Japeri | 74,5 | Intermediário | pendentes | 5 de 6 | 60,0 | 73,3 | 4.6 Inconclusivo (fora do cálculo); 12.1 Parcial; 15.4 Não atende |

Leitura dos números:

- **Nota gradual (média binária para média das notas).** A média binária trata Parcial como falha total: Itaboraí perde 1/6 inteiro por ter o link do portal só no submenu (83,3). Com a nota gradual, o mesmo Parcial custa metade (91,7). Cachoeiras sobe de 66,7 para 82,2, porque o atraso de 2 quadrimestres e os 3 de 5 subitens do 15.4 deixam de valer zero.
- **Pesos (média das notas para score).** O peso desloca o resultado conforme o lugar da falha. A falha de Itaboraí está num critério obrigatório (1.2): o score sobe para 92,9. A de Cachoeiras está num essencial (12.1): o score cai para 81,6. Com média simples, as duas falhas teriam o mesmo efeito.
- **Faixa e essenciais (compensação).** Cachoeiras, com 81,6, estaria na faixa Prata pelo número. Como o RGF (essencial) está atrasado, fica em Elevado: a falha no essencial não é compensada pelos demais critérios.
- **Cobertura.** Japeri tem 5 de 6 critérios no cálculo: o 4.6 ficou Inconclusivo porque a API da Prefeitura não respondeu no tempo limite da coleta (corrigido em 15/10; a partir da execução seguinte o critério volta ao cálculo). Contar o Inconclusivo como 0 baixaria o score para 60,3 por uma limitação do coletor.
- **Empate Rio e Caxias.** Os dois atendem integralmente aos 6 critérios medidos. O empate é resultado correto para o que foi medido; separar os dois exige mais critérios (ver seção 7).

Comparação com os selos do Radar da Transparência Pública (PNTP), observados nos portais:

| Entidade | Selo PNTP | Faixa do sistema |
|---|---|---|
| Rio de Janeiro | Diamante (2024) | Diamante |
| Duque de Caxias | Ouro (2025) | Diamante |
| Itaboraí | Prata | Ouro |

A ordem das três entidades é a mesma do PNTP (Rio e Caxias à frente de Itaboraí). Duas das três ficam uma faixa acima do selo oficial. Explicação provável: o sistema mede 6 critérios e o PNTP mede mais de 100; quem cumpre os 6 tende a ficar no topo. A comparação completa entra na validação (§15).

## 7. Limitações

| Limitação | Efeito | Melhoria futura |
|---|---|---|
| Os 0,5 do 1.2 e do 4.6 são convenção do sistema | Mudam o número, não a regra | Análise de sensibilidade (0,3 e 0,7) na documentação final |
| Classificação dos critérios inferida | Outra classificação mudaria os pesos | Usar a classificação oficial da matriz PNTP do ano, se o GATE adotar |
| Página que abre com erro do servidor (ex.: HTTP 500), com o resto do site no ar, sai Inconclusivo | Falha da plataforma sem punição; nenhum caso real até 15/10 | Se todas as fontes do critério voltarem com erro do servidor, classificar como Indisponível |
| Denominador muda com a cobertura | Scores com coberturas diferentes não são diretamente comparáveis | Mostrar sempre score e cobertura juntos (API e dashboard) |
