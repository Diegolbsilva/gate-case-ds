-- Perguntas da secao 7 do enunciado, respondidas pelo banco.
-- Cada consulta comeca com uma linha "-- ==" que vira o titulo na saida do teste_banco.py.

-- == P1. Situacao atual de cada prefeitura (ultima avaliacao de cada criterio)
SELECT s.entidade_id, c.codigo, s.status, s.avaliado_em
FROM v_situacao_atual s JOIN criterios c ON c.id = s.criterio_id
ORDER BY s.entidade_id, c.id;

-- == P2. Quais criterios mudaram de status entre a execucao 1 (09/10) e a 2 (10/10)?
SELECT a1.entidade_id, c.codigo, a1.status AS status_09_10, a2.status AS status_10_10
FROM avaliacoes a1
JOIN avaliacoes a2 ON a2.entidade_id = a1.entidade_id AND a2.criterio_id = a1.criterio_id
JOIN criterios c ON c.id = a1.criterio_id
WHERE a1.execucao_id = 1 AND a2.execucao_id = 2 AND a1.status <> a2.status;

-- == P3. Quais criterios continuam pendentes (parcial ou nao atende) na situacao atual?
SELECT s.entidade_id, c.codigo, s.status, s.justificativa
FROM v_situacao_atual s JOIN criterios c ON c.id = s.criterio_id
WHERE s.status IN ('parcial', 'nao_atende')
ORDER BY s.entidade_id, c.id;

-- == P4. Quando cada conformidade foi identificada pela primeira vez? (Japeri)
SELECT a.entidade_id, c.codigo, MIN(e.iniciada_em) AS primeira_vez_atende
FROM avaliacoes a JOIN execucoes e ON e.id = a.execucao_id JOIN criterios c ON c.id = a.criterio_id
WHERE a.status = 'atende' AND a.entidade_id = 'japeri'
GROUP BY a.entidade_id, c.codigo;

-- == P5. Contagem de status por prefeitura na situacao atual
SELECT entidade_id,
       SUM(status = 'atende') AS atende, SUM(status = 'parcial') AS parcial, SUM(status = 'nao_atende') AS nao_atende
FROM v_situacao_atual GROUP BY entidade_id ORDER BY atende DESC;

-- == P6. Evidencias registradas
SELECT ev.id, a.entidade_id, c.codigo, ev.tipo, substr(ev.conteudo, 1, 60) AS conteudo
FROM evidencias ev JOIN avaliacoes a ON a.id = ev.avaliacao_id JOIN criterios c ON c.id = a.criterio_id;

-- == P7. Ocorrencias (erros e novas tentativas)
SELECT entidade_id, tipo, mensagem, ocorrido_em FROM ocorrencias;
