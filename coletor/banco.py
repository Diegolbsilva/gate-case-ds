"""Acesso ao banco SQLite: criar, registrar execucao, artefatos e ocorrencias."""
import sqlite3
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ESQUEMA = RAIZ / "db" / "schema.sql"


def agora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def conectar(caminho_banco):
    """Abre o banco; se o arquivo nao existe, cria as tabelas a partir de db/schema.sql."""
    caminho_banco = Path(caminho_banco)
    novo = not caminho_banco.exists()
    caminho_banco.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(caminho_banco)
    con.execute("PRAGMA foreign_keys = ON")
    if novo:
        con.executescript(ESQUEMA.read_text(encoding="utf-8"))
    return con


def sincronizar_entidades(con, entidades):
    """Garante que as entidades do entidades.yaml existem no banco (nao apaga nem altera as existentes)."""
    for e in entidades:
        con.execute(
            "INSERT OR IGNORE INTO entidades (id, nome, municipio, tipo, fornecedor) VALUES (?, ?, ?, ?, ?)",
            (e["id"], e["nome"], e["municipio"], e["tipo"], e.get("fornecedor")),
        )
    con.commit()


def iniciar_execucao(con, origem, versao_checklist, versao_codigo, observacao=None):
    cur = con.execute(
        "INSERT INTO execucoes (iniciada_em, origem, versao_checklist, versao_codigo, status, observacao) "
        "VALUES (?, ?, ?, ?, 'em_andamento', ?)",
        (agora(), origem, versao_checklist, versao_codigo, observacao),
    )
    con.commit()
    return cur.lastrowid


def finalizar_execucao(con, execucao_id, status="concluida"):
    con.execute("UPDATE execucoes SET finalizada_em = ?, status = ? WHERE id = ?", (agora(), status, execucao_id))
    con.commit()


def registrar_artefato(con, execucao_id, entidade_id, artefato, criterio_id=None):
    """artefato: dicionario devolvido por navegador.salvar_pagina (ou equivalente para API)."""
    cur = con.execute(
        "INSERT INTO artefatos (execucao_id, entidade_id, criterio_id, papel, url, url_final, tipo, caminho, "
        "hash_sha256, tamanho_bytes, status_http, coletado_em) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (execucao_id, entidade_id, criterio_id, artefato["papel"], artefato["url"], artefato.get("url_final"),
         artefato["tipo"], artefato["caminho"], artefato["hash_sha256"], artefato["tamanho_bytes"],
         artefato.get("status_http"), artefato["coletado_em"]),
    )
    con.commit()
    return cur.lastrowid


def registrar_ocorrencia(con, execucao_id, entidade_id, ocorrencia, criterio_id=None):
    con.execute(
        "INSERT INTO ocorrencias (execucao_id, entidade_id, criterio_id, url, tipo, mensagem, tentativa, ocorrido_em) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (execucao_id, entidade_id, criterio_id, ocorrencia["url"], ocorrencia["tipo"], ocorrencia["mensagem"],
         ocorrencia["tentativa"], ocorrencia["ocorrido_em"]),
    )
    con.commit()
