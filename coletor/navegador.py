"""Abrir paginas com novas tentativas e salvar o que foi visto (HTML + print da pagina inteira)."""
import hashlib
import time
from pathlib import Path

from playwright.sync_api import Error as ErroPlaywright
from playwright.sync_api import TimeoutError as TempoEsgotado

from coletor.banco import agora
from coletor.descoberta import GENERICOS, normalizar

# Textos que indicam erro mesmo quando o servidor responde com HTTP 200 (ex.: modal de erro em Caxias).
TEXTOS_ERRO = {
    "erro_servidor": ["Internal Server Error", "Network error IOException", "Service Unavailable", "Bad Gateway"],
    "bloqueio": ["403 Forbidden", "Access Denied", "Acesso negado"],
}


def abrir_pagina(pagina, url, tentativas, espera_inicial_s=5, espera_js_ms=3000):
    """Abre a URL; em caso de erro, tenta de novo com intervalo crescente (5 s, 15 s, 45 s...).

    Devolve (resposta, ocorrencias). resposta = None quando todas as tentativas falharam:
    nesse caso o criterio fica 'indisponivel' e a proxima execucao tenta de novo.
    """
    ocorrencias = []
    for n in range(1, tentativas + 1):
        tipo, mensagem, resposta = None, None, None
        try:
            resposta = pagina.goto(url, wait_until="load", timeout=60000)
            pagina.wait_for_timeout(espera_js_ms)  # tempo para o JavaScript montar a pagina
            status = resposta.status if resposta else None
            texto = pagina.inner_text("body")[:20000] if pagina.query_selector("body") else ""
            if status is not None and status >= 400:
                tipo = "bloqueio" if status in (401, 403) else ("erro_servidor" if status >= 500 else "erro_http")
                mensagem = f"HTTP {status}"
            for tipo_erro, textos in TEXTOS_ERRO.items():
                achado = next((t for t in textos if t.lower() in texto.lower()), None)
                if tipo is None and achado:
                    tipo, mensagem = tipo_erro, f"Texto de erro na pagina: {achado}"
        except TempoEsgotado:
            tipo, mensagem = "timeout", "Pagina nao carregou em 60 s"
        except ErroPlaywright as erro:
            tipo, mensagem = "erro_http", str(erro).splitlines()[0][:300]

        if tipo is None:
            return resposta, ocorrencias
        ocorrencias.append({"url": url, "tipo": tipo, "mensagem": mensagem, "tentativa": n, "ocorrido_em": agora()})
        if n < tentativas:
            time.sleep(espera_inicial_s * 3 ** (n - 1))
    return None, ocorrencias


def salvar_pagina(pagina, resposta, url, pasta, nome, papel):
    """Salva o HTML renderizado e o print da pagina inteira. Devolve a lista de artefatos para o banco."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    coletado_em = agora()
    status = resposta.status if resposta else None

    arquivos = []
    for i, frame in enumerate(pagina.frames):
        if i > 0 and frame.url in ("", "about:blank"):
            continue
        try:
            html = frame.content().encode("utf-8")
        except ErroPlaywright:
            continue
        caminho_html = pasta / (f"{nome}.html" if i == 0 else f"{nome}_frame{i}.html")
        caminho_html.write_bytes(html)
        arquivos.append(("html", caminho_html, html, frame.url))

    caminho_png = pasta / f"{nome}.png"
    pagina.screenshot(path=str(caminho_png), full_page=True)
    arquivos.append(("png", caminho_png, caminho_png.read_bytes(), pagina.url))

    return [
        {"papel": papel, "url": url, "url_final": url_final, "tipo": tipo, "caminho": str(caminho),
         "hash_sha256": hashlib.sha256(conteudo).hexdigest(), "tamanho_bytes": len(conteudo),
         "status_http": status, "coletado_em": coletado_em}
        for tipo, caminho, conteudo, url_final in arquivos
    ]


def html_dos_frames(pagina):
    """[(indice_do_frame, html, url)] da pagina principal e dos iframes com conteudo."""
    saida = []
    for i, frame in enumerate(pagina.frames):
        if i > 0 and frame.url in ("", "about:blank"):
            continue
        try:
            saida.append((i, frame.content(), frame.url))
        except ErroPlaywright:
            pass
    return saida


JS_TEXTOS_VISIVEIS = """sel => Array.from(document.querySelectorAll(sel)).filter(e => {
    const r = e.getBoundingClientRect();
    const rendered = e.checkVisibility ? e.checkVisibility({checkOpacity: true, checkVisibilityCSS: true})
                                       : e.getClientRects().length > 0;
    return rendered && r.width > 0 && r.height > 0;
}).flatMap(e => [e.innerText || e.textContent || '', e.getAttribute('title') || '', e.getAttribute('aria-label') || ''])
  .filter(t => t.trim().length > 0)"""


def texto_da_pagina(pagina):
    """Texto visivel de todas as molduras, para saber se um clique mudou alguma coisa."""
    partes = []
    for frame in pagina.frames:
        try:
            partes.append(frame.inner_text("body", timeout=5000))
        except ErroPlaywright:
            pass
    return hashlib.sha256("\n".join(partes).encode("utf-8")).hexdigest()


def textos_visiveis(pagina, seletor):
    """Textos dos elementos clicaveis VISIVEIS agora (todas as molduras). Usado para saber o que um clique revelou."""
    textos = []
    for frame in pagina.frames:
        try:
            textos += frame.evaluate(JS_TEXTOS_VISIVEIS, seletor)
        except ErroPlaywright:
            pass
    return textos


SELETORES_FECHAR = ['[aria-label*="fechar" i]', '[aria-label*="close" i]', 'button.close', '.btn-close',
                    '.modal [data-dismiss="modal"]', '.modal [data-bs-dismiss="modal"]', '[class*="popup"] [class*="close"]']


def fechar_popups(pagina):
    """Tenta fechar pop-ups que cobrem a pagina (Esc e botoes de fechar comuns). Devolve quantos fechou."""
    fechados = 0
    pagina.keyboard.press("Escape")
    for seletor in SELETORES_FECHAR:
        for el in pagina.locator(seletor).all()[:3]:
            try:
                if el.is_visible():
                    el.click(timeout=2000)
                    fechados += 1
            except ErroPlaywright:
                pass
    if fechados:
        pagina.wait_for_timeout(1000)
    return fechados


def examinar_elemento(pagina, candidato):
    """Ao vivo: o elemento do candidato esta visivel sem interacao? Precisa rolar para aparecer?"""
    frame = pagina.frames[candidato.get("frame", 0)]
    el = frame.locator(candidato["css"]).first
    if el.count() == 0:
        return {"encontrado": False, "visivel": None, "precisa_rolar": None}
    visivel = el.is_visible()
    caixa = el.bounding_box() if visivel else None
    altura = pagina.viewport_size["height"] if pagina.viewport_size else 768
    rolagem = pagina.evaluate("window.scrollY") if visivel else 0
    precisa_rolar = bool(caixa and caixa["y"] + rolagem > altura)
    return {"encontrado": True, "visivel": visivel, "precisa_rolar": precisa_rolar}


def seguir(contexto, pagina, candidato, tentativas):
    """Vai ao destino do candidato: abre o endereco se ele existe; senao clica no elemento.

    Devolve (pagina_resultante, modo, ocorrencias). modo: 'endereco', 'mesma_aba', 'nova_aba';
    em falha, pagina None e modo None ou 'sem_efeito' (clicou e nada mudou: mesmo endereco e mesmo texto na tela).
    """
    if candidato.get("destino"):
        nova = contexto.new_page()
        resposta, ocorrencias = abrir_pagina(nova, candidato["destino"], tentativas)
        if resposta is None:
            nova.close()
            return None, None, ocorrencias
        return nova, "endereco", ocorrencias

    frame = pagina.frames[candidato.get("frame", 0)]
    el = frame.locator(candidato["css"]).first
    if el.count() == 0:
        el = frame.get_by_text(candidato["texto"], exact=True).first
    if el.count() == 0:
        return None, None, [{"url": pagina.url, "tipo": "layout_inesperado", "tentativa": 1, "ocorrido_em": agora(),
                             "mensagem": f"Elemento nao encontrado ao vivo: {candidato['texto'][:80]}"}]
    if not el.is_visible() and normalizar(candidato["texto"]) not in GENERICOS:
        # o mesmo texto pode existir escondido (menu lateral) e visivel (lista na tela): usa o visivel
        gemeos = frame.get_by_text(candidato["texto"], exact=True)
        for i in range(min(gemeos.count(), 10)):
            if gemeos.nth(i).is_visible():
                el = gemeos.nth(i)
                break
    abas_antes = len(contexto.pages)
    antes = (pagina.url, texto_da_pagina(pagina))
    try:
        if el.is_visible():
            el.scroll_into_view_if_needed(timeout=5000)
            el.click(timeout=10000)
        else:
            el.dispatch_event("click")  # item de submenu escondido: dispara o clique sem abrir o menu
    except ErroPlaywright as erro:
        return None, None, [{"url": pagina.url, "tipo": "layout_inesperado", "tentativa": 1, "ocorrido_em": agora(),
                             "mensagem": f"Clique falhou em '{candidato['texto'][:60]}': {str(erro).splitlines()[0][:200]}"}]
    pagina.wait_for_timeout(4000)
    if len(contexto.pages) > abas_antes:
        nova = contexto.pages[-1]
        try:
            nova.wait_for_load_state("load", timeout=60000)
        except TempoEsgotado:
            pass
        nova.wait_for_timeout(3000)
        return nova, "nova_aba", []
    if (pagina.url, texto_da_pagina(pagina)) == antes:
        return None, "sem_efeito", [{"url": pagina.url, "tipo": "layout_inesperado", "tentativa": 1, "ocorrido_em": agora(),
                                     "mensagem": f"Clique sem efeito em '{candidato['texto'][:60]}': a pagina nao mudou"}]
    return pagina, "mesma_aba", []
