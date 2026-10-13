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
# Textos de botao que nao dizem para onde vao. O rotulo passa a incluir o titulo do bloco (card) ao redor.
# Ex.: Betha mostra cards "Despesas publicas" com um botao "ACESSAR".
GENERICOS = {"acessar", "acesse", "acessar sistema", "saiba mais", "clique aqui", "ver mais", "veja mais", "leia mais",
             "consultar", "entrar", "abrir", "mais informacoes"}
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
        # alt das imagens dentro do elemento: banner "Portal da Transparencia" feito so de imagem (decidido em 13/10/2026)
        alts = [img.get("alt", "").strip() for img in el.find_all("img") if img.get("alt", "").strip()]
        rotulo = " ".join(filter(None, [texto, el.get("title", ""), el.get("aria-label", ""), *alts]))
        if normalizar(texto) in GENERICOS:
            # sobe ate 4 niveis procurando o bloco com titulo (h1 a h6) e usa os titulos como contexto
            bloco = el.parent
            for _ in range(4):
                if bloco is None:
                    break
                titulos = bloco.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
                if titulos:
                    rotulo = f"{texto} ({' '.join(t.get_text(' ', strip=True) for t in titulos)[:150]})"
                    break
                bloco = bloco.parent
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


def chave(texto):
    """Texto para comparacao: sem acento, minusculo e SEM espacos.

    Sem espacos porque o navegador e o leitor de HTML juntam pedacos do texto de jeitos diferentes
    (ex.: '<i>insert_chart</i><p>Despesas</p>' vira 'insert_chartDespesas' ou 'insert_chart Despesas').
    """
    return normalizar(texto).replace(" ", "")


def generico(candidato):
    return normalizar(candidato["texto"]) in GENERICOS


def melhores(candidatos, alvo, quantos=3, ignorar=(), visiveis=None):
    """Os candidatos com maior nota para o alvo (nota > 0). Em empate, o texto mais curto vem antes.

    ignorar: textos que nao podem ser escolhidos (ja clicados ou ja visiveis antes do clique anterior).
    Compara pelo texto E pelo rotulo (texto + title + aria-label), para nao escapar quando o elemento
    repete o texto no title (erro visto em Caxias: clicou duas vezes no mesmo item).
    Botao generico ("ACESSAR") e comparado so pelo rotulo, que inclui o titulo do card.

    visiveis: textos visiveis agora na tela. Se informado, elemento ESCONDIDO e SEM ENDERECO nao pode ser
    escolhido: o clique forcado nele nao funciona em todo portal (Betha: menu lateral fechado, nada acontece).
    Escondido COM endereco continua valendo, porque o coletor abre o endereco direto.
    """
    ignorar = {chave(t) for t in ignorar}
    visiveis = None if visiveis is None else {chave(t) for t in visiveis}

    def bloqueado(c):
        if generico(c):
            return chave(c["rotulo"]) in ignorar
        return chave(c["texto"]) in ignorar or chave(c["rotulo"]) in ignorar

    def alcancavel(c):
        return visiveis is None or c["destino"] or chave(c["texto"]) in visiveis or chave(c["rotulo"]) in visiveis

    notas = [(pontuar(c, alvo), c) for c in candidatos if not bloqueado(c) and alcancavel(c)]
    notas = [(n, c) for n, c in notas if n > 0]
    notas.sort(key=lambda par: (-par[0], len(par[1]["rotulo"])))
    return [dict(c, nota=n) for n, c in notas[:quantos]]


def mesmo_dominio_ou_permitido(url, dominios_permitidos):
    """True se o host da URL termina com algum dominio permitido (lista vazia = tudo permitido)."""
    host = urlparse(url).hostname or ""
    return not dominios_permitidos or any(host == d or host.endswith("." + d) for d in dominios_permitidos)
