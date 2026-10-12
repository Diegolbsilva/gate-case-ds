"""Abrir paginas com novas tentativas e salvar o que foi visto (HTML + print da pagina inteira)."""
import hashlib
import time
from pathlib import Path

from playwright.sync_api import Error as ErroPlaywright
from playwright.sync_api import TimeoutError as TempoEsgotado

from coletor.banco import agora

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

    html = pagina.content().encode("utf-8")
    caminho_html = pasta / f"{nome}.html"
    caminho_html.write_bytes(html)

    caminho_png = pasta / f"{nome}.png"
    pagina.screenshot(path=str(caminho_png), full_page=True)
    png = caminho_png.read_bytes()

    return [
        {"papel": papel, "url": url, "url_final": pagina.url, "tipo": tipo, "caminho": str(caminho),
         "hash_sha256": hashlib.sha256(conteudo).hexdigest(), "tamanho_bytes": len(conteudo),
         "status_http": status, "coletado_em": coletado_em}
        for tipo, caminho, conteudo in [("html", caminho_html, html), ("png", caminho_png, png)]
    ]
