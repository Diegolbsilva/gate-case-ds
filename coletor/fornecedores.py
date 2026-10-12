"""Deteccao do fornecedor do portal e adaptadores por fornecedor (nao por prefeitura).

Cada fornecedor atende muitos municipios: um adaptador escrito uma vez serve para todos os clientes.
Portal sem fornecedor conhecido segue pela descoberta generica (coletor/descobrir.py).
"""
import re
import time
from datetime import date, timedelta
from urllib.parse import urlparse

import requests

from coletor.banco import agora
from coletor.descoberta import normalizar

# Assinaturas: regex na URL do portal e/ou no HTML da capa. A evidencia encontrada fica registrada.
ASSINATURAS = {
    "geosiap": {"url": r"\.geosiap\.net\.br", "html": r"geosiap|embras"},
    "betha": {"url": r"(^|\.)betha\.cloud", "html": r"Betha Sistemas"},
    "modernizacao_webrun": {"url": None, "html": r"/webrun/form\.jsp\?sys=LAI"},  # plataforma Webrun (Caxias)
    "supernova": {"url": r"supernova\.com\.br", "html": r"supernova\.com\.br"},       # subsistema de consultas (Itaborai)
}
# Fornecedores com adaptador neste prototipo. Os demais seguem pela descoberta generica.
COM_ADAPTADOR = ("geosiap", "modernizacao_webrun")
# Entidades do mesmo portal que nunca entram na avaliacao da Prefeitura (outro Poder).
EXCLUIR_ENTIDADES = ("camara", "legislativ")


def detectar(url_portal, html):
    """Lista de (fornecedor, evidencia). Pode haver mais de um (ex.: portal proprio + subsistema)."""
    achados = []
    for nome, regra in ASSINATURAS.items():
        if regra["url"] and re.search(regra["url"], urlparse(url_portal).hostname or "", re.I):
            achados.append((nome, f"dominio do portal: {urlparse(url_portal).hostname}"))
        elif regra["html"]:
            achado = re.search(regra["html"], html, re.I)
            if achado:
                achados.append((nome, f"texto no HTML da capa: '{achado.group(0)}'"))
    return achados


def baixar_json(sessao, metodo, url, tentativas, **kwargs):
    """Chama a API com novas tentativas. Devolve (dados, ocorrencias, status_http). dados = None se falhou."""
    ocorrencias = []
    for n in range(1, tentativas + 1):
        tipo, mensagem, status = None, None, None
        try:
            resposta = sessao.request(metodo, url, timeout=90, **kwargs)
            status = resposta.status_code
            if status >= 400:
                tipo = "bloqueio" if status in (401, 403) else ("erro_servidor" if status >= 500 else "erro_http")
                mensagem = f"HTTP {status}"
            else:
                return resposta.json(), ocorrencias, status
        except requests.Timeout:
            tipo, mensagem = "timeout", "API nao respondeu em 90 s"
        except requests.RequestException as erro:
            tipo, mensagem = "erro_http", str(erro)[:300]
        except ValueError:
            tipo, mensagem = "layout_inesperado", "Resposta nao e JSON"
        ocorrencias.append({"url": url, "tipo": tipo, "mensagem": mensagem, "tentativa": n, "ocorrido_em": agora()})
        if n < tentativas and tipo != "layout_inesperado":
            time.sleep(5 * 3 ** (n - 1))
        elif tipo == "layout_inesperado":
            break
    return None, ocorrencias, status


def geosiap(sessao, url_portal, tentativas, dias=30):
    """API GeoSiap: entidades do portal (sem a Camara) e despesas detalhadas dos ultimos `dias` dias.

    Devolve (lista de (nome_arquivo, conteudo_json, url)), ocorrencias, resumo).
    """
    raiz = f"{urlparse(url_portal).scheme}://{urlparse(url_portal).netloc}"  # netloc inclui a porta, se houver
    base = f"{raiz}/portal-transparencia/api"
    arquivos, ocorrencias = [], []
    entidades, oc, _ = baixar_json(sessao, "GET", f"{base}/sis_entidade", tentativas)
    ocorrencias += oc
    if entidades is None:
        return arquivos, ocorrencias, {"sucesso": False, "motivo": "sis_entidade falhou"}
    arquivos.append(("api_sis_entidade", entidades, f"{base}/sis_entidade"))

    incluidas = [e for e in entidades if not any(t in normalizar(e["ds_entidade"]) for t in EXCLUIR_ENTIDADES)]
    excluidas = [e["ds_entidade"] for e in entidades if e not in incluidas]
    fim, inicio = date.today(), date.today() - timedelta(days=dias)
    url_despesas = f"{base}/execucao/despesas_detalhadas/despesas_detalhadas"
    por_entidade, registros, datas = {}, 0, []
    for e in incluidas:
        dados, oc, _ = baixar_json(sessao, "GET", url_despesas, tentativas, params={
            "id_entidade": e["id_entidade"], "data_inicial": inicio.isoformat(), "data_final": fim.isoformat()})
        ocorrencias += oc
        if dados is None:
            continue
        linhas = dados.get("despesas_detalhadas", []) if isinstance(dados, dict) else []
        por_entidade[e["id_entidade"]] = {"ds_entidade": e["ds_entidade"], "resposta": dados}
        registros += len(linhas)
        datas += [l["dt_doc_despesa"] for l in linhas if l.get("dt_doc_despesa")]
    arquivos.append(("api_despesas_detalhadas", por_entidade, url_despesas))
    resumo = {"sucesso": bool(por_entidade), "entidades_incluidas": len(incluidas), "entidades_com_resposta": len(por_entidade),
              "entidades_excluidas": excluidas, "periodo": [inicio.isoformat(), fim.isoformat()],
              "registros": registros, "data_maxima": max(datas) if datas else None,
              "rgf_rota_conhecida": f"{raiz}/portal-transparencia/publicacoes?id_publicacao_tipo=5"}
    return arquivos, ocorrencias, resumo


def modernizacao_webrun(sessao, url_portal, tentativas, servicos=("despesas_todas", "consulta_rgf_m2")):
    """API da plataforma Webrun (Modernizacao): um endpoint, servico e ano no corpo da requisicao.

    O metodo HTTP nao esta documentado na tela: testa POST com JSON, POST com formulario e GET, nessa ordem,
    e registra qual funcionou.
    """
    endpoint = f"{urlparse(url_portal).scheme}://{urlparse(url_portal).netloc}/sincronia/apidados.rule?sys=LAI"
    arquivos, ocorrencias, resumo = [], [], {"sucesso": False, "servicos": {}}
    for servico in servicos:
        corpo = {"api": servico, "ano": date.today().year}
        for variante, kwargs in [("POST json", {"json": corpo}), ("POST form", {"data": corpo}), ("GET", {"params": corpo})]:
            metodo = variante.split()[0]
            dados, oc, status = baixar_json(sessao, metodo, endpoint, tentativas=1, **kwargs)
            ocorrencias += [dict(o, mensagem=f"[{servico}, {variante}] {o['mensagem']}") for o in oc]
            erro_api = isinstance(dados, list) and dados and isinstance(dados[0], dict) and dados[0].get("status") == "erro"
            if dados is not None and not erro_api:
                arquivos.append((f"api_{servico}", dados, endpoint))
                lista = dados.get("dados") if isinstance(dados, dict) else dados
                tamanho = len(lista) if isinstance(lista, list) else None
                resumo["servicos"][servico] = {"variante": variante, "status_http": status, "itens": tamanho}
                resumo["sucesso"] = True
                break
        else:
            resumo["servicos"][servico] = {"variante": None, "erro": "nenhuma variante funcionou"}
    return arquivos, ocorrencias, resumo


ADAPTADORES = {"geosiap": geosiap, "modernizacao_webrun": modernizacao_webrun}
