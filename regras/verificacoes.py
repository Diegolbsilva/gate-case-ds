"""Regras de cada criterio: recebem UMA fonte (pagina HTML ou resposta de API) e dizem o que ela mostra.

Cada funcao devolve None quando a fonte nao e evidencia para o criterio (pagina errada, tabela que nao
carregou, API sem dados), ou um dicionario:
    {"status": "atende" | "parcial" | "nao_atende", "justificativa": texto curto, "trecho": o que foi lido,
     "detalhe": dados para a nota gradual do score}
Quem junta as fontes e escolhe o resultado final e regras/avaliar.py.

Regras decididas (docs/gate_descobertas.md, secao 4, e docs/decisoes_regras.md):
- 1.2: link do portal visivel na capa = Atende (rolar nao conta como clique); so no submenu = Parcial;
  capa carregada e nenhum texto clicavel relacionado a transparencia = Nao atende (decisao de 13/10/2026).
- 4.1: numero do empenho + valores empenhado, liquidado e pago, em colunas (formato largo) ou em linhas
  por fase (formato longo, Caxias). Le os CABECALHOS da tabela, nao o texto solto da pagina.
- 4.6: data mais recente dos dados (API) ou rotulo "dados atualizados ate/em" da pagina. Referencia legal:
  "tempo real" = ate o 1o dia util seguinte ao registro contabil (Decreto 10.540/2020, art. 7o, par. 1o, e
  Anexo incluido pelo Decreto 11.644/2023). Atende: ate 1 dia util de defasagem; Parcial: ate 30 dias
  corridos (criterio proprio do sistema, o decreto nao define parcial); Nao atende: mais de 30 dias (decisao de 13/10/2026).
- 12.1: periodo mais recente publicado, lido no titulo do relatorio, contra o ultimo que ja deveria
  estar publicado (prazo da LRF: 30 dias apos o fim do quadrimestre).
- 16.2: controle de "alto contraste" no HTML completo da capa do portal, inclusive em menus fechados.
"""
import re
import unicodedata
from datetime import date, datetime, timedelta

from bs4 import BeautifulSoup

# Feriados nacionais de 2026 (dias sem expediente na administracao publica), para contar dias uteis no 4.6.
# Inclui Carnaval e Corpus Christi (pontos facultativos de praxe). Lista fixa e documentada: em producao,
# viria de uma tabela de feriados por ano e por municipio.
FERIADOS = {date(2026, 1, 1), date(2026, 2, 16), date(2026, 2, 17), date(2026, 4, 3), date(2026, 4, 21),
            date(2026, 5, 1), date(2026, 6, 4), date(2026, 9, 7), date(2026, 10, 12), date(2026, 11, 2),
            date(2026, 11, 15), date(2026, 11, 20), date(2026, 12, 25)}
# Avaliando no dia D, o registro do ultimo dia util antes de D ainda esta no prazo (vence no proprio D).
# Ja o de qualquer dia util anterior a esse tem que estar publicado. Por isso: ate 1 dia util entre a data
# mais recente e D = Atende. Ex.: avaliacao em 13/10/2026 (12/10 feriado), dados ate 08/10: so 09/10 no meio.
ATENDE_ATE_DIAS_UTEIS = 1
PARCIAL_ATE_DIAS_CORRIDOS = 30
MESES = {"janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
         "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}
CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")


def normalizar(texto):
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def mascarar(texto):
    """Nunca gravar CPF completo numa evidencia."""
    return CPF.sub("***.***.***-**", texto or "")


def sopa_sem_script(html):
    sopa = BeautifulSoup(html, "html.parser")
    for el in sopa(["script", "style", "noscript", "template"]):
        el.decompose()
    return sopa


def texto_da_sopa(sopa):
    return re.sub(r"\s+", " ", sopa.get_text(" ", strip=True))


def dias_uteis_entre(inicio, fim):
    """Dias uteis depois de `inicio` e antes de `fim` (os dois excluidos)."""
    dias, d = 0, inicio + timedelta(days=1)
    while d < fim:
        if d.weekday() < 5 and d not in FERIADOS:
            dias += 1
        d += timedelta(days=1)
    return dias


# ---------------------------------------------------------------- 1.2

def regra_1_2(passo_portal, html_capa):
    """Fontes: o 1o passo da descoberta (linha da tabela descobertas, alvo 'portal') e o HTML da capa do site.

    Link nao achado = Nao atende, com duas travas (decisao de 13/10/2026):
    - a capa precisa ter carregado com conteudo (mais de 200 caracteres de texto) e sem captcha;
      senao, sem evidencia (Inconclusivo, ou Indisponivel se a capa nem abriu);
    - o robo le tambem o texto alternativo (alt) das imagens: banner "Portal da Transparencia" sem texto conta.
    """
    if not passo_portal or not passo_portal["sucesso"]:
        if not html_capa:
            return None
        sopa = sopa_sem_script(html_capa)
        if len(texto_da_sopa(sopa)) < 200 or sopa.select_one("iframe[src*=recaptcha], .g-recaptcha, [data-sitekey]"):
            return None  # capa nao carregou direito: nao da para afirmar que o link nao existe
        return {"status": "nao_atende",
                "justificativa": "Capa do site carregada e nenhum texto clicavel (inclusive alt de imagem) relacionado a transparencia",
                "trecho": texto_da_sopa(sopa)[:200], "detalhe": {"link_encontrado": False}}
    detalhe = {"cliques": 1, "visivel": bool(passo_portal["visivel_sem_interacao"]),
               "precisou_rolar": bool(passo_portal["precisou_rolar"]), "texto": passo_portal["texto_clicado"]}
    trecho = f"Link '{passo_portal['texto_clicado']}' na capa do site, leva a {passo_portal['url_destino']}"
    if detalhe["visivel"]:
        rolar = " (aparece depois de rolar a pagina)" if detalhe["precisou_rolar"] else ""
        return {"status": "atende", "justificativa": f"Link do portal visivel na capa, 1 clique{rolar}",
                "trecho": trecho, "detalhe": detalhe}
    return {"status": "parcial", "justificativa": "Link do portal na capa so dentro de submenu (escondido ate passar o mouse)",
            "trecho": trecho, "detalhe": detalhe}


# ---------------------------------------------------------------- 4.1

COLUNA_NUMERO = re.compile(r"(numero|nr\.?|n[o.]?)\s*(do |da )?empenho|nota de empenho|^empenho$|doc\.? despesa")
COLUNA_FASE = {"empenhado": re.compile(r"empenhad|valor do empenho|valor empenho"),
               "liquidado": re.compile(r"liquidad"),
               "pago": re.compile(r"\bpago\b|pagamento de rp")}


def cabecalhos(sopa):
    """Textos dos cabecalhos de tabela: <th>, role=columnheader e cabecalhos de grade Vaadin."""
    els = sopa.select("th, [role=columnheader], .v-grid-header .v-grid-cell, .v-table-caption-container")
    return [re.sub(r"\s+", " ", el.get_text(" ", strip=True)) for el in els if el.get_text(strip=True)]


def regra_4_1_pagina(html):
    sopa = sopa_sem_script(html)
    cols = cabecalhos(sopa)
    norm = [normalizar(c) for c in cols]
    tem_numero = any(COLUNA_NUMERO.search(c) for c in norm)
    fases = {f for f, rx in COLUNA_FASE.items() if any(rx.search(c) for c in norm)}
    # formato longo (uma linha por fase): valores Empenho / Liquidacao / Pagamento nas celulas
    celulas = {normalizar(td.get_text(" ", strip=True)) for td in sopa.select("td, [role=gridcell]")}
    if {"empenho", "liquidacao", "pagamento"} <= celulas:
        fases |= {"empenhado", "liquidado", "pago"}
    if not tem_numero and not fases:
        return None  # sem tabela de despesa legivel (formulario, carregando, pagina errada)
    detalhe = {"numero_empenho": tem_numero, "fases": sorted(fases), "colunas": cols[:30]}
    trecho = "Colunas: " + "; ".join(cols[:30])
    if tem_numero and len(fases) == 3:
        return {"status": "atende", "justificativa": "Tabela com numero do empenho e valores empenhado, liquidado e pago",
                "trecho": trecho, "detalhe": detalhe}
    faltam = (["numero do empenho"] if not tem_numero else []) + sorted({"empenhado", "liquidado", "pago"} - fases)
    return {"status": "parcial", "justificativa": "Tabela de despesa sem: " + ", ".join(faltam),
            "trecho": trecho, "detalhe": detalhe}


def regra_4_1_api(fornecedor, dados):
    if fornecedor == "geosiap":
        linhas = [r for v in dados.values() for r in v["resposta"].get("despesas_detalhadas", [])]
        campos = ["nr_doc_despesa", "vl_empenhado", "vl_liquidado", "vl_pago"]
    else:  # modernizacao_webrun: formato longo, uma linha por fase
        linhas = [r for r in dados.get("dados", []) if "TOTAL" not in (r.get("nome_secretria") or "").upper()]
        fases = {r.get("Despesa") for r in linhas}
        if not {"Empenho", "Liquidação", "Pagamento"} <= fases:
            return None
        campos = ["empenho", "Despesa", "valor_despesa"]
    completas = [r for r in linhas if all(r.get(c) not in (None, "") for c in campos)]
    if not completas:
        return None
    exemplo = {c: completas[0].get(c) for c in campos}
    return {"status": "atende", "justificativa": f"API do fornecedor: {len(completas)} registros com numero do empenho e valores por fase",
            "trecho": f"Campos {', '.join(campos)}; exemplo {exemplo}", "detalhe": {"registros": len(completas), "campos": campos}}


# ---------------------------------------------------------------- 4.6

ROTULO_ATUALIZACAO = re.compile(
    r"(dados atualizados (?:ate|em)|ultima atualizacao(?: dos dados)?(?: em)?(?: \(\w+\))?|data de atualizacao dos dados)"
    r"\s*:?\s*(\d{1,2}/\d{1,2}/\d{4}(?:\s+\d{1,2}:\d{2})?|\d{1,2} de [a-z]+ de \d{4})")


def ler_data(texto):
    """'09/10/2026', '09/10/2026 14:44' ou '06 de outubro de 2026' -> (date, hora ou None)."""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:\s+(\d{1,2}):(\d{2}))?", texto)
    if m:
        d = date(int(m[3]), int(m[2]), int(m[1]))
        return d, (datetime(d.year, d.month, d.day, int(m[4]), int(m[5])) if m[4] else None)
    m = re.match(r"(\d{1,2}) de ([a-z]+) de (\d{4})", texto)
    if m and m[2] in MESES:
        return date(int(m[3]), MESES[m[2]], int(m[1])), None
    return None, None


def classificar_atualizacao(data_dados, data_avaliacao, origem):
    dias_uteis = dias_uteis_entre(data_dados, data_avaliacao)
    dias_corridos = (data_avaliacao - data_dados).days
    detalhe = {"data_dados": data_dados.isoformat(), "data_avaliacao": data_avaliacao.isoformat(),
               "defasagem_dias_uteis": dias_uteis, "defasagem_dias_corridos": dias_corridos, "origem": origem}
    texto = f"Dados de {data_dados:%d/%m/%Y} ({origem}); {dias_uteis} dia(s) util(eis) de defasagem"
    if dias_uteis <= ATENDE_ATE_DIAS_UTEIS:
        return {"status": "atende", "justificativa": texto, "detalhe": detalhe}
    if dias_corridos <= PARCIAL_ATE_DIAS_CORRIDOS:
        return {"status": "parcial", "justificativa": texto, "detalhe": detalhe}
    return {"status": "nao_atende", "justificativa": texto, "detalhe": detalhe}


def regra_4_6_pagina(html, data_avaliacao, coletado_em):
    texto = normalizar(texto_da_sopa(sopa_sem_script(html)))
    for m in ROTULO_ATUALIZACAO.finditer(texto):
        d, hora = ler_data(m.group(2))
        if d is None or d > data_avaliacao:
            continue  # data invalida ou futura
        if hora and abs((hora - coletado_em).total_seconds()) < 15 * 60:
            continue  # carimbo da hora da visita, nao da carga dos dados (rodape de Japeri)
        resultado = classificar_atualizacao(d, data_avaliacao, f"rotulo '{m.group(1)}' na pagina")
        resultado["trecho"] = m.group(0)
        return resultado
    return None


def regra_4_6_api(fornecedor, dados, data_avaliacao, resumo):
    if fornecedor == "geosiap":
        datas = [r.get("dt_doc_despesa") for v in dados.values() for r in v["resposta"].get("despesas_detalhadas", [])]
    else:
        datas = [r.get("data_despesa") for r in dados.get("dados", [])
                 if "TOTAL" not in (r.get("nome_secretria") or "").upper()]  # linhas de total tem data do fim do mes
    datas = [date.fromisoformat(d[:10]) for d in datas if d]
    datas = [d for d in datas if d <= data_avaliacao]
    if not datas:
        return None
    resultado = classificar_atualizacao(max(datas), data_avaliacao, "data mais recente dos registros da API")
    sem_resposta = (resumo or {}).get("entidades_sem_resposta")
    if sem_resposta:
        # Com entidade sem resposta, a data maxima vista e so um minimo: a real e igual ou mais recente.
        # Atende continua provado; Parcial ou Nao atende nao (decisao de 15/10/2026, opcao B).
        if resultado["status"] != "atende":
            return {"nao_evidencia": f"API sem resposta de {', '.join(sem_resposta)}; a data vista "
                                     f"({max(datas):%d/%m/%Y}) daria {resultado['status']}, mas a real pode ser mais recente"}
        resultado["detalhe"]["entidades_sem_resposta"] = sem_resposta
        resultado["justificativa"] += f" (sem resposta da API: {', '.join(sem_resposta)})"
    resultado["trecho"] = f"Data maxima entre {len(datas)} registros: {max(datas):%d/%m/%Y}"
    return resultado


# ---------------------------------------------------------------- 12.1

QUADRIMESTRE = re.compile(r"(?<!\d)0?([123])\s*(?:o|º|°|ª|a)?\s*quadrimestre(?:\s*(?:/|de|-|do ano)?\s*(20\d\d))?", re.I)
ANO_TITULO = re.compile(r"(?:exercicio|ano)\s*:?\s*(20\d\d)", re.I)


def periodo_devido(data_avaliacao):
    """Ultimo quadrimestre cujo prazo de publicacao (30 dias apos o fim) ja passou. Devolve (ano, q)."""
    candidatos = []
    for ano in (data_avaliacao.year - 1, data_avaliacao.year):
        candidatos += [((ano, 1), date(ano, 5, 30)), ((ano, 2), date(ano, 9, 30)), ((ano, 3), date(ano + 1, 1, 30))]
    return max(p for p, prazo in candidatos if prazo < data_avaliacao)


def classificar_rgf(periodos, data_avaliacao, origem):
    devido = periodo_devido(data_avaliacao)
    ultimo = max(periodos)
    atraso = max(0, (devido[0] * 3 + devido[1]) - (ultimo[0] * 3 + ultimo[1]))
    detalhe = {"ultimo_publicado": f"{ultimo[1]}o quadrimestre de {ultimo[0]}",
               "devido": f"{devido[1]}o quadrimestre de {devido[0]}", "quadrimestres_de_atraso": atraso,
               "periodos": sorted({f"{a}-Q{q}" for a, q in periodos}), "origem": origem}
    texto = f"RGF mais recente: {ultimo[1]}o quadrimestre de {ultimo[0]}; devido: {devido[1]}o de {devido[0]}"
    return {"status": "atende" if atraso == 0 else "parcial",
            "justificativa": texto + (f" ({atraso} quadrimestre(s) de atraso)" if atraso else ""), "detalhe": detalhe}


def regra_12_1_pagina(html, data_avaliacao, url):
    """Le os periodos publicados. Ano: o que vem junto do quadrimestre ('2o Quadrimestre / 2026');
    se a pagina nao traz o ano junto, o ultimo 'Exercicio: 2026' / 'Ano 2026' antes dele, ou o ano da URL.
    So conta periodo com link para o arquivo: o Rio lista o 3o quadrimestre ainda sem link."""
    sopa = sopa_sem_script(html)
    texto_pagina = normalizar(texto_da_sopa(sopa))
    if not re.search(r"gestao fiscal|\brgf\b", texto_pagina):
        return None
    # "pagina do RGF" para fins de Nao atende: titulo ou cabecalho fala do RGF. Uma pagina que so cita
    # "gestao fiscal" (Rio: "Plano de execucoes orcamentaria e de gestao fiscal") nao prova ausencia.
    titulos = normalizar(" ".join(el.get_text(" ") for el in sopa.select("title, h1, h2")))
    pagina_do_rgf = bool(re.search(r"relatorio de gestao fiscal|\brgf\b", titulos))
    # Tambem nao prova ausencia: pagina com captcha visivel (o conteudo esta atras dele) ou com o conteudo
    # dentro de uma moldura (iframe), que e salva e avaliada como arquivo proprio (Caxias: Webrun).
    if sopa.select_one("iframe[src*=recaptcha], .g-recaptcha, [data-sitekey]") or \
            any(f.get("src") not in (None, "", "about:blank") for f in sopa.find_all("iframe")):
        pagina_do_rgf = False
    ano_url = re.search(r"(20\d\d)", url or "")
    achados, com_ano_junto, ano_atual = [], False, (int(ano_url[1]) if ano_url else None)
    for no in sopa.find_all(string=True):
        if any("display:none" in (p.get("style") or "").replace(" ", "") for p in no.parents):
            continue  # tabela escondida (Itaborai tem uma copia oculta da lista, so para exportar CSV)
        trecho = normalizar(str(no))
        for m in ANO_TITULO.finditer(trecho):
            ano_atual = int(m[1])
        for m in QUADRIMESTRE.finditer(trecho):
            # link: procura so no ITEM do periodo, nao na pagina toda. Sobe a partir do texto ate achar um
            # <a>, um botao ou "ver arquivos", parando quando o bloco ja contem outro quadrimestre (passou do item).
            # Rio: cada periodo e um <p>; "1o Quadrimestre" e um <a>, "3o Quadrimestre" e texto puro (nao publicado).
            # Japeri: <a> sem href (clique por JavaScript) na mesma linha da tabela. Itaborai: card com titulo e
            # botao "Ver mais detalhes". Betha: linha com "Ver arquivos".
            tem_link, bloco = bool(no.find_parent("a")), no.parent
            for _ in range(6):
                if tem_link or bloco is None:
                    break
                if len({x[1] for x in QUADRIMESTRE.finditer(normalizar(bloco.get_text(" ")))}) > 1:
                    break
                tem_link = bool(bloco.find(["a", "button"]) or "ver arquivo" in normalizar(bloco.get_text(" ")))
                bloco = bloco.parent
            if m[2]:
                com_ano_junto = True
            achados.append({"q": int(m[1]), "ano": int(m[2]) if m[2] else ano_atual, "ano_junto": bool(m[2]),
                            "link": tem_link, "texto": str(no).strip()[:80]})
    # se a pagina escreve o ano junto em algum lugar, usa so esses (evita parear com um ano solto errado)
    validos = [a for a in achados if a["ano"] and a["link"] and (a["ano_junto"] or not com_ano_junto)]
    if not validos:
        if achados or not pagina_do_rgf:
            return None  # cita quadrimestres sem ano ou sem link legivel, ou nao e a pagina do RGF
        return {"status": "nao_atende", "justificativa": "Pagina do RGF sem nenhum relatorio por quadrimestre",
                "trecho": texto_pagina[:200], "detalhe": {"periodos": []}}
    resultado = classificar_rgf([(a["ano"], a["q"]) for a in validos], data_avaliacao, "titulos dos relatorios na pagina")
    sem_link = sorted({f"{a['ano']}-Q{a['q']}" for a in achados if not a["link"] and a["ano"]})
    if sem_link:
        resultado["detalhe"]["listados_sem_link"] = sem_link
    ultimo = max(validos, key=lambda a: (a["ano"], a["q"]))
    resultado["trecho"] = ultimo["texto"]
    return resultado


def regra_12_1_api(dados, data_avaliacao):
    """API Webrun (consulta_rgf_m2): um registro por demonstrativo, com RGF_ANO e RGF_QUADRIMESTRE."""
    lista = dados.get("dados", []) if isinstance(dados, dict) else []
    periodos = [(int(r["RGF_ANO"]), int(r["RGF_QUADRIMESTRE"])) for r in lista
                if str(r.get("RGF_ANO", "")).isdigit() and str(r.get("RGF_QUADRIMESTRE", "")).isdigit()]
    if not periodos:
        return None
    resultado = classificar_rgf(periodos, data_avaliacao, "API do fornecedor (consulta_rgf_m2)")
    ultimo = max(periodos)
    n = sum(1 for p in periodos if p == ultimo)
    resultado["trecho"] = f"{n} demonstrativo(s) do {ultimo[1]}o quadrimestre de {ultimo[0]}"
    return resultado


# ---------------------------------------------------------------- 16.2

CONTRASTE = re.compile(r"contraste|high-contrast|alto-contraste", re.I)


def regra_16_2_pagina(html):
    """Procura um controle de alto contraste: texto proprio do elemento ou title/aria-label/data-*.
    Classe CSS sozinha nao conta (estilo pode existir sem o botao), exceto 'high-contrast'."""
    sopa = sopa_sem_script(html)
    if len(texto_da_sopa(sopa)) < 200:
        return None  # pagina nao carregou
    for el in sopa.find_all(True):
        if el.name in ("img", "svg", "path", "link", "meta"):
            continue
        proprio = " ".join(el.find_all(string=True, recursive=False)).strip()
        attrs = " ".join(str(v) for k, v in el.attrs.items()
                         if k in ("title", "aria-label", "data-original-title", "data-action", "alt"))
        classe = " ".join(el.get("class", []))
        if CONTRASTE.search(proprio) or CONTRASTE.search(attrs) or "high-contrast" in classe:
            achado = (proprio or attrs or classe)[:100]
            return {"status": "atende", "justificativa": "Controle de alto contraste no portal",
                    "trecho": f"<{el.name}> {achado}", "detalhe": {"elemento": el.name, "texto": achado}}
    return {"status": "nao_atende", "justificativa": "Nenhum controle de alto contraste no HTML completo da capa do portal",
            "trecho": "", "detalhe": {}}


# ---------------------------------------------------------------- grau de confianca (secao 4 do enunciado)

def nivel_confianca(status, detalhe):
    """Grau de confianca do veredito, pela natureza da evidencia (decisao de 16/10/2026). Vale para os 6 criterios.
    A presenca de uma informacao se prova com um trecho; a ausencia depende de o sistema ter olhado no lugar certo.
    - alta: o que foi lido prova o veredito (Atende com trecho conferido; 4.6 com a data lida no rotulo da pagina;
      Indisponivel com os erros de acesso registrados);
    - media: o veredito depende de ausencia (Nao atende; Parcial por falta de item, de subitem ou de periodo) ou de
      valor inferido (4.6 Parcial pela data mais recente dos registros da API: pode nao ter havido despesa no dia);
    - None: sem veredito (Inconclusivo) ou fora da avaliacao (Nao aplicavel): o "quando aplicavel" do enunciado."""
    if status in ("inconclusivo", "nao_aplicavel"):
        return None
    if status in ("atende", "indisponivel"):
        return "alta"
    if str((detalhe or {}).get("origem", "")).startswith("rotulo "):
        return "alta"  # 4.6: "dados atualizados ate DD/MM" lido na pagina; a defasagem e conta, nao inferencia
    return "media"
