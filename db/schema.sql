-- Esquema do banco SQLite do prototipo GATE/MPRJ.
-- Principio: cada execucao ACRESCENTA resultados; nada e sobrescrito nem apagado.
-- Isso permite responder: o portal melhorou ou piorou? quais criterios foram corrigidos?
-- quando a conformidade foi identificada? qual a evolucao ao longo do tempo?

PRAGMA foreign_keys = ON;

-- Quem e avaliado (vem do entidades.yaml).
CREATE TABLE entidades (
    id          TEXT PRIMARY KEY,                       -- ex.: 'japeri'
    nome        TEXT NOT NULL,
    municipio   TEXT NOT NULL,
    tipo        TEXT NOT NULL CHECK (tipo IN ('prefeitura', 'camara', 'autarquia', 'fundo', 'outro')),
    fornecedor  TEXT,
    ativo       INTEGER NOT NULL DEFAULT 1,             -- 0 = deixou de ser avaliada (nao apagar)
    criado_em   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Enderecos de cada entidade, com periodo de validade (portal muda de endereco: secao 7 do enunciado).
-- URL antiga nao e apagada: recebe valido_ate.
CREATE TABLE entidade_urls (
    id            INTEGER PRIMARY KEY,
    entidade_id   TEXT NOT NULL REFERENCES entidades(id),
    papel         TEXT NOT NULL CHECK (papel IN ('site_oficial', 'portal', 'api', 'sistema')),
    url           TEXT NOT NULL,
    valido_desde  TEXT NOT NULL,                        -- data em que a URL foi vista pela primeira vez
    valido_ate    TEXT,                                 -- NULL = ainda valida
    observacao    TEXT,
    UNIQUE (entidade_id, papel, url, valido_desde)
);

-- Itens do checklist. O mesmo codigo pode existir em versoes diferentes do checklist
-- (ex.: secao 13 de emendas entrou em 2025): scores so sao comparaveis na mesma versao.
CREATE TABLE criterios (
    id                INTEGER PRIMARY KEY,
    codigo            TEXT NOT NULL,                    -- ex.: '4.1'
    versao_checklist  TEXT NOT NULL,                    -- ex.: 'v1-2026-10'
    categoria         TEXT NOT NULL,                    -- ex.: 'DESPESA'
    descricao         TEXT NOT NULL,
    fundamentacao     TEXT,
    matriz            TEXT NOT NULL CHECK (matriz IN ('comum', 'executivo')),
    tipo_verificacao  TEXT NOT NULL CHECK (tipo_verificacao IN
                        ('existencia', 'navegacao', 'dados_estruturados', 'documento', 'atualizacao', 'semantica')),
    peso              REAL NOT NULL DEFAULT 1.0,        -- definido na metodologia do score
    UNIQUE (codigo, versao_checklist)
);

-- Para quais tipos de entidade cada criterio vale (base do status 'nao_aplicavel', secao 11).
CREATE TABLE criterio_aplicabilidade (
    criterio_id    INTEGER NOT NULL REFERENCES criterios(id),
    tipo_entidade  TEXT NOT NULL CHECK (tipo_entidade IN ('prefeitura', 'camara', 'autarquia', 'fundo', 'outro')),
    PRIMARY KEY (criterio_id, tipo_entidade)
);

-- Cada rodada do sistema (agendada, manual ou o gabarito feito a mao).
CREATE TABLE execucoes (
    id                INTEGER PRIMARY KEY,
    iniciada_em       TEXT NOT NULL,
    finalizada_em     TEXT,
    origem            TEXT NOT NULL CHECK (origem IN ('agendada', 'manual', 'gabarito')),
    versao_checklist  TEXT NOT NULL,
    versao_codigo     TEXT,                             -- commit do git, para reproduzir o resultado
    status            TEXT NOT NULL CHECK (status IN ('em_andamento', 'concluida', 'falhou')),
    observacao        TEXT
);

-- Resultado de UM criterio, para UMA entidade, em UMA execucao.
CREATE TABLE avaliacoes (
    id             INTEGER PRIMARY KEY,
    execucao_id    INTEGER NOT NULL REFERENCES execucoes(id),
    entidade_id    TEXT NOT NULL REFERENCES entidades(id),
    criterio_id    INTEGER NOT NULL REFERENCES criterios(id),
    status         TEXT NOT NULL CHECK (status IN
                     ('atende', 'parcial', 'nao_atende', 'inconclusivo', 'indisponivel', 'nao_aplicavel')),
    nota           REAL CHECK (nota IS NULL OR (nota >= 0 AND nota <= 1)),   -- nota gradual; NULL nos status fora do score
    confianca      REAL CHECK (confianca IS NULL OR (confianca >= 0 AND confianca <= 1)),
    metodo         TEXT NOT NULL CHECK (metodo IN ('api', 'pagina', 'navegador', 'llm', 'manual')),
    justificativa  TEXT,                                -- explicacao curta, legivel por humano
    url_avaliada   TEXT,
    avaliado_em    TEXT NOT NULL,
    detalhe_json   TEXT,                                -- detalhe da regra (ex.: subitens do 15.4, atraso do 12.1)
    UNIQUE (execucao_id, entidade_id, criterio_id)
);

-- Provas de cada avaliacao (secao 6). Uma avaliacao pode ter varias evidencias.
CREATE TABLE evidencias (
    id               INTEGER PRIMARY KEY,
    avaliacao_id     INTEGER NOT NULL REFERENCES avaliacoes(id),
    tipo             TEXT NOT NULL CHECK (tipo IN
                       ('trecho', 'tabela', 'arquivo', 'screenshot', 'resposta_api', 'metadado')),
    url              TEXT,
    titulo_pagina    TEXT,
    conteudo         TEXT,                              -- trecho citado, cabecalhos da tabela etc. (CPF mascarado)
    caminho_arquivo  TEXT,                              -- PDF, print ou JSON guardado em disco
    hash_sha256      TEXT,                              -- detecta mudanca e arquivo repetido em periodos diferentes
    coletado_em      TEXT NOT NULL
);

-- Score de cada entidade em cada execucao (alimenta a evolucao no dashboard).
CREATE TABLE scores (
    execucao_id           INTEGER NOT NULL REFERENCES execucoes(id),
    entidade_id           TEXT NOT NULL REFERENCES entidades(id),
    score                 REAL NOT NULL CHECK (score >= 0 AND score <= 1),
    criterios_avaliados   INTEGER NOT NULL,             -- entraram no calculo
    criterios_aplicaveis  INTEGER NOT NULL,             -- cobertura = avaliados / aplicaveis
    metodologia           TEXT NOT NULL,                -- versao da formula do score
    detalhe_json          TEXT,
    PRIMARY KEY (execucao_id, entidade_id)
);

-- Erros e novas tentativas (explica cada 'indisponivel' e 'inconclusivo').
CREATE TABLE ocorrencias (
    id           INTEGER PRIMARY KEY,
    execucao_id  INTEGER NOT NULL REFERENCES execucoes(id),
    entidade_id  TEXT REFERENCES entidades(id),
    criterio_id  INTEGER REFERENCES criterios(id),
    url          TEXT,
    tipo         TEXT NOT NULL CHECK (tipo IN
                   ('erro_http', 'erro_servidor', 'timeout', 'captcha', 'layout_inesperado', 'outro')),
    mensagem     TEXT,
    tentativa    INTEGER,
    ocorrido_em  TEXT NOT NULL
);

CREATE INDEX idx_avaliacoes_entidade_criterio ON avaliacoes (entidade_id, criterio_id);
CREATE INDEX idx_evidencias_avaliacao ON evidencias (avaliacao_id);

-- Ultima avaliacao de cada criterio em cada entidade (o que o dashboard mostra como "situacao atual").
CREATE VIEW v_situacao_atual AS
SELECT a.*
FROM avaliacoes a
JOIN execucoes e ON e.id = a.execucao_id
WHERE e.status = 'concluida'
  AND e.iniciada_em = (
      SELECT MAX(e2.iniciada_em)
      FROM avaliacoes a2
      JOIN execucoes e2 ON e2.id = a2.execucao_id
      WHERE a2.entidade_id = a.entidade_id
        AND a2.criterio_id = a.criterio_id
        AND e2.status = 'concluida'
  );
