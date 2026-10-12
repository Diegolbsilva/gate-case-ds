"""Descoberta automatica: a partir de uma pagina, encontrar onde clicar para chegar a cada alvo.

Funciona com qualquer fornecedor porque trabalha com TEXTOS CLICAVEIS, nao so com links:
os portais montam menus de jeitos diferentes (links comuns, links '#' abertos por JavaScript,
blocos clicaveis sem link). Cada candidato guarda o caminho CSS do elemento; ao vivo,
o coletor vai direto ao endereco quando ele existe ou clica no elemento e registra para onde foi.

Os termos vem do proprio checklist (ex.: 4.1 'empenho, liquidacao e pagamento') e de sinonimos
comuns nos portais. Nao ha termo especifico de um municipio.
"""
import re
import unicodedata
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

# (termo, peso). Termos sem acento e em minusculas; comparados com limite de palavra.
TERMOS = {
    "portal": [("portal da transparencia", 10), ("portal de transparencia", 10), ("transparencia", 5)],
    "despesa": [("execucao detalhada de despesas", 10), ("despesas detalhadas", 10), ("detalhamento das despesas", 9),
                ("empenho", 6), ("liquidacao", 4), ("pagamento", 3), ("despesas", 6), ("despesa", 5),
                ("execucao orcamentaria", 5)],
    "rgf": [("relatorio de gestao fiscal", 10), ("rgf", 10), ("gestao fiscal", 8), ("relatorios fiscais", 6),
            ("responsabilidade fiscal", 5), ("lrf", 5), ("prestacao de contas", 4), ("relatorios", 2)],
    "esic": [("prazos de respostas do sic", 10), ("e-sic", 8), ("esic", 8), ("pedido de informacao", 8),
             ("acesso a informacao", 6), ("sic", 6), ("lei de acesso", 4), ("ouvidoria", 2)],
}
# Termos que indicam recorte ou outro assunto: cada um tira pontos.
NEGATIVOS = {
    "portal": ["radar", "tce", "saude", "sus", "camara", "legislativo", "diario", "boletim", "ouvidoria", "contribuinte"],
    "despesa": ["multa", "transito", "pessoal", "diaria", "extraorcament", "covid", "cedae", "emenda", "educacao",
                "credor", "programas", "folha", "receita"],
    "rgf": ["rreo", "resumido", "balanco", "4.320", "9.755", "opcionais", "terceiro setor", "saude"],
    "esic": ["lgpd", "estatistic", "sigilo", "carta de servicos", "satisfacao"],
}
PENALIDADE_NEGATIVO = 6
# Elementos que costumam ser clicaveis em qualquer fornecedor.
SELETOR_CLICAVEL = "a, button, [onclick], [role=button], [role=link], [ng-click], [data-rellink], dxi-item, li"
ONCLICK_URL = re.compile(r"""(?:location\.href\s*=|window\.open\()\s*['"]([^'"]+)['"]""")


def normalizar(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def caminho_css(el):
    """Caminho CSS unico do elemento (tag:nth-of-type desde a raiz), para achar o mesmo elemento ao vivo."""
    partes = []
    while el is not None and el.name not in (None, "[document]"):
        irmaos = [i for i in el.parent.find_all(el.name, recursive=False)] if el.parent else [el]
        partes.append(f"{el.name}:nth-of-type({irmaos.index(el) + 1})")
        el = el.parent
    return " > ".join(reversed(partes))


def extrair_candidatos(html, url_base, frame=0):
    """Lista de textos clicaveis da pagina, com endereco (quando existe no HTML) e caminho CSS."""
    sopa = BeautifulSoup(html, "html.parser")
    vistos, candidatos = {}, []
    for el in sopa.select(SELETOR_CLICAVEL):
        if el.find_parent(["script", "style", "noscript", "template"]):
            continue
        texto = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
        rotulo = " ".join(filter(None, [texto, el.get("title", ""), el.get("aria-label", "")]))
        if not (3 <= len(texto) <= 120 or 3 <= len(rotulo) <= 120):
            continue
        href = el.get("href") or ""
        destino = None
        if (href and not href.startswith(("#", "javascript", "mailto:", "tel:"))) or href.startswith("#/"):
            destino = urljoin(url_base, href)
        achado = ONCLICK_URL.search(el.get("onclick", ""))
        if destino is None and achado:
            destino = urljoin(url_base, achado.group(1))
        chave = normalizar(rotulo)
        if chave in vistos:
            # mesmo texto ja visto (ex.: <li> e o <a> dentro dele): fica o que tem endereco
            anterior = vistos[chave]
            if anterior["destino"] is None and destino:
                anterior.update(destino=destino, css=caminho_css(el))
            continue
        candidato = {"texto": texto or rotulo, "rotulo": rotulo, "destino": destino, "tag": el.name,
                     "css": caminho_css(el), "frame": frame}
        vistos[chave] = candidato
        candidatos.append(candidato)
    return candidatos


def pontuar(candidato, alvo):
    rotulo = normalizar(candidato["rotulo"])
    pontos = sum(peso for termo, peso in TERMOS[alvo] if re.search(rf"(?<![a-z0-9]){re.escape(termo)}(?![a-z0-9])", rotulo))
    pontos -= PENALIDADE_NEGATIVO * sum(1 for termo in NEGATIVOS[alvo] if termo in rotulo)
    return pontos


def melhores(candidatos, alvo, quantos=3, ignorar=()):
    """Os candidatos com maior nota para o alvo (nota > 0). Em empate, o texto mais curto vem antes."""
    ignorar = {normalizar(t) for t in ignorar}
    notas = [(pontuar(c, alvo), c) for c in candidatos if normalizar(c["rotulo"]) not in ignorar]
    notas = [(n, c) for n, c in notas if n > 0]
    notas.sort(key=lambda par: (-par[0], len(par[1]["rotulo"])))
    return [dict(c, nota=n) for n, c in notas[:quantos]]


def mesmo_dominio_ou_permitido(url, dominios_permitidos):
    """True se o host da URL termina com algum dominio permitido (lista vazia = tudo permitido)."""
    host = urlparse(url).hostname or ""
    return not dominios_permitidos or any(host == d or host.endswith("." + d) for d in dominios_permitidos)
