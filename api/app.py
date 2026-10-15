"""API de consulta dos resultados (par. 9 do enunciado: entidades, avaliacao mais recente, historico e criterios).

Somente leitura: abre o banco SQLite em modo leitura e nunca dispara coleta nem avaliacao. A coleta e a
avaliacao continuam nos comandos do coletor e das regras; a API so expoe o que ja foi gravado.

Execucao considerada: so as execucoes oficiais, isto e, completas (as 4 etapas), concluidas, para todas as
entidades (sem "--entidade") e ja avaliadas. Testes parciais (ex.: so o cadastro do Rio) nao aparecem.

Uso, na raiz do projeto:
    uvicorn api.app:app --reload
    documentacao interativa em http://127.0.0.1:8000/docs
Banco: GATE_BANCO, se definido; senao dados/gate.db; senao amostra/gate.db (amostra publica do repositorio).

Arquivos de evidencia (HTML, prints, PDFs) nao sao servidos pela API: podem conter dados pessoais de credores
(nome e CPF em tabelas de despesa). A API devolve o caminho, o hash e o trecho ja mascarado.
"""
import json
import os
import sqlite3
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException

RAIZ = Path(__file__).resolve().parent.parent
# Banco: GATE_BANCO, se definido; senao dados/gate.db (coleta local); senao a amostra publica do repositorio
# (amostra/gate.db, gerada por db/exportar_amostra.py), para quem clona o projeto ver os resultados sem coletar.
if os.environ.get("GATE_BANCO"):
    BANCO, FONTE = Path(os.environ["GATE_BANCO"]), "GATE_BANCO"
elif (RAIZ / "dados" / "gate.db").exists():
    BANCO, FONTE = RAIZ / "dados" / "gate.db", "coleta local (dados/gate.db)"
else:
    BANCO, FONTE = RAIZ / "amostra" / "gate.db", "amostra publica (amostra/gate.db)"
CFG_SCORE = yaml.safe_load((RAIZ / "config" / "score.yaml").read_text(encoding="utf-8"))
ORDEM = {"nao_atende": 0, "parcial": 1, "atende": 2}  # para dizer se um criterio melhorou ou piorou
SQL_OFICIAIS = ("SELECT e.id, e.iniciada_em, e.versao_codigo FROM execucoes e WHERE e.status = 'concluida' "
                "AND e.observacao LIKE 'Execucao completa%' AND e.observacao NOT LIKE '%(so %' "
                "AND EXISTS (SELECT 1 FROM avaliacoes a WHERE a.execucao_id = e.id) ORDER BY e.id")

app = FastAPI(title="GATE: conformidade de portais da transparencia",
              description="Consulta das avaliacoes automaticas dos portais municipais (somente leitura).",
              version="0.1")


def conectar():
    if not BANCO.exists():
        raise HTTPException(503, f"Banco nao encontrado em {BANCO}; rode o coletor e as regras antes")
    con = sqlite3.connect(f"file:{BANCO.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def oficiais(con):
    return [dict(r) for r in con.execute(SQL_OFICIAIS)]


def score_da_execucao(con, execucao_id, eid):
    r = con.execute("SELECT score, criterios_avaliados, criterios_aplicaveis, metodologia, detalhe_json FROM scores "
                    "WHERE execucao_id = ? AND entidade_id = ?", (execucao_id, eid)).fetchone()
    if not r:
        return None
    d = json.loads(r["detalhe_json"] or "{}")
    return {"score": round(r["score"] * 100, 1), "faixa": d.get("faixa"), "faixa_provisoria": d.get("faixa_provisoria", False),
            "cobertura": f"{r['criterios_avaliados']} de {r['criterios_aplicaveis']}",
            "essenciais_completos": d.get("essenciais_completos"), "essenciais_pendentes": d.get("essenciais_pendentes", []),
            "essenciais_nao_verificados": d.get("essenciais_nao_verificados", []),
            "media_simples_binaria": None if d.get("media_simples_binaria") is None else round(d["media_simples_binaria"] * 100, 1),
            "metodologia": r["metodologia"]}


def status_por_criterio(con, execucao_id, eid):
    return {r["codigo"]: r["status"] for r in con.execute(
        "SELECT k.codigo, a.status FROM avaliacoes a JOIN criterios k ON k.id = a.criterio_id "
        "WHERE a.execucao_id = ? AND a.entidade_id = ?", (execucao_id, eid))}


def entidade_ou_404(con, eid):
    r = con.execute("SELECT id, nome, municipio, tipo, fornecedor FROM entidades WHERE id = ?", (eid,)).fetchone()
    if not r:
        raise HTTPException(404, f"Entidade '{eid}' nao cadastrada")
    return dict(r)


@app.get("/entidades", summary="Entidades avaliadas, com o score da avaliacao mais recente")
def listar_entidades():
    con = conectar()
    execs = oficiais(con)
    ultima = execs[-1] if execs else None
    resultado = []
    for e in con.execute("SELECT id, nome, municipio, tipo, fornecedor FROM entidades WHERE ativo = 1 ORDER BY nome"):
        resultado.append({**dict(e), "ultima_execucao": ultima["id"] if ultima else None,
                          "avaliado_em": ultima["iniciada_em"] if ultima else None,
                          **((score_da_execucao(con, ultima["id"], e["id"]) or {}) if ultima else {})})
    return resultado


@app.get("/entidades/{entidade_id}/avaliacao", summary="Avaliacao mais recente de uma entidade, com evidencias")
def avaliacao_mais_recente(entidade_id: str):
    con = conectar()
    entidade = entidade_ou_404(con, entidade_id)
    execs = oficiais(con)
    if not execs:
        raise HTTPException(404, "Nenhuma execucao oficial avaliada")
    ultima = execs[-1]
    criterios = []
    for a in con.execute(
            "SELECT a.id, k.codigo, k.categoria, k.descricao, a.status, a.nota, a.metodo, a.justificativa, a.url_avaliada, "
            "a.avaliado_em FROM avaliacoes a JOIN criterios k ON k.id = a.criterio_id "
            "WHERE a.execucao_id = ? AND a.entidade_id = ? ORDER BY a.id", (ultima["id"], entidade_id)):
        evidencias = [dict(ev) for ev in con.execute(
            "SELECT tipo, url, conteudo AS trecho, caminho_arquivo, hash_sha256, coletado_em FROM evidencias "
            "WHERE avaliacao_id = ?", (a["id"],))]
        item = {k: a[k] for k in a.keys() if k != "id"}
        criterios.append({**item, "evidencias": evidencias})
    return {"entidade": entidade, "execucao": ultima, "score": score_da_execucao(con, ultima["id"], entidade_id),
            "criterios": criterios}


@app.get("/entidades/{entidade_id}/historico",
         summary="Historico: score e status por execucao, e o que melhorou ou piorou (e quando)")
def historico(entidade_id: str):
    con = conectar()
    entidade = entidade_ou_404(con, entidade_id)
    linhas, anterior, mudancas = [], None, []
    for e in oficiais(con):
        status = status_por_criterio(con, e["id"], entidade_id)
        if not status:
            continue
        linhas.append({"execucao": e["id"], "data": e["iniciada_em"], "versao_codigo": e["versao_codigo"],
                       **(score_da_execucao(con, e["id"], entidade_id) or {}), "status": status})
        if anterior:
            for codigo, novo in status.items():
                velho = anterior["status"].get(codigo)
                if velho == novo or velho is None:
                    continue
                if velho in ORDEM and novo in ORDEM:
                    sentido = "melhorou" if ORDEM[novo] > ORDEM[velho] else "piorou"
                else:
                    sentido = "sem comparacao (sem veredito em uma das execucoes)"
                mudancas.append({"criterio": codigo, "de": velho, "para": novo, "sentido": sentido,
                                 "execucao": e["id"], "data": e["iniciada_em"],
                                 "mesma_versao_do_codigo": anterior["versao_codigo"] == e["versao_codigo"]})
        anterior = {"status": status, "versao_codigo": e["versao_codigo"]}
    return {"entidade": entidade, "execucoes": linhas, "mudancas": mudancas,
            "aviso": "Mudanca entre execucoes com versoes de codigo diferentes pode ser efeito do sistema, nao do portal; "
                     "para comparar, reavaliar as coletas antigas com o codigo atual (python -m regras.avaliar --execucao N)."}


@app.get("/criterios", summary="Criterios avaliados, com classificacao e peso do score")
def listar_criterios():
    con = conectar()
    return [{**dict(r), "classificacao": CFG_SCORE["classificacao"].get(r["codigo"]),
             "peso_score": CFG_SCORE["pesos"].get(CFG_SCORE["classificacao"].get(r["codigo"]))}
            for r in con.execute("SELECT codigo, versao_checklist, categoria, descricao, fundamentacao, tipo_verificacao "
                                 "FROM criterios ORDER BY CAST(codigo AS REAL)")]


@app.get("/execucoes", summary="Execucoes oficiais avaliadas e a fonte dos dados")
def listar_execucoes():
    return {"fonte": FONTE, "execucoes": oficiais(conectar())}
