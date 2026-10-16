# Anexo: validação dos resultados

Responde a três pontos do enunciado: §15 (como os resultados da IA são validados), §16 (qualidade dos resultados: consistência e evidências que permitem auditoria) e §18 (avaliar os próprios resultados). Código: `regras/validar.py`. Referências: `config/gabarito.yaml` (interna) e `config/referencias.yaml` (externa).

## 1. Método

| Item | Escolha |
|---|---|
| Referência interna | Avaliação manual das 30 células (5 entidades × 6 critérios), feita em 09 e 10/10/2026. O 4.6 tem gabarito só no dia conferido à mão (15/10), porque o resultado correto muda a cada dia |
| Referência externa | Selos do Radar da Transparência Pública (PNTP) exibidos nos portais: Rio Diamante 2024, Caxias Ouro 2025, Itaboraí Prata |
| Execuções | As 4 execuções oficiais completas: 16 (13/10), 19 (14/10), 25 (15/10) e 27 (16/10). As três primeiras reavaliadas com o código de 15/10; a 27, com o de 16/10 (mesmas regras, mais o grau de confiança). Mede o sistema atual sobre coletas de dias diferentes |
| Células comparadas | 105: 25 por execução nos dias sem gabarito do 4.6 e 30 em 15/10 |
| Medidas | Concordância nas células conclusivas; taxa sem veredito (Inconclusivo ou Indisponível); matriz sistema × gabarito; estabilidade entre execuções; faixa do score × selo do PNTP; concordância por grau de confiança |

Separar concordância e abstenção evita que um sistema que se abstém muito pareça preciso, ou que um que nunca se abstém esconda erros.

## 2. Resultados

| Medida | Resultado |
|---|---|
| Concordância nas células conclusivas | 100 de 102 (98%) |
| Taxa sem veredito | 3 de 105 (3%) |
| Falso Não atende (o sistema acusa ausência e o gabarito não) | 0 |
| Células estáveis nas 4 execuções (sem o 4.6) | 23 de 25 |
| Faixa igual ao selo do PNTP (execução 27) | 1 de 3 |
| Pares de entidades sem inversão de ordem em relação ao selo | 3 de 3 |

Por critério (4 execuções):

| Critério | Células | Sem veredito | Conclusivas | Acertos | Concordância |
|---|---|---|---|---|---|
| 1.2 | 20 | 0 | 20 | 20 | 100% |
| 4.1 | 20 | 2 | 18 | 18 | 100% |
| 4.6 | 5 | 1 | 4 | 4 | 100% |
| 12.1 | 20 | 0 | 20 | 20 | 100% |
| 15.4 | 20 | 0 | 20 | 18 | 90% |
| 16.2 | 20 | 0 | 20 | 20 | 100% |

Por execução: 96% (16), 96% (19), 100% (25) e 100% (27, 25 de 25, sem nenhuma célula sem veredito) de concordância nas conclusivas.

Matriz (linhas: sistema; colunas: gabarito):

| Sistema \ Gabarito | Atende | Parcial | Não atende |
|---|---|---|---|
| Atende | 80 | 0 | 0 |
| Parcial | 2 | 16 | 0 |
| Não atende | 0 | 0 | 4 |
| Inconclusivo | 2 | 1 | 0 |
| Indisponível | 0 | 0 | 0 |

Os 2 erros conclusivos são do mesmo tipo: Parcial no lugar de Atende, ou seja, o sistema foi mais exigente que o gabarito, nunca mais brando. Não houve Atende falso nem Não atende falso.

## 3. Divergências e causas

| Execução | Célula | Sistema | Gabarito | Causa | Correção |
|---|---|---|---|---|---|
| 16 | Caxias 15.4 | Parcial (1 de 5) | Atende | O caminho de cliques ainda não existia: a página com o prazo de resposta e o infográfico do recurso não eram coletados | Caminho de cliques, 14/10 |
| 19 | Caxias 15.4 | Parcial (2 de 5) | Atende | O infográfico do recurso ficava cortado no print (caixa com rolagem própria); o prazo recursal e o procedimento do recurso estavam nele | Download da imagem original e transcrição, 14 e 15/10 |
| 16 e 19 | Rio 4.1 | Inconclusivo | Atende | A tabela de empenhos não terminava de carregar em 90 s | Espera de até 180 s com indicador de carregamento visível, 15/10 |
| 25 | Japeri 4.6 | Inconclusivo | Parcial | A API da Prefeitura não respondeu em 90 s; sem ela, a data vista não prova atraso (regra B) | Tempo limite de 180 s nas APIs, 15/10 (teste: 14 de 14 entidades, data máxima 09/10, igual à conferência manual) |

Todas as divergências têm causa na coleta, não nas regras. Cada correção do coletor eliminou a divergência correspondente na execução seguinte: a execução 27 não tem nenhuma divergência, e Japeri 4.6 voltou a ter veredito (Parcial, data mais recente 09/10, com as 14 entidades respondendo à API). As duas células instáveis (Caxias 15.4 e Rio 4.1) são as mesmas da tabela: a instabilidade veio da evolução do coletor, não de variação aleatória.

## 4. Faixa do score × selo do PNTP

| Entidade | Selo PNTP | Execução 16 | Execução 19 | Execução 25 | Execução 27 |
|---|---|---|---|---|---|
| Rio de Janeiro | Diamante (2024) | 100,0 Diamante (provisória) | 100,0 Diamante (provisória) | 100,0 Diamante | 100,0 Diamante |
| Duque de Caxias | Ouro (2025) | 88,6 Ouro | 91,4 Ouro | 100,0 Diamante | 100,0 Diamante |
| Itaboraí | Prata | 92,9 Ouro | 92,9 Ouro | 92,9 Ouro | 92,9 Ouro |
| Cachoeiras de Macacu | sem selo observado | 81,6 Elevado | 81,6 Elevado | 81,6 Elevado | 81,6 Elevado |
| Japeri | sem selo observado | 79,4 Elevado | 69,8 Intermediário | 74,5 Intermediário (provisória) | 69,8 Intermediário |

- A ordem das três entidades com selo é preservada (Rio e Caxias à frente de Itaboraí).
- Nas execuções 25 e 27, Caxias e Itaboraí ficam uma faixa acima do selo. Explicação provável: o sistema mede 6 critérios e o PNTP mais de 100; quem cumpre os 6 tende a ficar no topo.
- "Provisória": um critério essencial ficou Inconclusivo na execução; a faixa não é rebaixada por limitação do método, mas fica sinalizada (`docs/documentacao_tecnica.md`, seção 6).
- O score de Caxias subiu entre as execuções sem mudança no portal: o que mudou foi a coleta do 15.4. Consequência para o histórico (§7): comparações entre execuções só indicam mudança do portal quando feitas com a mesma versão do código. Por isso cada execução grava a versão do código (`versao_codigo`) e as coletas antigas podem ser reavaliadas com o código atual.

## 5. Concordância por grau de confiança (§4)

O nível de cada célula vem da regra `nivel_confianca` (`docs/documentacao_tecnica.md`, seção 5.6), recalculada pelo `validar` também nas execuções avaliadas antes de a coluna existir.

| Nível | Conclusivas com gabarito | Acertos | Concordância |
|---|---|---|---|
| Alta | 80 | 80 | 100% |
| Média | 22 | 20 | 91% |

- Os 2 erros conclusivos (Caxias 15.4 nas execuções 16 e 19) caíram no nível médio, como previsto pela regra: Parcial por subitens não encontrados depende de ausência, e a ausência veio de uma coleta incompleta.
- Nenhum veredito de confiança alta errou. A separação entre os níveis é o que torna a confiança útil: em escala (§17), a revisão humana pode se concentrar nos vereditos de confiança média (22 de 102 células, cerca de 1 em 5).
- Os percentuais são gravados em `config/confianca_observada.yaml` e exibidos pela API e pelo dashboard ao lado do nível de cada critério.
- Amostra pequena: 100% em 80 células não significa que a confiança alta nunca erra; significa que nenhum erro apareceu nesta base. Os 2 erros têm a mesma causa, então a separação entre os níveis é um indício, que precisa de mais amostra para ser confirmado. Em produção, a revisão humana amostral contínua amplia a base (`docs/documentacao_tecnica.md`, seção 13.4).

## 6. Ressalvas

| Ressalva | Efeito | Mitigação |
|---|---|---|
| O gabarito foi feito pela mesma pessoa que escreveu as regras | A leitura dos critérios é compartilhada; a concordância pode estar inflada | Selos do PNTP como referência independente; em produção, gabarito de um segundo avaliador |
| O gabarito foi corrigido uma vez (Japeri 1.2, de Parcial para Atende, em 12/10), depois que a descoberta achou um link que a visita manual não viu | A referência não é infalível | Correção registrada com data e motivo no próprio `gabarito.yaml` |
| Amostra pequena: 5 entidades, 105 células, 4 dias | Percentuais com pouca precisão | Execuções diárias até a entrega ampliam a base |
| 4.6 conferido à mão em um único dia | 5 células de 4.6 na concordância | Conferência manual em mais dias |
| Japeri 4.6 na execução 19 saiu Parcial com dado incompleto: a coleta daquele dia não registrava qual entidade da API ficou sem resposta | Provável erro, fora da concordância (14/10 sem gabarito do 4.6) | Coletas a partir de 15/10 registram as entidades sem resposta |
| O 15.4 depende do LLM; em subitens no limite, a resposta pode variar entre versões do prompt (Cachoeiras, "procedimento do pedido", aceito na v2 e não na v1) | Variação na nota, sem mudança de status | Respostas guardadas: mesma entrada e mesmo prompt dão o mesmo resultado; medir a variação com repetições é melhoria futura |
| Selos de anos diferentes (2024 e 2025) e de outra metodologia | Comparação só de ordem, não de valor | Usada como sinal, não como gabarito |

## 7. Como reproduzir

```
python -m regras.avaliar --execucao 16
python -m regras.avaliar --execucao 19
python -m regras.avaliar --execucao 25
python -m regras.avaliar --execucao 27
python -m regras.validar --execucoes 16 19 25 27 --gravar-confianca
```

Sem chave da API, a reavaliação usa as respostas do LLM guardadas no banco para as mesmas entradas.
