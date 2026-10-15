"""Avalia os criterios de cada entidade a partir do que uma execucao do coletor salvou.

Nao acessa nenhum portal: le so o banco (artefatos, descobertas) e os arquivos em dados/execucoes/<N>/.
Por isso pode ser rodado de novo sobre a mesma coleta quando uma regra mudar (reavaliacao).

Para cada entidade e criterio:
1. Junta as fontes disponiveis, nesta ordem: API do fornecedor, paginas da descoberta, paginas do cadastro.
2. Aplica a regra do criterio (regras/verificacoes.py) a CADA fonte. Cada fonte responde: atende,
   parcial, nao_atende ou "nao e evidencia" (pagina errada, tabela que nao carregou).
3. Fica com o MELHOR resultado entre as fontes (atende > parcial > nao_atende). Motivo: a descoberta
   pode trazer uma pagina errada (no Rio, "Plano de execucoes... gestao fiscal" no lugar do RGF), e uma
   pagina errada nao pode derrubar o que a pagina certa mostra. Em empate, vale a fonte que vem
   primeiro na ordem acima. Todas as fontes avaliadas ficam no detalhe, para auditoria.
4. Nenhuma fonte serviu: Inconclusivo (havia pagina, mas nao deu para ler) ou Indisponivel (nao havia
   nenhuma fonte salva e houve erro de acesso). Os dois ficam fora do score.

Grava em avaliacoes (status, justificativa, detalhe) e evidencias (trecho, arquivo, hash).
Rodar de novo para a mesma execucao apaga e refaz as avaliacoes dela.
O 15.4 e avaliado pelo LLM (regras/llm_15_4.py), com a citacao de cada subitem conferida no texto de origem.

Uso, na raiz do projeto, com o ambiente ativo:
    python -m regras.avaliar                 (ultima execucao concluida)
    python -m regras.avaliar --execucao 16
"""
import argparse
import json
from datetime import date, datetime
from pathlib import Path, PureWindowsPath

import yaml

from coletor import banco
from regras import llm_15_4 as llm
from regras import score as sc
from regras import verificacoes as v

RAIZ = Path(__file__).resolve().parent.parent
ORDEM = {"atende": 3, "parcial": 2, "nao_atende": 1}
CRITERIOS = ["1.2", "4.1", "4.6", "12.1", "16.2"]
ALVO_DESCOBERTA = {"4.1": "despesa", "4.6": "despesa", "12.1": "rgf", "16.2": "portal"}

parser = argparse.ArgumentParser()
parser.add_argument("--config", default=RAIZ / "config" / "entidades.yaml")
parser.add_argument("--gabarito", default=RAIZ / "config" / "gabarito.yaml")
parser.add_argument("--score", default=RAIZ / "config" / "score.yaml")
parser.add_argument("--dados", default=RAIZ / "dados")
parser.add_argument("--execucao", type=int, help="id da execucao; sem isso, a ultima concluida")
args = parser.parse_args()

cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
pasta_dados = Path(args.dados)
con = banco.conectar(pasta_dados / "gate.db")
execucao_id = args.execucao or con.execute(
    "SELECT MAX(id) FROM execucoes WHERE status = 'concluida' AND observacao LIKE 'Execucao completa%'").fetchone()[0]
iniciada_em = con.execute("SELECT iniciada_em FROM execucoes WHERE id = ?", (execucao_id,)).fetchone()[0]
data_avaliacao = datetime.strptime(iniciada_em, "%Y-%m-%d %H:%M:%S").date()
ids_criterios = dict(con.execute("SELECT codigo, id FROM criterios"))
print(f"Avaliando a execucao {execucao_id} (coleta de {iniciada_em}); data de referencia {data_avaliacao:%d/%m/%Y}")

# reavaliacao: apaga o que ja havia para esta execucao
con.execute("DELETE FROM evidencias WHERE avaliacao_id IN (SELECT id FROM avaliacoes WHERE execucao_id = ?)", (execucao_id,))
con.execute("DELETE FROM avaliacoes WHERE execucao_id = ?", (execucao_id,))


def caminho_local(caminho):
    """O banco guarda o caminho de quem coletou (ex.: C:\\Users\\...\\dados\\execucoes\\16\\japeri\\x.html).
    Refaz o caminho a partir da pasta de dados desta maquina, para funcionar em qualquer computador."""
    partes = (PureWindowsPath(caminho) if "\\" in caminho else Path(caminho)).parts
    return pasta_dados.joinpath(*partes[partes.index("execucoes"):])


def gravar_nao_aplicavel(eid, codigo, tipo):
    """Criterio que nao vale para o tipo da entidade (secao 11 do enunciado): status proprio, fora do score e da
    cobertura, sem coleta nem regra. A aplicabilidade vem de config/criterios.yaml (aplica_a), gravada no banco."""
    justificativa = f"Criterio nao se aplica a entidade do tipo '{tipo}' (config/criterios.yaml, aplica_a)"
    con.execute("INSERT INTO avaliacoes (execucao_id, entidade_id, criterio_id, status, metodo, justificativa, avaliado_em, "
                "detalhe_json) VALUES (?, ?, ?, 'nao_aplicavel', 'manual', ?, ?, ?)",
                (execucao_id, eid, ids_criterios[codigo], justificativa, banco.agora(), json.dumps({"tipo_entidade": tipo})))
    resultados[(eid, codigo)] = ("nao_aplicavel", None, justificativa)


resultados = {}
for entidade in cfg["entidades"]:
    eid = entidade["id"]
    artefatos = [dict(zip(["id", "criterio_id", "papel", "url", "url_final", "tipo", "caminho", "hash", "coletado_em"], r))
                 for r in con.execute(
                     "SELECT id, criterio_id, papel, url, url_final, tipo, caminho, hash_sha256, coletado_em FROM artefatos "
                     "WHERE execucao_id = ? AND entidade_id = ? ORDER BY id", (execucao_id, eid))]
    for a in artefatos:
        a["arquivo"] = caminho_local(a["caminho"])
    jsons = {a["arquivo"].stem: a for a in artefatos if a["tipo"] == "json"}
    resumo_geosiap = json.loads(jsons["resumo_geosiap"]["arquivo"].read_text(encoding="utf-8")) if "resumo_geosiap" in jsons else None
    teve_erro_acesso = con.execute(
        "SELECT COUNT(*) FROM ocorrencias WHERE execucao_id = ? AND entidade_id = ? AND tipo IN "
        "('timeout', 'erro_http', 'erro_servidor', 'bloqueio')", (execucao_id, eid)).fetchone()[0] > 0
    passo_portal = con.execute(
        "SELECT texto_clicado, url_destino, visivel_sem_interacao, precisou_rolar, sucesso FROM descobertas "
        "WHERE execucao_id = ? AND entidade_id = ? AND alvo = 'portal' AND passo = 1 ORDER BY id DESC LIMIT 1",
        (execucao_id, eid)).fetchone()

    aplicaveis = {r[0] for r in con.execute(
        "SELECT k.codigo FROM criterio_aplicabilidade ca JOIN criterios k ON k.id = ca.criterio_id "
        "WHERE ca.tipo_entidade = ?", (entidade["tipo"],))}
    for codigo in CRITERIOS:
        if codigo not in aplicaveis:
            gravar_nao_aplicavel(eid, codigo, entidade["tipo"])
            continue
        criterio_id = ids_criterios[codigo]
        # 1. fontes, na ordem API > descoberta > cadastro: (rotulo, artefato ou None, funcao que avalia)
        fontes = []
        if codigo == "1.2":
            linha = dict(zip(["texto_clicado", "url_destino", "visivel_sem_interacao", "precisou_rolar", "sucesso"],
                             passo_portal)) if passo_portal else None
            capa = next((a for a in artefatos if a["papel"] == "descoberta_capa_site" and a["tipo"] == "html"
                         and a["arquivo"].name == "descoberta_capa_site.html"), None)
            fontes.append(("descoberta: capa do site e 1o clique", capa,
                           lambda a, l=linha: v.regra_1_2(l, a["arquivo"].read_text(encoding="utf-8") if a else None)))
        if codigo in ("4.1", "4.6"):
            for nome, fornecedor in (("api_despesas_detalhadas", "geosiap"), ("api_despesas_todas", "modernizacao_webrun")):
                if nome in jsons:
                    regra = (lambda a, f=fornecedor: v.regra_4_1_api(f, json.loads(a["arquivo"].read_text(encoding="utf-8")))) \
                        if codigo == "4.1" else \
                        (lambda a, f=fornecedor: v.regra_4_6_api(f, json.loads(a["arquivo"].read_text(encoding="utf-8")),
                                                                 data_avaliacao, resumo_geosiap if f == "geosiap" else None))
                    fontes.append((f"API {fornecedor}", jsons[nome], regra))
        if codigo == "12.1" and "api_consulta_rgf_m2" in jsons:
            fontes.append(("API modernizacao_webrun", jsons["api_consulta_rgf_m2"],
                           lambda a: v.regra_12_1_api(json.loads(a["arquivo"].read_text(encoding="utf-8")), data_avaliacao)))
        paginas = []  # o 1.2 nao le paginas: a evidencia e o passo da descoberta (visivel, rolou, clicou)
        if codigo in ALVO_DESCOBERTA:
            prefixo = f"descoberta_{ALVO_DESCOBERTA[codigo]}"
            paginas += [("descoberta", a) for a in artefatos if a["tipo"] == "html" and a["papel"].startswith(prefixo)]
        if codigo != "1.2":
            paginas += [("cadastro", a) for a in artefatos if a["tipo"] == "html" and a["criterio_id"] == criterio_id]
        for origem, a in paginas:
            if codigo == "4.1":
                regra = lambda a: v.regra_4_1_pagina(a["arquivo"].read_text(encoding="utf-8"))
            elif codigo == "4.6":
                regra = lambda a: v.regra_4_6_pagina(a["arquivo"].read_text(encoding="utf-8"), data_avaliacao,
                                                     datetime.strptime(a["coletado_em"], "%Y-%m-%d %H:%M:%S"))
            elif codigo == "12.1":
                regra = lambda a: v.regra_12_1_pagina(a["arquivo"].read_text(encoding="utf-8"), data_avaliacao,
                                                      a["url_final"] or a["url"])
            else:
                regra = lambda a: v.regra_16_2_pagina(a["arquivo"].read_text(encoding="utf-8"))
            fontes.append((f"{origem}: {a['arquivo'].name}", a, regra))

        # 2. avalia cada fonte
        avaliadas = []
        for rotulo, artefato, regra in fontes:
            if artefato is not None and not artefato["arquivo"].exists():
                avaliadas.append((rotulo, artefato, None, "arquivo nao encontrado"))
                continue
            res = regra(artefato)
            if res and "nao_evidencia" in res:  # a regra leu, mas o dado nao prova nada (motivo vai para o detalhe)
                avaliadas.append((rotulo, artefato, None, res["nao_evidencia"]))
                continue
            avaliadas.append((rotulo, artefato, res, None))

        # 3. melhor resultado (empate: a primeira fonte na ordem)
        validas = [x for x in avaliadas if x[2]]
        escolhida = max(validas, key=lambda x: ORDEM[x[2]["status"]]) if validas else None
        if escolhida:
            rotulo, artefato, res, _ = escolhida
            status, justificativa = res["status"], res["justificativa"]
            metodo = "api" if rotulo.startswith("API") else "navegador"
        else:
            rotulo, artefato, res = None, None, None
            # Indisponivel: nada foi salvo para este criterio E houve erro de acesso (site fora do ar, timeout).
            # Inconclusivo: havia o que ler, mas nenhuma fonte mostrou a informacao de forma legivel.
            if codigo == "1.2":  # sem capa salva = a capa do site nem abriu
                sem_fonte = not any(a["papel"] == "descoberta_capa_site" for a in artefatos)
            else:
                sem_fonte = not paginas and not any(f[1] is not None for f in fontes)
            status = "indisponivel" if sem_fonte and teve_erro_acesso else "inconclusivo"
            justificativa = ("Nenhuma fonte salva e houve erro de acesso" if status == "indisponivel" else
                             "Nenhuma das fontes salvas mostrou a informacao de forma legivel; revisao humana")
            motivos = [f"{r}: {o}" for r, _, x, o in avaliadas if o and o != "arquivo nao encontrado"]
            if motivos:
                justificativa += " (" + "; ".join(motivos) + ")"
            metodo = "navegador"
        detalhe = {"fonte_usada": rotulo, **(res["detalhe"] if res else {}),
                   "fontes_avaliadas": [{"fonte": r, "status": (x["status"] if x else None), "obs": o}
                                        for r, _, x, o in avaliadas]}
        cur = con.execute(
            "INSERT INTO avaliacoes (execucao_id, entidade_id, criterio_id, status, metodo, justificativa, url_avaliada, "
            "avaliado_em, detalhe_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (execucao_id, eid, criterio_id, status, metodo, v.mascarar(justificativa),
             (artefato["url_final"] or artefato["url"]) if artefato else (passo_portal[1] if codigo == "1.2" and passo_portal else None),
             banco.agora(), json.dumps(detalhe, ensure_ascii=False)))
        if res:
            con.execute(
                "INSERT INTO evidencias (avaliacao_id, artefato_id, tipo, url, conteudo, caminho_arquivo, hash_sha256, coletado_em) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (cur.lastrowid, artefato["id"] if artefato else None,
                 "resposta_api" if metodo == "api" else ("metadado" if codigo == "1.2" else "trecho"),
                 (artefato["url_final"] or artefato["url"]) if artefato else None, v.mascarar(res.get("trecho", ""))[:2000],
                 artefato["caminho"] if artefato else None, artefato["hash"] if artefato else None,
                 artefato["coletado_em"] if artefato else banco.agora()))
        resultados[(eid, codigo)] = (status, rotulo, justificativa)

    # 15.4: LLM com citacao conferida (regras/llm_15_4.py). Sem fonte: Indisponivel ou Inconclusivo, como os outros.
    if "15.4" not in aplicaveis:
        gravar_nao_aplicavel(eid, "15.4", entidade["tipo"])
    else:
        criterio_id = ids_criterios["15.4"]
        res = llm.avaliar_15_4(con, execucao_id, eid, artefatos, criterio_id)
        if res and "status" in res:
            status, justificativa = res["status"], res["justificativa"]
        else:
            status = "indisponivel" if res is None and teve_erro_acesso else "inconclusivo"
            justificativa = ("Nenhuma pagina do e-SIC salva e houve erro de acesso" if status == "indisponivel" else
                             "Nao deu para avaliar com o LLM; revisao humana" + (f" ({res['nao_evidencia']})" if res else
                                                                                 " (nenhuma pagina do e-SIC salva)"))
        cur = con.execute(
            "INSERT INTO avaliacoes (execucao_id, entidade_id, criterio_id, status, nota, metodo, justificativa, url_avaliada, "
            "avaliado_em, detalhe_json) VALUES (?, ?, ?, ?, ?, 'llm', ?, ?, ?, ?)",
            (execucao_id, eid, criterio_id, status, res.get("nota") if res else None, v.mascarar(justificativa),
             res["evidencias"][0][0]["url_final"] if res and res.get("evidencias") else None, banco.agora(),
             json.dumps(res.get("detalhe", {}) if res else {}, ensure_ascii=False)))
        for artefato, trecho in (res or {}).get("evidencias", []):
            con.execute(
                "INSERT INTO evidencias (avaliacao_id, artefato_id, tipo, url, conteudo, caminho_arquivo, hash_sha256, coletado_em) "
                "VALUES (?, ?, 'trecho', ?, ?, ?, ?, ?)",
                (cur.lastrowid, artefato["id"], artefato["url_final"] or artefato["url"], v.mascarar(trecho)[:2000],
                 artefato["caminho"], artefato["hash"], artefato["coletado_em"]))
        resultados[(eid, "15.4")] = (status, "LLM" if res and "status" in res else None, justificativa)
con.commit()

# conferencia rapida contra o gabarito manual (nao entra no calculo)
gabarito = yaml.safe_load(Path(args.gabarito).read_text(encoding="utf-8")) if Path(args.gabarito).exists() else {}
acertos = total = 0
print(f"\n{'entidade':22} {'crit':5} {'sistema':13} {'gabarito':11} fonte usada / justificativa")
for (eid, codigo), (status, rotulo, justificativa) in resultados.items():
    esperado = gabarito.get(eid, {}).get(codigo)
    if isinstance(esperado, dict):  # gabarito com data (4.6 muda a cada dia): so compara no dia conferido
        esperado = esperado.get(data_avaliacao.isoformat())
    marca ="" if esperado is None else ("ok" if esperado == status else "DIFERENTE")
    acertos, total = acertos + (marca == "ok"), total + (esperado is not None)
    print(f"{eid:22} {codigo:5} {status:13} {str(esperado):11} {marca:9} {rotulo or '-'} | {justificativa[:90]}")
print(f"\nConcordancia com o gabarito: {acertos} de {total}")

# score de cada entidade (regras/score.py), com as avaliacoes que acabaram de ser gravadas
sc.imprimir(sc.calcular(con, execucao_id, yaml.safe_load(Path(args.score).read_text(encoding="utf-8"))))
con.close()
